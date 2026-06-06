"""
Razorpay webhook handler — processes payment events and updates user plans.
"""
import json
import logging
from datetime import datetime, timedelta, timezone
from fastapi import Request, HTTPException
from app.auth.supabase_client import get_supabase
from app.billing.razorpay_client import verify_webhook_signature
from app.email.resend_client import send_payment_confirmation, send_subscription_ended

logger = logging.getLogger(__name__)


async def handle_razorpay_webhook(request: Request) -> dict:
    """
    Parse and process incoming Razorpay webhook events.

    Events handled:
      - subscription.activated  → activate plan
      - subscription.charged    → extend subscription
      - subscription.cancelled  → downgrade to free
      - subscription.completed  → downgrade to free
      - payment.failed          → notify user
    """
    # 1. Read raw body for signature verification
    payload_bytes = await request.body()
    signature     = request.headers.get("X-Razorpay-Signature", "")

    if not verify_webhook_signature(payload_bytes, signature):
        logger.warning("Invalid Razorpay webhook signature — rejecting")
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    # 2. Parse event
    try:
        event = json.loads(payload_bytes)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_type = event.get("event", "")
    entity     = event.get("payload", {}).get("subscription", {}).get("entity", {})
    payment    = event.get("payload", {}).get("payment", {}).get("entity", {})

    logger.info("Razorpay webhook received: %s", event_type)

    supabase = get_supabase()

    # ── subscription.activated ────────────────────────────────────────────────
    if event_type == "subscription.activated":
        sub_id    = entity.get("id")
        notes     = entity.get("notes", {})
        plan_name = notes.get("plan", "pro")

        result = (
            supabase.table("profiles")
            .update({
                "plan":                    plan_name,
                "subscription_status":     "active",
                "subscription_ends_at":    _next_month_iso(),
            })
            .eq("razorpay_subscription_id", sub_id)
            .execute()
        )
        profile = result.data[0] if result.data else {}
        logger.info("Activated plan=%s for subscription %s", plan_name, sub_id)

        if profile.get("email"):
            await send_payment_confirmation(
                user_email=profile["email"],
                plan=plan_name,
                amount=_plan_amount(plan_name),
            )
        return {"status": "activated"}

    # ── subscription.charged ──────────────────────────────────────────────────
    elif event_type == "subscription.charged":
        sub_id = entity.get("id")
        supabase.table("profiles").update({
            "subscription_status":  "active",
            "subscription_ends_at": _next_month_iso(),
        }).eq("razorpay_subscription_id", sub_id).execute()
        logger.info("Renewed subscription %s", sub_id)
        return {"status": "renewed"}

    # ── subscription.cancelled / completed ────────────────────────────────────
    elif event_type in ("subscription.cancelled", "subscription.completed"):
        sub_id  = entity.get("id")
        result  = (
            supabase.table("profiles")
            .update({
                "plan":                "free",
                "subscription_status": "inactive",
            })
            .eq("razorpay_subscription_id", sub_id)
            .execute()
        )
        profile = result.data[0] if result.data else {}
        logger.info("Subscription %s ended — user downgraded to free", sub_id)
        if profile.get("email"):
            await send_subscription_ended(user_email=profile["email"])
        return {"status": "cancelled"}

    # ── payment.failed ────────────────────────────────────────────────────────
    elif event_type == "payment.failed":
        email = payment.get("email")
        if email:
            from app.email.resend_client import send_payment_failed
            await send_payment_failed(user_email=email)
        logger.warning("Payment failed for %s", email)
        return {"status": "payment_failed_notified"}

    else:
        logger.debug("Unhandled Razorpay event: %s", event_type)
        return {"status": "ignored", "event": event_type}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _next_month_iso() -> str:
    return (datetime.now(timezone.utc) + timedelta(days=31)).isoformat()


def _plan_amount(plan_name: str) -> int:
    return {"pro": 499, "team": 1499}.get(plan_name, 0)
