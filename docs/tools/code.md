# Code Tool

Symbol and structure operations for source code (HIP-0300 operator).

## Installation

```bash
pip install hanzo-tools-code
```

## Overview

The `code` tool handles all code analysis and transformation operations:

| Action | Signature | Effect |
|--------|-----------|--------|
| `parse` | `(Path \| Text, lang?) → AST` | PURE |
| `serialize` | `AST → Text` | PURE |
| `symbols` | `(Path \| AST, kind?) → [Symbol]` | PURE |
| `definition` | `(Path, Position) → [Location]` | DETERMINISTIC |
| `references` | `(Path, Position) → [Location]` | DETERMINISTIC |
| `transform` | `(Path \| Text, kind, params) → Patch` | PURE |
| `summarize` | `(Diff \| Log \| Report) → Summary` | PURE |

## Actions

### parse

Parse source code into an Abstract Syntax Tree using tree-sitter.

```python
code(action="parse", path="/src/main.py")
# Returns: {tree: {...}, lang: "python", node_count: 142}

code(action="parse", text="def foo(): pass", lang="python")
# Returns: {tree: {...}, lang: "python", node_count: 5}
```

**Parameters:**
- `path` (str, optional): Path to source file
- `text` (str, optional): Source code text (provide one of path or text)
- `lang` (str, optional): Language hint (auto-detected from extension)

### serialize

Convert AST back to source code.

```python
code(action="serialize", tree=ast_tree, lang="python")
# Returns: {text: "def foo(): pass", size: 16}
```

### symbols

Extract symbols (functions, classes, variables) from code.

```python
code(action="symbols", path="/src/main.py")
# Returns: {symbols: [{name: "foo", kind: "function", line: 1}, ...]}

code(action="symbols", path="/src/main.py", kind="class")
# Returns: {symbols: [{name: "MyClass", kind: "class", line: 10}]}
```

**Parameters:**
- `path` (str, optional): Path to source file
- `text` (str, optional): Source code text
- `kind` (str, optional): Filter by symbol kind (function, class, variable, etc.)

### definition

Find the definition of a symbol at a position (requires LSP).

```python
code(action="definition", path="/src/main.py", line=42, col=10)
# Returns: {locations: [{uri: "file:///src/utils.py", line: 15, col: 0}]}
```

### references

Find all references to a symbol (requires LSP).

```python
code(action="references", path="/src/main.py", line=42, col=10)
# Returns: {locations: [{uri: "...", line: ..., col: ...}, ...], count: 7}
```

### transform

Apply a transformation and produce a Patch (PURE - no side effects).

```python
# Rename a symbol
code(action="transform", path="/src/main.py", kind="rename",
     old_name="authenticate", new_name="verify_user")
# Returns: {patch: [...], base_hash: "sha256:abc...", new_hash: "sha256:def...", changes_count: 5}

# Extract a function
code(action="transform", path="/src/main.py", kind="extract",
     start_line=10, end_line=20, new_name="helper_function")
# Returns: {patch: [...], base_hash: "...", new_hash: "..."}
```

**Transform Kinds:**
- `rename` - Rename a symbol (old_name, new_name)
- `extract` - Extract code to function (start_line, end_line, new_name)
- `inline` - Inline a function/variable
- `move` - Move symbol to another file

### summarize

Compress diff/log/report into actionable summary.

```python
code(action="summarize", diff=patch_content)
# Returns: {summary: "Renamed authenticate to verify_user in 5 locations",
#           risks: ["Breaking change for external callers"],
#           next_actions: ["Update API documentation", "Run integration tests"]}

code(action="summarize", log=[{"sha": "abc", "message": "..."}])
# Returns: {summary: "3 commits: added auth, fixed bug, updated tests", ...}
```

## Transform vs Apply

The `code.transform` action is PURE - it produces a Patch value without modifying files. To apply the patch:

```python
# 1. Generate transform (PURE)
result = code(action="transform", path="/src/main.py", kind="rename",
              old_name="foo", new_name="bar")

# 2. Review the patch
print(result["patch"])
print(result["summary"])

# 3. Apply with precondition (EFFECT)
fs(action="patch", path="/src/main.py", patch=result["patch"],
   base_hash=result["base_hash"])  # Fails if file changed
```

## Language Support

Tree-sitter languages supported:
- Python, JavaScript, TypeScript, Rust, Go, C, C++, Java
- JSON, YAML, TOML, Markdown, HTML, CSS

Languages auto-detected from file extensions.

## See Also

- [HIP-0300](../hip/HIP-0300.md) - Unified Tools Architecture
- [Filesystem Tool](fs.md) - For applying patches with `fs.patch`
- [LSP Tool](lsp.md) - For additional semantic operations
- [Refactor Tool](refactor.md) - High-level refactoring operations
