"""
LangChain tools for Coder Buddy agent.

All tools are decorated with @tool so they can be bound to LangChain
agents or called directly from node functions.
"""
import os
import subprocess
import logging
from pathlib import Path
from langchain_core.tools import tool

try:
    import git
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tool 1 — read_file
# ---------------------------------------------------------------------------

@tool
def read_file(file_path: str) -> str:
    """
    Read and return the full contents of a file given its absolute path.

    Args:
        file_path: Absolute path to the file to read.

    Returns:
        File contents as a string, or an error message prefixed with 'ERROR:'.
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return f"ERROR: File not found: {file_path}"
        if not path.is_file():
            return f"ERROR: Path is not a file: {file_path}"
        contents = path.read_text(encoding="utf-8", errors="replace")
        logger.debug("read_file: read %d chars from %s", len(contents), file_path)
        return contents
    except PermissionError:
        return f"ERROR: Permission denied reading file: {file_path}"
    except Exception as exc:
        return f"ERROR: Unexpected error reading file: {exc}"


# ---------------------------------------------------------------------------
# Tool 2 — write_file
# ---------------------------------------------------------------------------

@tool
def write_file(file_path: str, content: str) -> str:
    """
    Write content to a file, creating parent directories if needed.

    Args:
        file_path: Absolute path where the file should be written.
        content:   Text content to write.

    Returns:
        "success" on success, or an error message prefixed with 'ERROR:'.
    """
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        logger.info("write_file: wrote %d chars to %s", len(content), file_path)
        return "success"
    except PermissionError:
        return f"ERROR: Permission denied writing to: {file_path}"
    except Exception as exc:
        return f"ERROR: Unexpected error writing file: {exc}"


# ---------------------------------------------------------------------------
# Tool 3 — run_tests
# ---------------------------------------------------------------------------

@tool
def run_tests(repo_path: str, timeout: int = 60) -> dict:
    """
    Run pytest against a repository and return structured results.

    Args:
        repo_path: Absolute path to the repository root.
        timeout:   Maximum seconds to wait for pytest (default 60).

    Returns:
        {"passed": bool, "output": str} where output is the full pytest output.
    """
    try:
        path = Path(repo_path)
        if not path.is_dir():
            return {"passed": False, "output": f"ERROR: {repo_path} is not a directory"}

        result = subprocess.run(
            ["python", "-m", "pytest", str(path), "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(path),
        )
        output = result.stdout + result.stderr
        passed = result.returncode == 0
        logger.info(
            "run_tests: returncode=%d repo=%s passed=%s",
            result.returncode,
            repo_path,
            passed,
        )
        return {"passed": passed, "output": output}
    except subprocess.TimeoutExpired:
        return {"passed": False, "output": f"ERROR: pytest timed out after {timeout}s"}
    except FileNotFoundError:
        return {
            "passed": False,
            "output": "ERROR: pytest not found. Ensure it is installed (pip install pytest).",
        }
    except Exception as exc:
        return {"passed": False, "output": f"ERROR: {exc}"}


# ---------------------------------------------------------------------------
# Tool 4 — list_python_files
# ---------------------------------------------------------------------------

EXCLUDED_DIRS = {"__pycache__", ".venv", "venv", ".git", ".tox", "dist", "build", ".mypy_cache"}


@tool
def list_python_files(repo_path: str) -> list[str]:
    """
    Walk a directory and return all Python (.py) file paths.
    Automatically excludes common noise directories.

    Args:
        repo_path: Absolute path to the repository root.

    Returns:
        Sorted list of absolute file paths ending in '.py'.
    """
    try:
        root = Path(repo_path)
        if not root.is_dir():
            logger.error("list_python_files: %s is not a directory", repo_path)
            return []

        files: list[str] = []
        for dirpath, dirnames, filenames in os.walk(root):
            # Prune excluded directories in-place so os.walk skips them
            dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
            for fname in filenames:
                if fname.endswith(".py"):
                    files.append(str(Path(dirpath) / fname))

        files.sort()
        logger.debug("list_python_files: found %d files in %s", len(files), repo_path)
        return files
    except Exception as exc:
        logger.error("list_python_files error: %s", exc)
        return []


# ---------------------------------------------------------------------------
# Tool 5 — get_git_diff
# ---------------------------------------------------------------------------

@tool
def get_git_diff(repo_path: str) -> str:
    """
    Return the unstaged unified diff for a git repository.

    Args:
        repo_path: Absolute path to a git repository root.

    Returns:
        Unified diff string, or an error/empty-diff message.
    """
    if not GIT_AVAILABLE:
        return "ERROR: GitPython is not installed. Run: pip install gitpython"

    try:
        repo = git.Repo(repo_path, search_parent_directories=True)
        # Unstaged changes (working tree vs index)
        diff = repo.git.diff()
        if not diff:
            # Try staged changes as fallback
            diff = repo.git.diff("--cached")
        if not diff:
            return "(no changes detected in working tree or index)"
        logger.debug("get_git_diff: diff length=%d for %s", len(diff), repo_path)
        return diff
    except git.InvalidGitRepositoryError:
        return f"ERROR: {repo_path} is not a git repository"
    except git.GitCommandError as exc:
        return f"ERROR: git command failed: {exc}"
    except Exception as exc:
        return f"ERROR: Unexpected error getting diff: {exc}"


# ---------------------------------------------------------------------------
# Convenience export
# ---------------------------------------------------------------------------

ALL_TOOLS = [read_file, write_file, run_tests, list_python_files, get_git_diff]
