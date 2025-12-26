#!/usr/bin/env python3
"""Tests for MCP startup performance.

These tests ensure that MCP server startup remains fast by checking
import times. Slow imports cause MCP connections to timeout and hang.

IMPORTANT: If these tests fail, it means imports have become slow again.
The fix is to make heavy imports LAZY - only import when actually needed,
not at module load time.

Common culprits for slow imports:
- sentence_transformers (2.5+ seconds)
- litellm (1+ second)
- hanzo_memory embedding services (3+ seconds)
"""

import sys
import time
import subprocess
from pathlib import Path

import pytest

# Maximum allowed import times (in seconds)
# These are intentionally generous to avoid flaky tests
MAX_MODULE_IMPORT_TIME = 0.7  # hanzo_mcp.tools module (generous for CI variance)
MAX_TOTAL_IMPORT_TIME = 1.0  # All core imports combined
MAX_CLI_STARTUP_TIME = 3.0  # CLI --help should respond quickly


class TestImportPerformance:
    """Test that imports are fast enough for MCP to work."""

    def test_tools_module_import_is_fast(self):
        """Test that hanzo_mcp.tools imports quickly.

        This is critical because slow imports cause MCP to hang.
        The tools module must NOT import heavy dependencies at load time.
        """
        code = """
import time
start = time.time()
import hanzo_mcp.tools
elapsed = time.time() - start
print(f"ELAPSED:{elapsed:.3f}")
"""
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"Import failed: {result.stderr}"

        # Extract elapsed time
        for line in result.stdout.split("\n"):
            if line.startswith("ELAPSED:"):
                elapsed = float(line.split(":")[1])
                break
        else:
            pytest.fail(f"Could not find elapsed time in output: {result.stdout}")

        assert elapsed < MAX_MODULE_IMPORT_TIME, (
            f"hanzo_mcp.tools import took {elapsed:.2f}s (max: {MAX_MODULE_IMPORT_TIME}s). "
            "This is too slow! Check for heavy imports at module load time. "
            "Common culprits: sentence_transformers, litellm, hanzo_memory"
        )

    def test_no_heavy_imports_at_module_level(self):
        """Test that heavy packages are NOT imported at module load time."""
        code = """
import sys
# Clear any cached modules
for mod in list(sys.modules.keys()):
    if any(x in mod for x in ['hanzo', 'sentence', 'litellm']):
        del sys.modules[mod]

# Import the tools module
import hanzo_mcp.tools

# Check what got imported
heavy_modules = []
for name in ['sentence_transformers', 'litellm', 'hanzo_memory']:
    if name in sys.modules:
        heavy_modules.append(name)

if heavy_modules:
    print(f"FAIL:Heavy modules imported at load time: {heavy_modules}")
    sys.exit(1)
else:
    print("PASS:No heavy modules imported")
"""
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if "FAIL:" in result.stdout:
            pytest.fail(result.stdout.split("FAIL:")[1].strip())

        assert "PASS:" in result.stdout, f"Unexpected output: {result.stdout}"

    def test_total_import_time(self):
        """Test that all core imports combined are fast."""
        code = """
import time
start = time.time()
import hanzo_mcp
import hanzo_mcp.tools
from hanzo_mcp.server import create_server
elapsed = time.time() - start
print(f"ELAPSED:{elapsed:.3f}")
"""
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"Import failed: {result.stderr}"

        for line in result.stdout.split("\n"):
            if line.startswith("ELAPSED:"):
                elapsed = float(line.split(":")[1])
                break
        else:
            pytest.fail(f"Could not find elapsed time in output: {result.stdout}")

        assert elapsed < MAX_TOTAL_IMPORT_TIME, (
            f"Total imports took {elapsed:.2f}s (max: {MAX_TOTAL_IMPORT_TIME}s). "
            "Imports are too slow! MCP connections will timeout."
        )


class TestCLIPerformance:
    """Test that CLI starts quickly."""

    def test_cli_help_is_fast(self):
        """Test that --help responds quickly."""
        start = time.time()
        result = subprocess.run(
            [sys.executable, "-m", "hanzo_mcp", "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        elapsed = time.time() - start

        assert result.returncode == 0, f"CLI help failed: {result.stderr}"
        assert elapsed < MAX_CLI_STARTUP_TIME, (
            f"CLI --help took {elapsed:.2f}s (max: {MAX_CLI_STARTUP_TIME}s). This is too slow for MCP connections."
        )

    def test_cli_does_not_hang(self):
        """Test that CLI starts without hanging.

        This was the original issue - MCP tools would hang for 4+ hours
        because imports were too slow.
        """
        try:
            result = subprocess.run(
                [sys.executable, "-m", "hanzo_mcp", "--help"],
                capture_output=True,
                text=True,
                timeout=10,  # Should respond within 10 seconds max
            )
            assert "hanzo" in result.stdout.lower() or "mcp" in result.stdout.lower()
        except subprocess.TimeoutExpired:
            pytest.fail("CLI hung for more than 10 seconds! This indicates slow imports causing MCP to hang.")


class TestLazyImportPattern:
    """Test that lazy import patterns are correctly implemented."""

    def test_memory_tools_use_lazy_import(self):
        """Test that memory tools use lazy imports."""
        code = """
import sys

# Import the memory tools module
from hanzo_tools.memory import memory_tools

# Check that hanzo_memory was NOT imported
if 'hanzo_memory' in sys.modules:
    print("FAIL:hanzo_memory imported at module load")
    sys.exit(1)
print("PASS:hanzo_memory not imported at module load")
"""
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if "FAIL:" in result.stdout:
            pytest.fail(
                "memory_tools.py imports hanzo_memory at module load time. Use lazy imports with TYPE_CHECKING pattern."
            )

    def test_search_tool_no_heavy_deps(self):
        """Test that search tool does not import heavy ML dependencies.

        Vector search with sentence_transformers has been removed to keep MCP lightweight.
        If semantic search is needed, use external services (hanzo-node, hanzo desktop).
        """
        code = """
import sys

# Import the search tool module
from hanzo_mcp.tools.search import search_tool

# Check that sentence_transformers was NOT imported (should be removed entirely)
if 'sentence_transformers' in sys.modules:
    print("FAIL:sentence_transformers imported - should be removed from search_tool")
    sys.exit(1)
print("PASS:no heavy ML dependencies in search_tool")
"""
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if "FAIL:" in result.stdout:
            pytest.fail(
                "search_tool.py imports sentence_transformers. Vector search has been removed - keep MCP lightweight."
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
