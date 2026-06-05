"""
LangGraph node functions for the Coder Buddy agent pipeline.

Pipeline order:
  planner → file_reader → code_fixer → test_runner → (conditional) → commit_proposer
"""
import json
import logging
import re
from typing import Any

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from app.config import settings
from app.agent.state import AgentState
from app.agent.tools import (
    list_python_files,
    read_file,
    write_file,
    run_tests,
    get_git_diff,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_llm(temperature: float = 0.2) -> ChatGroq:
    """Return a configured ChatGroq instance."""
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        groq_api_key=settings.GROQ_API_KEY,
        temperature=temperature,
        max_retries=2,
    )


def _extract_json(text: str) -> Any:
    """
    Try to parse JSON from an LLM response.
    Handles markdown code fences like ```json ... ```.
    """
    # Strip markdown fences
    cleaned = re.sub(r"```(?:json)?\s*", "", text).replace("```", "").strip()
    # Try direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    # Try to find first JSON object/array in the text
    for pattern in (r"\{.*\}", r"\[.*\]"):
        match = re.search(pattern, cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                continue
    raise ValueError(f"Could not extract valid JSON from LLM output:\n{text[:500]}")


def _log_usage(response: Any, node_name: str) -> None:
    """Log token usage metadata returned by Groq."""
    try:
        usage = response.usage_metadata
        logger.info(
            "[%s] tokens — input: %s, output: %s, total: %s",
            node_name,
            usage.get("input_tokens"),
            usage.get("output_tokens"),
            usage.get("total_tokens"),
        )
    except Exception:
        pass  # usage metadata not always available


# ---------------------------------------------------------------------------
# Node 1 — Planner
# ---------------------------------------------------------------------------

async def planner_node(state: AgentState) -> dict:
    """
    Analyse the repo path and user instructions, then produce a numbered
    JSON action plan.

    Returns partial state: {"plan": [...], "iteration": 0}
    """
    logger.info("[planner_node] Starting for repo=%s", state["repo_path"])

    system_prompt = (
        "You are an expert Python software engineer and code reviewer. "
        "Given a repository path and user instructions, produce a concise, numbered "
        "action plan as a JSON array of strings. Each element is one concrete step "
        "(e.g., 'Read calculator.py and identify the division bug'). "
        "Output ONLY valid JSON — no markdown, no explanations, no extra text. "
        "Example output: [\"Step 1: ...\", \"Step 2: ...\"]"
    )

    user_prompt = (
        f"Repository path: {state['repo_path']}\n"
        f"User instructions: {state['user_instructions']}\n\n"
        "Produce a numbered action plan to analyse and fix the issues described."
    )

    llm = _get_llm()
    try:
        response = await llm.ainvoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        )
        _log_usage(response, "planner_node")
        plan = _extract_json(response.content)
        if not isinstance(plan, list):
            plan = [str(plan)]
        logger.info("[planner_node] Generated %d-step plan", len(plan))
        return {"plan": plan, "iteration": 0, "error": None}
    except Exception as exc:
        logger.exception("[planner_node] Failed: %s", exc)
        return {
            "plan": [f"ERROR in planner: {exc}"],
            "iteration": 0,
            "error": str(exc),
        }


# ---------------------------------------------------------------------------
# Node 2 — File Reader
# ---------------------------------------------------------------------------

async def file_reader_node(state: AgentState) -> dict:
    """
    Discover all Python files in the repo and read their contents.

    Returns partial state: {"files_read": {filepath: content, ...}}
    """
    logger.info("[file_reader_node] Reading files from %s", state["repo_path"])

    files_read: dict[str, str] = {}
    try:
        py_files: list[str] = list_python_files.invoke({"repo_path": state["repo_path"]})
        logger.info("[file_reader_node] Found %d Python files", len(py_files))

        for fp in py_files:
            content = read_file.invoke({"file_path": fp})
            files_read[fp] = content
            logger.debug("[file_reader_node] Read %s (%d chars)", fp, len(content))

        return {"files_read": files_read, "error": None}
    except Exception as exc:
        logger.exception("[file_reader_node] Failed: %s", exc)
        return {"files_read": files_read, "error": str(exc)}


# ---------------------------------------------------------------------------
# Node 3 — Code Fixer
# ---------------------------------------------------------------------------

async def code_fixer_node(state: AgentState) -> dict:
    """
    Given the plan and file contents, produce corrected file contents and
    write them to disk.

    Returns partial state: {"proposed_fix": {...}, "iteration": n+1 (on retry)}
    """
    iteration = state.get("iteration", 0)
    logger.info("[code_fixer_node] Iteration %d", iteration)

    # Build a condensed view of file contents for the prompt
    files_summary = "\n\n".join(
        f"=== {fp} ===\n{content[:3000]}"  # truncate very large files
        for fp, content in state.get("files_read", {}).items()
    )

    # Include previous test error if retrying
    error_context = ""
    prev_test = state.get("test_result", {})
    if iteration > 0 and prev_test:
        error_context = (
            f"\n\nPREVIOUS TEST FAILURE (attempt {iteration}):\n"
            f"{prev_test.get('output', '')[:1500]}\n"
            "The fix you applied did NOT pass the tests. "
            "Analyse the failure output above and produce a corrected fix."
        )

    system_prompt = (
        "You are a senior Python debugger. "
        "Given file contents and a fix plan, output ONLY the corrected file contents "
        "as a JSON object where each key is the ABSOLUTE file path and each value is "
        "the complete corrected file content as a string. "
        "Fix ALL bugs described in the plan. "
        "Output ONLY valid JSON — no markdown fences, no explanations, no extra text."
    )

    user_prompt = (
        f"Fix Plan:\n{json.dumps(state.get('plan', []), indent=2)}\n\n"
        f"User Instructions: {state.get('user_instructions', '')}\n\n"
        f"Current File Contents:\n{files_summary}"
        f"{error_context}"
    )

    llm = _get_llm(temperature=0.1)
    try:
        response = await llm.ainvoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        )
        _log_usage(response, "code_fixer_node")
        proposed_fix: dict[str, str] = _extract_json(response.content)

        if not isinstance(proposed_fix, dict):
            raise ValueError("LLM did not return a JSON object for proposed_fix")

        # Write each fixed file to disk
        for fp, new_content in proposed_fix.items():
            result = write_file.invoke({"file_path": fp, "content": new_content})
            if result != "success":
                logger.warning("[code_fixer_node] write_file issue for %s: %s", fp, result)

        logger.info(
            "[code_fixer_node] Wrote fixes for %d files (iteration %d)",
            len(proposed_fix),
            iteration,
        )
        return {
            "proposed_fix": proposed_fix,
            "iteration": iteration + 1,
            "error": None,
        }
    except Exception as exc:
        logger.exception("[code_fixer_node] Failed: %s", exc)
        return {
            "proposed_fix": {},
            "iteration": iteration + 1,
            "error": str(exc),
        }


# ---------------------------------------------------------------------------
# Node 4 — Test Runner
# ---------------------------------------------------------------------------

async def test_runner_node(state: AgentState) -> dict:
    """
    Run pytest against the repository and record results.

    Returns partial state: {"test_result": {"passed": bool, "output": str}}
    """
    logger.info("[test_runner_node] Running tests in %s", state["repo_path"])
    try:
        test_result: dict = run_tests.invoke(
            {"repo_path": state["repo_path"], "timeout": settings.TEST_TIMEOUT}
        )
        logger.info(
            "[test_runner_node] Tests %s",
            "PASSED" if test_result.get("passed") else "FAILED",
        )
        return {"test_result": test_result, "error": None}
    except Exception as exc:
        logger.exception("[test_runner_node] Failed: %s", exc)
        error_result = {"passed": False, "output": f"ERROR running tests: {exc}"}
        return {"test_result": error_result, "error": str(exc)}


# ---------------------------------------------------------------------------
# Node 5 — Commit Proposer
# ---------------------------------------------------------------------------

async def commit_proposer_node(state: AgentState) -> dict:
    """
    Generate a conventional commit message and PR description based on
    the git diff and test results.

    Returns partial state: {"commit_proposal": {"message": str, "diff": str, "pr_body": str}}
    """
    logger.info("[commit_proposer_node] Generating commit proposal")

    diff = get_git_diff.invoke({"repo_path": state["repo_path"]})
    test_output = state.get("test_result", {}).get("output", "")

    system_prompt = (
        "You are an expert Git commit message author following the Conventional Commits spec. "
        "Given a code diff and test results, produce a JSON object with these keys:\n"
        '  "message": a single-line conventional commit message (e.g. "fix(calculator): resolve division and factorial bugs")\n'
        '  "pr_body": a well-structured pull request description in markdown format including '
        "Summary, Changes Made, and Testing sections.\n"
        "Output ONLY valid JSON — no markdown fences, no extra text."
    )

    user_prompt = (
        f"Git Diff:\n{diff[:3000]}\n\n"
        f"Test Output:\n{test_output[:1500]}\n\n"
        f"User's Original Instructions: {state.get('user_instructions', '')}\n\n"
        "Generate the commit message and PR description."
    )

    llm = _get_llm(temperature=0.3)
    try:
        response = await llm.ainvoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        )
        _log_usage(response, "commit_proposer_node")
        proposal = _extract_json(response.content)

        if not isinstance(proposal, dict):
            raise ValueError("LLM did not return a JSON object for commit_proposal")

        # Ensure the diff is embedded in the proposal
        proposal["diff"] = diff
        logger.info(
            "[commit_proposer_node] Commit message: %s", proposal.get("message", "")
        )
        return {"commit_proposal": proposal, "error": None}
    except Exception as exc:
        logger.exception("[commit_proposer_node] Failed: %s", exc)
        return {
            "commit_proposal": {
                "message": "fix: apply AI-generated code fixes",
                "diff": diff,
                "pr_body": f"Automated fix generated by Coder Buddy.\n\nError generating detailed description: {exc}",
            },
            "error": str(exc),
        }
