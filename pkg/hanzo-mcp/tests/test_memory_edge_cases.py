"""Edge case tests for memory tools."""

import asyncio
from unittest.mock import Mock, patch

import pytest

from tests.test_utils import ToolTestHelper, create_mock_ctx

# Check if hanzo-memory is available
try:
    from hanzo_memory.services.memory import get_memory_service

    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False

# Import memory tools only if available
if MEMORY_AVAILABLE:
    from hanzo_mcp.tools.memory.memory_tools import (
        CreateMemoriesTool,
        DeleteMemoriesTool,
        ManageMemoriesTool,
        RecallMemoriesTool,
    )
    from hanzo_mcp.tools.memory.knowledge_tools import (
        StoreFactsTool,
        RecallFactsTool,
        ManageKnowledgeBasesTool,
    )

# Skip all tests if hanzo-memory is not available
pytestmark = pytest.mark.skipif(
    not MEMORY_AVAILABLE, reason="hanzo-memory package not installed"
)


@pytest.fixture
def tool_helper():
    return ToolTestHelper


@pytest.fixture
def mock_ctx():
    return create_mock_ctx()


class TestMemoryEdgeCases:
    """Test edge cases for memory tools."""

    @patch("hanzo_memory.services.memory.get_memory_service")
    def test_empty_queries(self, mock_get_service, tool_helper, mock_ctx):
        """Test recall with empty queries."""
        mock_service = Mock()
        mock_service.search_memories.return_value = []
        mock_get_service.return_value = mock_service

        tool = RecallMemoriesTool()

        # Empty query list
        result = asyncio.run(tool.call(mock_ctx, queries=[]))
        tool_helper.assert_in_result("No relevant memories found", result)

        # Queries with empty strings
        result = asyncio.run(tool.call(mock_ctx, queries=["", "  ", None]))
        assert mock_service.search_memories.call_count == 3

    @patch("hanzo_memory.services.memory.get_memory_service")
    def test_large_batch_operations(self, mock_get_service, tool_helper, mock_ctx):
        """Test handling large batch operations."""
        mock_service = Mock()
        created_memories = []

        def mock_create(user_id, project_id, content, **kwargs):
            memory = Mock()
            memory.memory_id = f"mem_{len(created_memories)}"
            memory.content = content
            created_memories.append(memory)
            return memory

        mock_service.create_memory = mock_create
        mock_get_service.return_value = mock_service

        tool = CreateMemoriesTool()

        # Create 100 memories
        large_batch = [f"Memory {i}" for i in range(100)]
        result = asyncio.run(tool.call(mock_ctx, statements=large_batch))

        tool_helper.assert_in_result("Successfully created 100 new memories", result)
        assert len(created_memories) == 100

    @patch("hanzo_memory.services.memory.get_memory_service")
    def test_special_characters_in_content(
        self, tool_helper, mock_get_service, mock_ctx
    ):
        """Test handling special characters in memory content."""
        mock_service = Mock()
        mock_service.create_memory.return_value = Mock(
            memory_id="mem_123",
            content="Test with special chars: 'quotes' \"double\" \n newline \t tab",
        )
        mock_get_service.return_value = mock_service

        tool = CreateMemoriesTool()

        # Create memory with special characters
        special_content = (
            "Test with special chars: 'quotes' \"double\" \n newline \t tab"
        )
        result = asyncio.run(tool.call(mock_ctx, statements=[special_content]))

        tool_helper.assert_in_result("Successfully created 1 new memories", result)

        # Verify the service was called with the original content
        mock_service.create_memory.assert_called_once()
        call_args = mock_service.create_memory.call_args[1]
        assert call_args["content"] == special_content

    @patch("hanzo_memory.services.memory.get_memory_service")
    def test_unicode_content(self, tool_helper, mock_get_service, mock_ctx):
        """Test handling Unicode content."""
        mock_service = Mock()
        mock_service.create_memory.return_value = Mock(memory_id="mem_123")
        mock_service.search_memories.return_value = [
            Mock(
                memory_id="mem_123",
                content="Unicode test: 你好世界 🌍 émojis",
                metadata={},
                similarity_score=0.95,
            )
        ]
        mock_get_service.return_value = mock_service

        # Create with Unicode
        create_tool = CreateMemoriesTool()
        unicode_content = "Unicode test: 你好世界 🌍 émojis"
        result = asyncio.run(create_tool.call(mock_ctx, statements=[unicode_content]))
        tool_helper.assert_in_result("Successfully created 1 new memories", result)

        # Search with Unicode
        recall_tool = RecallMemoriesTool()
        result = asyncio.run(recall_tool.call(mock_ctx, queries=["你好"]))
        tool_helper.assert_in_result("Unicode test", result)
        tool_helper.assert_in_result("🌍", result)

    @patch("hanzo_memory.services.memory.get_memory_service")
    def test_concurrent_operations(self, tool_helper, mock_get_service, mock_ctx):
        """Test concurrent memory operations."""
        mock_service = Mock()
        call_order = []

        async def mock_create_async(user_id, project_id, content, **kwargs):
            call_order.append(f"create_{content}")
            await asyncio.sleep(0.01)  # Simulate async work
            return Mock(memory_id=f"mem_{len(call_order)}")

        mock_service.create_memory = Mock(
            side_effect=lambda *args, **kwargs: asyncio.create_task(
                mock_create_async(*args, **kwargs)
            )
        )
        mock_get_service.return_value = mock_service

        tool = ManageMemoriesTool()

        # Concurrent creates
        result = asyncio.run(
            tool.call(
                mock_ctx, operations={"create": ["Memory A", "Memory B", "Memory C"]}
            )
        )

        tool_helper.assert_in_result("Created 3 memories", result)
        assert len(call_order) == 3

    @patch("hanzo_memory.services.memory.get_memory_service")
    def test_invalid_scope_handling(self, tool_helper, mock_get_service, mock_ctx):
        """Test handling of invalid scopes."""
        mock_service = Mock()
        mock_service.search_memories.return_value = []
        mock_get_service.return_value = mock_service

        tool = RecallMemoriesTool(user_id="test_user", project_id="test_project")

        # Invalid scope should still work (treated as custom scope)
        result = asyncio.run(
            tool.call(mock_ctx, queries=["test"], scope="invalid_scope")
        )

        # Should use the invalid scope as-is
        mock_service.search_memories.assert_called()
        call_args = mock_service.search_memories.call_args[1]
        assert call_args["user_id"] == "test_user"  # Uses default user_id

    @patch("hanzo_memory.services.memory.get_memory_service")
    def test_metadata_handling(self, tool_helper, mock_get_service, mock_ctx):
        """Test complex metadata handling."""
        mock_service = Mock()
        mock_service.create_memory.return_value = Mock(
            memory_id="mem_123",
            metadata={"nested": {"key": "value"}, "list": [1, 2, 3]},
        )
        mock_get_service.return_value = mock_service

        tool = StoreFactsTool()

        # Store fact with complex metadata
        complex_metadata = {
            "source": "research_paper",
            "confidence": 0.95,
            "tags": ["python", "performance"],
            "nested": {"author": "John Doe", "year": 2023},
        }

        result = asyncio.run(
            tool.call(
                mock_ctx,
                facts=["Complex fact"],
                kb_name="research",
                metadata=complex_metadata,
            )
        )

        tool_helper.assert_in_result("Successfully stored 1 facts", result)

        # Verify metadata was passed correctly
        call_args = mock_service.create_memory.call_args[1]
        assert call_args["metadata"]["source"] == "research_paper"
        assert call_args["metadata"]["nested"]["author"] == "John Doe"

    @patch("hanzo_memory.services.memory.get_memory_service")
    async def test_service_timeout_handling(
        self, tool_helper, mock_get_service, mock_ctx
    ):
        """Test handling of service timeouts."""
        mock_service = Mock()

        async def slow_search(*args, **kwargs):
            await asyncio.sleep(10)  # Simulate slow operation
            return []

        mock_service.search_memories = Mock(side_effect=slow_search)
        mock_get_service.return_value = mock_service

        tool = RecallMemoriesTool()

        # This should complete without hanging
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(tool.call(mock_ctx, queries=["test"]), timeout=0.1)

    @patch("hanzo_memory.services.memory.get_memory_service")
    def test_knowledge_base_name_validation(
        self, tool_helper, mock_get_service, mock_ctx
    ):
        """Test KB name validation."""
        mock_service = Mock()
        mock_service.create_memory.return_value = Mock(memory_id="kb_123")
        mock_get_service.return_value = mock_service

        tool = ManageKnowledgeBasesTool()

        # Test with various KB names
        test_names = [
            "valid_name",
            "valid-name-123",
            "UPPERCASE",
            "name with spaces",
            "name/with/slashes",
            "name.with.dots",
            "",  # Empty name
            "a" * 100,  # Very long name
        ]

        for kb_name in test_names:
            if kb_name:  # Skip empty name for create
                result = asyncio.run(
                    tool.call(
                        mock_ctx,
                        action="create",
                        kb_name=kb_name,
                        description=f"Test KB: {kb_name}",
                    )
                )
                tool_helper.assert_in_result("Created knowledge base", result)
            else:
                result = asyncio.run(
                    tool.call(mock_ctx, action="create", kb_name=kb_name)
                )
                tool_helper.assert_in_result("Error: kb_name required", result)

    @patch("hanzo_memory.services.memory.get_memory_service")
    def test_fact_deduplication(self, tool_helper, mock_get_service, mock_ctx):
        """Test fact deduplication in recall."""
        mock_service = Mock()

        # Return duplicate facts
        duplicate_fact = Mock(
            memory_id="fact_1",
            content="fact: Duplicate fact",
            metadata={"type": "fact", "kb_name": "test_kb"},
            similarity_score=0.95,
        )

        mock_service.search_memories.return_value = [
            duplicate_fact,
            duplicate_fact,  # Same fact returned twice
            Mock(
                memory_id="fact_2",
                content="fact: Different fact",
                metadata={"type": "fact", "kb_name": "test_kb"},
                similarity_score=0.85,
            ),
        ]
        mock_get_service.return_value = mock_service

        tool = RecallFactsTool()

        result = asyncio.run(tool.call(mock_ctx, queries=["test"], kb_name="test_kb"))

        # Should deduplicate
        tool_helper.assert_in_result("Found 2 relevant facts", result)  # Not 3
        assert result.count("Duplicate fact") == 1  # Appears only once
        tool_helper.assert_in_result("Different fact", result)


class TestMemoryToolsPerformance:
    """Performance-related tests for memory tools."""

    @patch("hanzo_memory.services.memory.get_memory_service")
    def test_large_result_set_handling(self, tool_helper, mock_get_service, mock_ctx):
        """Test handling of large result sets."""
        mock_service = Mock()

        # Create 1000 mock memories
        large_results = []
        for i in range(1000):
            large_results.append(
                Mock(
                    memory_id=f"mem_{i}",
                    content=f"Memory content {i}",
                    metadata={},
                    similarity_score=0.9 - (i * 0.0001),
                )
            )

        mock_service.search_memories.return_value = large_results
        mock_get_service.return_value = mock_service

        tool = RecallMemoriesTool()

        # Request only top 10
        result = asyncio.run(tool.call(mock_ctx, queries=["test"], limit=10))

        # Should only return 10
        tool_helper.assert_in_result("Found 10 relevant memories", result)

        # Verify only 10 are in the output
        memory_count = result.count("Memory content")
        assert memory_count == 10

    @patch("hanzo_memory.services.memory.get_memory_service")
    def test_empty_database_performance(self, tool_helper, mock_get_service, mock_ctx):
        """Test performance with empty database."""
        mock_service = Mock()
        mock_service.search_memories.return_value = []
        mock_get_service.return_value = mock_service

        tool = RecallMemoriesTool()

        # Should handle empty results efficiently
        import time

        start_time = time.time()

        result = asyncio.run(
            tool.call(mock_ctx, queries=["test1", "test2", "test3", "test4", "test5"])
        )

        elapsed = time.time() - start_time

        tool_helper.assert_in_result("No relevant memories found", result)
        assert elapsed < 1.0  # Should be fast even with multiple queries


class TestMemoryToolsSecurity:
    """Security-related tests for memory tools."""

    @patch("hanzo_memory.services.memory.get_memory_service")
    def test_user_isolation(self, tool_helper, mock_get_service, mock_ctx):
        """Test that users can't access other users' memories."""
        mock_service = Mock()

        # Mock service that tracks user_id in calls
        accessed_users = []

        def track_search(user_id, **kwargs):
            accessed_users.append(user_id)
            return []

        mock_service.search_memories = Mock(side_effect=track_search)
        mock_service.delete_memory = Mock(
            side_effect=lambda uid, mid: accessed_users.append(uid)
        )
        mock_get_service.return_value = mock_service

        # Create tool for user1
        tool = RecallMemoriesTool(user_id="user1", project_id="project1")

        # Try to access memories
        asyncio.run(tool.call(mock_ctx, queries=["test"]))

        # Should only access user1's memories
        assert all(uid == "user1" for uid in accessed_users)

        # Try delete tool
        delete_tool = DeleteMemoriesTool(user_id="user1", project_id="project1")
        asyncio.run(delete_tool.call(mock_ctx, ids=["mem_123"]))

        # Should still only access user1
        assert all(uid == "user1" for uid in accessed_users)

    @patch("hanzo_memory.services.memory.get_memory_service")
    def test_sql_injection_prevention(self, tool_helper, mock_get_service, mock_ctx):
        """Test that SQL injection attempts are handled safely."""
        mock_service = Mock()
        mock_service.search_memories.return_value = []
        mock_service.create_memory.return_value = Mock(memory_id="mem_123")
        mock_get_service.return_value = mock_service

        # Try SQL injection in queries
        tool = RecallMemoriesTool()

        injection_attempts = [
            "'; DROP TABLE memories; --",
            "1' OR '1'='1",
            "admin'--",
            "1; DELETE FROM memories WHERE '1'='1",
        ]

        for injection in injection_attempts:
            result = asyncio.run(tool.call(mock_ctx, queries=[injection]))
            # Should handle safely without errors
            assert "No relevant memories found" in result or "Found" in result

        # Verify the service received the queries as-is (service should handle escaping)
        assert mock_service.search_memories.call_count == len(injection_attempts)

    @patch("hanzo_memory.services.memory.get_memory_service")
    def test_xss_prevention_in_content(self, tool_helper, mock_get_service, mock_ctx):
        """Test that XSS attempts in content are handled safely."""
        mock_service = Mock()

        # Return memory with XSS attempt
        xss_content = "<script>alert('XSS')</script>Important memory"
        mock_service.search_memories.return_value = [
            Mock(
                memory_id="mem_xss",
                content=xss_content,
                metadata={},
                similarity_score=0.95,
            )
        ]
        mock_get_service.return_value = mock_service

        tool = RecallMemoriesTool()
        result = asyncio.run(tool.call(mock_ctx, queries=["test"]))

        # Content should be returned as-is (escaping is UI concern)
        assert xss_content in result

        # But verify no execution context
        assert "eval(" not in result
        assert "innerHTML" not in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
