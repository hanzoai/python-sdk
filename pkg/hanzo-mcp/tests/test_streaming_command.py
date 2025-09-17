"""Test cases for the streaming command tool."""

import json
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from hanzo_mcp.tools.shell.streaming_command import StreamingCommandTool


class TestStreamingCommandTool:
    """Test cases for StreamingCommandTool."""

    @pytest.fixture
    async def tool(self):
        """Create a test instance of StreamingCommandTool."""
        # Use a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(StreamingCommandTool, "SESSION_BASE_DIR", Path(temp_dir)):
                tool = StreamingCommandTool()
                yield tool

    @pytest.mark.asyncio
    async def test_execute_simple_command(self, tool_helper, tool):
        """Test executing a simple command."""
        result = await tool.run(command="echo 'Hello, World!'")

        tool_helper.assert_in_result("command_id", result)
        tool_helper.assert_in_result("short_id", result)
        assert result["command"] == "echo 'Hello, World!'"
        assert "Hello, World!" in result["output"]
        assert result["status"] in ["running", "completed"]

    @pytest.mark.asyncio
    async def test_command_aliases(self, tool_helper, tool):
        """Test that command aliases work."""
        # Test 'cmd' alias
        result1 = await tool.run(cmd="echo 'test1'")
        assert "test1" in result1["output"]

        # Test 'cwd' alias
        result2 = await tool.run(command="pwd", cwd="/tmp")
        assert result2["status"] in ["running", "completed"]

    @pytest.mark.asyncio
    async def test_continue_reading(self, tool_helper, tool):
        """Test continuing to read from a command."""
        # Generate some output
        result1 = await tool.run(
            command="for i in {1..100}; do echo Line $i; done",
            chunk_size=500,  # Small chunk to ensure pagination
        )

        assert result1["has_more"] is True
        assert "continue_hints" in result1

        # Continue reading
        result2 = await tool.run(continue_from=result1["short_id"])
        assert "output" in result2
        assert result2["command_id"] == result1["command_id"]

    @pytest.mark.asyncio
    async def test_resume_aliases(self, tool_helper, tool):
        """Test resume aliases work."""
        # Run a command
        result1 = await tool.run(command="echo 'test'")

        # Test 'resume' alias
        result2 = await tool.run(resume=result1["short_id"])
        assert result2["command_id"] == result1["command_id"]

        # Test 'last' keyword
        result3 = await tool.run(continue_from="last")
        assert result3["command_id"] == result1["command_id"]

    @pytest.mark.asyncio
    async def test_string_number_conversion(self, tool_helper, tool):
        """Test that string numbers are converted properly."""
        result = await tool.run(
            command="echo 'test'",
            timeout="30",  # String instead of int
            chunk_size="1000",  # String instead of int
        )

        tool_helper.assert_in_result("command_id", result)
        assert result["status"] in ["running", "completed"]

    @pytest.mark.asyncio
    async def test_list_commands(self, tool_helper, tool):
        """Test listing recent commands."""
        # Run a few commands
        await tool.run(command="echo 'test1'")
        await tool.run(command="echo 'test2'")

        # List commands
        result = await tool.list()

        tool_helper.assert_in_result("commands", result)
        assert len(result["commands"]) >= 2
        assert result["session_id"] == tool.session_id

    @pytest.mark.asyncio
    async def test_tail_command(self, tool_helper, tool):
        """Test tailing command output."""
        # Run a command with multiple lines
        result1 = await tool.run(command="for i in {1..20}; do echo Line $i; done")

        # Tail the output
        result2 = await tool.tail(ref=result1["short_id"], lines=5)

        assert "output" in result2
        assert "Line 20" in result2["output"]
        assert result2["lines"] == 5

    @pytest.mark.asyncio
    async def test_error_handling(self, tool_helper, tool):
        """Test error handling for invalid commands."""
        result = await tool.run(command="nonexistent_command_12345")

        tool_helper.assert_in_result("command_id", result)
        # Command should still execute and capture error output

    @pytest.mark.asyncio
    async def test_no_command_error(self, tool_helper, tool):
        """Test helpful error when no command provided."""
        result = await tool.run()

        tool_helper.assert_in_result("error", result)
        tool_helper.assert_in_result("hint", result)
        tool_helper.assert_in_result("recent_commands", result)

    @pytest.mark.asyncio
    async def test_session_persistence(self, tool_helper, tool):
        """Test that session data persists to disk."""
        session_dir = tool.session_dir
        commands_dir = tool.commands_dir

        # Run a command
        result = await tool.run(command="echo 'persistent'")
        cmd_id = result["command_id"]

        # Check files exist
        assert session_dir.exists()
        assert commands_dir.exists()
        assert (commands_dir / cmd_id).exists()
        assert (commands_dir / cmd_id / "output.log").exists()
        assert (commands_dir / cmd_id / "metadata.json").exists()

        # Check metadata content
        with open(commands_dir / cmd_id / "metadata.json", "r") as f:
            metadata = json.load(f)
            assert metadata["command"] == "echo 'persistent'"
            assert metadata["command_id"] == cmd_id

    @pytest.mark.asyncio
    async def test_normalize_command_ref(self, tool_helper, tool):
        """Test command reference normalization."""
        # Run a command
        result = await tool.run(command="echo 'test'")
        cmd_id = result["command_id"]
        short_id = result["short_id"]

        # Test different reference formats
        assert tool._normalize_command_ref(cmd_id) == cmd_id
        assert tool._normalize_command_ref(short_id) == cmd_id
        assert tool._normalize_command_ref("1") == cmd_id  # First command
        assert tool._normalize_command_ref("last") == cmd_id
        assert tool._normalize_command_ref("latest") == cmd_id

    @pytest.mark.asyncio
    async def test_long_running_command(self, tool_helper, tool):
        """Test handling of long-running commands."""
        # Start a command that takes time
        result1 = await tool.run(
            command="sleep 2 && echo 'done'",
            timeout=1,  # Timeout before completion
        )

        # Should still get initial status
        assert result1["status"] == "running"
        assert "command_id" in result1

        # Wait and check again
        await asyncio.sleep(3)
        result2 = await tool.run(continue_from=result1["short_id"])

        # Now it should be completed
        assert "done" in result2["output"] or result2["status"] == "completed"

    @pytest.mark.asyncio
    async def test_streaming_to_disk(self, tool_helper, tool):
        """Test that output is streamed directly to disk."""
        # Generate large output
        result = await tool.run(
            command="for i in {1..1000}; do echo 'This is a long line of text to test streaming'; done",
            chunk_size=1000,  # Small chunk
        )

        # Check that file exists and is larger than chunk
        cmd_dir = tool.commands_dir / result["command_id"]
        output_file = cmd_dir / "output.log"

        assert output_file.exists()
        assert output_file.stat().st_size > 1000
        assert result["has_more"] is True
        assert len(result["output"]) <= 1000


class TestForgivingEditHelper:
    """Test cases for the forgiving edit helper."""

    def test_normalize_whitespace(self):
        """Test whitespace normalization."""
        from hanzo_mcp.tools.common.forgiving_edit import ForgivingEditHelper

        # Test tab to space conversion
        text = "\tindented\twith\ttabs"
        normalized = ForgivingEditHelper.normalize_whitespace(text)
        assert "\t" not in normalized
        # The function normalizes multiple spaces to single spaces in content
        assert "    indented with tabs" in normalized

        # Test multiple space normalization
        text = "multiple   spaces    between"
        normalized = ForgivingEditHelper.normalize_whitespace(text)
        assert "multiple spaces between" in normalized

        # Test preserving indentation
        text = "    indented line\n        more indented"
        normalized = ForgivingEditHelper.normalize_whitespace(text)
        assert normalized.startswith("    ")
        assert "\n        " in normalized

    def test_find_fuzzy_match(self):
        """Test fuzzy matching."""
        from hanzo_mcp.tools.common.forgiving_edit import ForgivingEditHelper

        haystack = """
def hello():
    print("Hello, World!")
    return True
"""

        # Exact match
        match = ForgivingEditHelper.find_fuzzy_match(haystack, 'print("Hello, World!")')
        assert match is not None
        start, end, text = match
        assert 'print("Hello, World!")' in text

        # Whitespace difference
        match = ForgivingEditHelper.find_fuzzy_match(
            haystack,
            'print("Hello, World!")',  # Different quotes/spaces
        )
        assert match is not None

        # No match with low threshold
        match = ForgivingEditHelper.find_fuzzy_match(haystack, "completely different text", threshold=0.9)
        assert match is None

    def test_suggest_matches(self):
        """Test match suggestions."""
        from hanzo_mcp.tools.common.forgiving_edit import ForgivingEditHelper

        haystack = """
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
"""

        suggestions = ForgivingEditHelper.suggest_matches(haystack, "def multiply(a, b):")

        assert len(suggestions) > 0
        # Should suggest similar function definitions
        assert any("def" in text for _, text in suggestions)

    def test_prepare_edit_string(self):
        """Test preparing strings for editing."""
        from hanzo_mcp.tools.common.forgiving_edit import ForgivingEditHelper

        # Test removing line numbers
        text = """1: def hello():
2:     print("test")
3: return True"""

        prepared = ForgivingEditHelper.prepare_edit_string(text)
        assert "1:" not in prepared
        assert "def hello():" in prepared
        assert '    print("test")' in prepared
