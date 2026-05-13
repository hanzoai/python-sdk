"""Filesystem tools for Hanzo AI (HIP-0300).

The MCP wire surface is a single action-routed tool: `fs`.

    fs.read   fs.write   fs.stat   fs.list
    fs.apply_patch        fs.search_text
    fs.mkdir  fs.rm

`apply_patch` is the only way to edit an existing file and requires
`base_hash` from a prior `read` so stale edits are impossible.

The per-action classes (ReadTool, WriteTool, …) are kept importable for
in-process consumers that need read-only sandboxes — they are NOT
registered with the MCP server. The wire contract is `fs` only.
"""

from hanzo_tools.fs.ast import ASTTool
from hanzo_tools.fs.edit import EditTool
from hanzo_tools.fs.find import FindTool
from hanzo_tools.fs.fs_tool import FsTool, fs_tool
from hanzo_tools.fs.read import ReadTool
from hanzo_tools.fs.search import SearchTool
from hanzo_tools.fs.tree import TreeTool
from hanzo_tools.fs.write import WriteTool

# HIP-0300 wire surface — what entry-point discovery registers with MCP.
TOOLS: list[type] = [FsTool]

# In-process read-only set, used by sandboxed agents (e.g. swarm subagents).
# NOT on the MCP wire.
READ_ONLY_TOOLS: list[type] = [ReadTool, TreeTool, FindTool, SearchTool, ASTTool]

__all__ = [
    "FsTool",
    "fs_tool",
    "ReadTool",
    "WriteTool",
    "EditTool",
    "TreeTool",
    "FindTool",
    "SearchTool",
    "ASTTool",
    "READ_ONLY_TOOLS",
    "TOOLS",
    "register_tools",
    "get_read_only_filesystem_tools",
]


def get_read_only_filesystem_tools(permission_manager) -> list:
    """Instantiate the read-only filesystem tool set for sandboxed agents.

    These are NOT exposed on the MCP wire — they're used in-process by
    agent runtimes that need to grant a sub-agent read-only file access
    without giving it `fs.write` / `fs.apply_patch` / `fs.rm`.
    """
    out = []
    for cls in READ_ONLY_TOOLS:
        try:
            out.append(cls(permission_manager))
        except TypeError:
            out.append(cls())
    return out


def register_tools(
    mcp_server, permission_manager, enabled_tools: dict[str, bool] | None = None
):
    """Register the unified `fs` tool with the MCP server."""
    from hanzo_tools.core import ToolRegistry

    enabled = enabled_tools or {}
    registered = []
    for tool_class in TOOLS:
        name = getattr(tool_class, "name", tool_class.__name__.lower())
        if not enabled.get(name, True):
            continue
        try:
            tool = tool_class(permission_manager)
        except TypeError:
            tool = tool_class()
        ToolRegistry.register_tool(mcp_server, tool)
        registered.append(tool)
    return registered
