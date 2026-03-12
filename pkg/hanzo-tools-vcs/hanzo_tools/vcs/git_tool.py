"""Unified version control tool for HIP-0300 architecture.

This module provides a single unified 'git' tool that handles all version control operations:
- status: Working tree status
- diff: Show differences
- apply: Apply patch
- commit: Create commit
- branch: Branch operations
- checkout: Switch branches
- log: Commit history

Following Unix philosophy: one tool for the Diffs + History axis.
Outputs diffs in unified patch format; integrates with fs.apply_patch.
"""

import asyncio
import os
from typing import ClassVar

from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import (
    BaseTool,
    InvalidParamsError,
    ToolError,
)


class GitTool(BaseTool):
    """Unified version control tool (HIP-0300).

    Handles all VCS operations on a single axis:
    - status: Working tree status
    - diff: Show differences
    - apply: Apply patch
    - commit: Create commit
    - branch: Branch operations
    - checkout: Switch branches
    - log: Commit history

    Outputs diffs in unified patch format.
    """

    name: ClassVar[str] = "git"
    VERSION: ClassVar[str] = "0.12.0"

    def __init__(self, cwd: str | None = None):
        super().__init__()
        self.cwd = cwd or os.getcwd()
        self._register_vcs_actions()

    @property
    def description(self) -> str:
        return """Unified version control tool (HIP-0300).

Actions:
- status: Working tree status
- diff: Show differences (unified patch format)
- apply: Apply patch
- commit: Create commit
- branch: Branch operations (list, create, delete)
- checkout: Switch branches
- log: Commit history

Outputs diffs in unified patch format for use with fs.apply_patch.
"""

    async def _run_git(
        self,
        *args: str,
        cwd: str | None = None,
        check: bool = True,
    ) -> tuple[str, str, int]:
        """Run git command and return stdout, stderr, returncode."""
        cmd = ["git", *args]
        work_dir = cwd or self.cwd

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=work_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)

            stdout_str = stdout.decode("utf-8", errors="replace")
            stderr_str = stderr.decode("utf-8", errors="replace")

            if check and proc.returncode != 0:
                raise ToolError(
                    code="INTERNAL_ERROR",
                    message=f"git {args[0]} failed: {stderr_str}",
                    details={"returncode": proc.returncode},
                )

            return stdout_str, stderr_str, proc.returncode

        except asyncio.TimeoutError:
            raise ToolError(
                code="TIMEOUT",
                message=f"git {args[0]} timed out",
            )
        except FileNotFoundError:
            raise ToolError(
                code="NOT_FOUND",
                message="git not found in PATH",
            )

    def _register_vcs_actions(self):
        """Register all VCS actions."""

        @self.action("status", "Get working tree status")
        async def status(
            ctx: MCPContext,
            cwd: str | None = None,
        ) -> dict:
            """Get working tree status.

            Returns lists of staged, unstaged, and untracked files.
            """
            work_dir = cwd or self.cwd

            # Get status in porcelain format for parsing
            stdout, _, _ = await self._run_git(
                "status",
                "--porcelain=v2",
                "--branch",
                cwd=work_dir,
            )

            branch = None
            staged = []
            unstaged = []
            untracked = []

            for line in stdout.splitlines():
                if line.startswith("# branch.head"):
                    branch = line.split()[-1]
                elif line.startswith("1 ") or line.startswith("2 "):
                    # Changed entry
                    parts = line.split()
                    xy = parts[1]  # XY status
                    path = parts[-1]

                    if xy[0] != ".":
                        staged.append({"path": path, "status": xy[0]})
                    if xy[1] != ".":
                        unstaged.append({"path": path, "status": xy[1]})
                elif line.startswith("? "):
                    # Untracked
                    path = line[2:]
                    untracked.append({"path": path})

            return {
                "branch": branch,
                "staged": staged,
                "unstaged": unstaged,
                "untracked": untracked,
                "clean": len(staged) == 0
                and len(unstaged) == 0
                and len(untracked) == 0,
            }

        @self.action("diff", "Show differences")
        async def diff(
            ctx: MCPContext,
            ref: str | None = None,
            staged: bool = False,
            path: str | None = None,
            cwd: str | None = None,
        ) -> dict:
            """Show diff in unified patch format.

            Args:
                ref: Commit or ref to compare against
                staged: Show staged changes only
                path: Limit to specific path
                cwd: Working directory

            Returns:
                Unified diff output
            """
            work_dir = cwd or self.cwd
            args = ["diff", "--no-color"]

            if staged:
                args.append("--cached")

            if ref:
                args.append(ref)

            if path:
                args.extend(["--", path])

            stdout, _, _ = await self._run_git(*args, cwd=work_dir)

            return {
                "diff": stdout,
                "format": "unified",
                "ref": ref,
                "staged": staged,
            }

        @self.action("apply", "Apply patch")
        async def apply(
            ctx: MCPContext,
            patch: str,
            cwd: str | None = None,
            check: bool = False,
        ) -> dict:
            """Apply a unified diff patch.

            Args:
                patch: Unified diff patch content
                cwd: Working directory
                check: Only check if patch applies cleanly

            Returns:
                Success status
            """
            work_dir = cwd or self.cwd
            args = ["apply"]

            if check:
                args.append("--check")

            args.append("-")  # Read from stdin

            try:
                proc = await asyncio.create_subprocess_exec(
                    "git",
                    *args,
                    cwd=work_dir,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(patch.encode()),
                    timeout=30,
                )

                if proc.returncode != 0:
                    raise ToolError(
                        code="CONFLICT",
                        message=f"Patch failed: {stderr.decode()}",
                    )

                return {
                    "applied": not check,
                    "clean": True,
                }

            except asyncio.TimeoutError:
                raise ToolError(code="TIMEOUT", message="git apply timed out")

        @self.action("commit", "Create commit")
        async def commit(
            ctx: MCPContext,
            message: str,
            files: list[str] | None = None,
            all: bool = False,
            cwd: str | None = None,
        ) -> dict:
            """Create a commit.

            Args:
                message: Commit message
                files: Specific files to commit
                all: Stage all modified files
                cwd: Working directory

            Returns:
                Commit hash and info
            """
            work_dir = cwd or self.cwd

            # Stage files if specified
            if files:
                await self._run_git("add", *files, cwd=work_dir)
            elif all:
                await self._run_git("add", "-A", cwd=work_dir)

            # Create commit
            args = ["commit", "-m", message]
            stdout, _, _ = await self._run_git(*args, cwd=work_dir)

            # Get commit hash
            hash_stdout, _, _ = await self._run_git(
                "rev-parse",
                "HEAD",
                cwd=work_dir,
            )

            return {
                "hash": hash_stdout.strip(),
                "message": message,
                "output": stdout,
            }

        @self.action("branch", "Branch operations")
        async def branch(
            ctx: MCPContext,
            op: str = "list",  # list, create, delete
            name: str | None = None,
            cwd: str | None = None,
        ) -> dict:
            """Branch operations.

            Args:
                op: Operation - list, create, delete
                name: Branch name (for create/delete)
                cwd: Working directory

            Returns:
                Operation result
            """
            work_dir = cwd or self.cwd

            if op == "list":
                stdout, _, _ = await self._run_git(
                    "branch",
                    "-a",
                    "--format=%(refname:short)",
                    cwd=work_dir,
                )
                branches = [b.strip() for b in stdout.splitlines() if b.strip()]

                # Get current branch
                current, _, _ = await self._run_git(
                    "branch",
                    "--show-current",
                    cwd=work_dir,
                )

                return {
                    "branches": branches,
                    "current": current.strip(),
                }

            elif op == "create":
                if not name:
                    raise InvalidParamsError("Branch name required", param="name")
                await self._run_git("branch", name, cwd=work_dir)
                return {"created": name}

            elif op == "delete":
                if not name:
                    raise InvalidParamsError("Branch name required", param="name")
                await self._run_git("branch", "-d", name, cwd=work_dir)
                return {"deleted": name}

            else:
                raise InvalidParamsError(
                    f"Unknown operation: {op}",
                    param="op",
                    expected="list, create, or delete",
                )

        @self.action("checkout", "Switch branches")
        async def checkout(
            ctx: MCPContext,
            ref: str,
            create: bool = False,
            cwd: str | None = None,
        ) -> dict:
            """Switch to a branch or commit.

            Args:
                ref: Branch name or commit
                create: Create branch if it doesn't exist
                cwd: Working directory

            Returns:
                Checkout result
            """
            work_dir = cwd or self.cwd
            args = ["checkout"]

            if create:
                args.append("-b")

            args.append(ref)

            stdout, _, _ = await self._run_git(*args, cwd=work_dir)

            return {
                "ref": ref,
                "created": create,
            }

        @self.action("log", "Commit history")
        async def log(
            ctx: MCPContext,
            limit: int = 10,
            path: str | None = None,
            ref: str | None = None,
            cwd: str | None = None,
        ) -> dict:
            """Get commit history.

            Args:
                limit: Number of commits
                path: Filter by path
                ref: Starting ref
                cwd: Working directory

            Returns:
                List of commits
            """
            work_dir = cwd or self.cwd
            args = [
                "log",
                f"-{limit}",
                "--format=format:%H|%an|%ae|%at|%s",
            ]

            if ref:
                args.append(ref)

            if path:
                args.extend(["--", path])

            stdout, _, _ = await self._run_git(*args, cwd=work_dir)

            commits = []
            for line in stdout.splitlines():
                if not line:
                    continue
                parts = line.split("|", 4)
                if len(parts) >= 5:
                    commits.append(
                        {
                            "hash": parts[0],
                            "author": parts[1],
                            "email": parts[2],
                            "timestamp": int(parts[3]),
                            "message": parts[4],
                        }
                    )

            return {
                "commits": commits,
                "total": len(commits),
            }

        # ── Advanced actions (TS parity) ──────────────────────────────────

        @self.action("blame", "Show line-by-line authorship")
        async def blame(ctx: MCPContext, path: str, cwd: str | None = None) -> dict:
            work_dir = cwd or self.cwd
            stdout, _, _ = await self._run_git("blame", "--porcelain", path, cwd=work_dir)
            return {"blame": stdout, "path": path}

        @self.action("show", "Show commit or object")
        async def show(ctx: MCPContext, ref: str = "HEAD", cwd: str | None = None) -> dict:
            work_dir = cwd or self.cwd
            stdout, _, _ = await self._run_git("show", "--stat", ref, cwd=work_dir)
            return {"output": stdout, "ref": ref}

        @self.action("stash", "Stash operations")
        async def stash(ctx: MCPContext, op: str = "list", message: str | None = None, cwd: str | None = None) -> dict:
            work_dir = cwd or self.cwd
            if op == "push":
                args = ["stash", "push"]
                if message:
                    args.extend(["-m", message])
                stdout, _, _ = await self._run_git(*args, cwd=work_dir)
            elif op == "pop":
                stdout, _, _ = await self._run_git("stash", "pop", cwd=work_dir)
            elif op == "drop":
                stdout, _, _ = await self._run_git("stash", "drop", cwd=work_dir)
            else:
                stdout, _, _ = await self._run_git("stash", "list", cwd=work_dir)
            return {"output": stdout, "op": op}

        @self.action("tag", "Tag operations")
        async def tag(ctx: MCPContext, op: str = "list", name: str | None = None, message: str | None = None, ref: str | None = None, cwd: str | None = None) -> dict:
            work_dir = cwd or self.cwd
            if op == "create":
                if not name:
                    raise InvalidParamsError("Tag name required", param="name")
                args = ["tag"]
                if message:
                    args.extend(["-a", name, "-m", message])
                else:
                    args.append(name)
                if ref:
                    args.append(ref)
                stdout, _, _ = await self._run_git(*args, cwd=work_dir)
                return {"created": name}
            elif op == "delete":
                if not name:
                    raise InvalidParamsError("Tag name required", param="name")
                stdout, _, _ = await self._run_git("tag", "-d", name, cwd=work_dir)
                return {"deleted": name}
            else:
                stdout, _, _ = await self._run_git("tag", "-l", cwd=work_dir)
                return {"tags": stdout.splitlines()}

        @self.action("remote", "Remote operations")
        async def remote(ctx: MCPContext, op: str = "list", name: str | None = None, url: str | None = None, cwd: str | None = None) -> dict:
            work_dir = cwd or self.cwd
            if op == "add":
                if not name or not url:
                    raise InvalidParamsError("name and url required", param="name")
                stdout, _, _ = await self._run_git("remote", "add", name, url, cwd=work_dir)
                return {"added": name, "url": url}
            elif op == "remove":
                if not name:
                    raise InvalidParamsError("Remote name required", param="name")
                stdout, _, _ = await self._run_git("remote", "remove", name, cwd=work_dir)
                return {"removed": name}
            else:
                stdout, _, _ = await self._run_git("remote", "-v", cwd=work_dir)
                return {"remotes": stdout}

        @self.action("merge", "Merge branches")
        async def merge(ctx: MCPContext, ref: str, message: str | None = None, no_ff: bool = False, cwd: str | None = None) -> dict:
            work_dir = cwd or self.cwd
            args = ["merge"]
            if no_ff:
                args.append("--no-ff")
            if message:
                args.extend(["-m", message])
            args.append(ref)
            stdout, _, _ = await self._run_git(*args, cwd=work_dir, check=False)
            return {"output": stdout, "ref": ref}

        @self.action("rebase", "Rebase commits")
        async def rebase(ctx: MCPContext, ref: str | None = None, op: str = "start", cwd: str | None = None) -> dict:
            work_dir = cwd or self.cwd
            if op == "abort":
                stdout, _, _ = await self._run_git("rebase", "--abort", cwd=work_dir)
            elif op == "continue":
                stdout, _, _ = await self._run_git("rebase", "--continue", cwd=work_dir)
            else:
                if not ref:
                    raise InvalidParamsError("ref required for rebase", param="ref")
                stdout, _, _ = await self._run_git("rebase", ref, cwd=work_dir)
            return {"output": stdout, "op": op}

        @self.action("cherry_pick", "Cherry-pick commits")
        async def cherry_pick(ctx: MCPContext, ref: str, cwd: str | None = None) -> dict:
            work_dir = cwd or self.cwd
            stdout, _, _ = await self._run_git("cherry-pick", ref, cwd=work_dir)
            return {"output": stdout, "ref": ref}

        @self.action("reset", "Reset HEAD")
        async def reset(ctx: MCPContext, ref: str = "HEAD", mode: str = "mixed", cwd: str | None = None) -> dict:
            work_dir = cwd or self.cwd
            stdout, _, _ = await self._run_git("reset", f"--{mode}", ref, cwd=work_dir)
            return {"output": stdout, "ref": ref, "mode": mode}

        @self.action("clean", "Remove untracked files")
        async def clean(ctx: MCPContext, force: bool = False, directories: bool = False, dry_run: bool = True, cwd: str | None = None) -> dict:
            work_dir = cwd or self.cwd
            args = ["clean"]
            if dry_run:
                args.append("-n")
            if force:
                args.append("-f")
            if directories:
                args.append("-d")
            stdout, _, _ = await self._run_git(*args, cwd=work_dir)
            return {"output": stdout, "dry_run": dry_run}

        @self.action("init", "Initialize repository")
        async def init(ctx: MCPContext, path: str | None = None, bare: bool = False, cwd: str | None = None) -> dict:
            args = ["init"]
            if bare:
                args.append("--bare")
            if path:
                args.append(path)
            stdout, _, _ = await self._run_git(*args, cwd=cwd or self.cwd)
            return {"output": stdout}

        @self.action("clone", "Clone repository")
        async def clone(ctx: MCPContext, url: str, path: str | None = None, depth: int | None = None, cwd: str | None = None) -> dict:
            work_dir = cwd or self.cwd
            args = ["clone"]
            if depth:
                args.extend(["--depth", str(depth)])
            args.append(url)
            if path:
                args.append(path)
            stdout, _, _ = await self._run_git(*args, cwd=work_dir)
            return {"output": stdout, "url": url}

        @self.action("fetch", "Fetch from remote")
        async def fetch(ctx: MCPContext, remote: str = "origin", prune: bool = False, cwd: str | None = None) -> dict:
            work_dir = cwd or self.cwd
            args = ["fetch", remote]
            if prune:
                args.append("--prune")
            stdout, _, _ = await self._run_git(*args, cwd=work_dir)
            return {"output": stdout, "remote": remote}

        @self.action("pull", "Pull from remote")
        async def pull(ctx: MCPContext, remote: str = "origin", branch: str | None = None, rebase: bool = False, cwd: str | None = None) -> dict:
            work_dir = cwd or self.cwd
            args = ["pull"]
            if rebase:
                args.append("--rebase")
            args.append(remote)
            if branch:
                args.append(branch)
            stdout, _, _ = await self._run_git(*args, cwd=work_dir)
            return {"output": stdout}

        @self.action("push", "Push to remote")
        async def push(ctx: MCPContext, remote: str = "origin", branch: str | None = None, force: bool = False, tags: bool = False, cwd: str | None = None) -> dict:
            work_dir = cwd or self.cwd
            args = ["push"]
            if force:
                args.append("--force-with-lease")
            if tags:
                args.append("--tags")
            args.append(remote)
            if branch:
                args.append(branch)
            stdout, _, _ = await self._run_git(*args, cwd=work_dir)
            return {"output": stdout}

        @self.action("config", "Get/set config")
        async def config(ctx: MCPContext, key: str | None = None, value: str | None = None, scope: str = "local", cwd: str | None = None) -> dict:
            work_dir = cwd or self.cwd
            if key and value:
                stdout, _, _ = await self._run_git("config", f"--{scope}", key, value, cwd=work_dir)
                return {"set": key, "value": value}
            elif key:
                stdout, _, _ = await self._run_git("config", "--get", key, cwd=work_dir, check=False)
                return {"key": key, "value": stdout.strip()}
            else:
                stdout, _, _ = await self._run_git("config", "--list", f"--{scope}", cwd=work_dir)
                return {"config": stdout}

        @self.action("worktree", "Worktree operations")
        async def worktree(ctx: MCPContext, op: str = "list", path: str | None = None, branch: str | None = None, cwd: str | None = None) -> dict:
            work_dir = cwd or self.cwd
            if op == "add":
                if not path:
                    raise InvalidParamsError("path required", param="path")
                args = ["worktree", "add", path]
                if branch:
                    args.extend(["-b", branch])
                stdout, _, _ = await self._run_git(*args, cwd=work_dir)
            elif op == "remove":
                if not path:
                    raise InvalidParamsError("path required", param="path")
                stdout, _, _ = await self._run_git("worktree", "remove", path, cwd=work_dir)
            else:
                stdout, _, _ = await self._run_git("worktree", "list", cwd=work_dir)
            return {"output": stdout, "op": op}

        @self.action("reflog", "Show reflog")
        async def reflog(ctx: MCPContext, limit: int = 20, ref: str = "HEAD", cwd: str | None = None) -> dict:
            work_dir = cwd or self.cwd
            stdout, _, _ = await self._run_git("reflog", f"-{limit}", ref, cwd=work_dir)
            return {"output": stdout}

        @self.action("shortlog", "Summarize commits by author")
        async def shortlog(ctx: MCPContext, ref: str | None = None, cwd: str | None = None) -> dict:
            work_dir = cwd or self.cwd
            args = ["shortlog", "-sne"]
            if ref:
                args.append(ref)
            stdout, _, _ = await self._run_git(*args, cwd=work_dir)
            return {"output": stdout}

        @self.action("rev_parse", "Parse revision")
        async def rev_parse(ctx: MCPContext, ref: str = "HEAD", cwd: str | None = None) -> dict:
            work_dir = cwd or self.cwd
            stdout, _, _ = await self._run_git("rev-parse", ref, cwd=work_dir)
            return {"sha": stdout.strip(), "ref": ref}

        @self.action("describe", "Describe commit with tags")
        async def describe(ctx: MCPContext, ref: str | None = None, tags: bool = True, cwd: str | None = None) -> dict:
            work_dir = cwd or self.cwd
            args = ["describe"]
            if tags:
                args.append("--tags")
            args.append("--always")
            if ref:
                args.append(ref)
            stdout, _, _ = await self._run_git(*args, cwd=work_dir, check=False)
            return {"description": stdout.strip()}

        @self.action("bisect", "Binary search for bugs")
        async def bisect(ctx: MCPContext, op: str = "start", ref: str | None = None, cwd: str | None = None) -> dict:
            work_dir = cwd or self.cwd
            if op == "start":
                stdout, _, _ = await self._run_git("bisect", "start", cwd=work_dir)
            elif op == "good":
                args = ["bisect", "good"]
                if ref:
                    args.append(ref)
                stdout, _, _ = await self._run_git(*args, cwd=work_dir)
            elif op == "bad":
                args = ["bisect", "bad"]
                if ref:
                    args.append(ref)
                stdout, _, _ = await self._run_git(*args, cwd=work_dir)
            elif op == "reset":
                stdout, _, _ = await self._run_git("bisect", "reset", cwd=work_dir)
            else:
                stdout, _, _ = await self._run_git("bisect", "log", cwd=work_dir, check=False)
            return {"output": stdout, "op": op}

# Backward compatibility
git_tool = GitTool
