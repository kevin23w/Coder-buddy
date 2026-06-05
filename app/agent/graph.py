"""
LangGraph StateGraph definition for the Coder Buddy agent.

Pipeline:
  planner → file_reader → code_fixer → test_runner ──┬──> commit_proposer → END
                                             ▲         │ (tests pass)
                                             └─────────┘ (tests fail, iteration < MAX_RETRIES)
                                                       │
                                                       └──> END (max retries exceeded)
"""
import logging
from langgraph.graph import StateGraph, END

from app.agent.state import AgentState
from app.agent.nodes import (
    planner_node,
    file_reader_node,
    code_fixer_node,
    test_runner_node,
    commit_proposer_node,
)
from app.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Conditional routing function
# ---------------------------------------------------------------------------

def route_after_tests(state: AgentState) -> str:
    """
    Decide the next node after test_runner:
    - Tests passed → commit_proposer
    - Tests failed AND iteration < MAX_RETRIES → code_fixer (retry)
    - Tests failed AND max retries exhausted → END
    """
    test_result = state.get("test_result", {})
    iteration = state.get("iteration", 0)

    if test_result.get("passed", False):
        logger.info("[router] Tests PASSED — routing to commit_proposer")
        return "commit_proposer"

    if iteration < settings.MAX_RETRIES:
        logger.info(
            "[router] Tests FAILED (iteration %d / %d) — retrying code_fixer",
            iteration,
            settings.MAX_RETRIES,
        )
        return "code_fixer"

    logger.warning(
        "[router] Tests FAILED after %d retries — terminating", iteration
    )
    return END


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def build_agent() -> StateGraph:
    """Construct and compile the Coder Buddy LangGraph agent."""
    graph = StateGraph(AgentState)

    # Register nodes
    graph.add_node("planner", planner_node)
    graph.add_node("file_reader", file_reader_node)
    graph.add_node("code_fixer", code_fixer_node)
    graph.add_node("test_runner", test_runner_node)
    graph.add_node("commit_proposer", commit_proposer_node)

    # Linear edges
    graph.set_entry_point("planner")
    graph.add_edge("planner", "file_reader")
    graph.add_edge("file_reader", "code_fixer")
    graph.add_edge("code_fixer", "test_runner")

    # Conditional retry loop
    graph.add_conditional_edges(
        "test_runner",
        route_after_tests,
        {
            "commit_proposer": "commit_proposer",
            "code_fixer": "code_fixer",
            END: END,
        },
    )

    graph.add_edge("commit_proposer", END)

    compiled = graph.compile()
    logger.info("Coder Buddy agent graph compiled successfully")
    return compiled


# Singleton agent instance — imported by app/main.py
agent = build_agent()
