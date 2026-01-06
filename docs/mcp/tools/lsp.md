# LSP Tool

Language Server Protocol for code intelligence.

→ **Full documentation: [../../tools/lsp.md](../../tools/lsp.md)**

## Quick Reference

```python
# Go to definition
lsp(action="definition", file="main.py", line=10, character=15)

# Find references
lsp(action="references", file="main.py", line=10, character=15)

# Hover information
lsp(action="hover", file="main.py", line=10, character=15)

# Code completion
lsp(action="completion", file="main.py", line=10, character=15)

# Rename symbol
lsp(action="rename", file="main.py", line=10, character=15, new_name="newName")

# Get diagnostics
lsp(action="diagnostics", file="main.py")
```

Supported: Python, TypeScript, JavaScript, Go, Rust, Java, C/C++, Ruby, Lua
