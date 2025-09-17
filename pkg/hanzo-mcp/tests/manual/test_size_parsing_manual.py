#!/usr/bin/env python3
"""Test size parsing."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hanzo_mcp.tools.search.find_tool import FindTool


def test_parse_size():
    """Test size parsing."""
    tool = FindTool()

    test_cases = [
        ("5KB", 5 * 1024),
        ("10KB", 10 * 1024),
        ("1MB", 1024 * 1024),
        ("100", 100),
        ("5K", 5 * 1024),
    ]

    for size_str, expected in test_cases:
        result = tool._parse_size(size_str)
        print(f"'{size_str}' -> {result} bytes (expected: {expected}, match: {result == expected})")


if __name__ == "__main__":
    test_parse_size()
