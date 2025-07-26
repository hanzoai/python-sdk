#!/usr/bin/env python3
"""Demo of the unified search tool - THE primary search interface.

This demonstrates how the unified search tool intelligently combines multiple
search modalities to find anything in your codebase.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from hanzo_mcp.tools.search import create_unified_search_tool


async def demo_unified_search():
    """Demonstrate unified search capabilities."""
    print("=== Hanzo Unified Search Demo ===\n")
    
    # Create the search tool
    search = create_unified_search_tool()
    
    # Demo 1: Simple text search
    print("1. Simple text search for 'UnifiedSearch':")
    result = await search.run(
        pattern="UnifiedSearch",
        max_results_per_type=3
    )
    
    if result.data and "results" in result.data:
        print(f"   Found {len(result.data['results'])} results")
        print(f"   Search types used: {', '.join(result.data['statistics']['search_types_used'])}")
        for r in result.data["results"][:3]:
            print(f"   - {r['file']}:{r['line']} ({r['type']})")
    print()
    
    # Demo 2: Natural language query
    print("2. Natural language query:")
    result = await search.run(
        pattern="how does pagination work in search results",
        max_results_per_type=3
    )
    
    if result.data:
        stats = result.data["statistics"]
        print(f"   Search types: {', '.join(stats['search_types_used'])}")
        print(f"   Total matches: {stats['total_matches']}")
        print(f"   Note: Vector search would be used if embedding model is available")
    print()
    
    # Demo 3: Code pattern search
    print("3. Code pattern search for class definitions:")
    result = await search.run(
        pattern="class.*Tool",  # Regex for Tool classes
        max_results_per_type=5
    )
    
    if result.data and "results" in result.data:
        print(f"   Found {len(result.data['results'])} Tool classes")
        unique_files = set(r["file"] for r in result.data["results"])
        print(f"   Across {len(unique_files)} files")
    print()
    
    # Demo 4: File search
    print("4. Find Python test files:")
    result = await search.run(
        pattern="test_*.py",
        search_files=True,
        max_results_per_type=5
    )
    
    if result.data:
        stats = result.data["statistics"]
        if "files" in stats["search_types_used"]:
            file_results = [r for r in result.data["results"] if r["type"] == "file"]
            print(f"   Found {len(file_results)} test files")
            for r in file_results[:3]:
                print(f"   - {r['file']} ({r['context']['semantic']})")
    print()
    
    # Demo 5: Symbol search
    print("5. Symbol/identifier search:")
    result = await search.run(
        pattern="BaseTool",  # Looking for the BaseTool class
        max_results_per_type=3
    )
    
    if result.data:
        # Should find symbol definitions
        symbol_results = [r for r in result.data["results"] if r.get("context", {}).get("node_type")]
        if symbol_results:
            print(f"   Found {len(symbol_results)} symbol matches")
        else:
            print(f"   Found {len(result.data['results'])} text matches")
    print()
    
    # Demo 6: Combined search with pagination
    print("6. Paginated results demo:")
    result = await search.run(
        pattern="async def",
        page_size=10,
        page=1
    )
    
    if result.data and "pagination" in result.data:
        pag = result.data["pagination"]
        print(f"   Page {pag['page']} of {pag['total_pages']}")
        print(f"   Showing {len(result.data['results'])} of {pag['total_results']} total results")
        print(f"   Has next page: {pag['has_next']}")
    print()
    
    # Demo 7: Search with filters
    print("7. Filtered search (Python files only):")
    result = await search.run(
        pattern="import",
        include="*.py",
        max_results_per_type=5
    )
    
    if result.data:
        print(f"   Found {len(result.data['results'])} import statements in Python files")
        stats = result.data["statistics"]
        print(f"   Search completed in {stats['time_ms'].get('text', 0)}ms")
    print()
    
    # Summary
    print("\n=== Search Intelligence ===")
    print("The unified search tool automatically:")
    print("- Detects query intent (code vs natural language)")
    print("- Runs appropriate search types in parallel")
    print("- Combines and ranks results by relevance")
    print("- Deduplicates across search types")
    print("- Provides context and semantic information")
    print("- Handles pagination for large result sets")
    print("\nIt's THE primary search interface for finding anything!")


async def demo_find_tool():
    """Demonstrate the find tool for fast file discovery."""
    print("\n\n=== Find Tool Demo ===\n")
    
    from hanzo_mcp.tools.search import create_find_tool
    find = create_find_tool()
    
    # Demo 1: Find by pattern
    print("1. Find all Python files:")
    result = await find.run(
        pattern="*.py",
        max_results=5
    )
    
    if result.data and "results" in result.data:
        print(f"   Found {result.data['statistics']['total_found']} Python files")
        print(f"   Search time: {result.data['statistics']['search_time_ms']}ms")
    print()
    
    # Demo 2: Find with size filter
    print("2. Find large files (>10KB):")
    result = await find.run(
        pattern="*",
        min_size="10KB",
        max_results=5
    )
    
    if result.data and "results" in result.data:
        for r in result.data["results"][:3]:
            size_kb = r["size"] / 1024
            print(f"   - {r['name']} ({size_kb:.1f} KB)")
    print()
    
    # Demo 3: Find recently modified
    print("3. Find recently modified files:")
    result = await find.run(
        pattern="*",
        modified_after="1 hour ago",
        max_results=5
    )
    
    if result.data and "results" in result.data:
        print(f"   Found {len(result.data['results'])} recently modified files")
    
    print("\nFind tool is optimized for fast file discovery by name and attributes!")


if __name__ == "__main__":
    # Run demos
    asyncio.run(demo_unified_search())
    asyncio.run(demo_find_tool())