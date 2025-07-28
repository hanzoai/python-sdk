"""Integration tests for hanzo-mcp with Claude CLI and basic operations."""

import asyncio
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Dict, Any, Optional

import pytest
from mcp.server import FastMCP
from mcp.client import ClientSessionGroup
from mcp.client.stdio import stdio_client

from hanzo_mcp.server import create_server
from hanzo_mcp.tools import register_all_tools
from hanzo_mcp.tools.common.permissions import PermissionManager


class TestHanzoMCPIntegration:
    """Test hanzo-mcp server functionality and Claude CLI integration."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    async def mcp_server(self, temp_dir):
        """Create and start an MCP server instance."""
        # Create server
        server = create_server(
            name="test-hanzo-mcp",
            allowed_paths=[str(temp_dir)],
            enable_all_tools=True
        )
        
        # Start server (in test mode)
        yield server
    
    async def test_server_startup(self, mcp_server):
        """Test that the MCP server starts correctly."""
        assert mcp_server is not None
        assert isinstance(mcp_server, FastMCP)
        
        # Check that tools are registered
        tools = mcp_server.list_tools()
        assert len(tools) > 0
        
        # Check for essential tools
        tool_names = [tool.name for tool in tools]
        assert "read" in tool_names
        assert "write" in tool_names
        assert "edit" in tool_names
        assert "search" in tool_names
    
    async def test_file_operations(self, mcp_server, temp_dir):
        """Test basic file operations through MCP."""
        # Create a test file
        test_file = temp_dir / "test.txt"
        test_content = "Hello from hanzo-mcp!"
        
        # Test write operation
        write_result = await mcp_server.call_tool(
            "write",
            arguments={
                "path": str(test_file),
                "content": test_content
            }
        )
        assert "success" in write_result.lower() or test_file.exists()
        
        # Test read operation
        read_result = await mcp_server.call_tool(
            "read",
            arguments={"path": str(test_file)}
        )
        assert test_content in read_result
        
        # Test edit operation
        edit_result = await mcp_server.call_tool(
            "edit",
            arguments={
                "path": str(test_file),
                "old_text": "Hello",
                "new_text": "Greetings"
            }
        )
        
        # Verify edit
        read_after_edit = await mcp_server.call_tool(
            "read",
            arguments={"path": str(test_file)}
        )
        assert "Greetings from hanzo-mcp!" in read_after_edit
    
    async def test_search_functionality(self, mcp_server, temp_dir):
        """Test the unified search tool."""
        # Create test files with content
        for i in range(3):
            test_file = temp_dir / f"file{i}.py"
            test_file.write_text(f"""
def function_{i}():
    # TODO: Implement this function
    return "result_{i}"
""")
        
        # Test search
        search_result = await mcp_server.call_tool(
            "search",
            arguments={
                "pattern": "TODO",
                "path": str(temp_dir)
            }
        )
        
        # Parse result
        if isinstance(search_result, str):
            result_data = json.loads(search_result)
        else:
            result_data = search_result
        
        # Check results
        assert "results" in result_data
        assert len(result_data["results"]) >= 3
        
        # Verify each file was found
        found_files = {r["file"] for r in result_data["results"]}
        for i in range(3):
            expected_file = str(temp_dir / f"file{i}.py")
            assert any(expected_file in f for f in found_files)
    
    @pytest.mark.skipif(
        not os.path.exists(os.path.expanduser("~/.claude/bin/claude")),
        reason="Claude CLI not installed"
    )
    async def test_claude_cli_integration(self, temp_dir):
        """Test integration with Claude CLI."""
        # Create a simple test script that uses hanzo-mcp
        test_script = temp_dir / "test_claude.py"
        test_script.write_text("""
import subprocess
import json

# Call Claude with a simple file operation task
result = subprocess.run([
    "claude", 
    "--mcp-server", "hanzo-mcp",
    "--prompt", "Create a file called hello.txt with 'Hello Claude' content"
], capture_output=True, text=True)

print(result.stdout)
""")
        
        # Run the test script
        result = subprocess.run(
            ["python", str(test_script)],
            capture_output=True,
            text=True,
            cwd=str(temp_dir)
        )
        
        # Check that the file was created
        hello_file = temp_dir / "hello.txt"
        assert hello_file.exists() or "success" in result.stdout.lower()
    
    async def test_multi_tool_workflow(self, mcp_server, temp_dir):
        """Test a workflow using multiple tools."""
        # Create a Python file with issues
        test_file = temp_dir / "buggy.py"
        test_file.write_text("""
def calculate_sum(a, b):
    # TODO: Add type hints
    result = a + b
    print(f"Sum is: {result}")
    return result

def main():
    # This will fail with strings
    result = calculate_sum("10", "20")
    print(result)
""")
        
        # 1. Search for TODOs
        search_result = await mcp_server.call_tool(
            "search",
            arguments={
                "pattern": "TODO",
                "path": str(temp_dir)
            }
        )
        assert "TODO" in search_result
        
        # 2. Read the file
        content = await mcp_server.call_tool(
            "read",
            arguments={"path": str(test_file)}
        )
        assert "calculate_sum" in content
        
        # 3. Edit to add type hints
        await mcp_server.call_tool(
            "edit",
            arguments={
                "path": str(test_file),
                "old_text": "def calculate_sum(a, b):",
                "new_text": "def calculate_sum(a: int, b: int) -> int:"
            }
        )
        
        # 4. Run the critic tool
        critic_result = await mcp_server.call_tool(
            "critic",
            arguments={
                "analysis": f"Review the code in {test_file} for potential issues"
            }
        )
        
        # The critic should identify the type mismatch
        assert "string" in critic_result.lower() or "type" in critic_result.lower()
    
    async def test_notebook_operations(self, mcp_server, temp_dir):
        """Test notebook read/write operations."""
        notebook_path = temp_dir / "test.ipynb"
        
        # Create a notebook
        create_result = await mcp_server.call_tool(
            "notebook_write",
            arguments={
                "path": str(notebook_path),
                "cells": [
                    {
                        "cell_type": "code",
                        "source": "print('Hello from notebook')"
                    },
                    {
                        "cell_type": "markdown",
                        "source": "# Test Notebook\nThis is a test."
                    }
                ]
            }
        )
        
        assert notebook_path.exists()
        
        # Read the notebook
        read_result = await mcp_server.call_tool(
            "notebook_read",
            arguments={"path": str(notebook_path)}
        )
        
        # Parse result
        if isinstance(read_result, str):
            notebook_data = json.loads(read_result)
        else:
            notebook_data = read_result
            
        assert "cells" in notebook_data
        assert len(notebook_data["cells"]) == 2
        assert notebook_data["cells"][0]["source"] == "print('Hello from notebook')"


class TestHanzoMCPStdioServer:
    """Test hanzo-mcp as a stdio server (how Claude Desktop uses it)."""
    
    @pytest.fixture
    def server_env(self, tmp_path):
        """Environment for the server."""
        return {
            "HANZO_ALLOWED_PATHS": str(tmp_path),
            "PYTHONPATH": os.environ.get("PYTHONPATH", "")
        }
    
    async def test_stdio_server_basic(self, tmp_path, server_env):
        """Test basic stdio server operations."""
        # Start the server process
        server_process = subprocess.Popen(
            ["python", "-m", "hanzo_mcp"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={**os.environ, **server_env},
            text=True
        )
        
        try:
            # Give server time to start
            time.sleep(1)
            
            # Send initialize request
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "capabilities": {}
                }
            }
            
            server_process.stdin.write(json.dumps(init_request) + "\n")
            server_process.stdin.flush()
            
            # Read response (with timeout)
            import select
            readable, _, _ = select.select([server_process.stdout], [], [], 5)
            
            if readable:
                response = server_process.stdout.readline()
                response_data = json.loads(response)
                
                assert response_data["id"] == 1
                assert "result" in response_data
                assert "capabilities" in response_data["result"]
            
            # Test listing tools
            list_tools_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
            
            server_process.stdin.write(json.dumps(list_tools_request) + "\n")
            server_process.stdin.flush()
            
            readable, _, _ = select.select([server_process.stdout], [], [], 5)
            if readable:
                response = server_process.stdout.readline()
                response_data = json.loads(response)
                
                assert response_data["id"] == 2
                assert "result" in response_data
                assert "tools" in response_data["result"]
                assert len(response_data["result"]["tools"]) > 0
        
        finally:
            # Clean up
            server_process.terminate()
            server_process.wait(timeout=5)


@pytest.mark.asyncio
async def test_hanzo_mcp_cli_tool():
    """Test the hanzo-mcp CLI tool directly."""
    # Test help command
    result = subprocess.run(
        ["python", "-m", "hanzo_mcp", "--help"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert "hanzo-mcp" in result.stdout.lower() or "usage" in result.stdout.lower()
    
    # Test version command
    result = subprocess.run(
        ["python", "-m", "hanzo_mcp", "--version"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert "0.7" in result.stdout  # Should show version 0.7.x


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])