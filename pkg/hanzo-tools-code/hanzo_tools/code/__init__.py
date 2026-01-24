"""Code semantic tools for Hanzo AI (HIP-0300).

Tools:
- code: Unified code semantics tool (HIP-0300)
  - parse: Parse source to AST (tree-sitter)
  - serialize: AST back to text
  - symbols: List symbols in file
  - definition: Go to definition (LSP)
  - references: Find all references (LSP)
  - transform: Pure codemod → Patch
  - summarize: Compress diff/log/report

Effect lattice position: PURE
All operations are safe to cache and parallelize.

Install:
    pip install hanzo-tools-code
    pip install hanzo-tools-code[tree-sitter]  # For AST parsing
    pip install hanzo-tools-code[lsp]          # For LSP integration

Usage:
    from hanzo_tools.code import register_tools, TOOLS

    # Register with MCP server
    register_tools(mcp_server)

    # Or access the unified tool
    from hanzo_tools.code import CodeTool
"""

from hanzo_tools.core import BaseTool, ToolRegistry

from .code_tool import CodeTool, code_tool

# Export list for tool discovery - HIP-0300 unified tool
TOOLS = [CodeTool]

__all__ = [
    "CodeTool",
    "code_tool",
    "register_tools",
    "TOOLS",
]


def register_tools(mcp_server, **kwargs) -> list[BaseTool]:
    """Register code tools with the MCP server.

    Args:
        mcp_server: The FastMCP server instance
        **kwargs: Additional options (cwd, etc.)

    Returns:
        List of registered tool instances
    """
    cwd = kwargs.get("cwd")
    tool = CodeTool(cwd=cwd)
    ToolRegistry.register_tool(mcp_server, tool)
    return [tool]
