"""Test LSP tool functionality."""

import asyncio
import tempfile
from pathlib import Path

import pytest
from hanzo_mcp.tools.lsp import create_lsp_tool


@pytest.mark.asyncio
async def test_lsp_tool_status():
    """Test LSP tool status check."""
    lsp_tool = create_lsp_tool()

    # Create a test Go file
    with tempfile.NamedTemporaryFile(suffix=".go", mode="w", delete=False) as f:
        f.write(
            """package main

import "fmt"

func main() {
    fmt.Println("Hello, World!")
}

func greet(name string) string {
    return fmt.Sprintf("Hello, %s!", name)
}
"""
        )
        go_file = f.name

    try:
        # Check status for Go
        result = await lsp_tool.run(action="status", file=go_file)

        assert result.data is not None
        assert "language" in result.data
        assert result.data["language"] == "go"
        assert "lsp_server" in result.data
        assert result.data["lsp_server"] == "gopls"
        assert "capabilities" in result.data
        assert "definition" in result.data["capabilities"]

    finally:
        Path(go_file).unlink()


@pytest.mark.asyncio
async def test_lsp_tool_unsupported_file():
    """Test LSP tool with unsupported file type."""
    lsp_tool = create_lsp_tool()

    # Test with unsupported file
    result = await lsp_tool.run(action="status", file="test.unknown")

    assert result.data is not None
    assert "error" in result.data
    assert "Unsupported file type" in result.data["error"]
    assert "supported_languages" in result.data


@pytest.mark.asyncio
async def test_lsp_tool_invalid_action():
    """Test LSP tool with invalid action."""
    lsp_tool = create_lsp_tool()

    # Test with invalid action
    result = await lsp_tool.run(action="invalid_action", file="test.py")

    assert result.data is not None
    assert "error" in result.data
    assert "Invalid action" in result.data["error"]


@pytest.mark.asyncio
async def test_lsp_tool_definition_placeholder():
    """Test LSP tool definition action (placeholder)."""
    lsp_tool = create_lsp_tool()

    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write(
            """def hello():
    return "Hello"

result = hello()
"""
        )
        py_file = f.name

    try:
        # Test definition lookup
        result = await lsp_tool.run(
            action="definition",
            file=py_file,
            line=4,
            character=9,  # Position of 'hello' in 'hello()'
        )

        assert result.data is not None
        assert "action" in result.data
        assert result.data["action"] == "definition"
        assert "note" in result.data
        assert "fallback" in result.data

    finally:
        Path(py_file).unlink()


@pytest.mark.asyncio
async def test_lsp_tool_python_status():
    """Test LSP status for Python files."""
    lsp_tool = create_lsp_tool()

    # Check Python LSP status
    result = await lsp_tool.run(action="status", file="test.py")

    assert result.data is not None
    assert result.data["language"] == "python"
    assert result.data["lsp_server"] == "pylsp"
    assert "definition" in result.data["capabilities"]
    assert "hover" in result.data["capabilities"]


@pytest.mark.asyncio
async def test_lsp_tool_typescript_status():
    """Test LSP status for TypeScript files."""
    lsp_tool = create_lsp_tool()

    # Check TypeScript LSP status
    result = await lsp_tool.run(action="status", file="app.ts")

    assert result.data is not None
    assert result.data["language"] == "typescript"
    assert result.data["lsp_server"] == "typescript-language-server"
    assert "completion" in result.data["capabilities"]


@pytest.mark.asyncio
async def test_lsp_tool_rename_placeholder():
    """Test LSP rename action (placeholder)."""
    lsp_tool = create_lsp_tool()

    # Test rename
    result = await lsp_tool.run(
        action="rename",
        file="test.go",
        line=10,
        character=5,
        new_name="newFunctionName",
    )

    assert result.data is not None
    assert result.data["action"] == "rename"
    assert result.data["new_name"] == "newFunctionName"
    assert "fallback" in result.data


if __name__ == "__main__":
    # Run basic tests
    asyncio.run(test_lsp_tool_status())
    asyncio.run(test_lsp_tool_unsupported_file())
    asyncio.run(test_lsp_tool_invalid_action())
    print("LSP tool tests passed!")
