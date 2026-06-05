"""Agent state definition for Coder Buddy."""
from typing import TypedDict


class AgentState(TypedDict):
    """
    Central state object passed through every node of the LangGraph pipeline.
    Each node receives the full state and returns a partial dict to update it.
    """

    repo_path: str
    """Absolute path to the target Python repository."""

    user_instructions: str
    """Natural language description of what the user wants fixed."""

    plan: list[str]
    """Ordered list of action steps produced by the planner node."""

    files_read: dict[str, str]
    """Mapping of file path → raw file contents read from disk."""

    proposed_fix: dict[str, str]
    """Mapping of file path → corrected file contents to be written."""

    test_result: dict
    """Result of running pytest: {"passed": bool, "output": str}."""

    commit_proposal: dict
    """
    Ready-to-use commit info:
    {"message": str, "diff": str, "pr_body": str}
    """

    iteration: int
    """Number of fix→test retry attempts so far (0-indexed)."""

    error: str | None
    """Last error message captured during processing, if any."""
