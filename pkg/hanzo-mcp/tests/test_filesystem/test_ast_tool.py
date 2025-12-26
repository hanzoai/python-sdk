"""Tests for the Symbols tool."""

import pytest
from hanzo_tools.filesystem import ASTTool as SymbolsTool


def test_symbols_simple():
    """Simple test to verify collection works."""
    assert True


@pytest.mark.asyncio
async def test_symbols_import():
    """Test that the SymbolsTool can be imported."""
    assert SymbolsTool is not None
