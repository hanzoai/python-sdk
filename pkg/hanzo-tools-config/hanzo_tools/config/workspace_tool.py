"""Workspace context tool (HIP-0300).

One tool for the Project Context axis.
Actions: detect, capabilities, help, schema
"""

from __future__ import annotations

import os
import json
import shutil
import asyncio
from typing import Any, ClassVar
from pathlib import Path

from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import BaseTool


class WorkspaceTool(BaseTool):
    """Workspace context tool (HIP-0300).

    Detects project languages, build systems, test frameworks,
    and available tool capabilities.

    Actions:
    - detect: Detect project languages, build systems, and VCS
    - capabilities: List available system tools and runtimes
    - help: Show all tool summaries
    """

    name: ClassVar[str] = "workspace"
    VERSION: ClassVar[str] = "0.1.0"

    def __init__(self, cwd: str | None = None):
        super().__init__()
        self.cwd = cwd or os.getcwd()
        self._register_workspace_actions()

    @property
    def description(self) -> str:
        return """Workspace context tool (HIP-0300).

Actions:
- detect: Detect project languages, build systems, VCS, test frameworks
- capabilities: List available system tools and runtimes
- help: Show all tool summaries
"""

    def _register_workspace_actions(self):
        """Register all workspace actions."""

        @self.action("detect", "Detect project languages, build systems, and VCS")
        async def detect(ctx: MCPContext, path: str | None = None) -> dict:
            root = Path(path or self.cwd)
            languages: list[str] = []
            build: list[str] = []
            test: list[str] = []
            vcs: str | None = None

            # VCS
            if (root / ".git").exists():
                vcs = "git"

            # Languages & build systems
            if (root / "package.json").exists():
                languages.extend(["typescript", "javascript"])
                build.append("npm")
            if (root / "tsconfig.json").exists():
                if "typescript" not in languages:
                    languages.append("typescript")
            if (root / "pyproject.toml").exists():
                languages.append("python")
                build.append("uv")
            if (root / "Cargo.toml").exists():
                languages.append("rust")
                build.append("cargo")
            if (root / "go.mod").exists():
                languages.append("go")
                build.append("go")
            if (root / "Makefile").exists():
                build.append("make")
            if (root / "compose.yml").exists():
                build.append("docker-compose")
            if (root / "Dockerfile").exists():
                build.append("docker")

            # Test frameworks
            if (root / "jest.config.ts").exists() or (root / "jest.config.js").exists():
                test.append("jest")
            if (root / "vitest.config.ts").exists():
                test.append("vitest")
            if (root / "pytest.ini").exists() or (root / "conftest.py").exists():
                test.append("pytest")

            return {
                "root": str(root),
                "languages": list(dict.fromkeys(languages)),
                "build": list(dict.fromkeys(build)),
                "test": test,
                "vcs": vcs,
            }

        @self.action("capabilities", "List available system tools and runtimes")
        async def capabilities(ctx: MCPContext) -> dict:
            has_rg = shutil.which("rg") is not None
            has_git = shutil.which("git") is not None
            has_node = shutil.which("node") is not None
            has_python = shutil.which("python3") is not None
            has_cargo = shutil.which("cargo") is not None

            return {
                "search": "ripgrep" if has_rg else "grep",
                "vcs": "git" if has_git else None,
                "runtimes": {
                    "node": has_node,
                    "python": has_python,
                    "rust": has_cargo,
                },
                "tools": [
                    "fs", "exec", "code", "git", "fetch", "computer", "workspace",
                    "browser", "think", "llm", "memory", "hanzo", "plan", "tasks", "mode",
                ],
            }

        @self.action("help", "Show all tool summaries")
        async def help_action(ctx: MCPContext) -> dict:
            return {
                "tools": {
                    "fs": "Filesystem: read, write, stat, list, mkdir, rm, apply_patch, search_text",
                    "exec": "Processes: exec, ps, kill, logs",
                    "code": "Semantics: parse, symbols, definition, references, transform, summarize",
                    "git": "Version control: status, diff, apply, commit, branch, checkout, log",
                    "fetch": "Network: search, fetch, download, crawl, head",
                    "workspace": "Workspace: detect, capabilities, help",
                    "computer": "Native OS control: click, type, screenshot, window management",
                    "browser": "Web automation: navigate, click, fill, screenshot (Playwright)",
                    "think": "Structured reasoning: think, critic, review, summarize",
                    "llm": "LLM operations: query, consensus, models, enable, disable, test",
                    "memory": "Memory: store, recall, list, delete, search, stats, clear, export, import",
                    "hanzo": "Hanzo platform: iam, kms, paas, commerce, auth, api, billing, ingress, mpc, team",
                    "plan": "Planning: create, show, update, list, next, archive, add_step, remove_step",
                    "tasks": "Tasks: list, add, update, remove, clear",
                    "mode": "Modes: list, activate, show, current",
                }
            }

    async def call(self, ctx: MCPContext, **kwargs: Any) -> str:
        """Route to action handler."""
        action = kwargs.pop("action", "help")
        return await self._dispatch(ctx, action, **kwargs)
