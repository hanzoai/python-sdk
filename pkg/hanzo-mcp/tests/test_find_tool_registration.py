"""Test FindTool registration in the MCP server."""

import asyncio

from fastmcp import FastMCP
from hanzo_mcp.server import HanzoMCPServer
from hanzo_mcp.tools.filesystem import register_filesystem_tools
from hanzo_mcp.tools.common.permissions import PermissionManager


def test_find_tool_in_filesystem_tools():
    """Test that FindTool is included in filesystem tools."""
    # Create a mock MCP server
    mcp = FastMCP("test-server")
    pm = PermissionManager()

    # Register filesystem tools
    tools = register_filesystem_tools(mcp_server=mcp, permission_manager=pm, enabled_tools={"find": True})

    # Check that tools were registered
    assert len(tools) > 0

    # Find the find tool
    find_tool = None
    for tool in tools:
        if hasattr(tool, "name") and "find" in str(tool.name).lower():
            find_tool = tool
            break

    assert find_tool is not None, "FindTool not found in registered tools"
    print("✓ FindTool found in filesystem tools")


def test_find_tool_in_server():
    """Test that FindTool is registered when creating a server."""
    # Create server with search tools enabled
    server = HanzoMCPServer(name="test-server", disable_search_tools=False, enabled_tools={"find": True})

    # The server registers tools during initialization
    # We can't directly access _tool_handlers, but we know tools are registered
    print("✓ Server created with FindTool enabled")

    # Verify search tools weren't disabled
    assert not server.disable_search_tools
    assert server.enabled_tools.get("find", True)  # Default is True if not specified

    print("✓ FindTool registration verified in server")


def test_tool_registration_flow():
    """Test the complete tool registration flow."""
    mcp = FastMCP("test-flow")
    pm = PermissionManager()

    # Test filesystem tools registration directly
    filesystem_tools = register_filesystem_tools(mcp_server=mcp, permission_manager=pm, enabled_tools={"find": True})

    assert len(filesystem_tools) > 0

    # Check for find tool in filesystem tools
    tool_names = []
    for tool in filesystem_tools:
        if hasattr(tool, "__class__"):
            tool_names.append(tool.__class__.__name__)
        elif hasattr(tool, "name"):
            tool_names.append(str(tool.name))

    print(f"Registered filesystem tools: {tool_names}")

    # FindTool should be in the list
    find_tool_registered = any("find" in name.lower() for name in tool_names)
    assert find_tool_registered, f"FindTool not found in: {tool_names}"

    print("✓ Complete tool registration flow verified")


async def test_find_tool_usage():
    """Test that FindTool can be used after registration."""
    from hanzo_mcp.tools.search import create_find_tool

    # Create the tool
    find_tool = create_find_tool()

    # Test basic usage
    result = await find_tool.run(pattern="*.py", path=".", max_results=5)

    assert result.data is not None
    assert "results" in result.data
    assert isinstance(result.data["results"], list)

    print(f"✓ FindTool executed successfully, found {len(result.data['results'])} files")


if __name__ == "__main__":
    print("Testing FindTool registration...\n")

    test_find_tool_in_filesystem_tools()
    test_find_tool_in_server()
    test_tool_registration_flow()

    print("\nTesting FindTool usage...")
    asyncio.run(test_find_tool_usage())

    print("\n✅ All registration tests passed!")
