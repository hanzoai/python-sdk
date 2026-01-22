# ZAP Protocol: MCP Superset for Agentic Operations

ZAP (Zero-latency Agent Protocol) extends MCP with capabilities for:
- **Interactive Sessions**: REPL/notebook execution across languages
- **Streaming**: Real-time output for long-running operations
- **IDE Integration**: Full editor control (VS Code, JetBrains, Neovim)
- **Browser DevTools**: Console, network, debugger control
- **Extension Bridge**: Browser/IDE extension communication

## Protocol Versions

| Version | MCP Compat | Features |
|---------|------------|----------|
| 1.0.0 | 2025-06-18 | Full MCP + REPL + Browser + IDE |

## Wire Formats

- **Primary**: Cap'n Proto (binary, zero-copy)
- **Fallback**: JSON-RPC 2.0 (MCP compatible)

## Message Types

### Tool Execution (MCP Compatible)
```json
{
  "id": "1",
  "method": "tools/call",
  "params": {
    "name": "read",
    "arguments": {"file_path": "/path/to/file"}
  }
}
```

### REPL Session
```json
{
  "id": "1",
  "method": "repl/eval",
  "params": {
    "session_id": "py_abc123",
    "language": "python",
    "code": "x = 1 + 1\nprint(x)",
    "stream_output": true
  }
}
```

### Browser Console
```json
{
  "id": "1",
  "method": "browser/console",
  "params": {
    "action": "evaluate",
    "code": "document.title"
  }
}
```

### IDE Control
```json
{
  "id": "1",
  "method": "ide/command",
  "params": {
    "action": "rename",
    "line": 10,
    "column": 5,
    "new_name": "betterName"
  }
}
```

### Streaming
```json
{
  "id": "1",
  "method": "stream/start",
  "params": {
    "type": "repl_output",
    "session_id": "py_abc123"
  }
}
```

## Capabilities

### REPL Languages
- Python (ipykernel)
- Node.js/TypeScript (tslab)
- Bash (bash_kernel)
- Ruby, Go, Rust, Julia (with kernels)

### Browser Actions
- JavaScript evaluation
- Console message capture
- Network interception
- DOM manipulation
- Debugger control

### IDE Actions
- File operations (open, save, close)
- Editor operations (select, insert, replace)
- Navigation (go to definition, find references)
- Refactoring (rename, format, extract)
- Terminal control
- Diagnostics and quick fixes

## Extension Bridge

ZAP communicates with browser/IDE extensions via WebSocket:

| Extension | Port | Protocol |
|-----------|------|----------|
| Browser | 9224 | HTTP/WS |
| VS Code | 9225 | WebSocket |
| Cursor | 9226 | WebSocket |
| Windsurf | 9227 | WebSocket |
| Neovim | 9228 | WebSocket |

## Proto Files

- `zap.proto` - Main protocol definition
- Generated code available for:
  - Python: `pip install hanzo-zap`
  - TypeScript: `npm install @hanzo/zap`
  - Go: `go get github.com/hanzoai/zap`
  - Rust: `cargo add hanzo-zap`

## Usage with hanzo-mcp

ZAP is fully integrated into hanzo-mcp tools:

```python
# REPL evaluation
repl(action="eval", code="print('hello')", language="python")

# Browser console
browser(action="console")
browser(action="evaluate", code="document.title")

# IDE control
ide(action="open", path="/src/main.py")
ide(action="rename", new_name="newFunc", line=10, column=5)
```

## Compared to MCP

| Feature | MCP | ZAP |
|---------|-----|-----|
| Tool calls | ✓ | ✓ |
| Resources | ✓ | ✓ |
| Prompts | ✓ | ✓ |
| Streaming | ✗ | ✓ |
| REPL sessions | ✗ | ✓ |
| IDE integration | ✗ | ✓ |
| Browser DevTools | ✗ | ✓ |
| Binary protocol | ✗ | ✓ (Cap'n Proto) |
| Extension bridge | ✗ | ✓ |

## License

MIT - Hanzo Industries Inc
