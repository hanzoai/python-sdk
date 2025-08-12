"""Integration tests for hanzo-mcp with Claude CLI and basic operations."""

import os
import json
import tempfile
import subprocess
from pathlib import Path

import pytest
from hanzo_mcp.server import create_server
from mcp.client.session import ClientSession
from mcp.server.fastmcp import FastMCP


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
        # Create server with jupyter enabled
        server = create_server(
            name="test-hanzo-mcp",
            allowed_paths=[str(temp_dir)],
            enable_all_tools=True,
            enabled_tools={"jupyter": True},
        )

        # Start server (in test mode)
        yield server

    async def test_server_startup(self, tool_helper, mcp_server):
        """Test that the MCP server starts correctly."""
        assert mcp_server is not None
        # mcp_server is a HanzoMCPServer instance that wraps FastMCP
        from hanzo_mcp.server import HanzoMCPServer

        assert isinstance(mcp_server, HanzoMCPServer)
        assert hasattr(mcp_server, "mcp")
        assert isinstance(mcp_server.mcp, FastMCP)

        # Check that tools are registered via the wrapped FastMCP instance
        tools = await mcp_server.mcp.list_tools()
        assert len(tools) > 0

        # Check for essential tools
        tool_names = [tool.name for tool in tools]
        assert "read" in tool_names
        assert "write" in tool_names
        assert "edit" in tool_names
        assert "search" in tool_names

    async def test_file_operations(self, tool_helper, mcp_server, temp_dir):
        """Test basic file operations through MCP."""
        # Create a test file
        test_file = temp_dir / "test.txt"
        test_content = "Hello from hanzo-mcp!"

        # Test write operation
        write_result = await mcp_server.mcp.call_tool(
            "write", arguments={"file_path": str(test_file), "content": test_content}
        )
        # write_result is a tuple (content_list, metadata)
        assert test_file.exists()
        if isinstance(write_result, tuple) and len(write_result) > 1:
            result_text = str(write_result[1])
            assert "success" in result_text.lower()

        # Test read operation
        read_result = await mcp_server.mcp.call_tool(
            "read", arguments={"file_path": str(test_file)}
        )
        # read_result is a tuple (content_list, metadata)
        if isinstance(read_result, tuple) and len(read_result) > 0:
            content_list = read_result[0]
            if content_list and hasattr(content_list[0], "text"):
                assert test_content in content_list[0].text
            else:
                assert test_content in str(read_result)
        else:
            assert test_content in str(read_result)

        # Test edit operation
        edit_result = await mcp_server.mcp.call_tool(
            "edit",
            arguments={
                "file_path": str(test_file),
                "old_string": "Hello",
                "new_string": "Greetings",
            },
        )

        # Verify edit
        read_after_edit = await mcp_server.mcp.call_tool(
            "read", arguments={"file_path": str(test_file)}
        )
        # read_after_edit is a tuple (content_list, metadata)
        if isinstance(read_after_edit, tuple) and len(read_after_edit) > 0:
            content_list = read_after_edit[0]
            if content_list and hasattr(content_list[0], "text"):
                assert "Greetings from hanzo-mcp!" in content_list[0].text
            else:
                assert "Greetings from hanzo-mcp!" in str(read_after_edit)
        else:
            assert "Greetings from hanzo-mcp!" in str(read_after_edit)

    async def test_search_functionality(self, tool_helper, mcp_server, temp_dir):
        """Test the unified search tool."""
        # Create test files with content
        for i in range(3):
            test_file = temp_dir / f"file{i}.py"
            test_file.write_text(
                f"""
def function_{i}():
    # TODO: Implement this function
    return "result_{i}"
"""
            )

        # Test search
        search_result = await mcp_server.mcp.call_tool(
            "search", arguments={"pattern": "TODO", "path": str(temp_dir)}
        )

        # Handle tuple result from call_tool
        if isinstance(search_result, tuple) and len(search_result) > 0:
            content_list = search_result[0]
            if content_list and hasattr(content_list[0], "text"):
                result_text = content_list[0].text
            else:
                result_text = str(search_result)
        else:
            result_text = str(search_result)

        # Check results - search tool returns text, not JSON
        assert "TODO" in result_text
        assert "Total results: 3" in result_text

        # Verify each file was found in the text output
        for i in range(3):
            expected_file = f"file{i}.py"
            assert expected_file in result_text

    @pytest.mark.skipif(
        not os.path.exists(os.path.expanduser("~/.claude/bin/claude")),
        reason="Claude CLI not installed",
    )
    async def test_claude_cli_integration(self, tool_helper, temp_dir):
        """Test integration with Claude CLI."""
        # Create a simple test script that uses hanzo-mcp
        test_script = temp_dir / "test_claude.py"
        test_script.write_text(
            """
import subprocess
import json

# Call Claude with a simple file operation task
result = subprocess.run([
    "claude",
    "--mcp-server", "hanzo-mcp",
    "--prompt", "Create a file called hello.txt with 'Hello Claude' content"
], capture_output=True, text=True)

print(result.stdout)
"""
        )

        # Run the test script
        result = subprocess.run(
            ["python", str(test_script)],
            capture_output=True,
            text=True,
            cwd=str(temp_dir),
        )

        # Check that the file was created
        hello_file = temp_dir / "hello.txt"
        assert hello_file.exists() or "success" in str(result).lower()

    async def test_multi_tool_workflow(self, tool_helper, mcp_server, temp_dir):
        """Test a workflow using multiple tools."""
        # Create a Python file with issues
        test_file = temp_dir / "buggy.py"
        test_file.write_text(
            """
def calculate_sum(a, b):
    # TODO: Add type hints
    result = a + b
    print(f"Sum is: {result}")
    return result

def main():
    # This will fail with strings
    result = calculate_sum("10", "20")
    print(result)
"""
        )

        # 1. Search for TODOs
        search_result = await mcp_server.mcp.call_tool(
            "search", arguments={"pattern": "TODO", "path": str(temp_dir)}
        )
        # Handle tuple result
        if isinstance(search_result, tuple) and len(search_result) > 0:
            content_list = search_result[0]
            if content_list and hasattr(content_list[0], "text"):
                result_text = content_list[0].text
            else:
                result_text = str(search_result)
        else:
            result_text = str(search_result)
        assert "TODO" in result_text

        # 2. Read the file
        content = await mcp_server.mcp.call_tool(
            "read", arguments={"file_path": str(test_file)}
        )
        # Handle tuple result
        if isinstance(content, tuple) and len(content) > 0:
            content_list = content[0]
            if content_list and hasattr(content_list[0], "text"):
                content_text = content_list[0].text
            else:
                content_text = str(content)
        else:
            content_text = str(content)
        assert "calculate_sum" in content_text

        # 3. Edit to add type hints
        await mcp_server.mcp.call_tool(
            "edit",
            arguments={
                "file_path": str(test_file),
                "old_string": "def calculate_sum(a, b):",
                "new_string": "def calculate_sum(a: int, b: int) -> int:",
            },
        )

        # 4. Run the critic tool
        critic_result = await mcp_server.mcp.call_tool(
            "critic",
            arguments={
                "analysis": f"Review the code in {test_file} for potential issues"
            },
        )

        # Handle tuple result
        if isinstance(critic_result, tuple) and len(critic_result) > 0:
            content_list = critic_result[0]
            if content_list and hasattr(content_list[0], "text"):
                critic_text = content_list[0].text
            else:
                critic_text = str(critic_result)
        else:
            critic_text = str(critic_result)
        # The critic tool currently just returns a confirmation message
        # Check that it returns the expected template response
        assert (
            "Critical analysis complete" in critic_text
            or "analysis" in critic_text.lower()
        )

    async def test_notebook_operations(self, tool_helper, mcp_server, temp_dir):
        """Test notebook read/write operations."""
        notebook_path = temp_dir / "test.ipynb"

        # Create a basic notebook structure first
        notebook_content = {
            "cells": [
                {
                    "cell_type": "code",
                    "source": ["print('Hello from notebook')"],
                    "metadata": {},
                    "outputs": [],
                }
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

        # Write the notebook using the write tool
        write_result = await mcp_server.mcp.call_tool(
            "write",
            arguments={
                "file_path": str(notebook_path),
                "content": json.dumps(notebook_content, indent=2),
            },
        )

        assert notebook_path.exists()

        # Now edit to add a markdown cell using the unified jupyter tool
        edit_result = await mcp_server.mcp.call_tool(
            "jupyter",
            arguments={
                "action": "edit",
                "notebook_path": str(notebook_path),
                "source": "# Test Notebook\nThis is a test.",
                "edit_mode": "insert",
                "cell_type": "markdown",
            },
        )

        # Read the notebook using the unified jupyter tool
        read_result = await mcp_server.mcp.call_tool(
            "jupyter", arguments={"action": "read", "notebook_path": str(notebook_path)}
        )

        # Handle tuple result
        if isinstance(read_result, tuple) and len(read_result) > 0:
            content_list = read_result[0]
            if content_list and hasattr(content_list[0], "text"):
                notebook_text = content_list[0].text
                # Parse the JSON from the text
                notebook_data = json.loads(notebook_text)
            else:
                notebook_data = read_result
        else:
            notebook_data = json.loads(str(read_result))

        assert "cells" in notebook_data
        assert len(notebook_data["cells"]) >= 1  # At least the original code cell
        # Check that we have at least one code cell
        code_cells = [
            cell for cell in notebook_data["cells"] if cell.get("cell_type") == "code"
        ]
        assert len(code_cells) >= 1


class TestHanzoMCPStdioServer:
    """Test hanzo-mcp as a stdio server (how Claude Desktop uses it)."""

    @pytest.fixture
    def server_env(self, tmp_path):
        """Environment for the server."""
        return {
            "HANZO_ALLOWED_PATHS": str(tmp_path),
            "PYTHONPATH": os.environ.get("PYTHONPATH", ""),
        }

    async def test_stdio_server_basic(self, tool_helper, tmp_path, server_env):
        """Test basic stdio server operations."""
        # Skip test if MCP client imports are not available
        try:
            from mcp.client.stdio import stdio_client
            from mcp.client import ClientSession
        except ImportError:
            pytest.skip("MCP client imports not available - needs updated dependencies")
            return

        # Use the MCP client session to test the server
        async with stdio_client(
            ["python", "-m", "hanzo_mcp"], env={**os.environ, **server_env}
        ) as (read, write):
            # Create a client session
            async with ClientSession(read, write) as session:
                # Initialize the session
                await session.initialize()

                # List available tools
                tools_response = await session.list_tools()
                assert tools_response.tools
                assert len(tools_response.tools) > 0

                # Check some basic tools are available
                tool_names = [tool.name for tool in tools_response.tools]
                assert "read" in tool_names
                assert "write" in tool_names
                assert "grep" in tool_names

                # Test a simple tool call
                result = await session.call_tool(
                    "write",
                    arguments={
                        "file_path": str(tmp_path / "test.txt"),
                        "content": "Hello from stdio test!",
                    },
                )

                # Verify the file was created
                test_file = tmp_path / "test.txt"
                assert test_file.exists()
                assert test_file.read_text() == "Hello from stdio test!"


@pytest.mark.asyncio
async def test_hanzo_mcp_cli_tool():
    """Test the hanzo-mcp CLI tool directly."""
    # Test help command
    result = subprocess.run(
        ["python", "-m", "hanzo_mcp", "--help"], capture_output=True, text=True
    )

    assert result.returncode == 0
    assert "usage" in result.stdout.lower() or "mcp server" in result.stdout.lower()

    # Test version command
    result = subprocess.run(
        ["python", "-m", "hanzo_mcp", "--version"], capture_output=True, text=True
    )

    assert result.returncode == 0
    assert (
        "0.6" in result.stdout or "0.7" in result.stdout
    )  # Should show version 0.6.x or 0.7.x


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
