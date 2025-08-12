"""Unified Jupyter notebook tool."""

from typing import (
    Any,
    Dict,
    Unpack,
    Optional,
    Annotated,
    TypedDict,
    final,
    override,
)
from pathlib import Path

import nbformat
from pydantic import Field
from mcp.server.fastmcp import Context as MCPContext

from hanzo_mcp.tools.jupyter.base import JupyterBaseTool

# Parameter types
Action = Annotated[
    str,
    Field(
        description="Action to perform: read (default), edit, create, delete, execute",
        default="read",
    ),
]

NotebookPath = Annotated[
    str,
    Field(
        description="Path to the Jupyter notebook file (.ipynb)",
    ),
]

CellId = Annotated[
    Optional[str],
    Field(
        description="Cell ID for targeted operations",
        default=None,
    ),
]

CellIndex = Annotated[
    Optional[int],
    Field(
        description="Cell index (0-based) for operations",
        default=None,
    ),
]

CellType = Annotated[
    Optional[str],
    Field(
        description="Cell type: code or markdown",
        default=None,
    ),
]

Source = Annotated[
    Optional[str],
    Field(
        description="New source content for cell",
        default=None,
    ),
]

EditMode = Annotated[
    str,
    Field(
        description="Edit mode: replace (default), insert, delete",
        default="replace",
    ),
]


class NotebookParams(TypedDict, total=False):
    """Parameters for notebook tool."""

    action: str
    notebook_path: str
    cell_id: Optional[str]
    cell_index: Optional[int]
    cell_type: Optional[str]
    source: Optional[str]
    edit_mode: str


@final
class JupyterTool(JupyterBaseTool):
    """Tool for Jupyter notebook operations."""

    @property
    @override
    def name(self) -> str:
        """Get the tool name."""
        return "jupyter"

    @property
    @override
    def description(self) -> str:
        """Get the tool description."""
        return """Jupyter notebooks. Actions: read (default), edit, create, delete, execute.

Usage:
jupyter "path/to/notebook.ipynb"
jupyter "notebook.ipynb" --cell-index 2
jupyter --action edit "notebook.ipynb" --cell-index 0 --source "print('Hello')"
jupyter --action create "new.ipynb"
"""

    @override
    async def call(
        self,
        ctx: MCPContext,
        **params: Unpack[NotebookParams],
    ) -> str:
        """Execute notebook operation."""
        tool_ctx = self.create_tool_context(ctx)

        # Extract parameters
        action = params.get("action", "read")
        notebook_path = params.get("notebook_path")

        if not notebook_path:
            return "Error: notebook_path is required"

        # Validate path
        path_validation = self.validate_path(notebook_path)
        if path_validation.is_error:
            await tool_ctx.error(path_validation.error_message)
            return f"Error: {path_validation.error_message}"

        # Check permissions
        allowed, error_msg = await self.check_path_allowed(notebook_path, tool_ctx)
        if not allowed:
            return error_msg

        # Route to appropriate handler
        if action == "read":
            return await self._handle_read(notebook_path, params, tool_ctx)
        elif action == "edit":
            return await self._handle_edit(notebook_path, params, tool_ctx)
        elif action == "create":
            return await self._handle_create(notebook_path, tool_ctx)
        elif action == "delete":
            return await self._handle_delete(notebook_path, params, tool_ctx)
        elif action == "execute":
            return await self._handle_execute(notebook_path, params, tool_ctx)
        else:
            return f"Error: Unknown action '{action}'. Valid actions: read, edit, create, delete, execute"

    async def _handle_read(
        self, notebook_path: str, params: Dict[str, Any], tool_ctx
    ) -> str:
        """Read notebook or specific cell."""
        exists, error_msg = await self.check_path_exists(notebook_path, tool_ctx)
        if not exists:
            return error_msg

        try:
            nb = self.read_notebook(notebook_path)

            # Check if specific cell requested
            cell_id = params.get("cell_id")
            cell_index = params.get("cell_index")

            if cell_id:
                # Find cell by ID
                for i, cell in enumerate(nb.cells):
                    if cell.get("id") == cell_id:
                        return self._format_cell(cell, i)
                return f"Error: Cell with ID '{cell_id}' not found"

            elif cell_index is not None:
                # Get cell by index
                if 0 <= cell_index < len(nb.cells):
                    return self._format_cell(nb.cells[cell_index], cell_index)
                else:
                    return f"Error: Cell index {cell_index} out of range (notebook has {len(nb.cells)} cells)"

            else:
                # Return all cells
                return self.format_notebook(nb)

        except Exception as e:
            await tool_ctx.error(f"Failed to read notebook: {str(e)}")
            return f"Error reading notebook: {str(e)}"

    async def _handle_edit(
        self, notebook_path: str, params: Dict[str, Any], tool_ctx
    ) -> str:
        """Edit notebook cell."""
        exists, error_msg = await self.check_path_exists(notebook_path, tool_ctx)
        if not exists:
            return error_msg

        source = params.get("source")
        edit_mode = params.get("edit_mode", "replace")

        # Only require source for non-delete operations
        if edit_mode != "delete" and not source:
            return "Error: source is required for edit action"
        cell_id = params.get("cell_id")
        cell_index = params.get("cell_index")
        cell_type = params.get("cell_type")

        try:
            nb = self.read_notebook(notebook_path)

            if edit_mode == "insert":
                # Insert new cell
                new_cell = (
                    nbformat.v4.new_code_cell(source)
                    if cell_type != "markdown"
                    else nbformat.v4.new_markdown_cell(source)
                )

                if cell_index is not None:
                    nb.cells.insert(cell_index, new_cell)
                else:
                    nb.cells.append(new_cell)

                self.write_notebook(nb, notebook_path)
                return f"Successfully inserted new cell at index {cell_index if cell_index is not None else len(nb.cells) - 1}"

            elif edit_mode == "delete":
                # Delete cell
                if cell_id:
                    for i, cell in enumerate(nb.cells):
                        if cell.get("id") == cell_id:
                            nb.cells.pop(i)
                            self.write_notebook(nb, notebook_path)
                            return f"Successfully deleted cell with ID '{cell_id}'"
                    return f"Error: Cell with ID '{cell_id}' not found"

                elif cell_index is not None:
                    if 0 <= cell_index < len(nb.cells):
                        nb.cells.pop(cell_index)
                        self.write_notebook(nb, notebook_path)
                        return f"Successfully deleted cell at index {cell_index}"
                    else:
                        return f"Error: Cell index {cell_index} out of range"
                else:
                    return "Error: cell_id or cell_index required for delete"

            else:  # replace
                # Replace cell content
                if cell_id:
                    for cell in nb.cells:
                        if cell.get("id") == cell_id:
                            cell["source"] = source
                            if cell_type:
                                cell["cell_type"] = cell_type
                            self.write_notebook(nb, notebook_path)
                            return f"Successfully updated cell with ID '{cell_id}'"
                    return f"Error: Cell with ID '{cell_id}' not found"

                elif cell_index is not None:
                    if 0 <= cell_index < len(nb.cells):
                        nb.cells[cell_index]["source"] = source
                        if cell_type:
                            nb.cells[cell_index]["cell_type"] = cell_type
                        self.write_notebook(nb, notebook_path)
                        return f"Successfully updated cell at index {cell_index}"
                    else:
                        return f"Error: Cell index {cell_index} out of range"
                else:
                    return "Error: cell_id or cell_index required for replace"

        except Exception as e:
            await tool_ctx.error(f"Failed to edit notebook: {str(e)}")
            return f"Error editing notebook: {str(e)}"

    async def _handle_create(self, notebook_path: str, tool_ctx) -> str:
        """Create new notebook."""
        # Check if already exists
        path = Path(notebook_path)
        if path.exists():
            return f"Error: Notebook already exists at {notebook_path}"

        try:
            # Create new notebook
            nb = nbformat.v4.new_notebook()

            # Ensure parent directory exists
            path.parent.mkdir(parents=True, exist_ok=True)

            # Write notebook
            self.write_notebook(nb, notebook_path)
            return f"Successfully created notebook at {notebook_path}"

        except Exception as e:
            await tool_ctx.error(f"Failed to create notebook: {str(e)}")
            return f"Error creating notebook: {str(e)}"

    async def _handle_delete(
        self, notebook_path: str, params: Dict[str, Any], tool_ctx
    ) -> str:
        """Delete notebook or cell."""
        # If cell specified, delegate to edit with delete mode
        if params.get("cell_id") or params.get("cell_index") is not None:
            params["edit_mode"] = "delete"
            return await self._handle_edit(notebook_path, params, tool_ctx)

        # Otherwise, delete entire notebook
        exists, error_msg = await self.check_path_exists(notebook_path, tool_ctx)
        if not exists:
            return error_msg

        try:
            Path(notebook_path).unlink()
            return f"Successfully deleted notebook {notebook_path}"
        except Exception as e:
            await tool_ctx.error(f"Failed to delete notebook: {str(e)}")
            return f"Error deleting notebook: {str(e)}"

    async def _handle_execute(
        self, notebook_path: str, params: Dict[str, Any], tool_ctx
    ) -> str:
        """Execute notebook cells (placeholder for future implementation)."""
        return "Error: Cell execution not yet implemented. Use a Jupyter kernel or server for execution."

    def _format_cell(self, cell: dict, index: int) -> str:
        """Format a single cell for display."""
        output = [f"Cell {index} ({cell.get('cell_type', 'unknown')})"]
        if cell.get("id"):
            output.append(f"ID: {cell.get('id')}")
        output.append("-" * 40)
        # Get source content
        source = cell.get("source", "")
        if isinstance(source, list):
            source = "".join(source)
        output.append(source)

        if cell.get("cell_type") == "code" and cell.get("outputs"):
            output.append("\nOutputs:")
            for out in cell.get("outputs", []):
                out_type = out.get("output_type", "")

                if out_type == "stream":
                    text = out.get("text", "")
                    if isinstance(text, list):
                        text = "".join(text)
                    name = out.get("name", "stdout")
                    output.append(f"[{name}]: {text}")

                elif out_type == "execute_result":
                    exec_count = out.get("execution_count", "?")
                    data = out.get("data", {})
                    # Try to get plain text representation
                    if "text/plain" in data:
                        text_data = data["text/plain"]
                        if isinstance(text_data, list):
                            text_data = "".join(text_data)
                        output.append(f"[Out {exec_count}]: {text_data}")
                    else:
                        output.append(f"[Out {exec_count}]: {data}")

                elif out_type == "error":
                    ename = out.get("ename", "Error")
                    evalue = out.get("evalue", "")
                    output.append(f"[Error]: {ename}: {evalue}")
                    # Include traceback if available
                    traceback = out.get("traceback", [])
                    if traceback:
                        output.append("Traceback:")
                        for line in traceback:
                            output.append(f"  {line}")

        return "\n".join(output)

    def read_notebook(self, notebook_path: str) -> Any:
        """Read a notebook from disk using nbformat.

        Args:
            notebook_path: Path to the notebook file

        Returns:
            Notebook object
        """
        with open(notebook_path, "r") as f:
            return nbformat.read(f, as_version=4)

    def write_notebook(self, nb: Any, notebook_path: str) -> None:
        """Write a notebook to disk using nbformat.

        Args:
            nb: Notebook object to write
            notebook_path: Path to write the notebook to
        """
        with open(notebook_path, "w") as f:
            nbformat.write(nb, f)

    def format_notebook(self, nb: Any) -> str:
        """Format an entire notebook for display.

        Args:
            nb: Notebook object

        Returns:
            Formatted string representation of the notebook
        """
        output = []
        output.append(f"Notebook with {len(nb.cells)} cells")
        output.append("=" * 50)

        for i, cell in enumerate(nb.cells):
            output.append("")
            output.append(self._format_cell(cell, i))

        return "\n".join(output)

    def register(self, mcp_server) -> None:
        """Register this tool with the MCP server."""
        pass
