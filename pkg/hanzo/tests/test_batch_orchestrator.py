"""Test suite for batch orchestrator with parallel agent execution."""

import os
import shutil
import asyncio
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, AsyncMock, MagicMock, patch

import pytest
from hanzo.batch_orchestrator import (
    BatchTask,
    BatchConfig,
    BatchOrchestrator,
    MetaAIOrchestrator,
)


class TestBatchConfig:
    """Test batch configuration parsing."""

    def test_default_config(self):
        """Test default configuration values."""
        config = BatchConfig()
        assert config.batch_size == 5
        assert config.agent_model == "claude-3-5-sonnet-20241022"
        assert config.use_worktrees == False

    def test_parse_simple_batch(self):
        """Test parsing simple batch command."""
        config = BatchConfig.from_command("batch:10 add copyright to files")
        assert config.batch_size == 10
        assert config.agent_model == "claude-3-5-sonnet-20241022"  # Defaults to Claude
        assert config.operation == "add copyright to files"

    def test_parse_with_agent(self):
        """Test parsing with explicit agent."""
        config = BatchConfig.from_command("batch:5 agent:codex fix typing")
        assert config.batch_size == 5
        assert config.agent_model == "gpt-4-turbo"
        assert config.operation == "fix typing"

    def test_parse_with_worktree(self):
        """Test parsing with worktree option."""
        config = BatchConfig.from_command("batch:3 worktree:true agent:gemini add docs")
        assert config.batch_size == 3
        assert config.use_worktrees == True
        assert config.agent_model == "gemini-1.5-pro"
        assert config.operation == "add docs"

    def test_parse_with_files_pattern(self):
        """Test parsing with file pattern."""
        config = BatchConfig.from_command("batch:5 files:*.py add type hints")
        assert config.batch_size == 5
        assert config.target_pattern == "*.py"
        assert config.operation == "add type hints"

    def test_agent_aliases(self):
        """Test agent name aliases."""
        # Test Claude Code alias
        config = BatchConfig.from_command("batch:5 agent:cc refactor")
        assert config.agent_model == "claude-3-5-sonnet-20241022"

        # Test other aliases
        config = BatchConfig.from_command("batch:5 agent:llama optimize")
        assert config.agent_model == "ollama/llama-3.2-3b"

        config = BatchConfig.from_command("batch:5 agent:deepseek analyze")
        assert config.agent_model == "deepseek-coder-v2"


class TestBatchTask:
    """Test batch task functionality."""

    def test_task_creation(self):
        """Test task creation."""
        task = BatchTask(
            id="task_001",
            description="Add copyright",
            file_path=Path("test.py"),
            agent_model="claude-3-5-sonnet-20241022",
        )
        assert task.id == "task_001"
        assert task.status == "pending"
        assert task.result is None
        assert task.error is None

    def test_task_duration(self):
        """Test task duration calculation."""
        task = BatchTask(id="test", description="test")
        assert task.duration() is None

        task.start_time = datetime(2024, 1, 1, 10, 0, 0)
        task.end_time = datetime(2024, 1, 1, 10, 0, 5)
        assert task.duration() == 5.0


class TestBatchOrchestrator:
    """Test batch orchestrator functionality."""

    @pytest.fixture
    def mock_mcp_client(self):
        """Create mock MCP client."""
        client = MagicMock()
        client.call_tool = AsyncMock()
        return client

    @pytest.fixture
    def mock_hanzo_client(self):
        """Create mock Hanzo client."""
        client = MagicMock()
        client.chat.completions.create = AsyncMock()
        return client

    @pytest.fixture
    def orchestrator(self, mock_mcp_client, mock_hanzo_client):
        """Create batch orchestrator instance."""
        return BatchOrchestrator(
            mcp_client=mock_mcp_client,
            hanzo_client=mock_hanzo_client,
        )

    @pytest.mark.asyncio
    async def test_find_target_files_with_mcp(self, orchestrator, mock_mcp_client):
        """Test finding files with MCP client."""
        mock_mcp_client.call_tool.return_value = "file1.py\nfile2.py\nfile3.py"

        files = await orchestrator._find_target_files("*.py")

        assert len(files) == 3
        assert Path("file1.py") in files
        mock_mcp_client.call_tool.assert_called_once_with("find", {"pattern": "*.py"})

    @pytest.mark.asyncio
    async def test_execute_agent_task_with_mcp(self, orchestrator, mock_mcp_client):
        """Test executing task with MCP agent."""
        task = BatchTask(
            id="test_001",
            description="Add copyright",
            file_path=Path("test.py"),
        )
        config = BatchConfig(operation="add copyright")

        mock_mcp_client.call_tool.return_value = "Copyright added successfully"

        await orchestrator._execute_agent_task(task, config)

        assert task.status == "completed"
        assert task.result == "Copyright added successfully"
        assert task.duration() is not None

        mock_mcp_client.call_tool.assert_called_once()
        call_args = mock_mcp_client.call_tool.call_args[0]
        assert call_args[0] == "agent"
        assert "add copyright" in call_args[1]["prompt"]

    @pytest.mark.asyncio
    async def test_execute_agent_task_with_hanzo(self, orchestrator, mock_hanzo_client):
        """Test executing task with Hanzo client."""
        orchestrator.mcp_client = None  # Disable MCP to use Hanzo

        task = BatchTask(
            id="test_002",
            description="Fix typing",
        )
        config = BatchConfig(operation="fix typing", agent_model="gpt-4-turbo")

        # Mock Hanzo response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Typing fixed"
        mock_hanzo_client.chat.completions.create.return_value = mock_response

        await orchestrator._execute_agent_task(task, config)

        assert task.status == "completed"
        assert task.result == "Typing fixed"

        mock_hanzo_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_hanzo_client.chat.completions.create.call_args[1]
        assert call_kwargs["model"] == "gpt-4-turbo"

    @pytest.mark.asyncio
    async def test_execute_batch_simple(self, orchestrator, mock_mcp_client):
        """Test executing simple batch operation."""
        # Mock file finding
        mock_mcp_client.call_tool.side_effect = [
            "file1.py\nfile2.py",  # Find files
            "Task 1 complete",  # Agent task 1
            "Task 2 complete",  # Agent task 2
        ]

        summary = await orchestrator.execute_batch("batch:2 add copyright")

        assert summary["total_tasks"] == 2
        assert summary["completed"] == 2
        assert summary["failed"] == 0
        assert summary["batch_size"] == 2
        assert summary["agent_model"] == "claude-3-5-sonnet-20241022"

    @pytest.mark.asyncio
    async def test_parallel_execution(self, orchestrator, mock_mcp_client):
        """Test parallel task execution."""

        # Create delay to test parallelism
        async def delayed_response(*args, **kwargs):
            await asyncio.sleep(0.1)
            return f"Task complete"

        mock_mcp_client.call_tool.side_effect = [
            "file1.py\nfile2.py\nfile3.py\nfile4.py",  # Find files
        ] + [
            delayed_response
        ] * 4  # 4 agent tasks

        import time

        start = time.time()

        summary = await orchestrator.execute_batch("batch:2 process files")

        duration = time.time() - start

        # With batch size 2, should take ~0.2s (2 batches of 0.1s each)
        # Not 0.4s if sequential
        assert duration < 0.3
        assert summary["completed"] == 4
        assert summary["batch_size"] == 2

    @pytest.mark.asyncio
    async def test_task_failure_handling(self, orchestrator, mock_mcp_client):
        """Test handling of failed tasks."""
        mock_mcp_client.call_tool.side_effect = [
            "file1.py\nfile2.py",  # Find files
            "Success",  # Task 1 succeeds
            Exception("API error"),  # Task 2 fails
        ]

        summary = await orchestrator.execute_batch("batch:2 process")

        assert summary["completed"] == 1
        assert summary["failed"] == 1
        assert len(orchestrator.completed_tasks) == 1
        assert len(orchestrator.failed_tasks) == 1
        assert orchestrator.failed_tasks[0].error == "API error"


class TestGitWorktreeIntegration:
    """Test git worktree integration."""

    @pytest.fixture
    def temp_git_repo(self):
        """Create temporary git repository."""
        temp_dir = tempfile.mkdtemp()
        os.chdir(temp_dir)

        # Initialize git repo
        import subprocess

        subprocess.run(["git", "init"], capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"], capture_output=True
        )
        subprocess.run(["git", "config", "user.name", "Test User"], capture_output=True)

        # Create initial commit
        Path("test.txt").write_text("initial content")
        subprocess.run(["git", "add", "."], capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], capture_output=True)

        yield temp_dir

        # Cleanup
        os.chdir("/")
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_worktree_setup(self, temp_git_repo):
        """Test worktree setup and cleanup."""
        orchestrator = BatchOrchestrator()
        config = BatchConfig(use_worktrees=True)

        # Setup worktree
        worktree_path = await orchestrator._setup_worktree("test_task", config)

        assert worktree_path is not None
        assert worktree_path.exists()
        assert (worktree_path / "test.txt").exists()

        # Cleanup worktree
        await orchestrator._cleanup_worktree("test_task")

        assert not worktree_path.exists()
        assert "test_task" not in orchestrator._worktrees

    @pytest.mark.asyncio
    async def test_worktree_changes_merge(self, temp_git_repo):
        """Test merging changes from worktree."""
        orchestrator = BatchOrchestrator()
        config = BatchConfig(use_worktrees=True)

        # Setup worktree
        worktree_path = await orchestrator._setup_worktree("test_task", config)

        # Make changes in worktree
        (worktree_path / "new_file.txt").write_text("new content")

        # Merge changes
        await orchestrator._merge_worktree_changes("test_task", worktree_path)

        # Cleanup
        await orchestrator._cleanup_worktree("test_task")

        # Check changes are in main branch
        assert Path("new_file.txt").exists()
        assert Path("new_file.txt").read_text() == "new content"


class TestMetaAIOrchestrator:
    """Test meta AI orchestrator."""

    @pytest.fixture
    def meta_orchestrator(self):
        """Create meta AI orchestrator."""
        mock_mcp = MagicMock()
        mock_mcp.call_tool = AsyncMock()
        return MetaAIOrchestrator(mcp_client=mock_mcp)

    @pytest.mark.asyncio
    async def test_parse_batch_command(self, meta_orchestrator):
        """Test parsing batch commands."""
        # Mock file finding to avoid filesystem scan
        meta_orchestrator.mcp_client.call_tool.return_value = "file1.py\nfile2.py"

        result = await meta_orchestrator.parse_and_execute(
            "batch:5 files:*.py add copyright"
        )

        # Should recognize as batch command
        assert "total_tasks" in result or "error" not in result

    @pytest.mark.asyncio
    async def test_natural_language_to_batch(self, meta_orchestrator):
        """Test converting natural language to batch."""
        # Mock intent analysis
        meta_orchestrator.mcp_client.call_tool.return_value = """
        {
            "type": "batch_operation",
            "operation": "add copyright headers",
            "model": "claude-3-5-sonnet-20241022",
            "pattern": "*.py",
            "batch_size": 10
        }
        """

        intent = await meta_orchestrator._analyze_intent(
            "Add copyright headers to all Python files"
        )

        assert intent["type"] == "batch_operation"

        # Build batch command
        batch_cmd = meta_orchestrator._build_batch_command(intent)
        assert "batch:10" in batch_cmd
        assert "claude" in batch_cmd

    @pytest.mark.asyncio
    async def test_single_task_execution(self, meta_orchestrator):
        """Test single task execution."""
        meta_orchestrator.mcp_client.call_tool.return_value = """
        {
            "type": "single_task",
            "operation": "explain this code",
            "model": "claude-3-5-sonnet-20241022"
        }
        """

        result = await meta_orchestrator.parse_and_execute("explain this code")

        # Should execute as single task
        assert "task_id" in result or "error" not in result


@pytest.mark.integration
class TestBatchOrchestratorIntegration:
    """Integration tests for batch orchestrator."""

    @pytest.mark.asyncio
    async def test_real_batch_execution(self):
        """Test real batch execution with files."""
        # This test requires actual MCP client
        pytest.skip("Requires MCP server running")

        from hanzo_mcp import MCPClient

        client = MCPClient()
        orchestrator = BatchOrchestrator(mcp_client=client)

        # Create test files
        test_dir = Path("test_batch")
        test_dir.mkdir(exist_ok=True)

        for i in range(3):
            (test_dir / f"file{i}.txt").write_text(f"Content {i}")

        try:
            # Execute batch
            summary = await orchestrator.execute_batch(
                "batch:3 files:test_batch/*.txt add header"
            )

            assert summary["completed"] == 3
            assert summary["failed"] == 0

        finally:
            # Cleanup
            shutil.rmtree(test_dir, ignore_errors=True)
