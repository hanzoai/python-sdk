"""Git slash commands for the Hanzo REPL."""

import subprocess
from pathlib import Path
from typing import Optional


def _run(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True)


def git_status(cwd: Path) -> str:
    """Return git status summary."""
    r = _run(["git", "status", "--short", "--branch"], cwd)
    if r.returncode != 0:
        return r.stderr.strip()
    lines = [l for l in r.stdout.strip().splitlines() if not l.startswith("##")]
    if not lines:
        return "Nothing to commit, working tree clean."
    branch_line = r.stdout.strip().splitlines()[0] if r.stdout.strip() else ""
    return (branch_line + "\n" + "\n".join(lines)).strip()


def git_branch(args: str, cwd: Path) -> str:
    """List branches or create a new branch."""
    if not args.strip():
        r = _run(["git", "branch", "-a"], cwd)
        return r.stdout.strip() if r.returncode == 0 else r.stderr.strip()

    branch_name = args.strip().split()[0]
    r = _run(["git", "branch", branch_name], cwd)
    if r.returncode != 0:
        return r.stderr.strip()
    return f"Created branch: {branch_name}"


def git_commit(message: str, cwd: Path) -> str:
    """Stage all changes and commit with the given message."""
    # Stage everything
    _run(["git", "add", "-A"], cwd)

    # Check if anything is staged
    check = _run(["git", "diff", "--cached", "--quiet"], cwd)
    if check.returncode == 0:
        return "Nothing to commit, no changes staged."

    r = _run(["git", "commit", "-m", message], cwd)
    if r.returncode != 0:
        return r.stderr.strip()
    return r.stdout.strip()


def git_commit_push_pr(message: str, cwd: Path) -> str:
    """Commit staged changes, push, and open a pull request via gh."""
    # Commit
    commit_out = git_commit(message, cwd)
    if "nothing" in commit_out.lower():
        return commit_out

    # Get current branch
    branch_r = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd)
    if branch_r.returncode != 0:
        return f"Committed but failed to get branch: {branch_r.stderr.strip()}"
    branch = branch_r.stdout.strip()

    # Push
    push_r = _run(["git", "push", "-u", "origin", branch], cwd)
    if push_r.returncode != 0:
        return f"Committed but push failed: {push_r.stderr.strip()}"

    # Create PR
    pr_r = _run(["gh", "pr", "create", "--fill", "--head", branch], cwd)
    if pr_r.returncode != 0:
        # PR may already exist
        if "already exists" in pr_r.stderr.lower():
            return f"Committed and pushed. PR already exists for {branch}."
        return f"Committed and pushed but PR creation failed: {pr_r.stderr.strip()}"

    return pr_r.stdout.strip()


def git_worktree(args: str, cwd: Path) -> str:
    """List, add, or remove git worktrees."""
    parts = args.strip().split() if args.strip() else []

    if not parts or parts[0] == "list":
        r = _run(["git", "worktree", "list"], cwd)
        return r.stdout.strip() if r.returncode == 0 else r.stderr.strip()

    if parts[0] == "add" and len(parts) >= 3:
        r = _run(["git", "worktree", "add", parts[1], parts[2]], cwd)
        if r.returncode != 0:
            return r.stderr.strip()
        return f"Added worktree at {parts[1]} on branch {parts[2]}"

    if parts[0] == "remove" and len(parts) >= 2:
        r = _run(["git", "worktree", "remove", parts[1]], cwd)
        if r.returncode != 0:
            return r.stderr.strip()
        return f"Removed worktree at {parts[1]}"

    return "Usage: worktree [list | add <path> <branch> | remove <path>]"


def git_diff(cwd: Path) -> str:
    """Return working tree diff."""
    r = _run(["git", "diff"], cwd)
    if r.returncode != 0:
        return r.stderr.strip()
    return r.stdout.strip()


def git_stash(args: str, cwd: Path) -> str:
    """Stash operations: push (default), pop, list, drop."""
    subcmd = args.strip().split()[0] if args.strip() else "push"

    if subcmd == "list":
        r = _run(["git", "stash", "list"], cwd)
        return r.stdout.strip() if r.stdout.strip() else "No stashes."
    if subcmd == "pop":
        r = _run(["git", "stash", "pop"], cwd)
        return r.stdout.strip() if r.returncode == 0 else r.stderr.strip()
    if subcmd == "drop":
        r = _run(["git", "stash", "drop"], cwd)
        return r.stdout.strip() if r.returncode == 0 else r.stderr.strip()

    # Default: push
    r = _run(["git", "stash", "push"], cwd)
    if r.returncode != 0:
        return r.stderr.strip()
    return r.stdout.strip() if r.stdout.strip() else "No local changes to save."


def handle_git_command(command: str, args: str, cwd: Path) -> Optional[str]:
    """Dispatch a git slash command. Returns None for unknown commands."""
    dispatch = {
        "status": lambda: git_status(cwd),
        "branch": lambda: git_branch(args, cwd),
        "commit": lambda: git_commit(args, cwd),
        "push-pr": lambda: git_commit_push_pr(args, cwd),
        "worktree": lambda: git_worktree(args, cwd),
        "diff": lambda: git_diff(cwd),
        "stash": lambda: git_stash(args, cwd),
    }

    handler = dispatch.get(command)
    if handler is None:
        return None
    return handler()
