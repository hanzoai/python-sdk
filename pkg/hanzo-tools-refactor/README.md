# hanzo-tools-refactor

Advanced refactoring tools for Hanzo MCP.

## Installation

```bash
pip install hanzo-tools-refactor
```

## Tools

### refactor - Code Refactoring
AST/LSP-based refactoring with parallel processing.

**Rename symbol:**
```python
refactor(action="rename", file="/f.py", line=10, column=5, new_name="newName")
```

**Batch rename:**
```python
refactor(
    action="rename_batch",
    renames=[{"old": "foo", "new": "bar"}],
    path="./src"
)
```

**Extract function:**
```python
refactor(
    action="extract_function",
    file="/f.py",
    start_line=10,
    end_line=20,
    new_name="extracted_function"
)
```

**Extract variable:**
```python
refactor(
    action="extract_variable",
    file="/f.py",
    line=10,
    column=5,
    new_name="extracted_var"
)
```

**Inline:**
```python
refactor(action="inline", file="/f.py", line=10, column=5)
```

**Move:**
```python
refactor(action="move", file="/f.py", line=10, target_file="/new.py")
```

**Change signature:**
```python
refactor(
    action="change_signature",
    file="/f.py",
    line=10,
    add_parameter={"name": "x", "default": "None"}
)
```

**Find references:**
```python
refactor(action="find_references", file="/f.py", line=10, column=5)
```

**Organize imports:**
```python
refactor(action="organize_imports", file="/f.py")
```

## Options

- `preview=True` - Preview changes without applying
- `parallel=True` - Process files in parallel (default)

## License

MIT
