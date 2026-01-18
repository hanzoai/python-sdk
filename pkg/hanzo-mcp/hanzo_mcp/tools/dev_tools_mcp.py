"""
Unified Development Tools - MCP Integration
===========================================

Exposes the 6 orthogonal development tools as MCP tools:
- edit: Semantic refactoring via LSP
- fmt: Code formatting + import normalization
- test: Run tests narrowly by default
- build: Compile/build artifacts
- lint: Static analysis + type checking
- guard: Repository invariants enforcement

Each tool supports:
- Multi-language detection (go, ts, py, rs, cc, sol, schema)
- Workspace-aware operation (go.work, package.json, etc.)
- Consistent input/output schemas
- Composable workflows
"""

from typing import Any, Dict, List

from mcp.server import Server
from mcp.types import TextContent, Tool

try:
    from .build_tool import build_tool_handler
    from .edit_tool import edit_tool_handler
    from .fmt_tool import fmt_tool_handler
    from .guard_tool import guard_tool_handler
    from .lint_tool import lint_tool_handler
    from .test_tool import test_tool_handler
except ImportError:
    # Fallback for testing
    print("Warning: Could not import all dev tool handlers")

# MCP Server instance
dev_tools_server = Server("hanzo-dev-tools")

# Common parameter schemas
TARGET_PARAM = {
    "type": "string",
    "description": "Target specification: file:<path>, dir:<path>, pkg:<spec>, ws (workspace), or changed (git diff)",
}

LANGUAGE_PARAM = {
    "type": "string",
    "enum": ["auto", "go", "ts", "py", "rs", "cc", "sol", "schema"],
    "default": "auto",
    "description": "Language override (auto-detected by default)",
}

BACKEND_PARAM = {
    "type": "string",
    "enum": [
        "auto",
        "go",
        "pnpm",
        "yarn",
        "npm",
        "bun",
        "pytest",
        "uv",
        "poetry",
        "cargo",
        "cmake",
        "ninja",
        "make",
        "buf",
        "capnp",
    ],
    "default": "auto",
    "description": "Backend/tool override (auto-detected by default)",
}

COMMON_PARAMS = {
    "root": {"type": "string", "description": "Workspace root override"},
    "env": {"type": "object", "description": "Additional environment variables"},
    "dry_run": {
        "type": "boolean",
        "default": False,
        "description": "Show planned operations without executing",
    },
}


@dev_tools_server.list_tools()
async def list_tools() -> List[Tool]:
    """List all available development tools"""
    return [
        Tool(
            name="edit",
            description="Semantic refactoring via LSP (rename, code_action, organize_imports)",
            inputSchema={
                "type": "object",
                "properties": {
                    "target": TARGET_PARAM,
                    "op": {
                        "type": "string",
                        "enum": [
                            "rename",
                            "code_action",
                            "organize_imports",
                            "apply_workspace_edit",
                        ],
                        "description": "Edit operation to perform",
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
                        "description": "Position for rename/code_action (0-based)",
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
                        "description": "Code action kinds to apply",
                    },
                    "apply": {
                        "type": "boolean",
                        "default": True,
                        "description": "Whether to apply edits to disk",
                    },
                    "language": LANGUAGE_PARAM,
                    "backend": BACKEND_PARAM,
                    **COMMON_PARAMS,
                },
                "required": ["target", "op"],
            },
        ),
        Tool(
            name="fmt",
            description="Code formatting + import normalization",
            inputSchema={
                "type": "object",
                "properties": {
                    "target": TARGET_PARAM,
                    "language": LANGUAGE_PARAM,
                    "backend": BACKEND_PARAM,
                    "opts": {
                        "type": "object",
                        "properties": {
                            "local_prefix": {
                                "type": "string",
                                "description": "Local import prefix for Go (e.g. github.com/luxfi)",
                            }
                        },
                        "description": "Formatting options",
                    },
                    **COMMON_PARAMS,
                },
                "required": ["target"],
            },
        ),
        Tool(
            name="test",
            description="Run tests narrowly by default (file→package, dir→subtree, pkg→explicit, ws→all)",
            inputSchema={
                "type": "object",
                "properties": {
                    "target": TARGET_PARAM,
                    "language": LANGUAGE_PARAM,
                    "backend": BACKEND_PARAM,
                    "opts": {
                        "type": "object",
                        "properties": {
                            "run": {
                                "type": "string",
                                "description": "Test name pattern (Go -run)",
                            },
                            "count": {
                                "type": "integer",
                                "description": "Test count (Go -count)",
                            },
                            "race": {
                                "type": "boolean",
                                "description": "Enable race detection (Go -race)",
                            },
                            "filter": {
                                "type": "string",
                                "description": "Test filter (JS --filter, Python -k)",
                            },
                            "k": {"type": "string", "description": "Pytest -k filter"},
                            "m": {"type": "string", "description": "Pytest -m marker"},
                            "p": {
                                "type": "string",
                                "description": "Rust package filter",
                            },
                            "features": {
                                "type": "string",
                                "description": "Rust features",
                            },
                        },
                        "description": "Test options",
                    },
                    **COMMON_PARAMS,
                },
                "required": ["target"],
            },
        ),
        Tool(
            name="build",
            description="Compile/build artifacts (same scope as test)",
            inputSchema={
                "type": "object",
                "properties": {
                    "target": TARGET_PARAM,
                    "language": LANGUAGE_PARAM,
                    "backend": BACKEND_PARAM,
                    "opts": {
                        "type": "object",
                        "properties": {
                            "race": {
                                "type": "boolean",
                                "description": "Enable race detection (Go)",
                            },
                            "release": {
                                "type": "boolean",
                                "description": "Release build (Rust)",
                            },
                            "tags": {
                                "type": "string",
                                "description": "Build tags (Go)",
                            },
                            "ldflags": {
                                "type": "string",
                                "description": "Linker flags (Go)",
                            },
                            "features": {
                                "type": "string",
                                "description": "Features (Rust)",
                            },
                        },
                        "description": "Build options",
                    },
                    **COMMON_PARAMS,
                },
                "required": ["target"],
            },
        ),
        Tool(
            name="lint",
            description="Static analysis + type checking (language-specific linters + type checkers)",
            inputSchema={
                "type": "object",
                "properties": {
                    "target": TARGET_PARAM,
                    "language": LANGUAGE_PARAM,
                    "backend": BACKEND_PARAM,
                    "opts": {
                        "type": "object",
                        "properties": {
                            "fix": {
                                "type": "boolean",
                                "default": False,
                                "description": "Apply fixes where supported",
                            }
                        },
                        "description": "Lint options",
                    },
                    **COMMON_PARAMS,
                },
                "required": ["target"],
            },
        ),
        Tool(
            name="guard",
            description="Repository invariant enforcement (boundaries, forbidden imports, generated files)",
            inputSchema={
                "type": "object",
                "properties": {
                    "target": TARGET_PARAM,
                    "rules": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {
                                    "type": "string",
                                    "description": "Rule identifier",
                                },
                                "glob": {
                                    "type": "string",
                                    "description": "File glob pattern",
                                },
                                "pattern": {
                                    "type": "string",
                                    "description": "Regex pattern to match (for regex rules)",
                                },
                                "forbid_import_prefix": {
                                    "type": "string",
                                    "description": "Forbidden import prefix (for import rules)",
                                },
                                "forbid_writes": {
                                    "type": "boolean",
                                    "description": "Forbid writes to matched files (for generated rules)",
                                },
                                "message": {
                                    "type": "string",
                                    "description": "Custom violation message",
                                },
                                "description": {
                                    "type": "string",
                                    "description": "Rule description",
                                },
                            },
                            "required": ["id", "glob"],
                        },
                        "description": "Custom guard rules",
                    },
                    "use_defaults": {
                        "type": "boolean",
                        "default": True,
                        "description": "Include default Hanzo ecosystem rules",
                    },
                    "language": LANGUAGE_PARAM,
                    "backend": BACKEND_PARAM,
                    **COMMON_PARAMS,
                },
                "required": ["target"],
            },
        ),
    ]


@dev_tools_server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Execute development tools"""

    try:
        if name == "edit":
            result = await edit_tool_handler(**arguments)
        elif name == "fmt":
            result = await fmt_tool_handler(**arguments)
        elif name == "test":
            result = await test_tool_handler(**arguments)
        elif name == "build":
            result = await build_tool_handler(**arguments)
        elif name == "lint":
            result = await lint_tool_handler(**arguments)
        elif name == "guard":
            result = await guard_tool_handler(**arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

        # Format result
        output_lines = [
            f"{'✅' if result['ok'] else '❌'} {name.upper()} - {result['scope_resolved']}",
            f"Language: {result['language_used']} | Backend: {result['backend_used']}",
            f"Root: {result['root']}",
        ]

        if result["touched_files"]:
            output_lines.append(f"Modified {len(result['touched_files'])} files:")
            for file in result["touched_files"][:10]:  # Limit to first 10
                output_lines.append(f"  • {file}")
            if len(result["touched_files"]) > 10:
                output_lines.append(
                    f"  ... and {len(result['touched_files']) - 10} more"
                )

        if result["stdout"]:
            output_lines.append("\n📤 Output:")
            output_lines.append(result["stdout"])

        if result["stderr"]:
            output_lines.append("\n⚠️ Errors:")
            output_lines.append(result["stderr"])

        if result["errors"]:
            output_lines.append("\n❌ Issues:")
            for error in result["errors"]:
                output_lines.append(f"  • {error}")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error executing {name}: {str(e)}")]


# Composition recipes
@dev_tools_server.call_tool()
async def call_tool_compose(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Composition recipes for common workflows:

    - rename_and_test: edit(rename) -> fmt(changed) -> test(pkg) -> guard(ws)
    - fix_and_verify: fmt(target) -> lint(target, fix=true) -> test(target)
    - full_check: fmt(ws) -> lint(ws) -> test(ws) -> build(ws) -> guard(ws)
    """

    if name == "rename_and_test":
        return await _compose_rename_and_test(arguments)
    elif name == "fix_and_verify":
        return await _compose_fix_and_verify(arguments)
    elif name == "full_check":
        return await _compose_full_check(arguments)
    else:
        return [TextContent(type="text", text=f"Unknown composition: {name}")]


async def _compose_rename_and_test(args: Dict[str, Any]) -> List[TextContent]:
    """Compose: rename -> format changed files -> test -> guard"""
    results = []

    # 1. Rename
    rename_result = await edit_tool_handler(
        target=args["target"],
        op="rename",
        **{k: v for k, v in args.items() if k not in ["target"]},
    )
    results.append(("rename", rename_result))

    if not rename_result["ok"]:
        return [TextContent(type="text", text="❌ Rename failed, stopping workflow")]

    # 2. Format changed files
    fmt_result = await fmt_tool_handler(target="changed")
    results.append(("format", fmt_result))

    # 3. Test package
    pkg = args.get("package", ".")
    test_result = await test_tool_handler(target=f"pkg:{pkg}")
    results.append(("test", test_result))

    # 4. Guard workspace
    guard_result = await guard_tool_handler(target="ws")
    results.append(("guard", guard_result))

    # Format combined output
    output_lines = ["🔄 RENAME AND TEST WORKFLOW"]
    for step, result in results:
        status = "✅" if result["ok"] else "❌"
        output_lines.append(
            f"{status} {step.upper()}: {result.get('stdout', '')[:100]}"
        )

    overall_success = all(result["ok"] for _, result in results)
    output_lines.append(
        f"\n{'✅ Workflow completed successfully' if overall_success else '❌ Workflow failed'}"
    )

    return [TextContent(type="text", text="\n".join(output_lines))]


async def _compose_fix_and_verify(args: Dict[str, Any]) -> List[TextContent]:
    """Compose: format -> lint with fix -> test"""
    target = args["target"]
    results = []

    # 1. Format
    fmt_result = await fmt_tool_handler(target=target)
    results.append(("format", fmt_result))

    # 2. Lint with fix
    lint_result = await lint_tool_handler(target=target, opts={"fix": True})
    results.append(("lint", lint_result))

    # 3. Test
    test_result = await test_tool_handler(target=target)
    results.append(("test", test_result))

    output_lines = ["🔧 FIX AND VERIFY WORKFLOW"]
    for step, result in results:
        status = "✅" if result["ok"] else "❌"
        output_lines.append(
            f"{status} {step.upper()}: {result.get('stdout', '')[:100]}"
        )

    overall_success = all(result["ok"] for _, result in results)
    output_lines.append(
        f"\n{'✅ All checks passed' if overall_success else '❌ Some checks failed'}"
    )

    return [TextContent(type="text", text="\n".join(output_lines))]


async def _compose_full_check(args: Dict[str, Any]) -> List[TextContent]:
    """Compose: format -> lint -> test -> build -> guard"""
    results = []

    # Run all tools on workspace
    tools = [
        ("format", fmt_tool_handler, {"target": "ws"}),
        ("lint", lint_tool_handler, {"target": "ws"}),
        ("test", test_tool_handler, {"target": "ws"}),
        ("build", build_tool_handler, {"target": "ws"}),
        ("guard", guard_tool_handler, {"target": "ws"}),
    ]

    for step, handler, params in tools:
        result = await handler(**params)
        results.append((step, result))

        # Stop on first failure for critical steps
        if not result["ok"] and step in ["build", "test"]:
            break

    output_lines = ["🔍 FULL CHECK WORKFLOW"]
    for step, result in results:
        status = "✅" if result["ok"] else "❌"
        summary = result.get("stdout", "")[:200]
        output_lines.append(f"{status} {step.upper()}: {summary}")

    overall_success = all(result["ok"] for _, result in results)
    output_lines.append(
        f"\n{'🎉 All checks passed!' if overall_success else '⚠️ Some checks failed'}"
    )

    return [TextContent(type="text", text="\n".join(output_lines))]


# Export server for use in main MCP server
__all__ = ["dev_tools_server"]
