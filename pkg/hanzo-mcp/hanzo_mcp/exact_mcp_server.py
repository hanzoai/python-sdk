#!/usr/bin/env python3
"""
Enhanced MCP Server with Exact 6-Tool Implementation
====================================================

Precise implementation of the 6 universal tools according to specification.
"""

import asyncio
from typing import List

from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.types import (
    TextContent,
    Tool,
)

from .exact_tools import (
    BuildArgs,
    EditArgs,
    FmtArgs,
    GuardArgs,
    GuardRule,
    LintArgs,
    TargetSpec,
    TestArgs,
    tools,
)


class ExactHanzoMCPServer:
    """Enhanced MCP server with exact 6-tool specification"""

    def __init__(self):
        self.server = Server("hanzo-mcp-exact")
        self.setup_handlers()

    def setup_handlers(self):
        """Set up MCP server handlers with exact tool specifications"""

        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List the exact 6 universal tools"""
            return [
                Tool(
                    name="edit",
                    description="Semantic refactors via LSP across languages",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "target": {
                                "type": "string",
                                "description": "Target: file:<path>, dir:<path>, pkg:<spec>, ws, or changed",
                            },
                            "language": {
                                "type": "string",
                                "enum": [
                                    "auto",
                                    "go",
                                    "ts",
                                    "py",
                                    "rs",
                                    "cc",
                                    "sol",
                                    "schema",
                                ],
                                "default": "auto",
                                "description": "Language override",
                            },
                            "backend": {
                                "type": "string",
                                "default": "auto",
                                "description": "Backend override",
                            },
                            "root": {
                                "type": "string",
                                "description": "Explicit workspace root override",
                            },
                            "env": {
                                "type": "object",
                                "additionalProperties": {"type": "string"},
                                "description": "Extra environment variables",
                            },
                            "dry_run": {
                                "type": "boolean",
                                "default": False,
                                "description": "Preview mode - no file writes",
                            },
                            "op": {
                                "type": "string",
                                "enum": [
                                    "rename",
                                    "code_action",
                                    "organize_imports",
                                    "apply_workspace_edit",
                                ],
                                "description": "Operation to perform",
                            },
                            "file": {
                                "type": "string",
                                "description": "File path for rename/code_action operations",
                            },
                            "pos": {
                                "type": "object",
                                "properties": {
                                    "line": {"type": "integer"},
                                    "character": {"type": "integer"},
                                },
                                "description": "Position for rename/code_action",
                            },
                            "range": {
                                "type": "object",
                                "properties": {
                                    "start": {
                                        "type": "object",
                                        "properties": {
                                            "line": {"type": "integer"},
                                            "character": {"type": "integer"},
                                        },
                                    },
                                    "end": {
                                        "type": "object",
                                        "properties": {
                                            "line": {"type": "integer"},
                                            "character": {"type": "integer"},
                                        },
                                    },
                                },
                                "description": "Range for code actions",
                            },
                            "new_name": {
                                "type": "string",
                                "description": "New name for rename operation",
                            },
                            "only": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "LSP codeAction kinds filter",
                            },
                            "apply": {
                                "type": "boolean",
                                "default": True,
                                "description": "Apply edits to disk",
                            },
                            "workspace_edit": {
                                "type": "object",
                                "description": "WorkspaceEdit payload for apply_workspace_edit",
                            },
                        },
                        "required": ["target", "op"],
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="fmt",
                    description="Formatting + import normalization",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "target": {
                                "type": "string",
                                "description": "Target: file:<path>, dir:<path>, pkg:<spec>, ws, or changed",
                            },
                            "language": {
                                "type": "string",
                                "enum": [
                                    "auto",
                                    "go",
                                    "ts",
                                    "py",
                                    "rs",
                                    "cc",
                                    "sol",
                                    "schema",
                                ],
                                "default": "auto",
                            },
                            "backend": {
                                "type": "string",
                                "default": "auto",
                                "description": "Backend override (goimports, prettier, ruff, etc.)",
                            },
                            "root": {
                                "type": "string",
                                "description": "Workspace root override",
                            },
                            "env": {
                                "type": "object",
                                "additionalProperties": {"type": "string"},
                                "description": "Environment variables",
                            },
                            "dry_run": {"type": "boolean", "default": False},
                            "opts": {
                                "type": "object",
                                "properties": {
                                    "local_prefix": {
                                        "type": "string",
                                        "description": "Go import grouping prefix (e.g. github.com/luxfi)",
                                    }
                                },
                                "description": "Tool-specific options",
                            },
                        },
                        "required": ["target"],
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="test",
                    description="Run tests narrowly by default",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "target": {
                                "type": "string",
                                "description": "Target: file:<path>, dir:<path>, pkg:<spec>, ws, or changed",
                            },
                            "language": {
                                "type": "string",
                                "enum": [
                                    "auto",
                                    "go",
                                    "ts",
                                    "py",
                                    "rs",
                                    "cc",
                                    "sol",
                                    "schema",
                                ],
                                "default": "auto",
                            },
                            "backend": {
                                "type": "string",
                                "default": "auto",
                                "description": "Backend override (go, npm, pytest, cargo, etc.)",
                            },
                            "root": {
                                "type": "string",
                                "description": "Workspace root override",
                            },
                            "env": {
                                "type": "object",
                                "additionalProperties": {"type": "string"},
                            },
                            "dry_run": {"type": "boolean", "default": False},
                            "opts": {
                                "type": "object",
                                "properties": {
                                    "run": {
                                        "type": "string",
                                        "description": "Go test filter",
                                    },
                                    "count": {
                                        "type": "integer",
                                        "description": "Go test count",
                                    },
                                    "race": {
                                        "type": "boolean",
                                        "description": "Go race detection",
                                    },
                                    "filter": {
                                        "type": "string",
                                        "description": "TS test filter",
                                    },
                                    "watch": {
                                        "type": "boolean",
                                        "description": "TS watch mode",
                                    },
                                    "k": {
                                        "type": "string",
                                        "description": "Python test filter",
                                    },
                                    "m": {
                                        "type": "string",
                                        "description": "Python test marker",
                                    },
                                    "p": {
                                        "type": "string",
                                        "description": "Rust package",
                                    },
                                    "features": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "Rust features",
                                    },
                                },
                                "description": "Test-specific options",
                            },
                        },
                        "required": ["target"],
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="build",
                    description="Compile/build artifacts narrowly by default",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "target": {
                                "type": "string",
                                "description": "Target: file:<path>, dir:<path>, pkg:<spec>, ws, or changed",
                            },
                            "language": {
                                "type": "string",
                                "enum": [
                                    "auto",
                                    "go",
                                    "ts",
                                    "py",
                                    "rs",
                                    "cc",
                                    "sol",
                                    "schema",
                                ],
                                "default": "auto",
                            },
                            "backend": {
                                "type": "string",
                                "default": "auto",
                                "description": "Backend override",
                            },
                            "root": {
                                "type": "string",
                                "description": "Workspace root override",
                            },
                            "env": {
                                "type": "object",
                                "additionalProperties": {"type": "string"},
                            },
                            "dry_run": {"type": "boolean", "default": False},
                            "opts": {
                                "type": "object",
                                "properties": {
                                    "release": {
                                        "type": "boolean",
                                        "description": "Release build",
                                    },
                                    "features": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                },
                                "description": "Build-specific options",
                            },
                        },
                        "required": ["target"],
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="lint",
                    description="Lint/typecheck in one place",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "target": {
                                "type": "string",
                                "description": "Target: file:<path>, dir:<path>, pkg:<spec>, ws, or changed",
                            },
                            "language": {
                                "type": "string",
                                "enum": [
                                    "auto",
                                    "go",
                                    "ts",
                                    "py",
                                    "rs",
                                    "cc",
                                    "sol",
                                    "schema",
                                ],
                                "default": "auto",
                            },
                            "backend": {
                                "type": "string",
                                "default": "auto",
                                "description": "Backend override",
                            },
                            "root": {
                                "type": "string",
                                "description": "Workspace root override",
                            },
                            "env": {
                                "type": "object",
                                "additionalProperties": {"type": "string"},
                            },
                            "dry_run": {"type": "boolean", "default": False},
                            "opts": {
                                "type": "object",
                                "properties": {
                                    "fix": {
                                        "type": "boolean",
                                        "description": "Auto-fix issues where possible",
                                    }
                                },
                                "description": "Lint-specific options",
                            },
                        },
                        "required": ["target"],
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="guard",
                    description="Repo invariants (boundaries, forbidden imports/strings, generated dirs)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "target": {
                                "type": "string",
                                "description": "Target: file:<path>, dir:<path>, pkg:<spec>, ws, or changed",
                            },
                            "language": {
                                "type": "string",
                                "enum": [
                                    "auto",
                                    "go",
                                    "ts",
                                    "py",
                                    "rs",
                                    "cc",
                                    "sol",
                                    "schema",
                                ],
                                "default": "auto",
                            },
                            "backend": {"type": "string", "default": "auto"},
                            "root": {
                                "type": "string",
                                "description": "Workspace root override",
                            },
                            "env": {
                                "type": "object",
                                "additionalProperties": {"type": "string"},
                            },
                            "dry_run": {"type": "boolean", "default": False},
                            "rules": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "string"},
                                        "type": {
                                            "type": "string",
                                            "enum": ["regex", "import", "generated"],
                                        },
                                        "glob": {"type": "string"},
                                        "pattern": {"type": "string"},
                                        "forbid_import_prefix": {"type": "string"},
                                        "forbid_writes": {"type": "boolean"},
                                    },
                                    "required": ["id", "type", "glob"],
                                },
                                "description": "Guard rules to check",
                            },
                        },
                        "required": ["target", "rules"],
                        "additionalProperties": False,
                    },
                ),
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> List[TextContent]:
            """Handle tool calls with exact specifications"""
            try:
                # Create target spec from common arguments
                target_spec = TargetSpec(
                    target=arguments["target"],
                    language=arguments.get("language", "auto"),
                    backend=arguments.get("backend", "auto"),
                    root=arguments.get("root"),
                    env=arguments.get("env", {}),
                    dry_run=arguments.get("dry_run", False),
                )

                if name == "edit":
                    edit_args = EditArgs(
                        op=arguments["op"],
                        file=arguments.get("file"),
                        pos=arguments.get("pos"),
                        range=arguments.get("range"),
                        new_name=arguments.get("new_name"),
                        only=arguments.get("only", []),
                        apply=arguments.get("apply", True),
                        workspace_edit=arguments.get("workspace_edit"),
                    )
                    result = await tools.edit(target_spec, edit_args)

                elif name == "fmt":
                    fmt_args = FmtArgs(opts=arguments.get("opts", {}))
                    result = await tools.fmt(target_spec, fmt_args)

                elif name == "test":
                    test_args = TestArgs(opts=arguments.get("opts", {}))
                    result = await tools.test(target_spec, test_args)

                elif name == "build":
                    build_args = BuildArgs(opts=arguments.get("opts", {}))
                    result = await tools.build(target_spec, build_args)

                elif name == "lint":
                    lint_args = LintArgs(opts=arguments.get("opts", {}))
                    result = await tools.lint(target_spec, lint_args)

                elif name == "guard":
                    rules = [GuardRule(**rule_data) for rule_data in arguments["rules"]]
                    guard_args = GuardArgs(rules=rules)
                    result = await tools.guard(target_spec, guard_args)

                else:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]

                return [
                    TextContent(
                        type="text", text=self._format_exact_result(result, name)
                    )
                ]

            except Exception as e:
                return [
                    TextContent(type="text", text=f"Error executing {name}: {str(e)}")
                ]

    def _format_exact_result(self, result, tool_name: str) -> str:
        """Format tool result according to exact specification"""
        status = "✅" if result.ok else "❌"

        output = f"=== {tool_name.upper()} RESULT ===\n"
        output += f"Status: {status} {result.ok}\n"
        output += f"Root: {result.root}\n"
        output += f"Language: {result.language_used}\n"
        output += f"Backend: {result.backend_used}\n"
        output += f"Scope: {result.scope_resolved}\n"
        output += f"Touched files: {len(result.touched_files)}\n"
        output += f"Exit code: {result.exit_code}\n"
        output += f"Execution time: {result.execution_time:.3f}s\n"

        if result.touched_files:
            output += "\nModified files:\n"
            for f in result.touched_files:
                output += f"  - {f}\n"

        if result.stdout:
            output += f"\nSTDOUT:\n{result.stdout}\n"

        if result.stderr:
            output += f"\nSTDERR:\n{result.stderr}\n"

        if result.errors:
            output += "\nErrors:\n"
            for error in result.errors:
                output += f"  - {error}\n"

        return output

    async def run(self, transport_type: str = "stdio"):
        """Run the exact MCP server"""
        if transport_type == "stdio":
            from mcp.server.stdio import stdio_server

            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name="hanzo-mcp-exact",
                        server_version="1.0.0",
                        capabilities=self.server.get_capabilities(
                            notification_options=NotificationOptions(),
                            experimental_capabilities={},
                        ),
                    ),
                )


if __name__ == "__main__":
    server = ExactHanzoMCPServer()
    asyncio.run(server.run())
