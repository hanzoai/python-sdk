#!/usr/bin/env python3
"""
Hanzo Development Tools - Unified 6-Tool Implementation
======================================================

Complete implementation of the 6 universal development tools:
edit, fmt, test, build, lint, guard

Features:
- Workspace detection (go.work, package.json, pyproject.toml, Cargo.toml, etc.)
- Multi-language support with proper backend selection
- Session tracking and codebase intelligence
- LSP integration for semantic operations
- Target resolution (file:, dir:, pkg:, ws, changed)
- Unified backend with SQLite vector storage
"""

import os
import json
import uuid
import asyncio
import logging
import sqlite3
import subprocess
from typing import Any, Dict, List, Union, Literal, Optional
from pathlib import Path
from datetime import datetime
from dataclasses import asdict, dataclass

from pydantic import Field, BaseModel
from hanzo_tools.lsp.lsp_tool import LSPTool

from .unified_backend import TargetSpec, ToolResult, UnifiedBackend

logger = logging.getLogger(__name__)


class DevToolsCore:
    """Core implementation of the 6 universal development tools"""

    def __init__(self):
        self.backend = UnifiedBackend()
        self.session_id = str(uuid.uuid4())

    async def edit(
        self,
        target: str,
        op: Literal["rename", "code_action", "organize_imports", "apply_workspace_edit"],
        file: Optional[str] = None,
        pos: Optional[Dict[str, int]] = None,
        range_: Optional[Dict[str, Dict[str, int]]] = None,
        new_name: Optional[str] = None,
        only: List[str] = None,
        apply: bool = True,
        workspace_edit: Optional[Dict[str, Any]] = None,
        **target_opts,
    ) -> ToolResult:
        """Semantic refactors via LSP across languages"""
        target_spec = TargetSpec(target=target, **target_opts)

        args = {
            "op": op,
            "file": file,
            "pos": pos,
            "range": range_,
            "new_name": new_name,
            "only": only or [],
            "apply": apply,
            "workspace_edit": workspace_edit,
        }

        result = await self.backend.execute_edit(target_spec, args)
        await self.backend.log_execution("edit", args, result)
        return result

    async def fmt(self, target: str, local_prefix: Optional[str] = None, **target_opts) -> ToolResult:
        """Format code and organize imports"""
        target_spec = TargetSpec(target=target, **target_opts)

        args = {"opts": {"local_prefix": local_prefix} if local_prefix else {}}

        result = await self.backend.execute_fmt(target_spec, args)
        await self.backend.log_execution("fmt", args, result)
        return result

    async def test(
        self,
        target: str,
        run: Optional[str] = None,
        count: Optional[int] = None,
        race: Optional[bool] = None,
        filter_: Optional[str] = None,
        watch: Optional[bool] = None,
        **target_opts,
    ) -> ToolResult:
        """Run tests narrowly by default"""
        target_spec = TargetSpec(target=target, **target_opts)

        args = {
            "opts": {
                k: v
                for k, v in {"run": run, "count": count, "race": race, "filter": filter_, "watch": watch}.items()
                if v is not None
            }
        }

        result = await self.backend.execute_test(target_spec, args)
        await self.backend.log_execution("test", args, result)
        return result

    async def build(
        self, target: str, release: Optional[bool] = None, features: Optional[List[str]] = None, **target_opts
    ) -> ToolResult:
        """Compile/build artifacts narrowly by default"""
        target_spec = TargetSpec(target=target, **target_opts)

        args = {"opts": {k: v for k, v in {"release": release, "features": features}.items() if v is not None}}

        result = await self.backend.execute_build(target_spec, args)
        await self.backend.log_execution("build", args, result)
        return result

    async def lint(self, target: str, fix: Optional[bool] = None, **target_opts) -> ToolResult:
        """Lint and typecheck code"""
        target_spec = TargetSpec(target=target, **target_opts)

        args = {"opts": {"fix": fix} if fix is not None else {}}

        result = await self.backend.execute_lint(target_spec, args)
        await self.backend.log_execution("lint", args, result)
        return result

    async def guard(self, target: str, rules: Optional[List[Dict[str, Any]]] = None, **target_opts) -> ToolResult:
        """Check repository invariants and boundaries"""
        target_spec = TargetSpec(target=target, **target_opts)

        args = {"rules": rules or []}

        result = await self.backend.execute_guard(target_spec, args)
        await self.backend.log_execution("guard", args, result)
        return result

    # Composition patterns
    async def multi_language_rename(
        self, symbol_name: str, new_name: str, languages: List[str], workspace: str = "ws"
    ) -> List[ToolResult]:
        """Multi-language rename operation"""
        results = []

        for lang in languages:
            result = await self.edit(target=workspace, op="rename", new_name=new_name, language=lang)
            results.append(result)

        # Format changed files
        changed_result = await self.fmt(target="changed")
        results.append(changed_result)

        # Run tests
        test_result = await self.test(target="ws")
        results.append(test_result)

        # Check guards
        guard_result = await self.guard(target="ws")
        results.append(guard_result)

        return results

    async def wide_refactor_go_workspace(self, workspace: str = "ws") -> List[ToolResult]:
        """Wide refactor in Go workspace"""
        results = []

        # Fix all and organize imports
        edit_result = await self.edit(
            target=f"pkg:./...", op="code_action", only=["source.fixAll", "source.organizeImports"], language="go"
        )
        results.append(edit_result)

        # Format with local prefix
        fmt_result = await self.fmt(target="pkg:./...", local_prefix="github.com/luxfi")
        results.append(fmt_result)

        # Test
        test_result = await self.test(target="pkg:./...")
        results.append(test_result)

        # Guard
        guard_result = await self.guard(
            target=workspace,
            rules=[
                {
                    "id": "no_node_in_sdk",
                    "type": "import",
                    "glob": "sdk/**",
                    "forbid_import_prefix": "github.com/luxfi/node/",
                },
                {"id": "no_generated_edits", "type": "generated", "glob": "api/pb/**", "forbid_writes": True},
            ],
        )
        results.append(guard_result)

        return results


# MCP Tool wrappers for the 6 universal tools
async def mcp_edit(
    target: str,
    op: str,
    file: Optional[str] = None,
    pos: Optional[Dict[str, int]] = None,
    range_: Optional[Dict[str, Dict[str, int]]] = None,
    new_name: Optional[str] = None,
    only: Optional[List[str]] = None,
    apply: bool = True,
    workspace_edit: Optional[Dict[str, Any]] = None,
    language: str = "auto",
    backend: str = "auto",
    root: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """MCP wrapper for edit tool"""
    tools = DevToolsCore()
    result = await tools.edit(
        target=target,
        op=op,
        file=file,
        pos=pos,
        range_=range_,
        new_name=new_name,
        only=only or [],
        apply=apply,
        workspace_edit=workspace_edit,
        language=language,
        backend=backend,
        root=root,
        env=env or {},
        dry_run=dry_run,
    )
    return asdict(result)


async def mcp_fmt(
    target: str,
    local_prefix: Optional[str] = None,
    language: str = "auto",
    backend: str = "auto",
    root: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """MCP wrapper for fmt tool"""
    tools = DevToolsCore()
    result = await tools.fmt(
        target=target,
        local_prefix=local_prefix,
        language=language,
        backend=backend,
        root=root,
        env=env or {},
        dry_run=dry_run,
    )
    return asdict(result)


async def mcp_test(
    target: str,
    run: Optional[str] = None,
    count: Optional[int] = None,
    race: Optional[bool] = None,
    filter_: Optional[str] = None,
    watch: Optional[bool] = None,
    language: str = "auto",
    backend: str = "auto",
    root: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """MCP wrapper for test tool"""
    tools = DevToolsCore()
    result = await tools.test(
        target=target,
        run=run,
        count=count,
        race=race,
        filter_=filter_,
        watch=watch,
        language=language,
        backend=backend,
        root=root,
        env=env or {},
        dry_run=dry_run,
    )
    return asdict(result)


async def mcp_build(
    target: str,
    release: Optional[bool] = None,
    features: Optional[List[str]] = None,
    language: str = "auto",
    backend: str = "auto",
    root: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """MCP wrapper for build tool"""
    tools = DevToolsCore()
    result = await tools.build(
        target=target,
        release=release,
        features=features,
        language=language,
        backend=backend,
        root=root,
        env=env or {},
        dry_run=dry_run,
    )
    return asdict(result)


async def mcp_lint(
    target: str,
    fix: Optional[bool] = None,
    language: str = "auto",
    backend: str = "auto",
    root: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """MCP wrapper for lint tool"""
    tools = DevToolsCore()
    result = await tools.lint(
        target=target, fix=fix, language=language, backend=backend, root=root, env=env or {}, dry_run=dry_run
    )
    return asdict(result)


async def mcp_guard(
    target: str,
    rules: Optional[List[Dict[str, Any]]] = None,
    language: str = "auto",
    backend: str = "auto",
    root: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """MCP wrapper for guard tool"""
    tools = DevToolsCore()
    result = await tools.guard(
        target=target, rules=rules, language=language, backend=backend, root=root, env=env or {}, dry_run=dry_run
    )
    return asdict(result)


def main():
    """CLI entry point"""
    import sys
    import asyncio

    from .dev_cli import main as cli_main

    sys.exit(asyncio.run(cli_main()))
