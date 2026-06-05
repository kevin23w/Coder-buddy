"""
FastAPI backend for Coder Buddy — v2.

Endpoints:
  POST /analyze         — single repo pipeline + GitHub PR + notifications
  POST /analyze/batch   — run agent on multiple repos concurrently
  GET  /health          — liveness check with integration status
"""
import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.schemas.models import (
    AnalyzeRequest,
    AnalyzeResponse,
    BatchAnalyzeRequest,
    BatchAnalyzeResponse,
    CommitProposal,
    GitHubPRInfo,
    HealthResponse,
    NotificationInfo,
    TestResult,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Validate critical settings and compile the agent on startup."""
    logger.info("🚀 Coder Buddy API v2 starting up…")

    if not settings.GROQ_API_KEY or settings.GROQ_API_KEY == "your_groq_api_key_here":
        raise RuntimeError("GROQ_API_KEY must be configured before starting.")

    from app.agent.graph import agent  # noqa: F401 — triggers compilation

    logger.info("✅ Agent compiled | GitHub=%s | Slack=%s | Discord=%s",
                settings.github_enabled, settings.slack_enabled, settings.discord_enabled)
    yield
    logger.info("🛑 Coder Buddy API shutting down")


# ---------------------------------------------------------------------------
# Rate limiter
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT])


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Coder Buddy API",
    description="Autonomous AI software engineer powered by LangGraph + Groq — v2",
    version="2.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    logger.info("→ %s %s", request.method, request.url.path)
    response = await call_next(request)
    elapsed = (time.perf_counter() - start) * 1000
    logger.info("← %s %s | %d | %.1fms", request.method, request.url.path, response.status_code, elapsed)
    return response


# ---------------------------------------------------------------------------
# Helper: run integrations after agent completes
# ---------------------------------------------------------------------------

def _run_integrations(
    result: dict,
    repo_path: str,
    create_pr: bool,
    notify_slack: bool,
    notify_discord: bool,
) -> tuple[GitHubPRInfo, NotificationInfo]:
    """
    Synchronously run GitHub PR creation and/or notifications.
    Called after a successful agent run.
    """
    gh_info    = GitHubPRInfo()
    notif_info = NotificationInfo()

    commit = result.get("commit_proposal", {})
    plan   = result.get("plan", [])
    test   = result.get("test_result", {})
    success = test.get("passed", False)

    commit_msg = commit.get("message", "fix: apply Coder Buddy fixes")
    pr_body    = commit.get("pr_body", "")
    pr_url     = ""

    # ── GitHub PR ────────────────────────────────────────────────────────────
    if create_pr and settings.github_enabled and success:
        from app.integrations.github_pr import create_github_pr
        pr_result = create_github_pr(
            repo_path=repo_path,
            commit_message=commit_msg,
            pr_body=pr_body,
            github_token=settings.GITHUB_TOKEN,
            github_repo=settings.GITHUB_REPO,
            base_branch=settings.GITHUB_BASE_BRANCH,
        )
        gh_info = GitHubPRInfo(
            created=pr_result.success,
            pr_url=pr_result.pr_url,
            pr_number=pr_result.pr_number,
            branch_name=pr_result.branch_name,
            error=pr_result.error,
        )
        pr_url = pr_result.pr_url if pr_result.success else ""
        logger.info("[main] GitHub PR: %s", gh_info)
    elif create_pr and not settings.github_enabled:
        gh_info = GitHubPRInfo(error="GITHUB_TOKEN / GITHUB_REPO not configured in .env")

    # ── Slack ─────────────────────────────────────────────────────────────────
    if notify_slack and settings.slack_enabled:
        from app.integrations.notifications import send_slack_notification
        sr = send_slack_notification(
            webhook_url=settings.SLACK_WEBHOOK_URL,
            repo_path=repo_path,
            success=success,
            plan=plan,
            test_output=test.get("output", ""),
            commit_message=commit_msg,
            pr_url=pr_url,
            iterations=result.get("iteration", 0),
        )
        notif_info.slack_sent  = sr.success
        notif_info.slack_error = sr.error
    elif notify_slack and not settings.slack_enabled:
        notif_info.slack_error = "SLACK_WEBHOOK_URL not configured in .env"

    # ── Discord ───────────────────────────────────────────────────────────────
    if notify_discord and settings.discord_enabled:
        from app.integrations.notifications import send_discord_notification
        dr = send_discord_notification(
            webhook_url=settings.DISCORD_WEBHOOK_URL,
            repo_path=repo_path,
            success=success,
            plan=plan,
            test_output=test.get("output", ""),
            commit_message=commit_msg,
            pr_url=pr_url,
            iterations=result.get("iteration", 0),
        )
        notif_info.discord_sent  = dr.success
        notif_info.discord_error = dr.error
    elif notify_discord and not settings.discord_enabled:
        notif_info.discord_error = "DISCORD_WEBHOOK_URL not configured in .env"

    return gh_info, notif_info


# ---------------------------------------------------------------------------
# Helper: run single repo through the agent
# ---------------------------------------------------------------------------

async def _run_single(repo_path: str, instructions: str) -> dict:
    """Validate path and invoke the LangGraph agent for one repo."""
    from app.agent.graph import agent

    abs_path = os.path.abspath(repo_path)

    if not os.path.isdir(abs_path):
        raise HTTPException(
            status_code=400,
            detail=f"repo_path does not exist or is not a directory: {abs_path}",
        )
    if not settings.is_repo_path_allowed(abs_path):
        raise HTTPException(
            status_code=403,
            detail="Access to this path is not permitted. Configure ALLOWED_REPO_PATHS.",
        )

    initial_state = {
        "repo_path": abs_path,
        "user_instructions": instructions,
        "plan": [],
        "files_read": {},
        "proposed_fix": {},
        "test_result": {},
        "commit_proposal": {},
        "iteration": 0,
        "error": None,
    }

    logger.info("Agent start | repo=%s", abs_path)
    return await agent.ainvoke(initial_state)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health():
    """Liveness check — returns model info and integration status."""
    return HealthResponse(
        status="ok",
        model="llama-3.3-70b-versatile",
        max_retries=settings.MAX_RETRIES,
        github_enabled=settings.github_enabled,
        slack_enabled=settings.slack_enabled,
        discord_enabled=settings.discord_enabled,
    )


@app.post("/analyze", response_model=AnalyzeResponse, tags=["Agent"])
@limiter.limit(settings.RATE_LIMIT)
async def analyze(request: Request, body: AnalyzeRequest):
    """
    Run the full Coder Buddy pipeline on a single Python repository.

    Optionally:
    - Opens a GitHub Pull Request (set create_github_pr=true + configure .env).
    - Sends a Slack / Discord notification on completion.
    """
    try:
        result = await _run_single(body.repo_path, body.instructions)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Agent pipeline error: %s", exc)
        raise HTTPException(status_code=500, detail=f"Agent pipeline failed: {exc}")

    abs_path = os.path.abspath(body.repo_path)
    gh_info, notif_info = _run_integrations(
        result=result,
        repo_path=abs_path,
        create_pr=body.create_github_pr,
        notify_slack=body.notify_slack,
        notify_discord=body.notify_discord,
    )

    raw_test   = result.get("test_result", {})
    raw_commit = result.get("commit_proposal", {})

    return AnalyzeResponse(
        plan=result.get("plan", []),
        test_result=TestResult(
            passed=raw_test.get("passed", False),
            output=raw_test.get("output", ""),
        ),
        commit_proposal=CommitProposal(
            message=raw_commit.get("message", ""),
            diff=raw_commit.get("diff", ""),
            pr_body=raw_commit.get("pr_body", ""),
        ),
        github_pr=gh_info,
        notifications=notif_info,
        iterations_used=result.get("iteration", 0),
        success=raw_test.get("passed", False),
        error=result.get("error"),
    )


@app.post("/analyze/batch", response_model=BatchAnalyzeResponse, tags=["Agent"])
@limiter.limit("3/minute")   # stricter limit for batch
async def analyze_batch(request: Request, body: BatchAnalyzeRequest):
    """
    Run the Coder Buddy pipeline concurrently on multiple repositories (max 5).

    Each repo is analysed in parallel. Optionally triggers PR creation
    and/or notifications for each one.
    """
    async def _process_one(item) -> dict:
        try:
            abs_path = os.path.abspath(item.repo_path)
            result   = await _run_single(item.repo_path, item.instructions)
            gh_info, notif_info = _run_integrations(
                result=result,
                repo_path=abs_path,
                create_pr=body.create_github_pr,
                notify_slack=body.notify_slack,
                notify_discord=body.notify_discord,
            )
            raw_test = result.get("test_result", {})
            return {
                "repo_path": abs_path,
                "success": raw_test.get("passed", False),
                "plan": result.get("plan", []),
                "test_output": raw_test.get("output", ""),
                "commit_message": result.get("commit_proposal", {}).get("message", ""),
                "iterations_used": result.get("iteration", 0),
                "github_pr": gh_info.model_dump(),
                "notifications": notif_info.model_dump(),
                "error": result.get("error"),
            }
        except HTTPException as e:
            return {
                "repo_path": item.repo_path,
                "success": False,
                "error": e.detail,
            }
        except Exception as e:
            logger.exception("Batch item failed for %s: %s", item.repo_path, e)
            return {
                "repo_path": item.repo_path,
                "success": False,
                "error": str(e),
            }

    results = await asyncio.gather(*[_process_one(item) for item in body.repos])

    passed = sum(1 for r in results if r.get("success"))
    return BatchAnalyzeResponse(
        results=list(results),
        total=len(results),
        passed=passed,
        failed=len(results) - passed,
    )
