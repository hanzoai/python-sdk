#!/usr/bin/env python3
"""Test hanzo-mcp locally to ensure it works."""

import sys
import json
import asyncio
import tempfile
import subprocess
from pathlib import Path

# Add the package to path for local testing
sys.path.insert(0, str(Path(__file__).parent.parent))

from hanzo_mcp import __version__
from hanzo_mcp.server import create_server


def test_basic_import():
    """Test that we can import hanzo-mcp."""
    print(f"✓ Successfully imported hanzo-mcp version {__version__}")
    assert __version__ == "0.7.7"


def test_server_creation():
    """Test creating an MCP server."""
    with tempfile.TemporaryDirectory() as tmpdir:
        server = create_server(name="test-server", allowed_paths=[tmpdir], enable_all_tools=True)

        print(f"✓ Created server: {server.__class__.__name__}")

        # List tools
        # Get tools from the MCP instance
        if (
            hasattr(server, "mcp")
            and hasattr(server.mcp, "_tool_manager")
            and hasattr(server.mcp._tool_manager, "_tools")
        ):
            tools = server.mcp._tool_manager._tools
            print(f"✓ Found {len(tools)} tools")
            tool_names = list(tools.keys())
        else:
            print("✗ Cannot access tools from server")
            raise AssertionError("Cannot access tools from server")
        essential_tools = ["read", "write", "edit", "search", "bash"]

        missing_tools = []
        for tool in essential_tools:
            if tool in tool_names:
                print(f"  ✓ {tool} tool available")
            else:
                print(f"  ✗ {tool} tool missing")
                missing_tools.append(tool)

        assert len(missing_tools) == 0, f"Missing tools: {missing_tools}"


import pytest


@pytest.mark.asyncio
async def test_file_operations():
    """Test basic file operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        server = create_server(name="test-server", allowed_paths=[tmpdir], enable_all_tools=True)

        test_file = Path(tmpdir) / "test.txt"
        test_content = "Hello from hanzo-mcp test!"

        # Test write operation using call_tool
        write_result = await server.mcp.call_tool(
            "write", arguments={"file_path": str(test_file), "content": test_content}
        )

        # Verify file was created
        assert test_file.exists()
        assert test_file.read_text() == test_content

        # Test read operation
        read_result = await server.mcp.call_tool("read", arguments={"file_path": str(test_file)})

        # Handle tuple result from call_tool
        if isinstance(read_result, tuple) and len(read_result) > 0:
            content_list = read_result[0]
            if content_list and hasattr(content_list[0], "text"):
                assert test_content in content_list[0].text
            else:
                assert test_content in str(read_result)
        else:
            assert test_content in str(read_result)

        # Test edit operation
        edit_result = await server.mcp.call_tool(
            "edit",
            arguments={
                "file_path": str(test_file),
                "old_string": "Hello",
                "new_string": "Greetings",
            },
        )

        # Verify edit worked
        edited_content = test_file.read_text()
        assert edited_content == "Greetings from hanzo-mcp test!"


@pytest.mark.asyncio
async def test_search_functionality():
    """Test search functionality."""
    with tempfile.TemporaryDirectory() as tmpdir:
        server = create_server(name="test-server", allowed_paths=[tmpdir], enable_all_tools=True)

        # Create test files
        for i in range(3):
            test_file = Path(tmpdir) / f"file{i}.py"
            test_file.write_text(
                f'''
def function_{i}():
    """Function {i} documentation."""
    # TODO: Implement feature {i}
    return {i}
'''
            )

        # Search for TODOs using the search tool
        search_result = await server.mcp.call_tool("search", arguments={"pattern": "TODO", "path": str(tmpdir)})

        # Handle tuple result from call_tool
        if isinstance(search_result, tuple) and len(search_result) > 0:
            content_list = search_result[0]
            if content_list and hasattr(content_list[0], "text"):
                result_text = content_list[0].text
            else:
                result_text = str(search_result)
        else:
            result_text = str(search_result)

        # Verify search found all TODOs
        assert "TODO" in result_text
        assert "Total results: 3" in result_text

        # Verify each file was found
        for i in range(3):
            assert f"file{i}.py" in result_text


def test_cli_invocation():
    """Test CLI invocation."""
    print("\n Testing CLI:")

    # Test help
    result = subprocess.run([sys.executable, "-m", "hanzo_mcp", "--help"], capture_output=True, text=True)

    if result.returncode == 0:
        print("  ✓ CLI help works")
    else:
        print(f"  ✗ CLI help failed: {result.stderr}")

    # Test version
    result = subprocess.run([sys.executable, "-m", "hanzo_mcp", "--version"], capture_output=True, text=True)

    if result.returncode == 0 and "0.7" in result.stdout:
        print(f"  ✓ CLI version works: {result.stdout.strip()}")
    else:
        print(f"  ✗ CLI version failed: {result.stderr}")


@pytest.mark.asyncio
async def test_notebook_operations():
    """Test notebook operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        server = create_server(name="test-server", allowed_paths=[tmpdir], enable_all_tools=True)

        notebook_path = Path(tmpdir) / "test.ipynb"

        # Create a notebook structure
        notebook_data = {
            "cells": [
                {
                    "cell_type": "code",
                    "source": ["print('Hello from notebook')"],
                    "metadata": {},
                    "outputs": [],
                },
                {
                    "cell_type": "markdown",
                    "source": ["# Test Notebook"],
                    "metadata": {},
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
            "nbformat_minor": 5,
        }

        # Write notebook using write tool
        await server.mcp.call_tool(
            "write",
            arguments={
                "file_path": str(notebook_path),
                "content": json.dumps(notebook_data, indent=2),
            },
        )

        assert notebook_path.exists()

        # Read notebook using jupyter tool
        read_result = await server.mcp.call_tool(
            "jupyter", arguments={"action": "read", "notebook_path": str(notebook_path)}
        )

        # Handle tuple result
        if isinstance(read_result, tuple) and len(read_result) > 0:
            content_list = read_result[0]
            if content_list and hasattr(content_list[0], "text"):
                notebook_text = content_list[0].text
                notebook_content = json.loads(notebook_text)
            else:
                notebook_content = read_result
        else:
            notebook_content = json.loads(str(read_result))

        # Verify notebook structure
        assert "cells" in notebook_content
        assert len(notebook_content["cells"]) >= 2
        assert notebook_content["cells"][0]["cell_type"] == "code"
        assert notebook_content["cells"][1]["cell_type"] == "markdown"

        # Test editing notebook to add a new cell
        edit_result = await server.mcp.call_tool(
            "jupyter",
            arguments={
                "action": "edit",
                "notebook_path": str(notebook_path),
                "new_source": "x = 42\nprint(f'The answer is {x}')",
                "edit_mode": "insert",
                "cell_type": "code",
            },
        )

        # Read again to verify the edit
        read_result2 = await server.mcp.call_tool(
            "jupyter", arguments={"action": "read", "notebook_path": str(notebook_path)}
        )

        # Handle tuple result
        if isinstance(read_result2, tuple) and len(read_result2) > 0:
            content_list = read_result2[0]
            if content_list and hasattr(content_list[0], "text"):
                notebook_text = content_list[0].text
                updated_content = json.loads(notebook_text)
            else:
                updated_content = read_result2
        else:
            updated_content = json.loads(str(read_result2))

        # Verify new cell was added
        assert len(updated_content["cells"]) >= 3


async def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Testing hanzo-mcp locally")
    print("=" * 60)

    try:
        test_basic_import()
        test_server_creation()
        await test_file_operations()
        await test_search_functionality()
        test_cli_invocation()
        await test_notebook_operations()

        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Run the tests
    asyncio.run(run_all_tests())
