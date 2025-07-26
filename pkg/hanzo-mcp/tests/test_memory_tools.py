"""Test memory tools integration with hanzo-memory package."""

import pytest
from unittest.mock import Mock, patch
from mcp.server import FastMCP
from hanzo_mcp.tools.common.permissions import PermissionManager

# Try to import memory tools, skip tests if not available
try:
    from hanzo_mcp.tools.memory import register_memory_tools
    MEMORY_TOOLS_AVAILABLE = True
except ImportError:
    MEMORY_TOOLS_AVAILABLE = False


@pytest.mark.skipif(not MEMORY_TOOLS_AVAILABLE, reason="hanzo-memory package not installed")
def test_memory_tools_registration():
    """Test that memory tools can be registered properly."""
    # Create mock MCP server
    mcp_server = FastMCP("test-server")
    
    # Create permission manager
    permission_manager = PermissionManager()
    permission_manager.set_allowed_paths(["/tmp"])
    
    # Try to register memory tools
    try:
        tools = register_memory_tools(
            mcp_server,
            permission_manager,
            user_id="test_user",
            project_id="test_project"
        )
        
        # Should have 9 tools registered
        assert len(tools) == 9
        
        # Check tool names
        tool_names = [tool.name for tool in tools]
        expected_names = [
            "recall_memories",
            "create_memories",
            "update_memories",
            "delete_memories",
            "manage_memories",
            "recall_facts",
            "store_facts",
            "summarize_to_memory",
            "manage_knowledge_bases",
        ]
        
        for name in expected_names:
            assert name in tool_names
            
    except ImportError as e:
        # If hanzo-memory is not installed, skip the test
        pytest.skip(f"hanzo-memory package not installed: {e}")


def test_memory_tool_descriptions():
    """Test that memory tools have proper descriptions."""
    try:
        from hanzo_mcp.tools.memory.memory_tools import (
            RecallMemoriesTool,
            CreateMemoriesTool,
            ManageMemoriesTool,
        )
        from hanzo_mcp.tools.memory.knowledge_tools import (
            RecallFactsTool,
            StoreFactsTool,
            SummarizeToMemoryTool,
        )
        
        # Test memory tools
        recall_tool = RecallMemoriesTool()
        assert "recall memories" in recall_tool.description.lower()
        assert "scope" in recall_tool.description
        
        create_tool = CreateMemoriesTool()
        assert "create new memories" in create_tool.description.lower()
        
        manage_tool = ManageMemoriesTool()
        assert "batch operations" in manage_tool.description.lower()
        
        # Test knowledge tools
        facts_tool = RecallFactsTool()
        assert "facts" in facts_tool.description.lower()
        assert "knowledge bases" in facts_tool.description.lower()
        
        store_facts = StoreFactsTool()
        assert "store new facts" in store_facts.description.lower()
        
        summarize_tool = SummarizeToMemoryTool()
        assert "summarize" in summarize_tool.description.lower()
        
    except ImportError:
        pytest.skip("hanzo-memory package not installed")


@patch('hanzo_memory.services.memory.get_memory_service')
def test_memory_tool_usage(mock_get_service):
    """Test basic memory tool usage."""
    # Mock the memory service
    mock_service = Mock()
    mock_get_service.return_value = mock_service
    
    # Mock memory creation
    from hanzo_memory.models.memory import Memory
    mock_memory = Memory(
        memory_id="test_123",
        user_id="test_user",
        project_id="test_project",
        content="Test memory content",
        metadata={"type": "statement"},
        importance=1.0,
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00",
        embedding=[0.1] * 1536
    )
    mock_service.create_memory.return_value = mock_memory
    
    # Create and test the tool
    from hanzo_mcp.tools.memory.memory_tools import CreateMemoriesTool
    
    tool = CreateMemoriesTool(user_id="test_user", project_id="test_project")
    
    # Mock context
    mock_ctx = Mock()
    
    # Call the tool
    import asyncio
    result = asyncio.run(tool.call(
        mock_ctx,
        statements=["This is a test memory", "This is another test"]
    ))
    
    # Verify result
    assert "Successfully created 2 new memories" in result
    
    # Verify service was called correctly
    assert mock_service.create_memory.call_count == 2


@patch('hanzo_memory.services.memory.get_memory_service')
def test_knowledge_tool_usage(mock_get_service):
    """Test knowledge tool usage."""
    # Mock the memory service
    mock_service = Mock()
    mock_get_service.return_value = mock_service
    
    # Mock memory creation for facts
    from hanzo_memory.models.memory import Memory
    mock_memory = Memory(
        memory_id="fact_123",
        user_id="test_user",
        project_id="test_project",
        content="fact: Python uses indentation",
        metadata={"type": "fact", "kb_name": "python_basics"},
        importance=1.5,
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00",
        embedding=[0.1] * 1536
    )
    mock_service.create_memory.return_value = mock_memory
    
    # Create and test the tool
    from hanzo_mcp.tools.memory.knowledge_tools import StoreFactsTool
    
    tool = StoreFactsTool(user_id="test_user", project_id="test_project")
    
    # Mock context
    mock_ctx = Mock()
    
    # Call the tool
    import asyncio
    result = asyncio.run(tool.call(
        mock_ctx,
        facts=["Python uses indentation for blocks"],
        kb_name="python_basics",
        scope="project"
    ))
    
    # Verify result
    assert "Successfully stored 1 facts in python_basics" in result
    
    # Verify service was called with correct metadata
    mock_service.create_memory.assert_called_with(
        user_id="test_user",
        project_id="test_project",
        content="fact: Python uses indentation for blocks",
        metadata={"type": "fact", "kb_name": "python_basics"},
        importance=1.5
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])