# hanzo-tools-jupyter

Jupyter notebook tools for Hanzo MCP.

## Installation

```bash
pip install hanzo-tools-jupyter
```

## Tools

### jupyter - Notebook Operations
Read and edit Jupyter notebooks.

**Read notebook:**
```python
jupyter(action="read", path="/path/to/notebook.ipynb")
jupyter(action="read", path="/path/to/notebook.ipynb", cell=5)  # Specific cell
```

**Edit cell:**
```python
jupyter(
    action="edit",
    path="/path/to/notebook.ipynb",
    cell=5,
    content="print('Hello, World!')"
)
```

**Insert cell:**
```python
jupyter(
    action="insert",
    path="/path/to/notebook.ipynb",
    after_cell=5,
    content="# New cell",
    cell_type="markdown"
)
```

**Delete cell:**
```python
jupyter(
    action="delete",
    path="/path/to/notebook.ipynb",
    cell=5
)
```

**List cells:**
```python
jupyter(action="list", path="/path/to/notebook.ipynb")
```

## Cell Types

- `code` - Python code cell
- `markdown` - Markdown text cell
- `raw` - Raw text cell

## License

MIT
