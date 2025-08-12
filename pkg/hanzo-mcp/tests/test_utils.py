"""Common test utilities to DRY up the test suite.

This module provides shared utilities, fixtures, and helpers to make tests
more maintainable and consistent.
"""

import os
import json
import asyncio
import tempfile
from typing import Any, Dict, List, Union, Optional
from pathlib import Path
from unittest.mock import Mock, AsyncMock, MagicMock, patch

import pytest
from fastmcp import FastMCP


# Create a mock context type for testing
class MCPContext:
    """Mock MCP Context for testing."""

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


from hanzo_mcp.tools.common.base import BaseTool
from hanzo_mcp.tools.common.permissions import PermissionManager

# Common test markers
requires_hanzo_agents = pytest.mark.skipif(
    "HANZO_AGENTS_AVAILABLE" not in globals()
    or not globals()["HANZO_AGENTS_AVAILABLE"],
    reason="hanzo-agents SDK not available",
)

requires_memory_tools = pytest.mark.skipif(
    "MEMORY_TOOLS_AVAILABLE" not in globals()
    or not globals()["MEMORY_TOOLS_AVAILABLE"],
    reason="hanzo-memory package not installed",
)


class TestContext:
    """Enhanced MCP context for testing."""

    def __init__(self):
        self.mock = MagicMock(spec=MCPContext)
        self.mock.request_id = "test-request-id"
        self.mock.client_id = "test-client-id"
        self.mock.info = AsyncMock()
        self.mock.debug = AsyncMock()
        self.mock.warning = AsyncMock()
        self.mock.error = AsyncMock()
        self.mock.report_progress = AsyncMock()
        self.mock.read_resource = AsyncMock()
        self.mock.get_tools = AsyncMock(return_value=[])
        self.mock.meta = {"disabled_tools": set()}
        # Add tool context methods
        self.mock.set_tool_info = AsyncMock()
        self.mock.send_completion_ping = AsyncMock()

    @property
    def ctx(self):
        return self.mock


class ToolTestHelper:
    """Helper for testing tools consistently."""

    @staticmethod
    def normalize_result(result: Any) -> str:
        """Normalize tool results to string for testing.

        Handles:
        - Dict results with 'output' key
        - Dict results with 'content' key
        - String results
        - Other types converted to string
        """
        if isinstance(result, dict):
            # Check common output keys
            for key in ["output", "content", "result", "data"]:
                if key in result:
                    return str(result[key])
            # If no known key, stringify the whole dict
            return json.dumps(result, default=str)
        return str(result)

    @staticmethod
    async def call_tool(tool: BaseTool, ctx: Any, **kwargs) -> str:
        """Call a tool and normalize the result."""
        result = await tool.call(ctx, **kwargs)
        return ToolTestHelper.normalize_result(result)

    @staticmethod
    def assert_in_result(expected: str, result: Any, message: str = None):
        """Assert that expected string is in the normalized result."""
        normalized = ToolTestHelper.normalize_result(result)
        if message:
            assert expected in normalized, f"{message}. Got: {normalized}"
        else:
            assert (
                expected in normalized
            ), f"Expected '{expected}' in result. Got: {normalized}"

    @staticmethod
    def assert_success(result: Any):
        """Assert that the result indicates success."""
        normalized = ToolTestHelper.normalize_result(result)
        error_indicators = ["error", "failed", "exception", "Error:", "Failed:"]
        for indicator in error_indicators:
            assert (
                indicator.lower() not in normalized.lower()
            ), f"Result indicates error: {normalized}"


class FileSystemTestHelper:
    """Helper for file system tests."""

    @staticmethod
    def create_test_directory(files: Dict[str, str]) -> tempfile.TemporaryDirectory:
        """Create a temporary directory with test files.

        Args:
            files: Dict mapping file paths to content

        Returns:
            TemporaryDirectory context manager
        """
        temp_dir = tempfile.TemporaryDirectory()
        base_path = Path(temp_dir.name)

        for file_path, content in files.items():
            full_path = base_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)

        return temp_dir

    @staticmethod
    def create_test_files(base_dir: Union[str, Path], files: Dict[str, str]):
        """Create test files in an existing directory."""
        base_path = Path(base_dir)

        for file_path, content in files.items():
            full_path = base_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)


class MockServiceHelper:
    """Helper for mocking external services."""

    @staticmethod
    def mock_memory_service():
        """Create a mock memory service."""
        mock_service = Mock()
        mock_service.search_memories = Mock(return_value=[])
        mock_service.create_memory = Mock(return_value=Mock(memory_id="test-id"))
        mock_service.delete_memory = Mock(return_value=True)
        return mock_service

    @staticmethod
    def mock_litellm_completion(response: str = "Test response"):
        """Create a mock litellm completion."""
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content=response))]
        return Mock(return_value=mock_response)

    @staticmethod
    def mock_subprocess_run(stdout: str = "", stderr: str = "", returncode: int = 0):
        """Create a mock subprocess.run result."""
        return Mock(stdout=stdout, stderr=stderr, returncode=returncode)


class AsyncTestHelper:
    """Helper for async testing."""

    @staticmethod
    def run_async(coro):
        """Run an async coroutine in tests."""
        return asyncio.run(coro)

    @staticmethod
    async def gather_results(tools: List[BaseTool], ctx: Any, **kwargs) -> List[str]:
        """Run multiple tools in parallel and gather results."""
        tasks = [ToolTestHelper.call_tool(tool, ctx, **kwargs) for tool in tools]
        results = await asyncio.gather(*tasks)
        return results


# Fixture factories
def create_mock_ctx():
    """Create a mock MCP context."""
    return TestContext().ctx


def create_permission_manager(allowed_paths: Optional[List[str]] = None):
    """Create a permission manager with optional allowed paths."""
    pm = PermissionManager()
    if allowed_paths:
        for path in allowed_paths:
            pm.add_allowed_path(path)
    else:
        # Default to temp directory
        pm.add_allowed_path("/tmp")
    return pm


def create_test_server(name: str = "test-server"):
    """Create a test MCP server."""
    return FastMCP(name)


# Common test patterns as decorators
def with_temp_dir(test_func):
    """Decorator to provide a temporary directory to a test."""

    def wrapper(*args, **kwargs):
        with tempfile.TemporaryDirectory() as temp_dir:
            return test_func(*args, temp_dir=temp_dir, **kwargs)

    return wrapper


def with_mock_service(service_name: str, mock_factory):
    """Decorator to mock a service for a test."""

    def decorator(test_func):
        def wrapper(*args, **kwargs):
            with patch(service_name, mock_factory()):
                return test_func(*args, **kwargs)

        return wrapper

    return decorator


# Test data generators
class TestDataGenerator:
    """Generate common test data."""

    @staticmethod
    def python_project_files() -> Dict[str, str]:
        """Generate a simple Python project structure."""
        return {
            "main.py": "def main():\n    print('Hello, world!')\n\nif __name__ == '__main__':\n    main()",
            "requirements.txt": "requests==2.31.0\npytest==7.3.1\n",
            "setup.py": "from setuptools import setup\n\nsetup(name='test-project', version='0.1.0')",
            "src/__init__.py": "# Test package",
            "src/utils.py": "def helper():\n    return 42",
            "tests/test_main.py": "def test_main():\n    assert True",
        }

    @staticmethod
    def javascript_project_files() -> Dict[str, str]:
        """Generate a simple JavaScript project structure."""
        return {
            "index.js": "console.log('Hello, world!');",
            "package.json": '{"name": "test-project", "version": "1.0.0", "main": "index.js"}',
            "src/app.js": "export function app() { return 'app'; }",
            "test/app.test.js": "import { app } from '../src/app.js';\ntest('app', () => expect(app()).toBe('app'));",
        }

    @staticmethod
    def mixed_files() -> Dict[str, str]:
        """Generate mixed file types for testing."""
        return {
            "readme.md": "# Test Project",
            "data.json": '{"key": "value"}',
            "config.yaml": "debug: true\nport: 3000",
            ".env": "API_KEY=secret",
            "script.sh": "#!/bin/bash\necho 'Hello'",
        }


# Environment setup helpers
class TestEnvironment:
    """Manage test environment setup and teardown."""

    def __init__(self):
        self.original_env = {}
        self.temp_dirs = []

    def set_env(self, key: str, value: str):
        """Set an environment variable, saving the original."""
        if key not in self.original_env:
            self.original_env[key] = os.environ.get(key)
        os.environ[key] = value

    def restore_env(self):
        """Restore original environment variables."""
        for key, value in self.original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def create_temp_dir(self) -> Path:
        """Create a temporary directory that will be cleaned up."""
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)
        return Path(temp_dir)

    def cleanup(self):
        """Clean up all resources."""
        self.restore_env()
        for temp_dir in self.temp_dirs:
            if os.path.exists(temp_dir):
                import shutil

                shutil.rmtree(temp_dir)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()


# Export commonly used items
__all__ = [
    "TestContext",
    "ToolTestHelper",
    "FileSystemTestHelper",
    "MockServiceHelper",
    "AsyncTestHelper",
    "TestDataGenerator",
    "TestEnvironment",
    "create_mock_ctx",
    "create_permission_manager",
    "create_test_server",
    "with_temp_dir",
    "with_mock_service",
    "requires_hanzo_agents",
    "requires_memory_tools",
]
