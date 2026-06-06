"""Usage tracking — check limits, log runs, fetch stats."""
import logging
from datetime import datetime, timezone
from fastapi import HTTPException
from app.auth.supabase_client import get_supabase
from app.billing.plans import get_run_limit

logger = logging.getLogger(__name__)


async def check_usage_limit(user_id: str, plan: str) -> None:
    """
    Raise HTTP 429 if the user has exhausted their monthly run limit.
    Does NOT increment — call log_run() after the agent finishes.
    """
    limit = get_run_limit(plan)
    if limit >= 999_999:
        return  # unlimited (Team plan)

    supabase = get_supabase()
    try:
        resp = (
            supabase.table("usage_logs")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .gte("created_at", _month_start())
            .execute()
        )
        used = resp.count or 0
    except Exception as exc:
        logger.error("Usage check failed for %s: %s", user_id, exc)
        used = 0  # fail open — don't block user on DB error

    if used >= limit:
        raise HTTPException(
            status_code=429,
            detail=(
                f"Monthly limit reached ({used}/{limit} runs used). "
                "Upgrade to Pro for 50 runs/month or Team for unlimited."
            ),
        )
    logger.info("Usage OK for %s: %d/%d runs used this month", user_id, used, limit)


async def log_run(
    user_id: str,
    repo_path: str,
    instructions: str,
    result: dict,
    tokens: int = 0,
) -> None:
    """
    Insert a usage log entry after a successful agent run.
    Stores the full result as JSONB for audit trail.
    """
    supabase = get_supabase()
    success  = result.get("test_result", {}).get("passed", False)

    # Trim result to avoid huge JSONB blobs
    slim_result = {
        "plan":           result.get("plan", [])[:5],
        "test_passed":    success,
        "iterations":     result.get("iteration", 0),
        "commit_message": result.get("commit_proposal", {}).get("message", ""),
    }

    try:
        supabase.table("usage_logs").insert({
            "user_id":     user_id,
            "repo_path":   repo_path,
            "instructions": instructions[:500],
            "run_result":  slim_result,
            "tokens_used": tokens,
            "success":     success,
        }).execute()
        logger.info("Logged run for user %s (success=%s)", user_id, success)
    except Exception as exc:
        logger.error("Failed to log run for %s: %s", user_id, exc)
        # Non-fatal — don't break the response


async def get_usage_this_month(user_id: str, plan: str) -> dict:
    """
    Return usage stats for the current calendar month.
    Used by GET /me and the frontend dashboard UsageBar.
    """
    limit    = get_run_limit(plan)
    supabase = get_supabase()

    try:
        resp = (
            supabase.table("usage_logs")
            .select("id, success, tokens_used, created_at", count="exact")
            .eq("user_id", user_id)
            .gte("created_at", _month_start())
            .order("created_at", desc=True)
            .execute()
        )
        rows = resp.data or []
        used = resp.count or 0
    except Exception as exc:
        logger.error("get_usage_this_month failed for %s: %s", user_id, exc)
        return {"used": 0, "limit": limit, "plan": plan, "history": []}

    total_tokens = sum(r.get("tokens_used", 0) for r in rows)
    history = [
        {
            "date":    r["created_at"],
            "success": r.get("success", False),
            "tokens":  r.get("tokens_used", 0),
        }
        for r in rows[:20]
    ]

    return {
        "used":         used,
        "limit":        limit if limit < 999_999 else "unlimited",
        "plan":         plan,
        "total_tokens": total_tokens,
        "history":      history,
    }


def _month_start() -> str:
    """Return ISO timestamp for the start of the current UTC month."""
    now = datetime.now(timezone.utc)
    return datetime(now.year, now.month, 1, tzinfo=timezone.utc).isoformat()
