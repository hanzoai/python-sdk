# hanzo-tools-lsp

Language Server Protocol tool for code intelligence. Provides go-to-definition, find references, rename, hover, and more.

## Installation

```bash
pip install hanzo-tools-lsp
```

Or as part of the full toolkit:

```bash
pip install hanzo-mcp[tools-all]
```

## Overview

`hanzo-tools-lsp` provides on-demand LSP configuration and automatic installation:

- **definition** - Go to definition of symbol at position
- **references** - Find all references to symbol
- **rename** - Rename symbol across codebase
- **hover** - Get hover information at position
- **completion** - Get code completions at position
- **diagnostics** - Get errors and warnings for file
- **status** - Check LSP server status

## Supported Languages

| Language | LSP Server | Install Command |
|----------|------------|-----------------|
| Go | gopls | `go install golang.org/x/tools/gopls@latest` |
| Python | pyright | `npm install -g pyright` |
| TypeScript/JS | typescript-language-server | `npm install -g typescript typescript-language-server` |
| Rust | rust-analyzer | `rustup component add rust-analyzer` |
| Java | jdtls | `brew install jdtls` |
| C/C++ | clangd | `brew install llvm` |
| Ruby | solargraph | `gem install solargraph` |
| Lua | lua-language-server | `brew install lua-language-server` |

## Quick Start

```python
# Go to definition
lsp(action="definition", file="/path/to/file.go", line=10, character=15)

# Find all references
lsp(action="references", file="/path/to/file.py", line=25, character=8)

# Rename symbol
lsp(action="rename", file="/path/to/file.ts", line=5, character=10, new_name="newName")

# Get hover info
lsp(action="hover", file="/path/to/file.rs", line=42, character=20)

# Get completions
lsp(action="completion", file="/path/to/file.py", line=30, character=5)

# Check status
lsp(action="status", file="/path/to/file.go")
```

## Actions Reference

### definition

Find where a symbol is defined.

```python
lsp(action="definition", file="main.go", line=42, character=15)
```

**Response:**
```json
{
  "action": "definition",
  "file": "main.go",
  "definition": {
    "file": "/project/pkg/utils.go",
    "start": {"line": 25, "character": 5},
    "end": {"line": 25, "character": 15}
  }
}
```

### references

Find all references to a symbol.

```python
lsp(action="references", file="utils.py", line=10, character=4)
```

**Response:**
```json
{
  "action": "references",
  "file": "utils.py",
  "references": [
    {"file": "main.py", "start": {"line": 15, "character": 8}},
    {"file": "tests/test_utils.py", "start": {"line": 22, "character": 12}}
  ],
  "count": 2
}
```

### rename

Rename a symbol across the codebase.

```python
lsp(action="rename", file="models.ts", line=5, character=10, new_name="newClassName")
```

**Response:**
```json
{
  "action": "rename",
  "file": "models.ts",
  "new_name": "newClassName",
  "changes": {
    "/project/models.ts": [
      {"range": {...}, "newText": "newClassName"}
    ],
    "/project/index.ts": [
      {"range": {...}, "newText": "newClassName"}
    ]
  },
  "files_affected": 2
}
```

### hover

Get documentation and type information at a position.

```python
lsp(action="hover", file="main.rs", line=30, character=8)
```

**Response:**
```json
{
  "action": "hover",
  "file": "main.rs",
  "position": {"line": 30, "character": 8},
  "contents": "fn process(data: &[u8]) -> Result<(), Error>\n\nProcesses the input data..."
}
```

### completion

Get code completions at a position.

```python
lsp(action="completion", file="app.py", line=25, character=10)
```

**Response:**
```json
{
  "action": "completion",
  "file": "app.py",
  "position": {"line": 25, "character": 10},
  "completions": [
    {"label": "append", "kind": 2, "detail": "(element) -> None"},
    {"label": "extend", "kind": 2, "detail": "(iterable) -> None"}
  ],
  "count": 2
}
```

### status

Check if LSP server is installed and get capabilities.

```python
lsp(action="status", file="main.go")
```

**Response:**
```json
{
  "language": "go",
  "lsp_server": "gopls",
  "installed": true,
  "capabilities": ["definition", "references", "rename", "diagnostics", "hover", "completion"]
}
```

## Architecture

### Automatic Server Management

The LSP tool automatically:
1. Detects language from file extension
2. Finds project root based on language markers (go.mod, package.json, etc.)
3. Checks if LSP server is installed
4. Installs LSP server if needed
5. Starts and initializes the server
6. Maintains singleton server per language:project_root

### Server Lifecycle

```
Request → Detect Language → Find Project Root
    ↓
Check Cache (language:root_uri)
    ↓
If not running: Install → Start → Initialize
    ↓
Execute LSP Request → Return Result
```

### Global Server Registry

LSP servers are managed globally to avoid redundant instances:

```python
# Servers are keyed by language:root_uri
# e.g., "go:/home/user/project"
# Cleanup happens automatically on process exit
```

## Examples

### Code Navigation

```python
# Find where a function is defined
lsp(action="definition", file="handlers/user.go", line=45, character=12)

# Find all places that call this function
lsp(action="references", file="handlers/user.go", line=45, character=12)
```

### Safe Refactoring

```python
# First, check all references
refs = lsp(action="references", file="models.py", line=10, character=6)

# Then rename
lsp(action="rename", file="models.py", line=10, character=6, new_name="UserProfile")
```

### IDE-like Experience

```python
# Get documentation on hover
lsp(action="hover", file="main.rs", line=25, character=8)

# Get completions while typing
lsp(action="completion", file="app.ts", line=30, character=15)
```

## Configuration

### Project Root Detection

The LSP tool finds project roots using language-specific markers:

| Language | Markers |
|----------|---------|
| Go | go.mod, go.sum |
| Python | pyproject.toml, setup.py, requirements.txt |
| TypeScript | tsconfig.json, package.json |
| Rust | Cargo.toml |
| Java | pom.xml, build.gradle |
| C/C++ | compile_commands.json, CMakeLists.txt |
| Ruby | Gemfile |

### Custom LSP Servers

For custom configurations, ensure the LSP server is in your PATH before using the tool.

## Best Practices

1. **Use status first** - Check if LSP is available before heavy operations
2. **Provide accurate positions** - Line and character must match exact symbol position
3. **Let servers persist** - Servers are cached; avoid restarting unnecessarily
4. **Combine with other tools** - Use with search/ast for comprehensive code analysis
