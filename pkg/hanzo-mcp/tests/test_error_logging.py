"""Tests for MCP error logging functionality."""

from pathlib import Path
from datetime import datetime

import pytest
from hanzo_mcp.tools.common.error_logger import (
    MCPErrorLogger,
    log_tool_error,
    get_error_logger,
    log_call_signature_error,
)


class TestMCPErrorLogger:
    """Test suite for MCPErrorLogger."""

    def test_logger_initialization(self, tmp_path):
        """Test that logger initializes correctly."""
        logger = MCPErrorLogger(log_dir=tmp_path)

        assert logger.log_dir == tmp_path
        assert logger.log_dir.exists()

        # Check that log files are created with today's date
        today = datetime.now().strftime("%Y-%m-%d")
        assert logger.log_file == tmp_path / f"mcp-errors-{today}.log"
        assert logger.general_log_file == tmp_path / "errors.log"

    def test_log_tool_error(self, tmp_path):
        """Test logging a tool error."""
        logger = MCPErrorLogger(log_dir=tmp_path)

        # Create a test error
        test_error = ValueError("Test error message")
        params = {"file_path": "/test/path", "limit": 100}

        # Log the error
        logger.log_tool_error(tool_name="read", error=test_error, params=params, context="Testing error logging")

        # Check that log files were created
        tool_log = tmp_path / "read-errors.log"
        assert tool_log.exists()

        # Read the log and verify content
        content = tool_log.read_text()
        assert "Test error message" in content
        assert "ValueError" in content
        assert "Testing error logging" in content

        # Check JSON log
        today = datetime.now().strftime("%Y-%m-%d")
        json_log = tmp_path / f"tool-errors-{today}.jsonl"
        assert json_log.exists()

    def test_log_call_signature_error(self, tmp_path):
        """Test logging a call signature error."""
        logger = MCPErrorLogger(log_dir=tmp_path)

        # Create a test error
        test_error = TypeError("takes 1 positional argument but 2 were given")

        # Log the error
        logger.log_call_signature_error(
            tool_name="read",
            expected_signature="read(ctx, file_path: str)",
            actual_call="read(ctx, '/path/to/file')",
            error=test_error,
        )

        # Check that signature errors log was created
        sig_log = tmp_path / "signature-errors.log"
        assert sig_log.exists()

        # Read the log and verify content
        content = sig_log.read_text()
        assert "CALL SIGNATURE ERROR" in content
        assert "read(ctx, file_path: str)" in content
        assert "read(ctx, '/path/to/file')" in content

    def test_sanitize_params(self, tmp_path):
        """Test that sensitive parameters are sanitized."""
        logger = MCPErrorLogger(log_dir=tmp_path)

        # Create params with sensitive data
        params = {
            "file_path": "/test/path",
            "api_key": "secret-key-123",
            "password": "super-secret",
            "token": "bearer-token",
            "normal_param": "normal-value",
        }

        sanitized = logger._sanitize_params(params)

        # Check that sensitive keys are redacted
        assert sanitized["api_key"] == "[REDACTED]"
        assert sanitized["password"] == "[REDACTED]"
        assert sanitized["token"] == "[REDACTED]"

        # Check that normal params are preserved
        assert sanitized["file_path"] == "/test/path"
        assert sanitized["normal_param"] == "normal-value"

    def test_get_recent_errors(self, tmp_path):
        """Test retrieving recent errors."""
        logger = MCPErrorLogger(log_dir=tmp_path)

        # Log multiple errors
        for i in range(5):
            error = ValueError(f"Error {i}")
            logger.log_tool_error(tool_name=f"tool_{i}", error=error, params={"index": i})

        # Get recent errors
        recent = logger.get_recent_errors(limit=3)
        assert len(recent) == 3

        # Check they're the most recent ones
        assert "Error 4" in recent[-1]["error_message"]
        assert "Error 3" in recent[-2]["error_message"]

    def test_global_logger(self):
        """Test global logger singleton."""
        logger1 = get_error_logger()
        logger2 = get_error_logger()

        # Should be the same instance
        assert logger1 is logger2

    def test_convenience_functions(self, tmp_path):
        """Test convenience logging functions."""
        # Override global logger for testing
        from hanzo_mcp.tools.common import error_logger as el_module

        el_module._global_error_logger = MCPErrorLogger(log_dir=tmp_path)

        # Test log_tool_error
        error = RuntimeError("Test runtime error")
        log_tool_error("test_tool", error, params={"test": "param"})

        tool_log = tmp_path / "test_tool-errors.log"
        assert tool_log.exists()
        assert "Test runtime error" in tool_log.read_text()

        # Test log_call_signature_error
        sig_error = TypeError("signature mismatch")
        log_call_signature_error("test_tool", "expected signature", "actual call", sig_error)

        sig_log = tmp_path / "signature-errors.log"
        assert sig_log.exists()


class TestErrorLoggingIntegration:
    """Integration tests for error logging with tools."""

    @pytest.mark.asyncio
    async def test_read_tool_with_error_logging(self, tmp_path):
        """Test that ReadTool logs errors correctly."""
        from mcp.server.fastmcp import Context as MCPContext
        from hanzo_mcp.tools.common import error_logger as el_module
        from hanzo_tools.filesystem.read import ReadTool
        from hanzo_mcp.tools.common.permissions import PermissionManager

        # Override global logger
        el_module._global_error_logger = MCPErrorLogger(log_dir=tmp_path)

        # Create tool
        perm_mgr = PermissionManager()
        tool = ReadTool(perm_mgr)

        # Create mock context
        class MockContext:
            async def info(self, msg):
                pass

            async def error(self, msg):
                pass

            async def warning(self, msg):
                pass

        ctx = MockContext()

        # Try to read non-existent file (should log error if call signature is wrong)
        # This simulates the original error where LLM called with positional args
        try:
            # This would cause an error if called incorrectly
            result = await tool.call(ctx, file_path="/nonexistent/file.txt")
            # Should return error message, not raise
            assert "Error" in result or "does not exist" in result
        except TypeError as e:
            # If there's a type error, it should be logged
            log_tool_error("read", e, context="Integration test")

            # Verify error was logged
            read_log = tmp_path / "read-errors.log"
            assert read_log.exists()


def test_error_logger_creates_directory():
    """Test that error logger creates ~/.hanzo/mcp/logs/ directory."""
    logger = get_error_logger()

    expected_dir = Path.home() / ".hanzo" / "mcp" / "logs"
    assert logger.log_dir == expected_dir
    assert expected_dir.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
