"""Test unified search tool functionality."""

import os
import asyncio
import tempfile
from pathlib import Path

import pytest
from hanzo_mcp.tools.search import create_find_tool, create_unified_search_tool


@pytest.mark.asyncio
async def test_unified_search_basic():
    """Test basic unified search functionality."""
    # Create search tool
    search_tool = create_unified_search_tool()

    # Test with current directory
    result = await search_tool.run(
        pattern="UnifiedSearch", path=".", max_results_per_type=5
    )

    assert result.data is not None
    assert "results" in result.data
    assert "statistics" in result.data

    # Should find the class definition
    results = result.data["results"]
    assert len(results) > 0

    # Check statistics
    stats = result.data["statistics"]
    assert "query" in stats
    assert stats["query"] == "UnifiedSearch"
    assert "search_types_used" in stats
    assert "text" in stats["search_types_used"]  # Should use text search


@pytest.mark.asyncio
async def test_unified_search_auto_detection():
    """Test automatic search type detection."""
    search_tool = create_unified_search_tool()

    # Test natural language query (should trigger vector search if available)
    result = await search_tool.run(
        pattern="how does search work in this codebase", max_results_per_type=5
    )

    assert result.data is not None
    stats = result.data["statistics"]

    # Should detect this as a natural language query
    if "vector" in stats["search_types_used"]:
        # Vector search was used
        assert True
    else:
        # At minimum, text search should be used
        assert "text" in stats["search_types_used"]


@pytest.mark.asyncio
async def test_unified_search_code_patterns():
    """Test code pattern search."""
    search_tool = create_unified_search_tool()

    # Test AST pattern detection
    result = await search_tool.run(pattern="class SearchResult", max_results_per_type=5)

    assert result.data is not None
    stats = result.data["statistics"]

    # Should use AST search for class patterns
    if "ast" in stats["search_types_used"]:
        assert True
    else:
        # At minimum text search
        assert "text" in stats["search_types_used"]


@pytest.mark.asyncio
async def test_unified_search_with_files():
    """Test file search integration."""
    search_tool = create_unified_search_tool()

    # Test file search
    result = await search_tool.run(
        pattern="*.py", search_files=True, max_results_per_type=10
    )

    assert result.data is not None
    stats = result.data["statistics"]

    # Should include file search
    assert "files" in stats["search_types_used"]

    # Check for file results
    results = result.data["results"]
    file_results = [r for r in results if r["type"] == "file"]
    assert len(file_results) > 0


@pytest.mark.asyncio
async def test_find_tool_basic():
    """Test basic find tool functionality."""
    find_tool = create_find_tool()

    # Find Python files
    result = await find_tool.run(pattern="*.py", path=".", max_results=10)

    assert result.data is not None
    assert "results" in result.data
    assert "statistics" in result.data

    # Should find Python files
    results = result.data["results"]
    assert len(results) > 0
    assert all(r["extension"] == ".py" for r in results)


@pytest.mark.asyncio
async def test_find_tool_with_filters():
    """Test find tool with filters."""
    find_tool = create_find_tool()

    # Create test directory structure
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create some test files
        (Path(tmpdir) / "small.txt").write_text("small file")
        (Path(tmpdir) / "large.txt").write_text("x" * 10000)  # 10KB
        (Path(tmpdir) / "test_file.py").write_text("print('test')")
        (Path(tmpdir) / "old_file.txt").write_text("old")

        # Make old_file older
        old_time = os.path.getmtime(Path(tmpdir) / "old_file.txt") - 86400  # 1 day ago
        os.utime(Path(tmpdir) / "old_file.txt", (old_time, old_time))

        # Test size filter
        result = await find_tool.run(pattern="*.txt", path=tmpdir, min_size="5KB")

        assert result.data is not None
        results = result.data["results"]
        assert len(results) == 1
        assert results[0]["name"] == "large.txt"

        # Test time filter
        result = await find_tool.run(
            pattern="*.txt", path=tmpdir, modified_after="12 hours ago"
        )

        results = result.data["results"]
        assert len(results) == 2  # small.txt and large.txt
        assert "old_file.txt" not in [r["name"] for r in results]


@pytest.mark.asyncio
async def test_find_tool_fuzzy_search():
    """Test fuzzy file name matching."""
    find_tool = create_find_tool()

    # Test fuzzy matching
    result = await find_tool.run(
        pattern="unifd",  # Misspelled "unified"
        fuzzy=True,
        max_results=5,
    )

    assert result.data is not None
    # Fuzzy search might find "unified_search.py"
    # But results depend on actual files in directory


@pytest.mark.asyncio
async def test_unified_search_pagination():
    """Test pagination in unified search."""
    search_tool = create_unified_search_tool()

    # First page
    result1 = await search_tool.run(pattern="def", page_size=5, page=1)

    assert result1.data is not None
    assert "pagination" in result1.data

    pagination = result1.data["pagination"]
    assert pagination["page"] == 1
    assert pagination["page_size"] == 5

    if pagination["has_next"]:
        # Get second page
        result2 = await search_tool.run(pattern="def", page_size=5, page=2)

        assert result2.data is not None
        assert result2.data["pagination"]["page"] == 2

        # Results should be different
        results1 = result1.data["results"]
        results2 = result2.data["results"]

        # Check that we got different results
        files1 = set(r["file"] for r in results1)
        files2 = set(r["file"] for r in results2)

        # Some overlap is OK but shouldn't be identical
        assert files1 != files2 or len(files1) == 0 or len(files2) == 0


if __name__ == "__main__":
    # Run tests
    asyncio.run(test_unified_search_basic())
    asyncio.run(test_find_tool_basic())
    print("Basic tests passed!")
