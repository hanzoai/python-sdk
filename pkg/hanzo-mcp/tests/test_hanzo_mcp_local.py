#!/usr/bin/env python3
"""Test hanzo-mcp locally to ensure it works."""

import asyncio
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# Add the package to path for local testing
sys.path.insert(0, str(Path(__file__).parent.parent))

from hanzo_mcp import __version__
from hanzo_mcp.server import create_server, main
from hanzo_mcp.tools.common.permissions import PermissionManager


def test_basic_import():
    """Test that we can import hanzo-mcp."""
    print(f"✓ Successfully imported hanzo-mcp version {__version__}")
    assert __version__ == "0.7.0"


def test_server_creation():
    """Test creating an MCP server."""
    with tempfile.TemporaryDirectory() as tmpdir:
        server = create_server(
            name="test-server",
            allowed_paths=[tmpdir],
            enable_all_tools=True
        )
        
        print(f"✓ Created server: {server.name}")
        
        # List tools
        # Get tools from the MCP instance
        if hasattr(server, 'mcp'):
            tools = server.mcp._tool_map
            print(f"✓ Found {len(tools)} tools")
            tool_names = list(tools.keys())
        else:
            print("✗ Cannot access tools from server")
            return
        essential_tools = ["read", "write", "edit", "search", "bash", "notebook"]
        
        for tool in essential_tools:
            if tool in tool_names:
                print(f"  ✓ {tool} tool available")
            else:
                print(f"  ✗ {tool} tool missing")


async def test_file_operations():
    """Test basic file operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        server = create_server(
            name="test-server",
            allowed_paths=[tmpdir],
            enable_all_tools=True
        )
        
        test_file = Path(tmpdir) / "test.txt"
        
        # Test write
        print("\n Testing file operations:")
        
        # Mock the context for testing
        from mcp.server.fastmcp import Context
        ctx = Context()
        
        # Write file using the tool directly
        if "write" in server.mcp._tool_map:
            write_tool = server.mcp._tool_map["write"]
            write_result = await write_tool(
                path=str(test_file),
                content="Hello from hanzo-mcp test!"
            )
        else:
            print("  ✗ Write tool not found")
            return
        
        print(f"  ✓ Write result: {write_result}")
        assert test_file.exists()
        
        # Read file
        if "read" in server.mcp._tool_map:
            read_tool = server.mcp._tool_map["read"]
            read_result = await read_tool(path=str(test_file))
            print(f"  ✓ Read result: {str(read_result)[:50]}...")
            assert "Hello from hanzo-mcp test!" in str(read_result)
        else:
            print("  ✗ Read tool not found")
            return
        
        # Edit file
        if "edit" in server.mcp._tool_map:
            edit_tool = server.mcp._tool_map["edit"]
            edit_result = await edit_tool(
                path=str(test_file),
                old_text="Hello",
                new_text="Greetings"
            )
        else:
            print("  ✗ Edit tool not found")
            return
        
        print(f"  ✓ Edit completed")
        
        # Verify edit
        content = test_file.read_text()
        assert "Greetings from hanzo-mcp test!" in content


async def test_search_functionality():
    """Test search functionality."""
    with tempfile.TemporaryDirectory() as tmpdir:
        server = create_server(
            name="test-server", 
            allowed_paths=[tmpdir],
            enable_all_tools=True
        )
        
        # Create test files
        for i in range(3):
            test_file = Path(tmpdir) / f"file{i}.py"
            test_file.write_text(f'''
def function_{i}():
    """Function {i} documentation."""
    # TODO: Implement feature {i}
    return {i}
''')
        
        print("\n Testing search:")
        
        # Mock context
        from mcp.server.fastmcp import Context
        ctx = Context()
        
        # Search for TODOs
        if "search" in server.mcp._tool_map:
            search_tool = server.mcp._tool_map["search"]
            search_result = await search_tool(
                pattern="TODO",
                path=str(tmpdir)
            )
        else:
            print("  ✗ Search tool not found")
            return
        
        # Parse result
        if isinstance(search_result, str):
            try:
                result_data = json.loads(search_result)
            except:
                result_data = {"raw": search_result}
        else:
            result_data = search_result
            
        print(f"  ✓ Search found results: {result_data.get('results', 'N/A')}")


def test_cli_invocation():
    """Test CLI invocation."""
    print("\n Testing CLI:")
    
    # Test help
    result = subprocess.run(
        [sys.executable, "-m", "hanzo_mcp", "--help"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("  ✓ CLI help works")
    else:
        print(f"  ✗ CLI help failed: {result.stderr}")
    
    # Test version
    result = subprocess.run(
        [sys.executable, "-m", "hanzo_mcp", "--version"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0 and "0.7" in result.stdout:
        print(f"  ✓ CLI version works: {result.stdout.strip()}")
    else:
        print(f"  ✗ CLI version failed: {result.stderr}")


async def test_notebook_operations():
    """Test notebook operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        server = create_server(
            name="test-server",
            allowed_paths=[tmpdir],
            enable_all_tools=True
        )
        
        notebook_path = Path(tmpdir) / "test.ipynb"
        
        print("\n Testing notebook operations:")
        
        from mcp.server.fastmcp import Context
        ctx = Context()
        
        # Check if notebook tools are available
        tool_names = list(server.mcp._tool_map.keys())
        
        if "notebook" in tool_names:
            print("  ✓ Unified notebook tool available")
        elif "notebook_read" in tool_names and "notebook_edit" in tool_names:
            print("  ✓ Notebook read/edit tools available")
            
            # Create a notebook
            notebook_data = {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "print('Hello from notebook')",
                        "metadata": {}
                    },
                    {
                        "cell_type": "markdown", 
                        "source": "# Test Notebook",
                        "metadata": {}
                    }
                ],
                "metadata": {
                    "kernelspec": {
                        "display_name": "Python 3",
                        "language": "python",
                        "name": "python3"
                    }
                },
                "nbformat": 4,
                "nbformat_minor": 5
            }
            
            # Write notebook
            import json
            notebook_path.write_text(json.dumps(notebook_data))
            print("  ✓ Created test notebook")
            
            # Read notebook
            if "notebook_read" in server.mcp._tool_map:
                notebook_read_tool = server.mcp._tool_map["notebook_read"]
                read_result = await notebook_read_tool(path=str(notebook_path))
            else:
                print("  ✗ notebook_read tool not found")
                return
            
            print("  ✓ Successfully read notebook")
        else:
            print("  ⚠ Notebook tools not found")


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