"""Simple memory test to verify functionality."""

import pytest


def test_memory_registration():
    """Test that memory tools can be registered."""
    from mcp.server.fastmcp import FastMCP
    from hanzo_mcp.tools.common.permissions import PermissionManager

    # Skip if memory not available
    try:
        from hanzo_mcp.tools.memory import register_memory_tools
    except ImportError:
        pytest.skip("hanzo-memory not available")

    mcp_server = FastMCP("test-server")
    permission_manager = PermissionManager()
    permission_manager.add_allowed_path("/tmp")

    tools = register_memory_tools(mcp_server, permission_manager, user_id="test_user", project_id="test_project")

    assert len(tools) == 9
    print(f"Successfully registered {len(tools)} memory tools")


def test_memory_descriptions():
    """Test memory tool descriptions."""
    try:
        from hanzo_mcp.tools.memory.memory_tools import CreateMemoriesTool
    except ImportError:
        pytest.skip("hanzo-memory not available")

    tool = CreateMemoriesTool()
    assert "save" in tool.description.lower()
    assert "memory" in tool.description.lower()
    print(f"CreateMemoriesTool description OK: {tool.description[:50]}...")


if __name__ == "__main__":
    test_memory_registration()
    test_memory_descriptions()
    print("\nAll simple tests passed!")
