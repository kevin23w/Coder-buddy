"""
Configuration management for Coder Buddy using pydantic-settings.
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── Required ──────────────────────────────────────────────────────────
    GROQ_API_KEY: str = Field(..., description="Groq API key for LLM access")

    # ── Core optional ─────────────────────────────────────────────────────
    MAX_RETRIES: int = Field(default=3, description="Max fix-test retry iterations")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    ALLOWED_REPO_PATHS: str = Field(
        default="",
        description="Comma-separated whitelist of allowed repo base paths. Empty = allow all.",
    )
    TEST_TIMEOUT: int = Field(default=60, description="Timeout in seconds for pytest runs")
    RATE_LIMIT: str = Field(default="10/minute", description="Rate limit for API endpoints")
    HOST: str = Field(default="0.0.0.0", description="API host")
    PORT: int = Field(default=8000, description="API port")

    # ── GitHub integration ────────────────────────────────────────────────
    GITHUB_TOKEN: str = Field(
        default="",
        description="GitHub Personal Access Token (repo scope) for creating PRs.",
    )
    GITHUB_REPO: str = Field(
        default="",
        description="Full GitHub repo name, e.g. 'username/my-repo'.",
    )
    GITHUB_BASE_BRANCH: str = Field(
        default="main",
        description="Target branch for PRs (default: main).",
    )

    # ── Slack integration ─────────────────────────────────────────────────
    SLACK_WEBHOOK_URL: str = Field(
        default="",
        description="Slack Incoming Webhook URL. Leave empty to disable.",
    )

    # ── Discord integration ───────────────────────────────────────────────
    DISCORD_WEBHOOK_URL: str = Field(
        default="",
        description="Discord Webhook URL. Leave empty to disable.",
    )

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    # ── Computed helpers ──────────────────────────────────────────────────

    @property
    def allowed_paths_list(self) -> list[str]:
        """Parse ALLOWED_REPO_PATHS into a list."""
        if not self.ALLOWED_REPO_PATHS.strip():
            return []
        return [p.strip() for p in self.ALLOWED_REPO_PATHS.split(",") if p.strip()]

    def is_repo_path_allowed(self, repo_path: str) -> bool:
        """
        Check if a repo path is within the allowed base paths.
        If allowed list is empty, all paths are allowed.
        """
        allowed = self.allowed_paths_list
        if not allowed:
            return True
        abs_path = os.path.abspath(repo_path)
        return any(abs_path.startswith(os.path.abspath(p)) for p in allowed)

    @property
    def github_enabled(self) -> bool:
        """True if both GITHUB_TOKEN and GITHUB_REPO are configured."""
        return bool(self.GITHUB_TOKEN.strip() and self.GITHUB_REPO.strip())

    @property
    def slack_enabled(self) -> bool:
        """True if SLACK_WEBHOOK_URL is configured."""
        return bool(self.SLACK_WEBHOOK_URL.strip())

    @property
    def discord_enabled(self) -> bool:
        """True if DISCORD_WEBHOOK_URL is configured."""
        return bool(self.DISCORD_WEBHOOK_URL.strip())


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


# Convenience singleton
settings = get_settings()
