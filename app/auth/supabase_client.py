"""Supabase client singleton for Coder Buddy backend."""
import logging
from functools import lru_cache
from supabase import create_client, Client
from app.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    """Return a cached Supabase client (service-role for server-side ops)."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env"
        )
    client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    logger.info("Supabase client initialized for %s", settings.SUPABASE_URL)
    return client


@lru_cache(maxsize=1)
def get_supabase_anon() -> Client:
    """Return a cached Supabase anon client (for JWT verification)."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env"
        )
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
