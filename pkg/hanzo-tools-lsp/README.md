# hanzo-tools-lsp

Language Server Protocol tools for Hanzo MCP.

## Installation

```bash
pip install hanzo-tools-lsp
```

## Tools

### lsp - Language Server Protocol
Code intelligence via LSP servers.

**Go to definition:**
```python
lsp(action="definition", file="/path/to/file.py", line=10, character=15)
```

**Find references:**
```python
lsp(action="references", file="/path/to/file.py", line=10, character=15)
```

**Hover information:**
```python
lsp(action="hover", file="/path/to/file.py", line=10, character=15)
```

**Code completion:**
```python
lsp(action="completion", file="/path/to/file.py", line=10, character=15)
```

**Diagnostics:**
```python
lsp(action="diagnostics", file="/path/to/file.py")
```

**Rename symbol:**
```python
lsp(action="rename", file="/path/to/file.py", line=10, character=15, new_name="newName")
```

**Check status:**
```python
lsp(action="status")  # Check LSP server status
```

## Supported Languages

- Go (gopls)
- Python (pyright)
- TypeScript/JavaScript (typescript-language-server)
- Rust (rust-analyzer)
- Java (jdtls)
- C/C++ (clangd)
- Ruby (solargraph)
- Lua (lua-language-server)

Language servers are automatically installed as needed.

## License

MIT
