"""Pydantic request/response models for the Coder Buddy API — v2 with integrations."""
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────────────────
# Shared sub-models
# ─────────────────────────────────────────────────────────────────────────────

class TestResult(BaseModel):
    """Structured pytest result."""
    passed: bool
    output: str = ""


class CommitProposal(BaseModel):
    """Ready-to-use git commit information."""
    message: str = ""
    diff: str = ""
    pr_body: str = ""


class GitHubPRInfo(BaseModel):
    """Info about a created GitHub Pull Request."""
    created: bool = False
    pr_url: str = ""
    pr_number: int = 0
    branch_name: str = ""
    error: str = ""


class NotificationInfo(BaseModel):
    """Result of sending a Slack/Discord notification."""
    slack_sent: bool = False
    discord_sent: bool = False
    slack_error: str = ""
    discord_error: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# Single-repo endpoints
# ─────────────────────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    """Request body for POST /analyze."""

    repo_path: str = Field(
        ...,
        description="Absolute path to the Python repository to analyse and fix.",
        examples=["C:/Users/acer/projects/my_repo"],
    )
    instructions: str = Field(
        ...,
        description="Natural language description of what should be fixed.",
        examples=["Fix all bugs in the calculator module"],
    )
    # Integration overrides (fall back to .env if not provided)
    create_github_pr: bool = Field(
        default=False,
        description="If true, push fixes and open a GitHub PR after tests pass.",
    )
    notify_slack: bool = Field(
        default=False,
        description="If true, send a Slack notification on completion.",
    )
    notify_discord: bool = Field(
        default=False,
        description="If true, send a Discord notification on completion.",
    )


class AnalyzeResponse(BaseModel):
    """Response body for POST /analyze."""

    plan: list[str] = Field(default_factory=list)
    test_result: TestResult = Field(default_factory=lambda: TestResult(passed=False))
    commit_proposal: CommitProposal = Field(default_factory=CommitProposal)
    github_pr: GitHubPRInfo = Field(default_factory=GitHubPRInfo)
    notifications: NotificationInfo = Field(default_factory=NotificationInfo)
    iterations_used: int = 0
    success: bool = False
    error: str | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Multi-repo batch endpoint
# ─────────────────────────────────────────────────────────────────────────────

class BatchRepoItem(BaseModel):
    """A single repo in a batch request."""
    repo_path: str = Field(..., description="Absolute path to the repository.")
    instructions: str = Field(..., description="What to fix in this repository.")


class BatchAnalyzeRequest(BaseModel):
    """Request body for POST /analyze/batch."""

    repos: list[BatchRepoItem] = Field(
        ...,
        description="List of repos to analyse (max 5).",
        min_length=1,
        max_length=5,
    )
    create_github_pr: bool = Field(default=False)
    notify_slack: bool = Field(default=False)
    notify_discord: bool = Field(default=False)


class BatchAnalyzeResponse(BaseModel):
    """Response body for POST /analyze/batch."""

    results: list[dict] = Field(default_factory=list)
    total: int = 0
    passed: int = 0
    failed: int = 0


# ─────────────────────────────────────────────────────────────────────────────
# System
# ─────────────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    """Response body for GET /health."""

    status: str
    model: str
    max_retries: int
    github_enabled: bool = False
    slack_enabled: bool = False
    discord_enabled: bool = False
    version: str = "2.0.0"
