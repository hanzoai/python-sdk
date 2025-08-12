"""Fixtures for swarm tests."""

import pytest

from tests.test_utils import ToolTestHelper


@pytest.fixture
def tool_helper():
    """Provide ToolTestHelper instance for tests."""
    return ToolTestHelper()
