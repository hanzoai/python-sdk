# hanzo-tools-fs

Filesystem tools for reading, writing, editing, and searching files with permission management.

## Installation

```bash
pip install hanzo-tools-fs
```

Or as part of the full toolkit:

```bash
pip install hanzo-mcp[tools-all]
```

## Overview

`hanzo-tools-fs` provides:

- **read** - Read file contents with line numbers
- **write** - Write/create files
- **edit** - Edit files with find/replace
- **tree** - Directory tree view
- **find** - Find files by pattern
- **search** - Search file contents (ripgrep-powered)
- **ast** - AST-based code structure search

## Quick Start

```python
# Read a file
read(file_path="/path/to/file.py")

# Write a file
write(file_path="/path/to/new.py", content="print('hello')")

# Edit a file
edit(file_path="/path/to/file.py", old_string="foo", new_string="bar")

# Search for patterns
search(pattern="TODO", path="./src")

# Find files
find(pattern="*.py", path="./src")

# View directory structure
tree(path="./src", depth=3)

# AST-based code search
ast(pattern="class.*Service", path="./src")
```

## Tools Reference

### read

Read file contents with line numbers.

```python
# Basic read
read(file_path="/path/to/file.py")

# Read with offset and limit (for large files)
read(file_path="/path/to/large.py", offset=100, limit=50)
```

**Parameters:**
- `file_path` (required): Absolute path to the file
- `offset`: Starting line number (0-based, default: 0)
- `limit`: Maximum lines to read (default: 2000)

**Output format:**
```
     1→def hello():
     2→    print("Hello, World!")
     3→
[Showing lines 1-3 of 3]
```

### write

Write content to a file, creating it if it doesn't exist.

```python
# Create new file
write(file_path="/path/to/new.py", content="print('hello')")

# Overwrite existing file
write(file_path="/path/to/existing.py", content="new content")
```

**Parameters:**
- `file_path` (required): Absolute path to the file
- `content` (required): Content to write

### edit

Edit a file by replacing text.

```python
# Simple replacement
edit(
    file_path="/path/to/file.py",
    old_string="def old_name():",
    new_string="def new_name():"
)

# Replace multiple occurrences
edit(
    file_path="/path/to/file.py",
    old_string="TODO",
    new_string="DONE",
    expected_replacements=5
)
```

**Parameters:**
- `file_path` (required): Absolute path to the file
- `old_string` (required): Text to find
- `new_string` (required): Text to replace with
- `expected_replacements`: Expected number of replacements (default: 1)

### tree

Display directory tree structure.

```python
# Basic tree view
tree(path="/project")

# Limited depth
tree(path="/project", depth=2)

# Include filtered directories
tree(path="/project", include_filtered=True)
```

**Parameters:**
- `path` (required): Directory path
- `depth`: Maximum depth (default: 3)
- `include_filtered`: Include commonly filtered dirs like node_modules (default: false)

**Output format:**
```
├── src/
│   ├── main.py
│   └── utils/
│       └── helpers.py
├── tests/
│   └── test_main.py
└── pyproject.toml
```

### find

Find files and directories by pattern.

```python
# Find Python files
find(pattern="*.py", path="/project")

# Find test files
find(pattern="test_*.py", path="/project")

# Find directories
find(pattern="*config*", path="/project", type="dir")

# Limit results
find(pattern="*.md", path="/project", max_results=20)
```

**Parameters:**
- `pattern` (required): Glob pattern to match
- `path`: Directory to search (default: current directory)
- `type`: Filter by type - "file", "dir", or None for both
- `max_results`: Maximum results (default: 100)

### search

Search for patterns in file contents using ripgrep.

```python
# Basic search
search(pattern="TODO", path="./src")

# Search with file filter
search(pattern="import", path="./src", include="*.py")

# Search with context lines
search(pattern="error", path="./logs", context_lines=5)

# Limit results
search(pattern="function", path="./src", max_results=20)
```

**Parameters:**
- `pattern` (required): Regex pattern to search for
- `path`: Directory or file to search (default: current directory)
- `include`: Glob pattern to filter files (e.g., "*.py")
- `context_lines`: Lines of context around matches (default: 2)
- `max_results`: Maximum results (default: 50)

**Features:**
- Uses ripgrep (rg) if available for high performance
- Falls back to Python regex if ripgrep not installed
- Async file I/O for non-blocking operation

### ast

AST-based code structure search using tree-sitter.

```python
# Find function definitions
ast(pattern="def test_", path="./tests")

# Find class definitions
ast(pattern="class.*Service", path="./src")

# Find with line numbers
ast(pattern="async def", path="./src", line_number=True)

# Case-insensitive search
ast(pattern="config", path="./src", ignore_case=True)
```

**Parameters:**
- `pattern` (required): Regex pattern to search for
- `path` (required): File or directory to search
- `ignore_case`: Case-insensitive matching (default: false)
- `line_number`: Display line numbers (default: false)

**Supported Languages:**
- Python (.py, .pyw)
- JavaScript/TypeScript (.js, .jsx, .ts, .tsx)
- Go (.go)
- Rust (.rs)
- C/C++ (.c, .cpp, .h, .hpp)
- Java (.java)
- Ruby (.rb)
- PHP (.php)
- And more...

## Permission Management

All filesystem tools respect permission boundaries:

```python
from hanzo_tools.fs import register_tools
from hanzo_tools.core import PermissionManager

# Set up permission manager
pm = PermissionManager(
    allowed_paths=["/home/user/project"],
    denied_paths=["/home/user/project/.env"]
)

# Register tools with MCP server
register_tools(mcp_server, pm)
```

### Read-Only Tools

For sandboxed environments, use read-only tools:

```python
from hanzo_tools.fs import get_read_only_filesystem_tools

# Get only read operations
tools = get_read_only_filesystem_tools(permission_manager)
# Includes: read, tree, find, search, ast
```

## Examples

### Code Review Workflow

```python
# Find all TODO comments
search(pattern="TODO|FIXME", path="./src")

# Check code structure
ast(pattern="class.*", path="./src")

# Review specific file
read(file_path="./src/main.py")
```

### Refactoring Workflow

```python
# Find all usages of old function name
search(pattern="old_function_name", path="./src")

# Find function definition
ast(pattern="def old_function_name", path="./src")

# Edit the function
edit(
    file_path="./src/utils.py",
    old_string="def old_function_name(",
    new_string="def new_function_name("
)
```

### Project Exploration

```python
# Get project structure
tree(path="./", depth=3)

# Find configuration files
find(pattern="*.toml", path="./")
find(pattern="*.json", path="./")

# Search for entry points
ast(pattern="def main|if __name__", path="./src")
```

## Best Practices

1. **Use absolute paths** - All tools expect absolute paths for reliability
2. **Set appropriate limits** - Use `limit` and `max_results` to avoid overwhelming output
3. **Prefer search over read** - Use search/ast to find relevant code instead of reading entire files
4. **Use tree for orientation** - Start with tree to understand project structure
5. **Combine tools** - Use find + read or search + edit for efficient workflows
