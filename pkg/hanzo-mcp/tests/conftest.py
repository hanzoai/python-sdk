"""Pytest configuration for the Hanzo AI project.

This module provides shared fixtures and configuration for all tests.
Uses the test_utils module for DRY test infrastructure.
"""

import os
import sys
import tempfile

import pytest

# pytest-asyncio is auto-discovered, no manual registration needed

# Add tests directory to path so we can import test_utils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_utils import (
    FileSystemTestHelper,
    TestContext,
    TestDataGenerator,
    TestEnvironment,
    ToolTestHelper,
    create_mock_ctx,
    create_permission_manager,
    create_test_server,
)

# Set environment variables for testing
os.environ["TEST_MODE"] = "1"
os.environ["HANZO_MCP_FAST_TESTS"] = "1"  # Enable fast test mode
os.environ["PYTEST_CURRENT_TEST"] = "1"  # Mark as pytest run


# Configure pytest
def pytest_configure(config):
    """Configure pytest."""
    # Register custom markers
    config.addinivalue_line(
        "markers", "requires_hanzo_agents: mark test as requiring hanzo-agents SDK"
    )
    config.addinivalue_line(
        "markers", "requires_memory_tools: mark test as requiring hanzo-memory package"
    )
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "integration: mark test as integration test")


# --- Basic Fixtures ---


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


@pytest.fixture
def test_env():
    """Create a test environment manager."""
    with TestEnvironment() as env:
        yield env


# --- Context and Permission Fixtures ---


@pytest.fixture
def mcp_context():
    """Create a mock MCP context for testing."""
    return create_mock_ctx()


@pytest.fixture
def mock_ctx(mcp_context):
    """Alias for mcp_context for backward compatibility."""
    return mcp_context


@pytest.fixture
def test_context():
    """Create a full test context helper."""
    return TestContext()


@pytest.fixture
def permission_manager():
    """Create a permission manager for testing."""
    return create_permission_manager(["/"])  # Allow all paths for testing


@pytest.fixture
def restricted_permission_manager(temp_dir):
    """Create a permission manager restricted to temp directory."""
    return create_permission_manager([temp_dir])


# --- Tool Testing Fixtures ---


@pytest.fixture
def tool_helper():
    """Get the tool test helper."""
    return ToolTestHelper


@pytest.fixture
def mock_server():
    """Create a mock MCP server for testing."""
    return create_test_server("test-server")


# --- File System Fixtures ---


@pytest.fixture
def fs_helper():
    """Get the file system test helper."""
    return FileSystemTestHelper


@pytest.fixture
def test_file(temp_dir):
    """Create a test file in the temporary directory."""
    file_path = os.path.join(temp_dir, "test.txt")
    with open(file_path, "w") as f:
        f.write("This is a test file content.")
    return file_path


@pytest.fixture
def test_notebook(temp_dir):
    """Create a test notebook in the temporary directory."""
    notebook_path = os.path.join(temp_dir, "test.ipynb")
    notebook_content = {
        "cells": [
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": ["# Test cell 1\n", "print('Hello, world!')"],
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": ["## Markdown cell\n", "This is a test."],
            },
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4,
    }

    import json

    with open(notebook_path, "w") as f:
        json.dump(notebook_content, f)

    return notebook_path


# --- Project Structure Fixtures ---


@pytest.fixture
def test_data():
    """Get the test data generator."""
    return TestDataGenerator


@pytest.fixture
def project_dir(temp_dir, fs_helper, test_data):
    """Create a simple Python project structure for testing."""
    fs_helper.create_test_files(temp_dir, test_data.python_project_files())
    return temp_dir


@pytest.fixture
def test_project_dir(project_dir):
    """Alias for project_dir fixture."""
    return project_dir


@pytest.fixture
def js_project_dir(temp_dir, fs_helper, test_data):
    """Create a simple JavaScript project structure for testing."""
    fs_helper.create_test_files(temp_dir, test_data.javascript_project_files())
    return temp_dir


# --- Tool-Specific Fixtures ---


@pytest.fixture
def command_executor(permission_manager):
    """Create a command executor for testing."""
    from hanzo_tools.shell.bash_session_executor import BashSessionExecutor

    return BashSessionExecutor(permission_manager=permission_manager)


@pytest.fixture
def tool_context(mcp_context):
    """Create a tool context for testing."""
    from hanzo_mcp.tools.common.context import ToolContext

    return ToolContext(mcp_context)


@pytest.fixture
def db_manager(permission_manager):
    """Create a database manager for testing."""
    from hanzo_tools.database.database_manager import DatabaseManager

    return DatabaseManager(permission_manager)


# --- Mock Service Fixtures ---


@pytest.fixture
def mock_memory_service():
    """Create a mock memory service."""
    from test_utils import MockServiceHelper

    return MockServiceHelper.mock_memory_service()


@pytest.fixture
def mock_litellm():
    """Create a mock litellm module."""
    from test_utils import MockServiceHelper

    with pytest.mock.patch("hanzo_tools.agent.agent_tool.litellm") as mock:
        mock.completion = MockServiceHelper.mock_litellm_completion()
        yield mock


# --- Async Fixtures ---


@pytest.fixture
def async_helper():
    """Get the async test helper."""
    from test_utils import AsyncTestHelper

    return AsyncTestHelper


# --- Autouse Fixtures ---


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment before each test."""
    # Save current environment
    original_env = os.environ.copy()

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture(autouse=True, scope="session")
def mock_slow_operations():
    """Mock slow operations for faster test execution."""
    from unittest.mock import AsyncMock, patch

    # Mock subprocess for LSP tests
    with patch("asyncio.create_subprocess_exec") as mock_subprocess:
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"", b""))
        mock_subprocess.return_value = mock_process
        yield


@pytest.fixture(autouse=True)
def cleanup_temp_files():
    """Clean up any temporary files after tests."""
    yield

    # Clean up any stray temp files
    import glob
    import shutil

    for pattern in ["/tmp/test_*", "/tmp/pytest-*"]:
        for path in glob.glob(pattern):
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.unlink(path)
            except Exception:
                pass  # Ignore cleanup errors


# --- Pytest Hooks ---


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Add integration marker to integration tests
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)

        # Add slow marker to certain tests
        slow_patterns = [
            "performance",
            "stress",
            "load",
            "e2e_",
            "swarm_",
            "streaming",
            "shell_features",
            "test_batch_tool_edge_cases",
            "test_memory_edge_cases",
        ]
        if any(pattern in item.nodeid for pattern in slow_patterns):
            item.add_marker(pytest.mark.slow)
