"""Auth middleware — JWT verification via Supabase."""
import logging
import hashlib
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.auth.supabase_client import get_supabase

logger = logging.getLogger(__name__)
bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(bearer),
) -> dict:
    """
    FastAPI dependency — validates Bearer JWT from Supabase Auth.

    Returns the user's full profile dict including plan and email.
    Raises HTTP 401 if missing/invalid, 403 if email not verified.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Missing Authorization header. Pass: Bearer <supabase_jwt>")

    token = credentials.credentials
    supabase = get_supabase()

    try:
        auth_resp = supabase.auth.get_user(token)
        user = auth_resp.user
    except Exception as exc:
        logger.warning("JWT verification failed: %s", exc)
        raise HTTPException(status_code=401, detail="Invalid or expired token. Please sign in again.")

    if not user:
        raise HTTPException(status_code=401, detail="Token did not resolve to a user.")

    if not user.email_confirmed_at:
        raise HTTPException(status_code=403, detail="Please verify your email before using the API.")

    # Fetch profile (plan, subscription status, etc.)
    try:
        profile_resp = (
            supabase.table("profiles")
            .select("*")
            .eq("id", str(user.id))
            .single()
            .execute()
        )
        profile = profile_resp.data
    except Exception as exc:
        logger.error("Failed to fetch profile for user %s: %s", user.id, exc)
        raise HTTPException(status_code=500, detail="Could not load user profile.")

    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found.")

    return {
        "id":     str(user.id),
        "email":  user.email,
        "plan":   profile.get("plan", "free"),
        "subscription_status": profile.get("subscription_status", "inactive"),
        "full_name": profile.get("full_name", ""),
    }


async def get_api_key_user(
    credentials: HTTPAuthorizationCredentials = Security(bearer),
) -> dict:
    """
    Alternative dependency for Team-plan API key authentication.
    Accepts raw API keys (prefixed 'cb_') for programmatic access.
    Falls back to JWT auth for browser clients.
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="No credentials provided.")

    raw_key = credentials.credentials

    # If it's a JWT (long, has dots), use normal auth
    if raw_key.count(".") == 2:
        return await get_current_user(credentials)

    # API key path — hash and look up
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    supabase  = get_supabase()

    try:
        key_resp = (
            supabase.table("api_keys")
            .select("user_id, is_active")
            .eq("key_hash", key_hash)
            .eq("is_active", True)
            .single()
            .execute()
        )
        key_row = key_resp.data
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid API key.")

    if not key_row:
        raise HTTPException(status_code=401, detail="API key not found or inactive.")

    # Update last_used_at
    supabase.table("api_keys").update({"last_used_at": "NOW()"}).eq("key_hash", key_hash).execute()

    # Fetch profile
    profile_resp = (
        supabase.table("profiles")
        .select("*")
        .eq("id", key_row["user_id"])
        .single()
        .execute()
    )
    profile = profile_resp.data
    if not profile or profile.get("plan") != "team":
        raise HTTPException(status_code=403, detail="API key access requires the Team plan.")

    return {
        "id":    profile["id"],
        "email": profile["email"],
        "plan":  profile["plan"],
        "subscription_status": profile.get("subscription_status", "inactive"),
        "full_name": profile.get("full_name", ""),
    }
