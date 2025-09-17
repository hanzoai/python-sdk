"""Test unified Jupyter tool implementation."""

import json

import pytest
from mcp.server.fastmcp import Context as MCPContext
from hanzo_mcp.tools.jupyter.jupyter import JupyterTool
from hanzo_mcp.tools.common.permissions import PermissionManager


@pytest.fixture
def permission_manager(tmp_path):
    """Create a permission manager with tmp_path as allowed."""
    pm = PermissionManager()
    pm.add_allowed_path(str(tmp_path))
    return pm


@pytest.fixture
def jupyter_tool(permission_manager):
    """Create JupyterTool instance."""
    return JupyterTool(permission_manager)


@pytest.fixture
def sample_notebook(tmp_path):
    """Create a sample notebook for testing."""
    notebook_path = tmp_path / "test.ipynb"
    notebook_content = {
        "cells": [
            {
                "cell_type": "code",
                "source": "print('Hello, World!')",
                "metadata": {},
                "outputs": [
                    {
                        "output_type": "stream",
                        "name": "stdout",
                        "text": "Hello, World!\n",
                    }
                ],
                "execution_count": 1,
            },
            {
                "cell_type": "markdown",
                "source": "# Test Notebook\nThis is a test.",
                "metadata": {},
            },
        ],
        "metadata": {"language_info": {"name": "python"}},
        "nbformat": 4,
        "nbformat_minor": 5,
    }

    with open(notebook_path, "w") as f:
        json.dump(notebook_content, f)

    return notebook_path


@pytest.mark.asyncio
class TestUnifiedJupyterTool:
    """Test the unified Jupyter tool."""

    @pytest.mark.asyncio
    async def test_read_action(self, jupyter_tool, sample_notebook):
        """Test reading a notebook."""
        ctx = MCPContext()

        # Read entire notebook
        result = await jupyter_tool.call(ctx, action="read", notebook_path=str(sample_notebook))

        assert "Notebook with 2 cells" in result
        assert "Hello, World!" in result
        assert "Test Notebook" in result
        assert "[stdout]: Hello, World!" in result

        # Read specific cell by index
        result = await jupyter_tool.call(ctx, action="read", notebook_path=str(sample_notebook), cell_index=0)

        assert "Cell 0 (code)" in result
        assert "print('Hello, World!')" in result

    @pytest.mark.asyncio
    async def test_create_action(self, jupyter_tool, tmp_path):
        """Test creating a new notebook."""
        ctx = MCPContext()
        new_notebook = tmp_path / "new.ipynb"

        result = await jupyter_tool.call(ctx, action="create", notebook_path=str(new_notebook))

        assert "Successfully created notebook" in result
        assert new_notebook.exists()

        # Verify it's a valid notebook
        with open(new_notebook) as f:
            nb = json.load(f)
            assert nb["nbformat"] == 4
            assert "cells" in nb

    @pytest.mark.asyncio
    async def test_edit_action_replace(self, jupyter_tool, sample_notebook):
        """Test editing a cell (replace mode)."""
        ctx = MCPContext()

        result = await jupyter_tool.call(
            ctx,
            action="edit",
            notebook_path=str(sample_notebook),
            cell_index=0,
            source="print('Modified!')",
            edit_mode="replace",
        )

        assert "Successfully updated cell at index 0" in result

        # Verify the change
        with open(sample_notebook) as f:
            nb = json.load(f)
            # nbformat stores source as list in JSON
            source = nb["cells"][0]["source"]
            if isinstance(source, list):
                source = "".join(source)
            assert source == "print('Modified!')"

    @pytest.mark.asyncio
    async def test_edit_action_insert(self, jupyter_tool, sample_notebook):
        """Test inserting a new cell."""
        ctx = MCPContext()

        result = await jupyter_tool.call(
            ctx,
            action="edit",
            notebook_path=str(sample_notebook),
            cell_index=1,
            source="x = 42",
            cell_type="code",
            edit_mode="insert",
        )

        assert "Successfully inserted new cell at index 1" in result

        # Verify the notebook now has 3 cells
        with open(sample_notebook) as f:
            nb = json.load(f)
            assert len(nb["cells"]) == 3
            # nbformat stores source as list in JSON
            source = nb["cells"][1]["source"]
            if isinstance(source, list):
                source = "".join(source)
            assert source == "x = 42"
            assert nb["cells"][1]["cell_type"] == "code"

    @pytest.mark.asyncio
    async def test_edit_action_delete(self, jupyter_tool, sample_notebook):
        """Test deleting a cell."""
        ctx = MCPContext()

        # First check we have 2 cells
        with open(sample_notebook) as f:
            nb = json.load(f)
            assert len(nb["cells"]) == 2

        result = await jupyter_tool.call(
            ctx,
            action="edit",
            notebook_path=str(sample_notebook),
            cell_index=1,
            edit_mode="delete",
        )

        assert "Successfully deleted cell at index 1" in result

        # Verify we now have 1 cell
        with open(sample_notebook) as f:
            nb = json.load(f)
            assert len(nb["cells"]) == 1

    @pytest.mark.asyncio
    async def test_delete_action_notebook(self, jupyter_tool, sample_notebook):
        """Test deleting entire notebook."""
        ctx = MCPContext()

        result = await jupyter_tool.call(ctx, action="delete", notebook_path=str(sample_notebook))

        assert "Successfully deleted notebook" in result
        assert not sample_notebook.exists()

    @pytest.mark.asyncio
    async def test_error_handling(self, jupyter_tool, tmp_path):
        """Test error handling."""
        ctx = MCPContext()

        # Non-existent file
        result = await jupyter_tool.call(ctx, action="read", notebook_path=str(tmp_path / "nonexistent.ipynb"))
        assert "Error: File does not exist" in result

        # Invalid action
        result = await jupyter_tool.call(ctx, action="invalid", notebook_path=str(tmp_path / "test.ipynb"))
        assert "Error: Unknown action" in result

        # Missing required params for edit (need to test insert mode)
        # First create a notebook to edit
        test_nb = tmp_path / "test_edit.ipynb"
        await jupyter_tool.call(ctx, action="create", notebook_path=str(test_nb))

        # Try to insert without source
        result = await jupyter_tool.call(
            ctx,
            action="edit",
            notebook_path=str(test_nb),
            cell_index=0,
            edit_mode="insert",
            cell_type="code",  # Required for insert
        )
        assert "Error: source is required" in result
