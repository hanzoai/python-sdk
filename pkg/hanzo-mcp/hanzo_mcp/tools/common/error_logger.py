"""Centralized error logging for MCP tools.

This module provides comprehensive error logging for all MCP tool operations,
writing errors to ~/.hanzo/mcp/logs/ for debugging and analysis.
"""

import os
import json
import logging
import traceback
from typing import Any, Optional
from pathlib import Path
from datetime import datetime


class MCPErrorLogger:
    """Centralized error logger for MCP tools."""

    def __init__(self, log_dir: Optional[Path] = None):
        """Initialize the error logger.

        Args:
            log_dir: Directory for log files (default: ~/.hanzo/mcp/logs/)
        """
        if log_dir is None:
            log_dir = Path.home() / ".hanzo" / "mcp" / "logs"

        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Create daily log file
        today = datetime.now().strftime("%Y-%m-%d")
        self.log_file = self.log_dir / f"mcp-errors-{today}.log"

        # Also create a general errors file
        self.general_log_file = self.log_dir / "errors.log"

        # Set up Python logging
        self._setup_logging()

    def _setup_logging(self):
        """Set up Python logging infrastructure."""
        # Create logger
        self.logger = logging.getLogger("hanzo_mcp.errors")
        self.logger.setLevel(logging.DEBUG)

        # Prevent duplicate handlers
        if self.logger.handlers:
            return

        # File handler for daily logs
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.ERROR)

        # File handler for general log
        general_handler = logging.FileHandler(self.general_log_file)
        general_handler.setLevel(logging.ERROR)

        # Formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)
        general_handler.setFormatter(formatter)

        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(general_handler)

    def log_tool_error(
        self,
        tool_name: str,
        error: Exception,
        params: Optional[dict[str, Any]] = None,
        context: Optional[str] = None,
    ):
        """Log a tool execution error.

        Args:
            tool_name: Name of the tool that errored
            error: The exception that was raised
            params: Tool parameters (will be sanitized)
            context: Additional context about the error
        """
        error_data = {
            "timestamp": datetime.now().isoformat(),
            "tool_name": tool_name,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "params": self._sanitize_params(params) if params else None,
            "context": context,
        }

        # Write to JSON log for structured parsing
        json_log_file = self.log_dir / f"tool-errors-{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        try:
            with open(json_log_file, "a") as f:
                json.dump(error_data, f)
                f.write("\n")
        except Exception as e:
            # If JSON logging fails, at least log that
            self.logger.error(f"Failed to write JSON log: {e}")

        # Also log to standard logger
        self.logger.error(
            f"Tool '{tool_name}' error: {type(error).__name__}: {str(error)}",
            extra={"tool": tool_name, "params": error_data.get("params")},
        )

        # Write detailed error to tool-specific file
        tool_log_file = self.log_dir / f"{tool_name}-errors.log"
        try:
            with open(tool_log_file, "a") as f:
                f.write(f"\n{'=' * 80}\n")
                f.write(f"ERROR at {error_data['timestamp']}\n")
                f.write(f"{'=' * 80}\n")
                f.write(f"Tool: {tool_name}\n")
                f.write(f"Error Type: {error_data['error_type']}\n")
                f.write(f"Error Message: {error_data['error_message']}\n")
                if context:
                    f.write(f"Context: {context}\n")
                if params:
                    f.write(f"\nParameters:\n{json.dumps(error_data['params'], indent=2)}\n")
                f.write(f"\nTraceback:\n{error_data['traceback']}\n")
        except Exception as e:
            self.logger.error(f"Failed to write tool-specific log: {e}")

    def log_call_signature_error(
        self,
        tool_name: str,
        expected_signature: str,
        actual_call: str,
        error: Exception,
    ):
        """Log an error related to incorrect tool call signature.

        Args:
            tool_name: Name of the tool
            expected_signature: Expected function signature
            actual_call: How the tool was actually called
            error: The exception that was raised
        """
        error_data = {
            "timestamp": datetime.now().isoformat(),
            "tool_name": tool_name,
            "error_type": "CallSignatureError",
            "expected_signature": expected_signature,
            "actual_call": actual_call,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
        }

        # Write to signature errors log
        sig_log_file = self.log_dir / "signature-errors.log"
        try:
            with open(sig_log_file, "a") as f:
                f.write(f"\n{'=' * 80}\n")
                f.write(f"CALL SIGNATURE ERROR at {error_data['timestamp']}\n")
                f.write(f"{'=' * 80}\n")
                f.write(f"Tool: {tool_name}\n")
                f.write(f"Expected: {expected_signature}\n")
                f.write(f"Actual: {actual_call}\n")
                f.write(f"Error: {error_data['error_message']}\n")
                f.write(f"\nTraceback:\n{error_data['traceback']}\n")
        except Exception as e:
            self.logger.error(f"Failed to write signature error log: {e}")

        # Also log as regular tool error
        self.log_tool_error(
            tool_name, error, context=f"Call signature mismatch - Expected: {expected_signature}, Got: {actual_call}"
        )

    def _sanitize_params(self, params: dict[str, Any]) -> dict[str, Any]:
        """Sanitize parameters to remove sensitive data.

        Args:
            params: Parameters to sanitize

        Returns:
            Sanitized parameters
        """
        sanitized = {}
        sensitive_keys = {
            "password",
            "token",
            "key",
            "secret",
            "api_key",
            "auth",
            "credential",
            "private",
            "ssh_key",
            "passphrase",
        }

        for key, value in params.items():
            # Check if key contains sensitive terms
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = "[REDACTED]"
            # Recursively sanitize nested dicts
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_params(value)
            # Convert non-serializable types to strings
            elif not isinstance(value, (str, int, float, bool, list, dict, type(None))):
                sanitized[key] = str(value)
            else:
                sanitized[key] = value

        return sanitized

    def get_recent_errors(self, tool_name: Optional[str] = None, limit: int = 10) -> list[dict]:
        """Get recent errors from the JSON log.

        Args:
            tool_name: Filter by tool name (optional)
            limit: Maximum number of errors to return

        Returns:
            List of error dictionaries
        """
        today = datetime.now().strftime("%Y-%m-%d")
        json_log_file = self.log_dir / f"tool-errors-{today}.jsonl"

        if not json_log_file.exists():
            return []

        errors = []
        try:
            with open(json_log_file, "r") as f:
                for line in f:
                    try:
                        error = json.loads(line)
                        if tool_name is None or error.get("tool_name") == tool_name:
                            errors.append(error)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            self.logger.error(f"Failed to read error log: {e}")

        # Return most recent errors
        return errors[-limit:]


# Global error logger instance
_global_error_logger: Optional[MCPErrorLogger] = None


def get_error_logger() -> MCPErrorLogger:
    """Get the global error logger instance.

    Returns:
        Global error logger
    """
    global _global_error_logger
    if _global_error_logger is None:
        _global_error_logger = MCPErrorLogger()
    return _global_error_logger


def log_tool_error(
    tool_name: str,
    error: Exception,
    params: Optional[dict[str, Any]] = None,
    context: Optional[str] = None,
):
    """Convenience function to log a tool error using the global logger.

    Args:
        tool_name: Name of the tool that errored
        error: The exception that was raised
        params: Tool parameters
        context: Additional context
    """
    logger = get_error_logger()
    logger.log_tool_error(tool_name, error, params, context)


def log_call_signature_error(
    tool_name: str,
    expected_signature: str,
    actual_call: str,
    error: Exception,
):
    """Convenience function to log a call signature error.

    Args:
        tool_name: Name of the tool
        expected_signature: Expected function signature
        actual_call: How the tool was actually called
        error: The exception that was raised
    """
    logger = get_error_logger()
    logger.log_call_signature_error(tool_name, expected_signature, actual_call, error)
