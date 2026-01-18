#!/usr/bin/env python3
"""
Enhanced Hanzo MCP Server
========================

MCP server implementation that exposes the 6 universal tools via Model Context Protocol.
Now includes the new unified development tools (edit, fmt, test, build, lint, guard)
plus the existing tool suite.
"""

import asyncio
from typing import List

from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.types import (
    TextContent,
    Tool,
)

from .tools.dev_tools_mcp import dev_tools_server
from .unified_backend import TargetSpec, ToolResult, backend


class HanzoMCPServer:
    """Enhanced MCP server with 6 universal tools"""

    def __init__(self):
        self.server = Server("hanzo-mcp")
        self.dev_tools_server = dev_tools_server  # New orthogonal dev tools
        self.setup_handlers()

    def setup_handlers(self):
        """Set up MCP server handlers"""

        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available tools"""
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
                            "op": {
                                "type": "string",
                                "enum": ["rename", "code_action", "organize_imports", "apply_workspace_edit"],
                                "description": "Operation to perform",
                            },
                            "language": {
                                "type": "string",
                                "default": "auto",
                                "description": "Language override (auto, go, ts, py, rs, cc, sol)",
                            },
                            "backend": {"type": "string", "default": "auto", "description": "Backend override"},
                            "root": {"type": "string", "description": "Workspace root override"},
                            "env": {
                                "type": "object",
                                "additionalProperties": {"type": "string"},
                                "description": "Environment variables",
                            },
                            "file": {"type": "string", "description": "File path for rename/code_action operations"},
                            "pos": {
                                "type": "object",
                                "properties": {"line": {"type": "integer"}, "character": {"type": "integer"}},
                                "description": "Position for rename/code_action",
                            },
                            "range": {
                                "type": "object",
                                "properties": {
                                    "start": {
                                        "type": "object",
                                        "properties": {"line": {"type": "integer"}, "character": {"type": "integer"}},
                                    },
                                    "end": {
                                        "type": "object",
                                        "properties": {"line": {"type": "integer"}, "character": {"type": "integer"}},
                                    },
                                },
                                "description": "Range for code actions",
                            },
                            "new_name": {"type": "string", "description": "New name for rename operation"},
                            "only": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Code action kinds filter",
                            },
                            "apply": {
                                "type": "boolean",
                                "default": True,
                                "description": "Apply changes (default true)",
                            },
                            "workspace_edit": {
                                "type": "object",
                                "description": "WorkspaceEdit payload for apply_workspace_edit",
                            },
                            "dry_run": {
                                "type": "boolean",
                                "default": False,
                                "description": "Preview mode - no file writes",
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
                            "language": {"type": "string", "default": "auto", "description": "Language override"},
                            "backend": {"type": "string", "default": "auto", "description": "Backend override"},
                            "root": {"type": "string", "description": "Workspace root override"},
                            "env": {
                                "type": "object",
                                "additionalProperties": {"type": "string"},
                                "description": "Environment variables",
                            },
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
                            "dry_run": {"type": "boolean", "default": False, "description": "Preview mode"},
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
                            "language": {"type": "string", "default": "auto", "description": "Language override"},
                            "backend": {"type": "string", "default": "auto", "description": "Backend override"},
                            "root": {"type": "string", "description": "Workspace root override"},
                            "env": {
                                "type": "object",
                                "additionalProperties": {"type": "string"},
                                "description": "Environment variables",
                            },
                            "opts": {
                                "type": "object",
                                "properties": {
                                    "run_filter": {"type": "string", "description": "Test filter pattern"},
                                    "count": {"type": "integer", "description": "Number of times to run each test"},
                                    "race": {"type": "boolean", "description": "Enable race detection (Go)"},
                                    "watch": {"type": "boolean", "default": False, "description": "Watch mode"},
                                },
                                "description": "Test-specific options",
                            },
                            "dry_run": {"type": "boolean", "default": False, "description": "Preview mode"},
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
                            "language": {"type": "string", "default": "auto", "description": "Language override"},
                            "backend": {"type": "string", "default": "auto", "description": "Backend override"},
                            "root": {"type": "string", "description": "Workspace root override"},
                            "env": {
                                "type": "object",
                                "additionalProperties": {"type": "string"},
                                "description": "Environment variables",
                            },
                            "opts": {
                                "type": "object",
                                "properties": {
                                    "release": {"type": "boolean", "default": False, "description": "Release build"},
                                    "features": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "Rust features to enable",
                                    },
                                },
                                "description": "Build-specific options",
                            },
                            "dry_run": {"type": "boolean", "default": False, "description": "Preview mode"},
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
                            "language": {"type": "string", "default": "auto", "description": "Language override"},
                            "backend": {"type": "string", "default": "auto", "description": "Backend override"},
                            "root": {"type": "string", "description": "Workspace root override"},
                            "env": {
                                "type": "object",
                                "additionalProperties": {"type": "string"},
                                "description": "Environment variables",
                            },
                            "opts": {
                                "type": "object",
                                "properties": {
                                    "fix": {
                                        "type": "boolean",
                                        "default": False,
                                        "description": "Auto-fix issues where possible",
                                    }
                                },
                                "description": "Lint-specific options",
                            },
                            "dry_run": {"type": "boolean", "default": False, "description": "Preview mode"},
                        },
                        "required": ["target"],
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="guard",
                    description="Repo invariants (boundaries, forbidden imports/strings)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "target": {
                                "type": "string",
                                "description": "Target: file:<path>, dir:<path>, pkg:<spec>, ws, or changed",
                            },
                            "language": {"type": "string", "default": "auto", "description": "Language override"},
                            "backend": {"type": "string", "default": "auto", "description": "Backend override"},
                            "root": {"type": "string", "description": "Workspace root override"},
                            "env": {
                                "type": "object",
                                "additionalProperties": {"type": "string"},
                                "description": "Environment variables",
                            },
                            "rules": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "string"},
                                        "type": {"type": "string", "enum": ["regex", "import", "generated"]},
                                        "glob": {"type": "string"},
                                        "pattern": {"type": "string"},
                                        "forbid_import_prefix": {"type": "string"},
                                        "forbid_writes": {"type": "boolean"},
                                    },
                                    "required": ["id", "type", "glob"],
                                },
                                "description": "Guard rules to check",
                            },
                            "dry_run": {"type": "boolean", "default": False, "description": "Preview mode"},
                        },
                        "required": ["target", "rules"],
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="search_codebase",
                    description="Search for symbols, files, or content across codebase",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query (symbol name, file pattern, or content)",
                            },
                            "type": {
                                "type": "string",
                                "enum": ["symbols", "files", "content"],
                                "default": "symbols",
                                "description": "Search type",
                            },
                            "language": {"type": "string", "description": "Filter by language"},
                            "limit": {"type": "integer", "default": 50, "description": "Maximum results"},
                        },
                        "required": ["query"],
                    },
                ),
                Tool(
                    name="get_session_history",
                    description="Get recent MCP tool usage history",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "limit": {"type": "integer", "default": 10, "description": "Number of recent sessions"}
                        },
                    },
                ),
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> List[TextContent]:
            """Handle tool calls"""
            try:
                if name == "edit":
                    target_spec = TargetSpec(
                        target=arguments["target"],
                        language=arguments.get("language", "auto"),
                        backend=arguments.get("backend", "auto"),
                        root=arguments.get("root"),
                        env=arguments.get("env", {}),
                        dry_run=arguments.get("dry_run", False),
                    )

                    result = await backend.edit(
                        target_spec,
                        op=arguments["op"],
                        file=arguments.get("file"),
                        pos=arguments.get("pos"),
                        range=arguments.get("range"),
                        new_name=arguments.get("new_name"),
                        only=arguments.get("only", []),
                    )

                    backend.session_manager.log_tool_execution("edit", arguments, result)

                    return [TextContent(type="text", text=self._format_tool_result(result))]

                elif name == "fmt":
                    target_spec = TargetSpec(
                        target=arguments["target"],
                        language=arguments.get("language", "auto"),
                        backend=arguments.get("backend", "auto"),
                        root=arguments.get("root"),
                        env=arguments.get("env", {}),
                        dry_run=arguments.get("dry_run", False),
                    )

                    result = await backend.fmt(target_spec, opts=arguments.get("opts", {}))

                    backend.session_manager.log_tool_execution("fmt", arguments, result)

                    return [TextContent(type="text", text=self._format_tool_result(result))]

                elif name == "test":
                    target_spec = TargetSpec(
                        target=arguments["target"],
                        language=arguments.get("language", "auto"),
                        backend=arguments.get("backend", "auto"),
                        root=arguments.get("root"),
                        env=arguments.get("env", {}),
                        dry_run=arguments.get("dry_run", False),
                    )

                    result = await backend.test(target_spec, opts=arguments.get("opts", {}))

                    backend.session_manager.log_tool_execution("test", arguments, result)

                    return [TextContent(type="text", text=self._format_tool_result(result))]

                elif name == "build":
                    target_spec = TargetSpec(
                        target=arguments["target"],
                        language=arguments.get("language", "auto"),
                        backend=arguments.get("backend", "auto"),
                        root=arguments.get("root"),
                        env=arguments.get("env", {}),
                        dry_run=arguments.get("dry_run", False),
                    )

                    result = await backend.build(target_spec, opts=arguments.get("opts", {}))

                    backend.session_manager.log_tool_execution("build", arguments, result)

                    return [TextContent(type="text", text=self._format_tool_result(result))]

                elif name == "lint":
                    target_spec = TargetSpec(
                        target=arguments["target"],
                        language=arguments.get("language", "auto"),
                        backend=arguments.get("backend", "auto"),
                        root=arguments.get("root"),
                        env=arguments.get("env", {}),
                        dry_run=arguments.get("dry_run", False),
                    )

                    result = await backend.lint(target_spec, opts=arguments.get("opts", {}))

                    backend.session_manager.log_tool_execution("lint", arguments, result)

                    return [TextContent(type="text", text=self._format_tool_result(result))]

                elif name == "guard":
                    target_spec = TargetSpec(
                        target=arguments["target"],
                        language=arguments.get("language", "auto"),
                        backend=arguments.get("backend", "auto"),
                        root=arguments.get("root"),
                        env=arguments.get("env", {}),
                        dry_run=arguments.get("dry_run", False),
                    )

                    result = await backend.guard(target_spec, rules=arguments["rules"])

                    backend.session_manager.log_tool_execution("guard", arguments, result)

                    return [TextContent(type="text", text=self._format_tool_result(result))]

                elif name == "search_codebase":
                    query = arguments["query"]
                    search_type = arguments.get("type", "symbols")
                    language = arguments.get("language")
                    limit = arguments.get("limit", 50)

                    if search_type == "symbols":
                        results = backend.indexer.search_symbols(query, language)
                        results_text = "\n".join(
                            [f"{r['path']}:{r['line']} - {r['kind']} {r['name']}" for r in results[:limit]]
                        )
                    else:
                        results_text = f"Search type '{search_type}' not implemented yet"

                    return [TextContent(type="text", text=f"Search results for '{query}':\n{results_text}")]

                elif name == "get_session_history":
                    limit = arguments.get("limit", 10)
                    sessions = backend.session_manager.get_recent_sessions(limit)

                    history_text = "Recent MCP Sessions:\n"
                    for session in sessions:
                        history_text += f"\nSession {session['session_id'][:8]}... ({session['start_time']})\n"
                        history_text += f"  Tools: {', '.join(session['tools_used'])} ({session['tool_count']} calls)\n"

                    return [TextContent(type="text", text=history_text)]

                else:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]

            except Exception as e:
                return [TextContent(type="text", text=f"Error executing {name}: {str(e)}")]

    def _format_tool_result(self, result: ToolResult) -> str:
        """Format tool result for display"""
        status = "✅ SUCCESS" if result.ok else "❌ FAILED"

        output = f"{status} ({result.execution_time:.2f}s)\n"
        output += f"Root: {result.root}\n"
        output += f"Language: {result.language_used}\n"
        output += f"Backend: {result.backend_used}\n"

        if result.scope_resolved:
            output += f"Scope: {len(result.scope_resolved)} files\n"

        if result.touched_files:
            output += f"Modified: {len(result.touched_files)} files\n"
            for f in result.touched_files[:5]:  # Show first 5
                output += f"  - {f}\n"
            if len(result.touched_files) > 5:
                output += f"  ... and {len(result.touched_files) - 5} more\n"

        if result.stdout:
            output += f"\nOutput:\n{result.stdout}\n"

        if result.stderr:
            output += f"\nErrors:\n{result.stderr}\n"

        if result.errors:
            output += "\nIssues:\n"
            for error in result.errors:
                output += f"  - {error}\n"

        return output

    async def run(self, transport_type: str = "stdio"):
        """Run the MCP server"""
        if transport_type == "stdio":
            from mcp.server.stdio import stdio_server

            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name="hanzo-mcp",
                        server_version="1.0.0",
                        capabilities=self.server.get_capabilities(
                            notification_options=NotificationOptions(), experimental_capabilities={}
                        ),
                    ),
                )


if __name__ == "__main__":
    server = HanzoMCPServer()
    asyncio.run(server.run())
