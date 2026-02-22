import pytest
import asyncio
from unittest.mock import MagicMock, patch
from hanzo_memory.mcp.server import MCPMemoryServer


@pytest.fixture
def memory_server():
    server = MCPMemoryServer()
    # Mock services to avoid external dependencies
    server.db_client = MagicMock()
    server.embedding_service = MagicMock()
    server.llm_service = MagicMock()

    # Mock embedding return
    server.embedding_service.embed_text.return_value = [[0.1, 0.2, 0.3]]

    # Mock DB returns
    server.db_client.search_memories.return_value = []
    server.db_client.search_facts.return_value = []
    server.db_client.delete_memory.return_value = True
    server.db_client.delete_fact.return_value = True

    return server


@pytest.mark.asyncio
async def test_remember_and_recall(memory_server):
    # Test remember
    remember_args = {"user_id": "user1", "content": "Test memory", "action": "remember"}
    result = await memory_server._handle_remember(remember_args)
    assert result["success"] is True
    assert "memory_id" in result

    # Verify DB call
    memory_server.db_client.add_memory.assert_called_once()

    # Test recall
    recall_args = {"user_id": "user1", "query": "Test", "action": "recall"}
    result = await memory_server._handle_recall(recall_args)
    assert result["success"] is True
    assert "memories" in result


@pytest.mark.asyncio
async def test_delete_memory(memory_server):
    delete_args = {"user_id": "user1", "id": "mem_123", "action": "delete"}
    result = await memory_server._handle_delete_memory(delete_args)
    assert result["success"] is True

    # Verify DB call
    memory_server.db_client.delete_memory.assert_called_once_with(
        memory_id="mem_123", user_id="user1", project_id="default"
    )


@pytest.mark.asyncio
async def test_knowledge_base_operations(memory_server):
    # Test create KB
    kb_args = {"user_id": "user1", "name": "My KB", "action": "create_kb"}
    result = await memory_server._handle_create_knowledge_base(kb_args)
    assert result["success"] is True
    assert "kb_id" in result
    kb_id = result["kb_id"]

    # Test add fact
    fact_args = {
        "user_id": "user1",
        "kb_id": kb_id,
        "content": "A fact",
        "action": "add_fact",
    }
    result = await memory_server._handle_add_fact(fact_args)
    assert result["success"] is True
    assert "fact_id" in result
    fact_id = result["fact_id"]

    # Test delete fact
    del_fact_args = {
        "user_id": "user1",  # required by schema though not strictly used in delete_fact impl
        "kb_id": kb_id,
        "id": fact_id,
        "action": "delete_fact",
    }
    result = await memory_server._handle_delete_fact(del_fact_args)
    assert result["success"] is True

    memory_server.db_client.delete_fact.assert_called_once_with(
        fact_id=fact_id, knowledge_base_id=kb_id
    )
