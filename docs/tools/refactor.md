# hanzo-tools-refactor

Advanced refactoring with LSP/AST support. FAST parallel processing for large codebases.

## Installation

```bash
pip install hanzo-tools-refactor
```

Or as part of the full toolkit:

```bash
pip install hanzo-mcp[tools-all]
```

## Overview

`hanzo-tools-refactor` provides intelligent code refactoring:

- **rename** - Rename symbol across entire codebase
- **rename_batch** - Batch rename multiple symbols
- **extract_function** - Extract code into a new function
- **extract_variable** - Extract expression into a variable
- **inline** - Inline a function or variable
- **move** - Move symbol to another file
- **change_signature** - Modify function parameters
- **find_references** - Find all references to a symbol
- **organize_imports** - Clean up and sort imports

## Quick Start

```python
# Rename a symbol
refactor(action="rename", file="main.py", line=10, column=5, new_name="newName")

# Batch rename multiple symbols
refactor(
    action="rename_batch",
    renames=[
        {"old": "foo", "new": "bar"},
        {"old": "baz", "new": "qux"}
    ],
    path="./src"
)

# Change function signature
refactor(
    action="change_signature",
    file="utils.py",
    line=15,
    add_parameter={"name": "timeout", "default": "30"}
)

# Find references
refactor(action="find_references", file="models.py", line=25, column=8)
```

## Actions Reference

### rename

Rename a symbol at a specific location.

```python
refactor(
    action="rename",
    file="/path/to/file.py",
    line=42,
    column=10,
    new_name="betterName"
)
```

**Parameters:**
- `file` (required): File containing the symbol
- `line` (required): Line number (1-based)
- `column` (required): Column number (1-based)
- `new_name` (required): New name for the symbol

### rename_batch

Rename multiple symbols across the codebase in parallel.

```python
refactor(
    action="rename_batch",
    renames=[
        {"old": "getUserData", "new": "fetchUserData"},
        {"old": "setUserData", "new": "updateUserData"},
        {"old": "deleteUserData", "new": "removeUserData"}
    ],
    path="./src",
    parallel=True  # Default: true
)
```

**Parameters:**
- `renames` (required): List of {old, new} pairs
- `path`: Directory to search (default: current directory)
- `parallel`: Process in parallel (default: true)

### extract_function

Extract selected code into a new function.

```python
refactor(
    action="extract_function",
    file="/path/to/file.py",
    start_line=20,
    end_line=30,
    new_name="processData"
)
```

**Parameters:**
- `file` (required): Source file
- `start_line` (required): First line of code to extract
- `end_line` (required): Last line of code to extract
- `new_name`: Name for the new function

### extract_variable

Extract an expression into a variable.

```python
refactor(
    action="extract_variable",
    file="/path/to/file.py",
    line=15,
    start_column=10,
    end_column=45,
    new_name="calculatedValue"
)
```

**Parameters:**
- `file` (required): Source file
- `line` (required): Line containing the expression
- `start_column`: Start of expression
- `end_column`: End of expression
- `new_name`: Variable name

### inline

Inline a function or variable at its call sites.

```python
refactor(
    action="inline",
    file="/path/to/file.py",
    line=10,
    column=5
)
```

**Parameters:**
- `file` (required): Source file
- `line` (required): Line of the symbol
- `column` (required): Column of the symbol

### move

Move a symbol to a different file.

```python
refactor(
    action="move",
    file="/path/to/source.py",
    line=15,
    column=6,
    target_file="/path/to/destination.py"
)
```

**Parameters:**
- `file` (required): Source file
- `line` (required): Line of the symbol
- `column` (required): Column of the symbol
- `target_file` (required): Destination file

### change_signature

Modify a function's parameters.

```python
# Add a parameter
refactor(
    action="change_signature",
    file="api.py",
    line=20,
    add_parameter={"name": "timeout", "default": "30", "type": "int"}
)

# Remove a parameter
refactor(
    action="change_signature",
    file="api.py",
    line=20,
    remove_parameter="deprecated_param"
)

# Reorder parameters
refactor(
    action="change_signature",
    file="api.py",
    line=20,
    reorder_parameters=["user_id", "data", "options"]
)
```

### find_references

Find all references to a symbol.

```python
refactor(action="find_references", file="models.py", line=10, column=6)
```

**Response:**
```json
{
  "symbol": "UserModel",
  "references": [
    {"file": "views.py", "line": 15, "column": 8},
    {"file": "tests/test_models.py", "line": 22, "column": 12}
  ],
  "count": 2
}
```

### organize_imports

Clean up and sort imports in a file.

```python
refactor(action="organize_imports", file="main.py")
```

## Parallel Processing

The refactor tool uses parallel processing for large-scale operations:

```python
# Parallel is enabled by default
refactor(
    action="rename_batch",
    renames=[...],  # Many renames
    path="./large_codebase",
    parallel=True   # Uses all CPU cores
)

# Disable for sequential processing
refactor(
    action="rename_batch",
    renames=[...],
    parallel=False
)
```

## Preview Mode

Preview changes before applying them:

```python
# Preview only - don't apply changes
refactor(
    action="rename",
    file="main.py",
    line=10,
    column=5,
    new_name="newName",
    preview=True
)
```

**Response:**
```json
{
  "preview": true,
  "changes": [
    {"file": "main.py", "line": 10, "old": "oldName", "new": "newName"},
    {"file": "utils.py", "line": 25, "old": "oldName", "new": "newName"}
  ],
  "files_affected": 2
}
```

## Examples

### Safe Symbol Rename

```python
# 1. Find all usages first
refs = refactor(action="find_references", file="models.py", line=10, column=5)

# 2. Preview the rename
preview = refactor(
    action="rename",
    file="models.py",
    line=10,
    column=5,
    new_name="BetterName",
    preview=True
)

# 3. Apply the rename
refactor(
    action="rename",
    file="models.py",
    line=10,
    column=5,
    new_name="BetterName"
)
```

### Large-Scale Refactoring

```python
# Rename multiple patterns across codebase
refactor(
    action="rename_batch",
    renames=[
        {"old": "v1_api", "new": "legacy_api"},
        {"old": "v2_api", "new": "current_api"},
        {"old": "v3_api", "new": "api"}
    ],
    path="./src",
    parallel=True
)
```

### Extract Common Code

```python
# Extract duplicated logic into a function
refactor(
    action="extract_function",
    file="handlers.py",
    start_line=45,
    end_line=60,
    new_name="validate_and_process"
)
```

## Best Practices

1. **Always preview first** - Use `preview=True` for important refactors
2. **Run tests after** - Verify refactoring didn't break functionality
3. **Use batch operations** - `rename_batch` is faster than individual renames
4. **Commit before refactoring** - Have a clean git state to easily revert
5. **Combine with LSP** - Use `lsp` tool for initial symbol discovery
