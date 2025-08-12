"""Comprehensive tests for MCP memory tools.

These tests are ported and adapted from the hanzo-memory test suite
to ensure our MCP memory tools work correctly.
"""

import asyncio
from typing import Dict
from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from mcp.server.fastmcp import Context as MCPContext, FastMCP
from hanzo_mcp.tools.common.permissions import PermissionManager

# Check if hanzo-memory is available
try:
    from hanzo_mcp.tools.memory import register_memory_tools
    from hanzo_mcp.tools.memory.memory_tools import (
        CreateMemoriesTool,
        DeleteMemoriesTool,
        ManageMemoriesTool,
        RecallMemoriesTool,
        UpdateMemoriesTool,
    )
    from hanzo_mcp.tools.memory.knowledge_tools import (
        StoreFactsTool,
        RecallFactsTool,
        SummarizeToMemoryTool,
        ManageKnowledgeBasesTool,
    )

    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False

# Skip all tests if hanzo-memory is not available
pytestmark = pytest.mark.skipif(
    not MEMORY_AVAILABLE, reason="hanzo-memory package not installed"
)


# Mock memory and knowledge models
class MockMemory:
    """Mock Memory model."""

    def __init__(self, **kwargs):
        self.memory_id = kwargs.get("memory_id", "mem_123")
        self.user_id = kwargs.get("user_id", "test_user")
        self.project_id = kwargs.get("project_id", "test_project")
        self.content = kwargs.get("content", "Test memory content")
        self.metadata = kwargs.get("metadata", {})
        self.importance = kwargs.get("importance", 1.0)
        self.created_at = kwargs.get("created_at", datetime.now())
        self.updated_at = kwargs.get("updated_at", datetime.now())
        self.embedding = kwargs.get("embedding", [0.1] * 1536)


class MockMemoryWithScore(MockMemory):
    """Mock MemoryWithScore model."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.similarity_score = kwargs.get("similarity_score", 0.95)


class MockMemoryService:
    """Mock memory service."""

    def __init__(self):
        self.memories = {}
        self.call_history = []

    def create_memory(
        self,
        user_id: str,
        project_id: str,
        content: str,
        metadata: Dict = None,
        importance: float = 1.0,
        **kwargs,
    ):
        """Mock create memory."""
        self.call_history.append(("create_memory", locals()))
        memory_id = f"mem_{len(self.memories) + 1}"
        memory = MockMemory(
            memory_id=memory_id,
            user_id=user_id,
            project_id=project_id,
            content=content,
            metadata=metadata or {},
            importance=importance,
        )
        self.memories[memory_id] = memory
        return memory

    def search_memories(
        self,
        user_id: str,
        query: str,
        project_id: str = None,
        limit: int = 10,
        **kwargs,
    ):
        """Mock search memories."""
        self.call_history.append(("search_memories", locals()))
        results = []
        for memory in self.memories.values():
            if memory.user_id == user_id:
                if project_id and memory.project_id != project_id:
                    continue
                # Simple mock search - return all matching user/project
                results.append(
                    MockMemoryWithScore(**memory.__dict__, similarity_score=0.95)
                )
        return results[:limit]

    def get_memory(self, user_id: str, memory_id: str):
        """Mock get memory."""
        self.call_history.append(("get_memory", locals()))
        memory = self.memories.get(memory_id)
        if memory and memory.user_id == user_id:
            return memory
        return None

    def delete_memory(self, user_id: str, memory_id: str):
        """Mock delete memory."""
        self.call_history.append(("delete_memory", locals()))
        memory = self.memories.get(memory_id)
        if memory and memory.user_id == user_id:
            del self.memories[memory_id]
            return True
        return False


@pytest.fixture
def mock_memory_service():
    """Create mock memory service."""
    return MockMemoryService()


@pytest.fixture
def mock_ctx():
    """Create mock MCP context."""
    ctx = Mock(spec=MCPContext)
    ctx.request_id = "test_request"
    ctx.meta = {}
    return ctx


class TestMemoryTools:
    """Test memory tools."""

    @patch("hanzo_memory.services.memory.get_memory_service")
    def test_recall_memories_basic(
        self, tool_helper, mock_get_service, mock_memory_service, mock_ctx
    ):
        """Test basic memory recall."""
        mock_get_service.return_value = mock_memory_service

        # Add some test memories
        mock_memory_service.create_memory(
            user_id="test_user",
            project_id="test_project",
            content="I love Python programming",
        )
        mock_memory_service.create_memory(
            user_id="test_user",
            project_id="test_project",
            content="Machine learning is fascinating",
        )

        # Create tool and test
        tool = RecallMemoriesTool(user_id="test_user", project_id="test_project")

        # Test recall
        result = asyncio.run(
            tool.call(mock_ctx, queries=["Python", "programming"], limit=5)
        )

        tool_helper.assert_in_result("Found 2 relevant memories", result)
        tool_helper.assert_in_result("Python programming", result)
        tool_helper.assert_in_result("Machine learning", result)

    @patch("hanzo_memory.services.memory.get_memory_service")
    def test_recall_memories_with_scope(
        self, tool_helper, mock_get_service, mock_memory_service, mock_ctx
    ):
        """Test memory recall with different scopes."""
        mock_get_service.return_value = mock_memory_service

        # Add memories at different scopes
        mock_memory_service.create_memory(
            user_id="test_user",
            project_id="test_project",
            content="Project-specific memory",
        )
        mock_memory_service.create_memory(
            user_id="session_test_user",
            project_id="test_project",
            content="Session-specific memory",
        )
        mock_memory_service.create_memory(
            user_id="global", project_id="global", content="Global memory"
        )

        tool = RecallMemoriesTool(user_id="test_user", project_id="test_project")

        # Test project scope (default)
        result = asyncio.run(tool.call(mock_ctx, queries=["memory"], scope="project"))
        tool_helper.assert_in_result("Project-specific memory", result)
        assert "Session-specific" not in result
        assert "Global memory" not in result

        # Test session scope
        result = asyncio.run(tool.call(mock_ctx, queries=["memory"], scope="session"))
        tool_helper.assert_in_result("Session-specific memory", result)

        # Test global scope
        result = asyncio.run(tool.call(mock_ctx, queries=["memory"], scope="global"))
        tool_helper.assert_in_result("Global memory", result)

    @patch("hanzo_memory.services.memory.get_memory_service")
    def test_create_memories(
        self, tool_helper, mock_get_service, mock_memory_service, mock_ctx
    ):
        """Test creating memories."""
        mock_get_service.return_value = mock_memory_service

        tool = CreateMemoriesTool(user_id="test_user", project_id="test_project")

        # Create memories
        result = asyncio.run(
            tool.call(
                mock_ctx,
                statements=[
                    "First important fact",
                    "Second important fact",
                    "Third important fact",
                ],
            )
        )

        tool_helper.assert_in_result("Successfully created 3 new memories", result)
        assert len(mock_memory_service.memories) == 3

        # Verify memories were created correctly
        memories = list(mock_memory_service.memories.values())
        assert memories[0].content == "First important fact"
        assert memories[1].content == "Second important fact"
        assert memories[2].content == "Third important fact"

    @patch("hanzo_memory.services.memory.get_memory_service")
    def test_update_memories(
        self, tool_helper, mock_get_service, mock_memory_service, mock_ctx
    ):
        """Test updating memories."""
        mock_get_service.return_value = mock_memory_service

        # Create a memory to update
        memory = mock_memory_service.create_memory(
            user_id="test_user", project_id="test_project", content="Original content"
        )

        tool = UpdateMemoriesTool(user_id="test_user", project_id="test_project")

        # Update memory
        result = asyncio.run(
            tool.call(
                mock_ctx,
                updates=[{"id": memory.memory_id, "statement": "Updated content"}],
            )
        )

        # Note: Update is not fully implemented in hanzo-memory
        tool_helper.assert_in_result("Would update 1 of 1 memories", result)
        tool_helper.assert_in_result("not fully implemented", result)

    @patch("hanzo_memory.services.memory.get_memory_service")
    def test_delete_memories(
        self, tool_helper, mock_get_service, mock_memory_service, mock_ctx
    ):
        """Test deleting memories."""
        mock_get_service.return_value = mock_memory_service

        # Create memories to delete
        memory1 = mock_memory_service.create_memory(
            user_id="test_user", project_id="test_project", content="Memory to delete 1"
        )
        memory2 = mock_memory_service.create_memory(
            user_id="test_user", project_id="test_project", content="Memory to delete 2"
        )
        memory3 = mock_memory_service.create_memory(
            user_id="other_user",
            project_id="test_project",
            content="Memory from other user",
        )

        tool = DeleteMemoriesTool(user_id="test_user", project_id="test_project")

        # Delete memories
        result = asyncio.run(
            tool.call(
                mock_ctx, ids=[memory1.memory_id, memory2.memory_id, memory3.memory_id]
            )
        )

        tool_helper.assert_in_result("Successfully deleted 2 of 3 memories", result)
        assert len(mock_memory_service.memories) == 1
        assert memory3.memory_id in mock_memory_service.memories

    @patch("hanzo_memory.services.memory.get_memory_service")
    def test_manage_memories_batch(
        self, tool_helper, mock_get_service, mock_memory_service, mock_ctx
    ):
        """Test batch memory operations."""
        mock_get_service.return_value = mock_memory_service

        # Create initial memory
        memory = mock_memory_service.create_memory(
            user_id="test_user", project_id="test_project", content="Existing memory"
        )

        tool = ManageMemoriesTool(user_id="test_user", project_id="test_project")

        # Batch operations
        result = asyncio.run(
            tool.call(
                mock_ctx,
                operations={
                    "create": ["New memory 1", "New memory 2"],
                    "update": [
                        {"id": memory.memory_id, "statement": "Updated existing"}
                    ],
                    "delete": ["invalid_id"],
                },
            )
        )

        tool_helper.assert_in_result("Created 2 memories", result)
        tool_helper.assert_in_result("Would update 1 memories", result)
        tool_helper.assert_in_result("Deleted 0 memories", result)

        # Verify state
        assert len(mock_memory_service.memories) == 3  # 1 existing + 2 new


class TestKnowledgeTools:
    """Test knowledge tools."""

    @patch("hanzo_memory.services.memory.get_memory_service")
    def test_store_facts(
        self, tool_helper, mock_get_service, mock_memory_service, mock_ctx
    ):
        """Test storing facts."""
        mock_get_service.return_value = mock_memory_service

        tool = StoreFactsTool(user_id="test_user", project_id="test_project")

        # Store facts
        result = asyncio.run(
            tool.call(
                mock_ctx,
                facts=[
                    "Python uses indentation for blocks",
                    "Python is dynamically typed",
                    "Python supports multiple paradigms",
                ],
                kb_name="python_basics",
                scope="project",
            )
        )

        tool_helper.assert_in_result(
            "Successfully stored 3 facts in python_basics", result
        )

        # Verify facts were stored as special memories
        assert len(mock_memory_service.memories) == 3
        memories = list(mock_memory_service.memories.values())

        for memory in memories:
            assert memory.content.startswith("fact: ")
            assert memory.metadata["type"] == "fact"
            assert memory.metadata["kb_name"] == "python_basics"
            assert memory.importance == 1.5  # Facts have higher importance

    @patch("hanzo_memory.services.memory.get_memory_service")
    def test_recall_facts(
        self, tool_helper, mock_get_service, mock_memory_service, mock_ctx
    ):
        """Test recalling facts."""
        mock_get_service.return_value = mock_memory_service

        # Store some facts first
        store_tool = StoreFactsTool(user_id="test_user", project_id="test_project")
        asyncio.run(
            store_tool.call(
                mock_ctx, facts=["Python fact 1", "Python fact 2"], kb_name="python_kb"
            )
        )

        # Mock search to return fact-type memories
        def mock_search(user_id, query, project_id=None, limit=10, **kwargs):
            results = []
            for memory in mock_memory_service.memories.values():
                if memory.user_id == user_id and memory.metadata.get("type") == "fact":
                    results.append(MockMemoryWithScore(**memory.__dict__))
            return results[:limit]

        mock_memory_service.search_memories = mock_search

        # Recall facts
        recall_tool = RecallFactsTool(user_id="test_user", project_id="test_project")
        result = asyncio.run(
            recall_tool.call(mock_ctx, queries=["Python"], kb_name="python_kb")
        )

        tool_helper.assert_in_result("Found 2 relevant facts", result)
        tool_helper.assert_in_result("Python fact 1", result)
        tool_helper.assert_in_result("Python fact 2", result)
        tool_helper.assert_in_result("(KB: python_kb)", result)

    @patch("hanzo_memory.services.memory.get_memory_service")
    def test_manage_knowledge_bases(
        self, tool_helper, mock_get_service, mock_memory_service, mock_ctx
    ):
        """Test managing knowledge bases."""
        mock_get_service.return_value = mock_memory_service

        tool = ManageKnowledgeBasesTool(user_id="test_user", project_id="test_project")

        # Create knowledge base
        result = asyncio.run(
            tool.call(
                mock_ctx,
                action="create",
                kb_name="test_kb",
                description="Test knowledge base",
                scope="project",
            )
        )

        tool_helper.assert_in_result("Created knowledge base 'test_kb'", result)

        # Verify KB was created as special memory
        assert len(mock_memory_service.memories) == 1
        kb_memory = list(mock_memory_service.memories.values())[0]
        assert kb_memory.metadata["type"] == "knowledge_base"
        assert kb_memory.metadata["kb_name"] == "test_kb"
        assert kb_memory.metadata["description"] == "Test knowledge base"
        assert kb_memory.importance == 2.0  # KBs have high importance

        # List knowledge bases
        # Mock search to return KB-type memories
        def mock_search_kb(user_id, query, project_id=None, limit=100, **kwargs):
            results = []
            for memory in mock_memory_service.memories.values():
                if memory.metadata.get("type") == "knowledge_base":
                    results.append(MockMemoryWithScore(**memory.__dict__))
            return results

        mock_memory_service.search_memories = mock_search_kb

        result = asyncio.run(tool.call(mock_ctx, action="list", scope="project"))

        tool_helper.assert_in_result("Knowledge bases in project scope:", result)
        tool_helper.assert_in_result("test_kb - Test knowledge base", result)

    @patch("hanzo_memory.services.memory.get_memory_service")
    def test_summarize_to_memory(
        self, tool_helper, mock_get_service, mock_memory_service, mock_ctx
    ):
        """Test summarizing content to memory."""
        mock_get_service.return_value = mock_memory_service

        tool = SummarizeToMemoryTool(user_id="test_user", project_id="test_project")

        # Summarize content
        long_content = "This is a very long discussion about API design patterns " * 20
        result = asyncio.run(
            tool.call(
                mock_ctx,
                content=long_content,
                topic="API Design Patterns",
                scope="project",
                auto_facts=True,
            )
        )

        tool_helper.assert_in_result(
            "Stored summary of API Design Patterns in project memory", result
        )
        tool_helper.assert_in_result(
            "Auto-fact extraction would extract key facts", result
        )

        # Verify summary was stored
        assert len(mock_memory_service.memories) == 1
        summary_memory = list(mock_memory_service.memories.values())[0]
        assert summary_memory.metadata["topic"] == "API Design Patterns"
        assert summary_memory.metadata["type"] == "summary"
        assert summary_memory.metadata["scope"] == "project"
        assert len(summary_memory.content) <= 515  # Truncated to 500 + "..."


class TestMemoryToolsIntegration:
    """Integration tests for memory tools."""

    @patch("hanzo_memory.services.memory.get_memory_service")
    def test_full_memory_workflow(
        self, tool_helper, mock_get_service, mock_memory_service, mock_ctx
    ):
        """Test complete memory workflow."""
        mock_get_service.return_value = mock_memory_service

        # 1. Create memories
        create_tool = CreateMemoriesTool(user_id="test_user", project_id="test_project")
        result = asyncio.run(
            create_tool.call(
                mock_ctx,
                statements=[
                    "User prefers dark mode",
                    "User works with Python and JavaScript",
                    "User likes automated testing",
                ],
            )
        )
        tool_helper.assert_in_result("Successfully created 3 new memories", result)

        # 2. Search memories
        recall_tool = RecallMemoriesTool(user_id="test_user", project_id="test_project")
        result = asyncio.run(
            recall_tool.call(
                mock_ctx, queries=["user preferences", "programming languages"]
            )
        )
        tool_helper.assert_in_result("Found 3 relevant memories", result)

        # 3. Create knowledge base
        kb_tool = ManageKnowledgeBasesTool(
            user_id="test_user", project_id="test_project"
        )
        result = asyncio.run(
            kb_tool.call(
                mock_ctx,
                action="create",
                kb_name="user_prefs",
                description="User preferences and settings",
            )
        )
        tool_helper.assert_in_result("Created knowledge base 'user_prefs'", result)

        # 4. Store facts
        facts_tool = StoreFactsTool(user_id="test_user", project_id="test_project")
        result = asyncio.run(
            facts_tool.call(
                mock_ctx,
                facts=[
                    "Preferred theme: dark mode",
                    "Primary languages: Python, JavaScript",
                    "Development practice: TDD",
                ],
                kb_name="user_prefs",
            )
        )
        tool_helper.assert_in_result("Successfully stored 3 facts", result)

        # 5. Verify total memories created
        assert len(mock_memory_service.memories) == 7  # 3 memories + 1 KB + 3 facts


class TestErrorHandling:
    """Test error handling in memory tools."""

    @patch("hanzo_memory.services.memory.get_memory_service")
    def test_memory_service_error(self, tool_helper, mock_get_service, mock_ctx):
        """Test handling of memory service errors."""
        mock_service = Mock()
        mock_service.create_memory.side_effect = Exception("Database connection failed")
        mock_get_service.return_value = mock_service

        tool = CreateMemoriesTool(user_id="test_user", project_id="test_project")

        with pytest.raises(Exception) as exc_info:
            asyncio.run(tool.call(mock_ctx, statements=["Test memory"]))

        assert "Database connection failed" in str(exc_info.value)

    def test_missing_hanzo_memory_package(self, tool_helper, mock_ctx):
        """Test behavior when hanzo-memory package is not installed."""
        with patch("hanzo_mcp.tools.memory.memory_tools.MEMORY_AVAILABLE", False):
            with pytest.raises(ImportError) as exc_info:
                from hanzo_mcp.tools.memory.memory_tools import RecallMemoriesTool

                tool = RecallMemoriesTool()

        # The import error should be raised at module level
        # This test documents the expected behavior


class TestMemoryToolsRegistration:
    """Test memory tools registration with MCP server."""

    @patch("hanzo_memory.services.memory.get_memory_service")
    def test_register_all_memory_tools(self, tool_helper, mock_get_service):
        """Test registering all memory tools."""
        mock_get_service.return_value = MockMemoryService()

        # Create MCP server
        mcp_server = FastMCP("test-server")

        # Create permission manager
        permission_manager = PermissionManager()
        permission_manager.set_allowed_paths(["/tmp"])

        # Register tools
        tools = register_memory_tools(
            mcp_server,
            permission_manager,
            user_id="test_user",
            project_id="test_project",
        )

        # Verify all tools registered
        assert len(tools) == 9
        tool_names = [tool.name for tool in tools]

        expected_tools = [
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

        for expected in expected_tools:
            assert expected in tool_names

        # Verify tools have correct descriptions
        for tool in tools:
            assert tool.description is not None
            assert len(tool.description) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
