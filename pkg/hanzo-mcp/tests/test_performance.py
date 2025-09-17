"""Performance tests for MCP tools."""

import os
import time
import asyncio
import tempfile
from unittest.mock import Mock, patch

import pytest

from tests.test_utils import create_mock_ctx

# Try to import memory tools, skip tests if not available
try:
    from hanzo_mcp.tools.memory.memory_tools import (
        CreateMemoriesTool,
        RecallMemoriesTool,
    )

    MEMORY_TOOLS_AVAILABLE = True
except ImportError:
    MEMORY_TOOLS_AVAILABLE = False
    RecallMemoriesTool = None
    CreateMemoriesTool = None

from hanzo_mcp.tools.agent.swarm_tool import SwarmTool
from hanzo_mcp.tools.common.batch_tool import BatchTool
from hanzo_mcp.tools.filesystem.search_tool import SearchTool as UnifiedSearchTool


class TestMemoryPerformance:
    """Performance tests for memory tools."""

    @patch("hanzo_memory.services.memory.get_memory_service")
    def test_bulk_memory_creation_performance(self, tool_helper, mock_get_service):
        """Test performance of bulk memory creation."""
        mock_service = Mock()
        created_count = 0

        def mock_create(*args, **kwargs):
            nonlocal created_count
            created_count += 1
            return Mock(memory_id=f"mem_{created_count}")

        mock_service.create_memory = mock_create
        mock_get_service.return_value = mock_service

        tool = CreateMemoriesTool()
        mock_ctx = create_mock_ctx()

        # Create 1000 memories
        memories = [f"Memory {i}" for i in range(1000)]

        start_time = time.time()
        result = asyncio.run(tool.call(mock_ctx, statements=memories))
        elapsed = time.time() - start_time

        tool_helper.assert_in_result("Successfully created 1000 new memories", result)
        assert created_count == 1000
        assert elapsed < 5.0  # Should complete within 5 seconds

        print(f"Created 1000 memories in {elapsed:.2f} seconds")

    @patch("hanzo_memory.services.memory.get_memory_service")
    def test_concurrent_memory_operations(self, tool_helper, mock_get_service):
        """Test concurrent memory operations."""
        mock_service = Mock()
        operation_times = []

        async def mock_operation(*args, **kwargs):
            start = time.time()
            await asyncio.sleep(0.01)  # Simulate work
            operation_times.append(time.time() - start)
            return Mock(memory_id=f"mem_{len(operation_times)}")

        mock_service.create_memory = Mock(side_effect=mock_operation)
        mock_service.search_memories = Mock(side_effect=lambda *a, **k: asyncio.create_task(mock_operation(*a, **k)))
        mock_get_service.return_value = mock_service

        async def run_concurrent_operations():
            """Run multiple operations concurrently."""
            create_tool = CreateMemoriesTool()
            recall_tool = RecallMemoriesTool()
            mock_ctx = create_mock_ctx()

            # Run 10 operations concurrently
            tasks = []
            for i in range(5):
                tasks.append(create_tool.call(mock_ctx, statements=[f"Memory {i}"]))
                tasks.append(recall_tool.call(mock_ctx, queries=[f"Query {i}"]))

            start_time = time.time()
            await asyncio.gather(*tasks)
            total_time = time.time() - start_time

            return total_time, operation_times

        total_time, op_times = asyncio.run(run_concurrent_operations())

        # Should be faster than sequential execution
        sequential_time = sum(op_times)
        assert total_time < sequential_time * 0.5  # At least 2x speedup

        print(f"Concurrent: {total_time:.2f}s, Sequential would be: {sequential_time:.2f}s")


class TestSearchPerformance:
    """Performance tests for search tools."""

    def test_large_directory_search(self):
        """Test search performance in large directory structure."""
        # Create temporary directory with many files
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create 1000 files in nested structure
            for i in range(10):
                subdir = os.path.join(tmpdir, f"dir_{i}")
                os.makedirs(subdir)
                for j in range(100):
                    filepath = os.path.join(subdir, f"file_{j}.txt")
                    with open(filepath, "w") as f:
                        f.write(f"Content of file {i}_{j}\n")
                        if j % 10 == 0:
                            f.write("SPECIAL_PATTERN\n")

            # Mock permission manager
            from hanzo_mcp.tools.common.permissions import PermissionManager

            pm = PermissionManager()
            pm.add_allowed_path(tmpdir)

            # Create search tool
            with patch("hanzo_mcp.tools.filesystem.search_tool.ProjectVectorManager"):
                tool = UnifiedSearchTool(permission_manager=pm)
                mock_ctx = create_mock_ctx()

                # Search for pattern
                start_time = time.time()
                result = asyncio.run(tool.call(mock_ctx, pattern="SPECIAL_PATTERN", path=tmpdir, max_results=50))
                elapsed = time.time() - start_time

                # Should find matches quickly
                tool_helper.assert_in_result("SPECIAL_PATTERN", result)
                assert elapsed < 2.0  # Should complete within 2 seconds

                print(f"Searched 1000 files in {elapsed:.2f} seconds")


class TestBatchToolPerformance:
    """Performance tests for batch tool."""

    def test_large_batch_processing(self):
        """Test processing large batches of tool calls."""
        # Create mock tools
        mock_tools = {}
        call_times = []

        async def mock_tool_call(*args, **kwargs):
            start = time.time()
            await asyncio.sleep(0.01)  # Simulate work
            call_times.append(time.time() - start)
            return f"Result {len(call_times)}"

        for i in range(10):
            tool = Mock()
            tool.name = f"tool_{i}"
            tool.call = Mock(side_effect=mock_tool_call)
            mock_tools[tool.name] = tool

        batch_tool = BatchTool(mock_tools)
        mock_ctx = create_mock_ctx()

        # Create 50 invocations
        invocations = []
        for i in range(50):
            invocations.append({"tool": f"tool_{i % 10}", "parameters": {"param": i}})

        # Process batch
        start_time = time.time()
        result = asyncio.run(batch_tool.call(mock_ctx, description="Large batch test", invocations=invocations))
        elapsed = time.time() - start_time

        # Should process efficiently
        assert "error" not in result.lower()

        # Should be much faster than sequential
        sequential_time = len(invocations) * 0.01
        assert elapsed < sequential_time * 0.5  # At least 2x speedup

        print(f"Processed 50 tool calls in {elapsed:.2f} seconds")


class TestSwarmPerformance:
    """Performance tests for swarm tool."""

    @patch("hanzo_mcp.tools.agent.swarm_tool.dispatch_to_model")
    def test_parallel_agent_execution(self, tool_helper, mock_dispatch):
        """Test parallel execution of swarm agents."""
        execution_times = []

        async def mock_agent_execution(*args, **kwargs):
            start = time.time()
            await asyncio.sleep(0.1)  # Simulate agent work
            execution_times.append(time.time() - start)
            return f"Agent result {len(execution_times)}"

        mock_dispatch.side_effect = mock_agent_execution

        tool = SwarmTool()
        mock_ctx = create_mock_ctx()

        # Create parallel agent network
        agents = []
        for i in range(10):
            agents.append({"id": f"agent_{i}", "query": f"Task {i}", "role": "worker"})

        # Add a final reviewer that depends on all
        agents.append(
            {
                "id": "reviewer",
                "query": "Review all results",
                "role": "reviewer",
                "receives_from": [f"agent_{i}" for i in range(10)],
            }
        )

        # Execute swarm
        start_time = time.time()
        result = asyncio.run(tool.call(mock_ctx, query="Parallel processing test", agents=agents))
        elapsed = time.time() - start_time

        # Should execute workers in parallel
        # Sequential would be 11 * 0.1 = 1.1 seconds
        # Parallel should be ~0.2 seconds (2 phases)
        assert elapsed < 0.6  # Allow some overhead

        print(f"Executed {len(agents)} agents in {elapsed:.2f} seconds")


class TestPaginationPerformance:
    """Test pagination system performance."""

    def test_large_output_pagination(self):
        """Test pagination with very large outputs."""
        from hanzo_mcp.tools.common.truncate import estimate_tokens
        from hanzo_mcp.tools.common.paginated_response import PaginatedResponse

        # Create large dataset
        large_data = []
        for i in range(10000):
            large_data.append(
                {
                    "id": i,
                    "content": f"This is item {i} with some content that makes it larger",
                    "metadata": {"category": i % 10, "priority": i % 5},
                }
            )

        # Test token estimation performance
        start_time = time.time()
        total_tokens = 0
        for item in large_data[:1000]:  # Test first 1000
            total_tokens += estimate_tokens(str(item))
        estimation_time = time.time() - start_time

        assert estimation_time < 1.0  # Should be fast
        print(f"Estimated tokens for 1000 items in {estimation_time:.2f} seconds")

        # Test pagination creation
        start_time = time.time()
        pages = []
        page_size = 100

        for i in range(0, len(large_data), page_size):
            page = PaginatedResponse(
                items=large_data[i : i + page_size],
                next_cursor=(str(i + page_size) if i + page_size < len(large_data) else None),
                has_more=i + page_size < len(large_data),
                total_items=len(large_data),
            )
            pages.append(page)

        pagination_time = time.time() - start_time

        assert len(pages) == 100  # 10000 items / 100 per page
        assert pagination_time < 0.5  # Should be very fast

        print(f"Created {len(pages)} pages in {pagination_time:.2f} seconds")


class TestMemoryStressTest:
    """Stress tests for memory system."""

    @patch("hanzo_memory.services.memory.get_memory_service")
    def test_memory_system_under_load(self, tool_helper, mock_get_service):
        """Test memory system under heavy load."""
        mock_service = Mock()

        # Track all operations
        operations = []

        def track_operation(op_type):
            def wrapper(*args, **kwargs):
                operations.append((op_type, time.time()))
                return Mock(memory_id=f"mem_{len(operations)}")

            return wrapper

        mock_service.create_memory = track_operation("create")
        mock_service.search_memories = Mock(side_effect=lambda *a, **k: [])
        mock_service.delete_memory = Mock(side_effect=lambda *a, **k: True)
        mock_get_service.return_value = mock_service

        async def stress_test():
            """Run many operations concurrently."""
            create_tool = CreateMemoriesTool()
            recall_tool = RecallMemoriesTool()
            mock_ctx = create_mock_ctx()

            tasks = []

            # Create 100 concurrent operations
            for i in range(100):
                if i % 3 == 0:
                    tasks.append(create_tool.call(mock_ctx, statements=[f"Memory {i}"]))
                else:
                    tasks.append(recall_tool.call(mock_ctx, queries=[f"Query {i}"]))

            start_time = time.time()
            await asyncio.gather(*tasks, return_exceptions=True)
            return time.time() - start_time

        elapsed = asyncio.run(stress_test())

        # Should handle load without crashing
        assert len(operations) > 30  # At least the creates
        assert elapsed < 5.0  # Should complete reasonably fast

        print(f"Completed {len(operations)} operations under load in {elapsed:.2f} seconds")


class TestConcurrentFileOperations:
    """Test concurrent file operations."""

    def test_concurrent_file_access(self):
        """Test multiple tools accessing files concurrently."""
        from hanzo_mcp.tools.common.permissions import PermissionManager
        from hanzo_mcp.tools.filesystem.read_tool import ReadTool
        from hanzo_mcp.tools.filesystem.write_tool import WriteTool

        with tempfile.TemporaryDirectory() as tmpdir:
            pm = PermissionManager()
            pm.add_allowed_path(tmpdir)

            # Create test files
            test_files = []
            for i in range(20):
                filepath = os.path.join(tmpdir, f"test_{i}.txt")
                with open(filepath, "w") as f:
                    f.write(f"Initial content {i}\n" * 100)
                test_files.append(filepath)

            read_tool = ReadTool(pm)
            write_tool = WriteTool(pm)

            async def concurrent_operations():
                """Run concurrent read/write operations."""
                tasks = []
                mock_ctx = create_mock_ctx()

                # Mix of reads and writes
                for i, filepath in enumerate(test_files):
                    if i % 3 == 0:
                        # Write operation
                        tasks.append(
                            write_tool.call(
                                mock_ctx,
                                file_path=filepath,
                                content=f"Updated content {i}\n" * 100,
                            )
                        )
                    else:
                        # Read operation
                        tasks.append(read_tool.call(mock_ctx, file_path=filepath))

                start_time = time.time()
                results = await asyncio.gather(*tasks, return_exceptions=True)
                return time.time() - start_time, results

            elapsed, results = asyncio.run(concurrent_operations())

            # Should complete without errors
            errors = [r for r in results if isinstance(r, Exception)]
            assert len(errors) == 0
            assert elapsed < 2.0  # Should be fast even with 20 operations

            print(f"Completed {len(results)} concurrent file operations in {elapsed:.2f} seconds")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])  # -s to see print statements
