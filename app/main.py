"""
FastAPI backend for Coder Buddy SaaS — v3.

Endpoints:
  POST /analyze              — single repo (auth + usage gated)
  POST /analyze/batch        — multi-repo batch (auth + usage gated)
  GET  /me                   — profile + usage stats
  POST /billing/subscribe    — create Razorpay subscription
  POST /billing/cancel       — cancel subscription
  GET  /billing/portal       — return Razorpay payment URL
  POST /webhook/razorpay     — payment event handler
  GET  /health               — liveness check
"""
import asyncio
import hashlib
import logging
import os
import secrets
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.schemas.models import (
    AnalyzeRequest, AnalyzeResponse,
    BatchAnalyzeRequest, BatchAnalyzeResponse,
    CommitProposal, GitHubPRInfo,
    HealthResponse, NotificationInfo, TestResult,
)
from app.auth.middleware import get_current_user, get_api_key_user
from app.billing.plans import PLANS, check_feature
from app.usage.tracker import check_usage_limit, log_run, get_usage_this_month

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Coder Buddy SaaS API v3 starting…")
    if not settings.GROQ_API_KEY or settings.GROQ_API_KEY == "your_groq_api_key_here":
        raise RuntimeError("GROQ_API_KEY must be configured.")
    from app.agent.graph import agent  # noqa — triggers compilation
    logger.info("✅ Agent compiled | Supabase=%s | Razorpay=%s | Resend=%s",
                bool(settings.SUPABASE_URL),
                bool(settings.RAZORPAY_KEY_ID),
                bool(settings.RESEND_API_KEY))
    yield
    logger.info("🛑 API shutting down")


# ── Rate limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT])

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Coder Buddy SaaS API",
    description="Autonomous AI software engineer with auth, billing & usage limits",
    version="3.0.0",
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start    = time.perf_counter()
    response = await call_next(request)
    elapsed  = (time.perf_counter() - start) * 1000
    logger.info("← %s %s | %d | %.0fms", request.method, request.url.path, response.status_code, elapsed)
    return response


# ── Internal helpers ──────────────────────────────────────────────────────────
def _run_integrations(result, repo_path, create_pr, notify_slack, notify_discord):
    """Identical to v2 integration runner — GitHub PR + notifications."""
    gh_info = GitHubPRInfo()
    notif   = NotificationInfo()
    commit  = result.get("commit_proposal", {})
    test    = result.get("test_result", {})
    success = test.get("passed", False)
    commit_msg = commit.get("message", "fix: apply Coder Buddy fixes")
    pr_body    = commit.get("pr_body", "")
    pr_url     = ""

    if create_pr and settings.github_enabled and success:
        from app.integrations.github_pr import create_github_pr
        pr = create_github_pr(repo_path, commit_msg, pr_body, settings.GITHUB_TOKEN,
                              settings.GITHUB_REPO, settings.GITHUB_BASE_BRANCH)
        gh_info = GitHubPRInfo(created=pr.success, pr_url=pr.pr_url,
                               pr_number=pr.pr_number, branch_name=pr.branch_name, error=pr.error)
        pr_url = pr.pr_url if pr.success else ""

    if notify_slack and settings.slack_enabled:
        from app.integrations.notifications import send_slack_notification
        sr = send_slack_notification(settings.SLACK_WEBHOOK_URL, repo_path, success,
                                     result.get("plan", []), test.get("output", ""),
                                     commit_msg, pr_url, result.get("iteration", 0))
        notif.slack_sent  = sr.success
        notif.slack_error = sr.error

    if notify_discord and settings.discord_enabled:
        from app.integrations.notifications import send_discord_notification
        dr = send_discord_notification(settings.DISCORD_WEBHOOK_URL, repo_path, success,
                                       result.get("plan", []), test.get("output", ""),
                                       commit_msg, pr_url, result.get("iteration", 0))
        notif.discord_sent  = dr.success
        notif.discord_error = dr.error

    return gh_info, notif


async def _run_single(repo_path: str, instructions: str) -> dict:
    from app.agent.graph import agent
    abs_path = os.path.abspath(repo_path)
    if not os.path.isdir(abs_path):
        raise HTTPException(400, f"Not a directory: {abs_path}")
    if not settings.is_repo_path_allowed(abs_path):
        raise HTTPException(403, "Path not in ALLOWED_REPO_PATHS whitelist.")
    initial_state = {
        "repo_path": abs_path, "user_instructions": instructions,
        "plan": [], "files_read": {}, "proposed_fix": {},
        "test_result": {}, "commit_proposal": {}, "iteration": 0, "error": None,
    }
    return await agent.ainvoke(initial_state)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health():
    return HealthResponse(
        status="ok", model="llama-3.3-70b-versatile",
        max_retries=settings.MAX_RETRIES,
        github_enabled=settings.github_enabled,
        slack_enabled=settings.slack_enabled,
        discord_enabled=settings.discord_enabled,
    )


@app.get("/me", tags=["User"])
async def get_me(user: dict = Depends(get_current_user)):
    """Return user profile, plan info, and current month usage."""
    usage = await get_usage_this_month(user["id"], user["plan"])
    plan_config = PLANS.get(user["plan"], PLANS["free"])
    return {
        "id":           user["id"],
        "email":        user["email"],
        "full_name":    user["full_name"],
        "plan":         user["plan"],
        "plan_display": plan_config["display_name"],
        "features":     plan_config,
        "usage":        usage,
        "subscription_status": user["subscription_status"],
    }


@app.post("/analyze", response_model=AnalyzeResponse, tags=["Agent"])
@limiter.limit(settings.RATE_LIMIT)
async def analyze(request: Request, body: AnalyzeRequest, user: dict = Depends(get_current_user)):
    """
    Run the Coder Buddy agent. Enforces plan limits and feature gates.
    Logs the run and sends email report if plan allows.
    """
    plan = user["plan"]

    # 1. Usage limit check
    await check_usage_limit(user["id"], plan)

    # 2. Feature gate — commit proposal
    if not check_feature(plan, "commit_proposal"):
        body.create_github_pr = False

    # 3. Run agent
    try:
        result = await _run_single(body.repo_path, body.instructions)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Agent failed: %s", exc)
        raise HTTPException(500, f"Agent error: {exc}")

    abs_path = os.path.abspath(body.repo_path)

    # 4. Log run
    await log_run(user["id"], abs_path, body.instructions, result)

    # 5. Email report (Pro+)
    if check_feature(plan, "email_report") and settings.RESEND_API_KEY:
        from app.email.resend_client import send_analysis_report
        await send_analysis_report(user["email"], result)

    # 6. Integrations
    gh_info, notif = _run_integrations(
        result, abs_path,
        body.create_github_pr and check_feature(plan, "github_pr"),
        body.notify_slack,
        body.notify_discord,
    )

    raw_test   = result.get("test_result", {})
    raw_commit = result.get("commit_proposal", {})
    return AnalyzeResponse(
        plan=result.get("plan", []),
        test_result=TestResult(passed=raw_test.get("passed", False), output=raw_test.get("output", "")),
        commit_proposal=CommitProposal(
            message=raw_commit.get("message", "") if check_feature(plan, "commit_proposal") else "",
            diff=raw_commit.get("diff", ""),
            pr_body=raw_commit.get("pr_body", ""),
        ),
        github_pr=gh_info, notifications=notif,
        iterations_used=result.get("iteration", 0),
        success=raw_test.get("passed", False),
        error=result.get("error"),
    )


@app.post("/analyze/batch", response_model=BatchAnalyzeResponse, tags=["Agent"])
@limiter.limit("3/minute")
async def analyze_batch(request: Request, body: BatchAnalyzeRequest, user: dict = Depends(get_current_user)):
    """Batch analyze up to 5 repos concurrently (requires Pro or Team plan)."""
    if user["plan"] == "free":
        raise HTTPException(403, "Batch analysis requires the Pro or Team plan.")

    async def _process(item) -> dict:
        try:
            await check_usage_limit(user["id"], user["plan"])
            abs_path = os.path.abspath(item.repo_path)
            result   = await _run_single(item.repo_path, item.instructions)
            await log_run(user["id"], abs_path, item.instructions, result)
            gh_info, notif = _run_integrations(result, abs_path, body.create_github_pr, body.notify_slack, body.notify_discord)
            raw_test = result.get("test_result", {})
            return {
                "repo_path": abs_path, "success": raw_test.get("passed", False),
                "plan": result.get("plan", []), "test_output": raw_test.get("output", ""),
                "commit_message": result.get("commit_proposal", {}).get("message", ""),
                "iterations_used": result.get("iteration", 0),
                "github_pr": gh_info.model_dump(), "notifications": notif.model_dump(),
                "error": result.get("error"),
            }
        except HTTPException as e:
            return {"repo_path": item.repo_path, "success": False, "error": e.detail}
        except Exception as e:
            return {"repo_path": item.repo_path, "success": False, "error": str(e)}

    results = await asyncio.gather(*[_process(item) for item in body.repos])
    passed  = sum(1 for r in results if r.get("success"))
    return BatchAnalyzeResponse(results=list(results), total=len(results), passed=passed, failed=len(results)-passed)


# ── Billing endpoints ─────────────────────────────────────────────────────────

@app.post("/billing/subscribe", tags=["Billing"])
async def subscribe(plan_name: str, user: dict = Depends(get_current_user)):
    """Create a Razorpay subscription and return the payment URL."""
    if plan_name not in ("pro", "team"):
        raise HTTPException(400, "plan_name must be 'pro' or 'team'.")
    if not settings.RAZORPAY_KEY_ID:
        raise HTTPException(503, "Payment gateway not configured yet.")
    from app.billing.razorpay_client import create_subscription
    try:
        sub = await create_subscription(user["id"], user["email"], plan_name)
        return {"status": "created", **sub}
    except Exception as exc:
        logger.exception("Subscription creation failed: %s", exc)
        raise HTTPException(500, str(exc))


@app.post("/billing/cancel", tags=["Billing"])
async def cancel(user: dict = Depends(get_current_user)):
    """Cancel active subscription at end of billing cycle."""
    from app.billing.razorpay_client import cancel_subscription
    try:
        return await cancel_subscription(user["id"])
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except Exception as exc:
        raise HTTPException(500, str(exc))


@app.get("/billing/portal", tags=["Billing"])
async def billing_portal(user: dict = Depends(get_current_user)):
    """Return the Razorpay subscription management URL."""
    supabase = __import__("app.auth.supabase_client", fromlist=["get_supabase"]).get_supabase()
    profile  = supabase.table("profiles").select("razorpay_subscription_id").eq("id", user["id"]).single().execute().data
    sub_id   = profile.get("razorpay_subscription_id") if profile else None
    if not sub_id:
        raise HTTPException(404, "No active subscription found.")
    return {"subscription_id": sub_id, "manage_url": f"https://dashboard.razorpay.com/app/subscriptions/{sub_id}"}


@app.post("/webhook/razorpay", tags=["Billing"])
async def razorpay_webhook(request: Request):
    """Handle Razorpay payment lifecycle events."""
    from app.billing.webhook_handler import handle_razorpay_webhook
    return await handle_razorpay_webhook(request)


# ── Team API key management (Team plan only) ──────────────────────────────────

@app.post("/api-keys", tags=["Team"])
async def create_api_key(label: str = "Default", user: dict = Depends(get_current_user)):
    """Generate a new API key (Team plan only)."""
    if user["plan"] != "team":
        raise HTTPException(403, "API key access requires the Team plan.")
    raw_key  = "cb_" + secrets.token_urlsafe(32)
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    supabase = __import__("app.auth.supabase_client", fromlist=["get_supabase"]).get_supabase()
    supabase.table("api_keys").insert({"user_id": user["id"], "key_hash": key_hash, "label": label}).execute()
    return {"api_key": raw_key, "label": label, "warning": "Save this key — it won't be shown again."}


@app.get("/api-keys", tags=["Team"])
async def list_api_keys(user: dict = Depends(get_current_user)):
    """List API keys (shows label + created_at, never the raw key)."""
    if user["plan"] != "team":
        raise HTTPException(403, "API key access requires the Team plan.")
    supabase = __import__("app.auth.supabase_client", fromlist=["get_supabase"]).get_supabase()
    keys = supabase.table("api_keys").select("id, label, is_active, last_used_at, created_at").eq("user_id", user["id"]).execute()
    return {"keys": keys.data}
