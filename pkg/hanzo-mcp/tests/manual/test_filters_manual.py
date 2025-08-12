#!/usr/bin/env python3
"""Test find tool filters."""

import os
import sys
import asyncio
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hanzo_mcp.tools.search import create_find_tool


async def test_filters():
    """Test find tool with filters."""
    find_tool = create_find_tool()

    # Create test directory structure
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"Test directory: {tmpdir}")

        # Create some test files
        (Path(tmpdir) / "small.txt").write_text("small file")
        (Path(tmpdir) / "large.txt").write_text("x" * 10000)  # 10KB
        (Path(tmpdir) / "test_file.py").write_text("print('test')")
        (Path(tmpdir) / "old_file.txt").write_text("old")

        # Make old_file older
        old_time = os.path.getmtime(Path(tmpdir) / "old_file.txt") - 86400  # 1 day ago
        os.utime(Path(tmpdir) / "old_file.txt", (old_time, old_time))

        print("\nTest 1: Size filter (min_size=5KB)")
        result = await find_tool.run(pattern="*.txt", path=tmpdir, min_size="5KB")

        if result.data:
            results = result.data.get("results", [])
            print(f"Found {len(results)} files:")
            for r in results:
                print(f"  - {r['name']} ({r['size']} bytes)")
        else:
            print("No results")

        print("\nTest 2: Time filter (modified_after='12 hours ago')")
        result = await find_tool.run(
            pattern="*.txt", path=tmpdir, modified_after="12 hours ago"
        )

        if result.data:
            results = result.data.get("results", [])
            print(f"Found {len(results)} files:")
            for r in results:
                print(f"  - {r['name']} (modified: {r.get('modified', 'unknown')})")
        else:
            print("No results")


if __name__ == "__main__":
    asyncio.run(test_filters())
