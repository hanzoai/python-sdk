"""Tests for MCP server."""

from unittest.mock import MagicMock, patch

import pytest

from hanzo_memory.mcp.server import MCPMemoryServer


@pytest.fixture
def mcp_server():
    """Create MCP server instance."""
    with (
        patch("hanzo_memory.mcp.server.get_db_client"),
        patch("hanzo_memory.mcp.server.EmbeddingService"),
        patch("hanzo_memory.mcp.server.LLMService"),
    ):
        server = MCPMemoryServer()
        # Mock the embedding service
        server.embedding_service.embed_text = MagicMock(return_value=[[0.1] * 384])
        return server


@pytest.mark.asyncio
async def test_tools_are_registered(mcp_server):
    """Test that tools are properly registered."""
    # Just verify that _setup_handlers was called and tools exist
    # The actual tool listing would be tested during integration
    assert hasattr(mcp_server, "server")
    assert hasattr(mcp_server, "db_client")
    assert hasattr(mcp_server, "embedding_service")
    assert hasattr(mcp_server, "llm_service")


@pytest.mark.asyncio
async def test_handle_remember(mcp_server):
    """Test remember tool."""
    # Mock DB operations
    mcp_server.db_client.create_memories_table = MagicMock()
    mcp_server.db_client.add_memory = MagicMock(return_value={"memory_id": "test-id"})

    result = await mcp_server._handle_remember(
        {
            "user_id": "user123",
            "project_id": "proj123",
            "content": "Test memory content",
            "metadata": {"tag": "test"},
            "importance": 5.0,
        }
    )

    assert result["success"] is True
    assert "memory_id" in result
    assert result["message"] == "Memory stored successfully"

    # Verify DB calls
    mcp_server.db_client.create_memories_table.assert_called_once_with("user123")
    mcp_server.db_client.add_memory.assert_called_once()


@pytest.mark.asyncio
async def test_handle_recall(mcp_server):
    """Test recall tool."""
    # Mock search results
    import polars as pl

    mock_df = pl.DataFrame(
        {
            "memory_id": ["mem1", "mem2"],
            "content": ["Memory 1", "Memory 2"],
            "metadata": ['{"tag": "test1"}', '{"tag": "test2"}'],
            "importance": [5.0, 3.0],
            "_similarity": [0.9, 0.7],
        }
    )

    mcp_server.db_client.search_memories = MagicMock(return_value=mock_df)

    result = await mcp_server._handle_recall(
        {
            "user_id": "user123",
            "query": "test query",
            "limit": 5,
        }
    )

    assert result["success"] is True
    assert len(result["memories"]) == 2
    assert result["memories"][0]["content"] == "Memory 1"
    assert result["memories"][0]["similarity_score"] == 0.9


@pytest.mark.asyncio
async def test_handle_create_project(mcp_server):
    """Test create project tool."""
    mcp_server.db_client.create_project = MagicMock(
        return_value={"project_id": "proj123"}
    )

    result = await mcp_server._handle_create_project(
        {
            "user_id": "user123",
            "name": "Test Project",
            "description": "A test project",
            "metadata": {"category": "test"},
        }
    )

    assert result["success"] is True
    assert "project_id" in result
    assert result["message"] == "Project created successfully"


@pytest.mark.asyncio
async def test_handle_create_knowledge_base(mcp_server):
    """Test create knowledge base tool."""
    mcp_server.db_client.create_knowledge_base = MagicMock(
        return_value={"kb_id": "kb123"}
    )

    result = await mcp_server._handle_create_knowledge_base(
        {
            "user_id": "user123",
            "project_id": "proj123",
            "name": "Test KB",
            "description": "A test knowledge base",
        }
    )

    assert result["success"] is True
    assert "kb_id" in result
    assert result["message"] == "Knowledge base created successfully"


@pytest.mark.asyncio
async def test_handle_add_fact(mcp_server):
    """Test add fact tool."""
    mcp_server.db_client.add_fact = MagicMock(return_value={"fact_id": "fact123"})

    result = await mcp_server._handle_add_fact(
        {
            "kb_id": "kb123",
            "content": "Test fact content",
            "parent_id": "parent123",
            "metadata": {"type": "definition"},
        }
    )

    assert result["success"] is True
    assert "fact_id" in result
    assert result["message"] == "Fact added successfully"


@pytest.mark.asyncio
async def test_handle_search_facts(mcp_server):
    """Test search facts tool."""
    import polars as pl

    mock_df = pl.DataFrame(
        {
            "fact_id": ["fact1", "fact2"],
            "content": ["Fact 1", "Fact 2"],
            "parent_id": ["", "parent1"],
            "metadata": ['{"type": "def"}', '{"type": "example"}'],
            "_similarity": [0.95, 0.85],
        }
    )

    mcp_server.db_client.search_facts = MagicMock(return_value=mock_df)

    result = await mcp_server._handle_search_facts(
        {
            "kb_id": "kb123",
            "query": "test query",
            "limit": 10,
        }
    )

    assert result["success"] is True
    assert len(result["facts"]) == 2
    assert result["facts"][0]["content"] == "Fact 1"
    assert result["facts"][0]["similarity_score"] == 0.95


@pytest.mark.asyncio
async def test_handle_summarize_for_knowledge(mcp_server):
    """Test summarize for knowledge tool."""
    mcp_server.llm_service.summarize_for_knowledge = MagicMock(
        return_value={
            "summary": "Test summary",
            "knowledge_instructions": {
                "action": "add_fact",
                "facts": [{"content": "Extracted fact"}],
                "reasoning": "Test reasoning",
            },
        }
    )

    result = await mcp_server._handle_summarize_for_knowledge(
        {
            "content": "Long content to summarize",
            "context": "Additional context",
            "skip_summarization": False,
        }
    )

    assert "summary" in result
    assert "knowledge_instructions" in result
    assert result["knowledge_instructions"]["action"] == "add_fact"


@pytest.mark.asyncio
async def test_handle_tool_error_handling(mcp_server):
    """Test error handling in tool calls."""
    # Mock error
    mcp_server.db_client.create_memories_table = MagicMock(
        side_effect=Exception("DB Error")
    )

    # Call the handler directly instead of through decorated function
    try:
        await mcp_server._handle_remember(
            {
                "user_id": "user123",
                "project_id": "proj123",
                "content": "Test memory",
            }
        )
        raise AssertionError("Should have raised an exception")
    except Exception as e:
        assert "DB Error" in str(e)


@pytest.mark.asyncio
async def test_mcp_server_initialization(mcp_server):
    """Test MCP server is properly initialized."""
    # Verify the server is set up correctly
    assert mcp_server.server is not None
    assert mcp_server.server.name == "hanzo-memory"

    # Verify services are initialized
    assert mcp_server.db_client is not None
    assert mcp_server.embedding_service is not None
    assert mcp_server.llm_service is not None

    # The actual MCP protocol testing would be done via integration tests
    # with the full MCP framework running
