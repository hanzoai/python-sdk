"""Test swarm tool for parallel file editing.

This test ensures the swarm tool can edit multiple files in parallel correctly.
"""

import asyncio
from pathlib import Path

import pytest
from hanzo_mcp.tools.agent.swarm_tool import SwarmTool
from hanzo_mcp.tools.common.permissions import PermissionManager


class TestSwarmParallelEdit:
    """Test swarm tool for parallel file editing."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a temporary project with multiple files."""
        # Create 5 test files
        files = {}
        for i in range(1, 6):
            file_path = tmp_path / f"file{i}.py"
            content = f"""# File {i}
import old_module

class TestClass{i}:
        def __init__(self):
            self.value = {i}
            self.old_attribute = "old_value"
        
        def old_method(self):
            return self.value * 2

def old_function():
        return "This is file {i}"
"""
            file_path.write_text(content)
            files[f"file{i}.py"] = file_path

        return tmp_path, files

    @pytest.fixture
    def mock_mcp_context(self):
        """Create a mock MCP context."""

        class MockContext:
            def __init__(self):
                self.logs = []

            async def log(self, level, message):
                self.logs.append((level, message))

        return MockContext()

    @pytest.mark.asyncio
    async def test_swarm_parallel_file_edits(
        self, tool_helper, temp_project, mock_mcp_context, monkeypatch
    ):
        """Test that swarm can edit multiple files in parallel."""
        project_dir, files = temp_project

        # Mock the agent tool to simulate edits
        class MockAgentTool:
            def __init__(self, *args, **kwargs):
                pass

            async def call(self, ctx, prompts):
                # Extract file path from prompt
                for line in prompts.split("\n"):
                    if line.startswith("File:"):
                        file_path = Path(line.replace("File:", "").strip())
                        break
                else:
                    return "Error: No file path found in prompt"

                # Simulate editing the file
                if file_path.exists():
                    content = file_path.read_text()
                    # Replace old_module with new_module
                    content = content.replace("import old_module", "import new_module")
                    # Replace old_method with new_method
                    content = content.replace("def old_method(", "def new_method(")
                    # Replace old_function with new_function
                    content = content.replace("def old_function(", "def new_function(")
                    # Replace old_attribute with new_attribute
                    content = content.replace(
                        "self.old_attribute", "self.new_attribute"
                    )

                    file_path.write_text(content)
                    return f"Successfully updated {file_path.name}: replaced old references with new ones"
                else:
                    return f"Error: File {file_path} not found"

        # Patch AgentTool
        monkeypatch.setattr("hanzo_mcp.tools.agent.swarm_tool.AgentTool", MockAgentTool)

        # Create permission manager
        permission_manager = PermissionManager(allowed_paths=[str(project_dir)])

        # Create swarm tool
        swarm_tool = SwarmTool(
            permission_manager=permission_manager,
            model="test-model",  # Use test model
        )

        # Create tasks for all 5 files
        tasks = []
        for filename, filepath in files.items():
            tasks.append(
                {
                    "file_path": str(filepath),
                    "instructions": "Update all imports from old_module to new_module, rename old_method to new_method, rename old_function to new_function, and rename old_attribute to new_attribute",
                    "description": f"Update {filename}",
                }
            )

        # Execute swarm
        result = await swarm_tool.call(
            mock_mcp_context,
            tasks=tasks,
            common_instructions="Ensure all changes maintain Python syntax",
            max_concurrent=3,  # Test concurrency limit
        )

        # Verify all files were updated
        tool_helper.assert_in_result("Successful: 5", result)
        tool_helper.assert_in_result("Failed: 0", result)

        # Check each file was actually modified
        for filename, filepath in files.items():
            content = filepath.read_text()
            assert "import new_module" in content
            assert "import old_module" not in content
            assert "def new_method(" in content
            assert "def old_method(" not in content
            assert "def new_function(" in content
            assert "def old_function(" not in content
            assert "self.new_attribute" in content
            assert "self.old_attribute" not in content

    @pytest.mark.asyncio
    async def test_swarm_handles_errors(
        self, tool_helper, temp_project, mock_mcp_context, monkeypatch
    ):
        """Test that swarm handles errors gracefully."""
        project_dir, files = temp_project

        # Mock agent to simulate some failures
        class MockAgentWithErrors:
            def __init__(self, *args, **kwargs):
                self.call_count = 0

            async def call(self, ctx, prompts):
                self.call_count += 1
                # Make every other task fail
                if self.call_count % 2 == 0:
                    return "Error: Simulated failure"

                # Extract file path and succeed
                for line in prompts.split("\n"):
                    if line.startswith("File:"):
                        file_path = Path(line.replace("File:", "").strip())
                        return f"Successfully processed {file_path.name}"

                return "Error: No file path found"

        monkeypatch.setattr(
            "hanzo_mcp.tools.agent.swarm_tool.AgentTool", MockAgentWithErrors
        )

        permission_manager = PermissionManager(allowed_paths=[str(project_dir)])
        swarm_tool = SwarmTool(permission_manager=permission_manager)

        # Create tasks
        tasks = []
        for i in range(1, 5):
            tasks.append(
                {
                    "file_path": str(project_dir / f"file{i}.py"),
                    "instructions": "Test task",
                }
            )

        # Execute swarm
        result = await swarm_tool.call(mock_mcp_context, tasks=tasks, max_concurrent=2)

        # Should handle partial failures
        tool_helper.assert_in_result("Successful: 2", result)
        tool_helper.assert_in_result("Failed: 2", result)
        tool_helper.assert_in_result("❌", result)  # Error indicator
        tool_helper.assert_in_result("✅", result)  # Success indicator

    @pytest.mark.asyncio
    async def test_swarm_respects_concurrency_limit(
        self, tool_helper, temp_project, mock_mcp_context, monkeypatch
    ):
        """Test that swarm respects max_concurrent setting."""
        project_dir, files = temp_project

        # Track concurrent executions
        concurrent_count = 0
        max_concurrent_seen = 0

        class MockAgentConcurrency:
            def __init__(self, *args, **kwargs):
                pass

            async def call(self, ctx, prompts):
                nonlocal concurrent_count, max_concurrent_seen

                concurrent_count += 1
                max_concurrent_seen = max(max_concurrent_seen, concurrent_count)

                # Simulate some work
                await asyncio.sleep(0.1)

                concurrent_count -= 1
                return "Success"

        monkeypatch.setattr(
            "hanzo_mcp.tools.agent.swarm_tool.AgentTool", MockAgentConcurrency
        )

        permission_manager = PermissionManager(allowed_paths=[str(project_dir)])
        swarm_tool = SwarmTool(permission_manager=permission_manager)

        # Create many tasks
        tasks = []
        for i in range(10):
            tasks.append(
                {
                    "file_path": str(project_dir / f"file{i}.py"),
                    "instructions": "Test task",
                }
            )

        # Execute with low concurrency limit
        await swarm_tool.call(mock_mcp_context, tasks=tasks, max_concurrent=2)

        # Should never exceed the limit
        assert max_concurrent_seen <= 2
