"""
GitHub integration for Coder Buddy.

Provides:
  - create_github_pr(): opens a real Pull Request using PyGithub
  - GitHubPRResult: dataclass with PR URL and metadata
"""
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class GitHubPRResult:
    """Result of creating a GitHub Pull Request."""
    success: bool
    pr_url: str = ""
    pr_number: int = 0
    branch_name: str = ""
    error: str = ""


def create_github_pr(
    repo_path: str,
    commit_message: str,
    pr_body: str,
    github_token: str,
    github_repo: str,
    base_branch: str = "main",
    new_branch: str = "",
) -> GitHubPRResult:
    """
    Stage all changes, push to a new branch, and open a GitHub Pull Request.

    Args:
        repo_path:      Absolute path to the local git repository.
        commit_message: Conventional commit message (used as PR title too).
        pr_body:        Markdown PR description.
        github_token:   GitHub Personal Access Token (repo scope).
        github_repo:    Full repo name, e.g. "username/my-repo".
        base_branch:    Target branch for the PR (default: "main").
        new_branch:     Branch name to push fixes to. Auto-generated if empty.

    Returns:
        GitHubPRResult with pr_url and pr_number on success.
    """
    try:
        import git
        from github import Github, GithubException
    except ImportError as e:
        return GitHubPRResult(
            success=False,
            error=f"Missing dependency: {e}. Run: pip install PyGithub gitpython",
        )

    import time

    # ── 1. Determine branch name ────────────────────────────────────────────
    if not new_branch:
        timestamp = int(time.time())
        safe_msg = commit_message[:30].lower().replace(" ", "-").replace("(", "").replace(")", "")
        new_branch = f"coder-buddy/{safe_msg}-{timestamp}"

    logger.info("[github] Creating branch: %s", new_branch)

    # ── 2. Git operations (stage + commit + push) ───────────────────────────
    try:
        repo = git.Repo(repo_path, search_parent_directories=True)

        # Create and checkout new branch
        new_git_branch = repo.create_head(new_branch)
        new_git_branch.checkout()

        # Stage all modified/new files
        repo.git.add(A=True)

        # Check if there's anything to commit
        if not repo.is_dirty(index=True):
            return GitHubPRResult(
                success=False,
                error="No staged changes to commit. The agent may not have modified any files.",
            )

        # Commit
        repo.index.commit(commit_message)
        logger.info("[github] Committed: %s", commit_message)

        # Push to remote
        origin = repo.remotes.origin
        origin.push(refspec=f"{new_branch}:{new_branch}")
        logger.info("[github] Pushed branch: %s", new_branch)

    except git.InvalidGitRepositoryError:
        return GitHubPRResult(
            success=False,
            error=f"{repo_path} is not a git repository.",
        )
    except git.GitCommandError as e:
        return GitHubPRResult(
            success=False,
            error=f"Git error (check remote is configured): {e}",
        )
    except Exception as e:
        return GitHubPRResult(
            success=False,
            error=f"Git operation failed: {e}",
        )

    # ── 3. Create PR via GitHub API ─────────────────────────────────────────
    try:
        gh = Github(github_token)
        gh_repo = gh.get_repo(github_repo)

        pr = gh_repo.create_pull(
            title=commit_message,
            body=pr_body,
            head=new_branch,
            base=base_branch,
        )

        logger.info("[github] PR created: #%d — %s", pr.number, pr.html_url)
        return GitHubPRResult(
            success=True,
            pr_url=pr.html_url,
            pr_number=pr.number,
            branch_name=new_branch,
        )

    except GithubException as e:
        return GitHubPRResult(
            success=False,
            error=f"GitHub API error: {e.data.get('message', str(e))}",
        )
    except Exception as e:
        return GitHubPRResult(
            success=False,
            error=f"Failed to create PR: {e}",
        )
