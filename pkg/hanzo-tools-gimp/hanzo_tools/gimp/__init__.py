"""GIMP automation tools for Hanzo AI (HIP-0300).

Drives GIMP 3.0 through the Hanzo GIMP bridge -- a clean-room, BSD-3 GIMP
plug-in that exposes GIMP's Procedural Database (PDB) over a JSON TCP socket.
No GPL lineage.

Tools:
- gimp: Unified GIMP automation tool (HIP-0300)
  - version: Bridge + GIMP version
  - open: Load an image file
  - export: Export/save an image
  - pdb_call: Invoke any PDB procedure (the core power)
  - new_image: Create a blank RGB image
  - image_info: Inspect an image
  - list_procedures: Enumerate PDB procedures
  - flatten: Flatten an image

Install:
    pip install hanzo-tools-gimp

Usage:
    from hanzo_tools.gimp import register_tools, TOOLS, GimpTool

    # Register with an MCP server
    register_tools(mcp_server)

    # Or use the unified tool directly
    tool = GimpTool(host="127.0.0.1", port=9876)

Requires the Hanzo GIMP bridge plug-in (hanzo/gimp-mcp) running inside GIMP.
"""

from hanzo_tools.core import BaseTool, ToolRegistry

from .gimp_tool import DEFAULT_HOST, DEFAULT_PORT, GimpTool, gimp_tool

# Export list for tool discovery - HIP-0300 unified tool
TOOLS = [GimpTool]

__all__ = [
    "GimpTool",
    "gimp_tool",
    "DEFAULT_HOST",
    "DEFAULT_PORT",
    "register_tools",
    "TOOLS",
]


def register_tools(mcp_server, **kwargs) -> list[BaseTool]:
    """Register gimp tools with the MCP server.

    Args:
        mcp_server: The FastMCP server instance.
        **kwargs: Optional ``host`` / ``port`` for the GIMP bridge.

    Returns:
        List of registered tool instances.
    """
    host = kwargs.get("host")
    port = kwargs.get("port")
    tool = GimpTool(host=host, port=port)
    ToolRegistry.register_tool(mcp_server, tool)
    return [tool]
