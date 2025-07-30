"""Simple test for the Grep AST tool."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from tests.test_utils import ToolTestHelper, create_mock_ctx, create_permission_manager

def test_simple():
    """Simple test to check if test collection works."""
    assert True

@pytest.mark.asyncio
async def test_async_simple():
    """Simple async test to check if test collection works."""
    assert True
