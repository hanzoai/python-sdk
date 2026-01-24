"""Unified version control tool for HIP-0300 architecture.

This module provides a single unified 'vcs' tool that handles all version control operations:
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

import os
import json
import asyncio
import subprocess
from typing import Any, Optional, ClassVar
from pathlib import Path

from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import (
    BaseTool,
    ToolError,
    InvalidParamsError,
    NotFoundError,
    Paging,
    file_uri,
)


class VcsTool(BaseTool):
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

    name: ClassVar[str] = "vcs"
    VERSION: ClassVar[str] = "0.12.0"

    def __init__(self, cwd: Optional[str] = None):
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
        cwd: Optional[str] = None,
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
                "status", "--porcelain=v2", "--branch",
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
                "clean": len(staged) == 0 and len(unstaged) == 0 and len(untracked) == 0,
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
                    "git", *args,
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
                "rev-parse", "HEAD",
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
                    "branch", "-a", "--format=%(refname:short)",
                    cwd=work_dir,
                )
                branches = [b.strip() for b in stdout.splitlines() if b.strip()]

                # Get current branch
                current, _, _ = await self._run_git(
                    "branch", "--show-current",
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
                    commits.append({
                        "hash": parts[0],
                        "author": parts[1],
                        "email": parts[2],
                        "timestamp": int(parts[3]),
                        "message": parts[4],
                    })

            return {
                "commits": commits,
                "total": len(commits),
            }

    def register(self, mcp_server: FastMCP) -> None:
        """Register as 'vcs' tool with MCP server."""
        tool_name = self.name
        tool_description = self.description

        @mcp_server.tool(name=tool_name, description=tool_description)
        async def handler(
            ctx: MCPContext,
            action: str = "help",
            **kwargs: Any,
        ) -> str:
            result = await self.call(ctx, action=action, **kwargs)
            return json.dumps(result, indent=2, default=str)


# Backward compatibility
vcs_tool = VcsTool
