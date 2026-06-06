"""
Razorpay billing integration — subscriptions, cancellation, customer management.
"""
import logging
from app.config import settings
from app.billing.plans import RAZORPAY_PLAN_IDS
from app.auth.supabase_client import get_supabase

logger = logging.getLogger(__name__)


def _get_client():
    """Return authenticated Razorpay client."""
    try:
        import razorpay
    except ImportError:
        raise RuntimeError("razorpay package not installed. Run: pip install razorpay")
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        raise RuntimeError("RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET must be set in .env")
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


async def create_subscription(user_id: str, user_email: str, plan_name: str) -> dict:
    """
    Create a Razorpay subscription for a user and store the subscription ID.

    Returns:
        {"subscription_id": str, "short_url": str}
    """
    if plan_name not in RAZORPAY_PLAN_IDS:
        raise ValueError(f"Unknown plan: {plan_name}. Must be 'pro' or 'team'.")

    plan_id = RAZORPAY_PLAN_IDS[plan_name]
    if "XXXXXXX" in plan_id:
        raise RuntimeError(
            f"Razorpay plan ID for '{plan_name}' is not configured. "
            "Create the plan in Razorpay Dashboard → Subscriptions → Plans, "
            "then update RAZORPAY_PLAN_IDS in app/billing/plans.py"
        )

    client = _get_client()

    # Create or reuse Razorpay customer
    supabase = get_supabase()
    profile  = supabase.table("profiles").select("razorpay_customer_id").eq("id", user_id).single().execute().data
    customer_id = profile.get("razorpay_customer_id") if profile else None

    if not customer_id:
        customer = client.customer.create({
            "name":  user_email.split("@")[0],
            "email": user_email,
            "fail_existing": 0,
        })
        customer_id = customer["id"]
        supabase.table("profiles").update({"razorpay_customer_id": customer_id}).eq("id", user_id).execute()
        logger.info("Created Razorpay customer %s for user %s", customer_id, user_id)

    # Create subscription
    sub = client.subscription.create({
        "plan_id":         plan_id,
        "customer_notify": 1,
        "total_count":     12,       # 12 billing cycles (1 year)
        "customer_id":     customer_id,
        "notes":           {"user_id": user_id, "plan": plan_name},
    })

    # Store subscription ID in profile
    supabase.table("profiles").update({
        "razorpay_subscription_id": sub["id"],
        "subscription_status":      "pending",
    }).eq("id", user_id).execute()

    logger.info("Created Razorpay subscription %s for user %s (plan=%s)", sub["id"], user_id, plan_name)
    return {"subscription_id": sub["id"], "short_url": sub.get("short_url", "")}


async def cancel_subscription(user_id: str) -> dict:
    """
    Cancel the user's subscription at end of current billing cycle.
    Returns {"status": "cancelling"}.
    """
    supabase = get_supabase()
    profile  = supabase.table("profiles").select("razorpay_subscription_id").eq("id", user_id).single().execute().data

    if not profile or not profile.get("razorpay_subscription_id"):
        raise ValueError("No active subscription found for this user.")

    sub_id = profile["razorpay_subscription_id"]
    client = _get_client()
    client.subscription.cancel(sub_id, {"cancel_at_cycle_end": 1})

    supabase.table("profiles").update({"subscription_status": "cancelling"}).eq("id", user_id).execute()
    logger.info("Cancelled subscription %s for user %s (at cycle end)", sub_id, user_id)
    return {"status": "cancelling", "message": "Subscription will cancel at end of billing period."}


def verify_webhook_signature(payload_bytes: bytes, signature: str) -> bool:
    """
    Verify a Razorpay webhook signature using HMAC-SHA256.
    Returns True if valid.
    """
    import hmac, hashlib
    if not settings.RAZORPAY_WEBHOOK_SECRET:
        logger.warning("RAZORPAY_WEBHOOK_SECRET not set — skipping signature verification!")
        return True  # Skip in dev, enforce in prod
    expected = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode(),
        payload_bytes,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
