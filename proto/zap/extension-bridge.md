# ZAP Extension Bridge Protocol

The ZAP Extension Bridge enables AI agents to control browsers and IDEs through native extensions.

## Architecture

```
┌─────────────────┐     WebSocket      ┌──────────────────┐
│  hanzo-mcp      │ ◄──────────────────► │ Browser Extension │
│  (AI Agent)     │     Port 9224       │ (Chrome/Firefox)  │
└─────────────────┘                      └──────────────────┘
        │
        │           WebSocket
        │ ◄──────────────────────────►  ┌──────────────────┐
        │           Port 9225           │ VS Code Extension │
        │                               └──────────────────┘
        │
        │           WebSocket
        └──────────────────────────────► ┌──────────────────┐
                    Port 9228           │ Neovim Plugin     │
                                        └──────────────────┘
```

## Browser Extension

### Installation
- Chrome: [Chrome Web Store - Hanzo AI](https://chrome.google.com/webstore/detail/hanzo-ai)
- Firefox: [Firefox Add-ons - Hanzo AI](https://addons.mozilla.org/firefox/addon/hanzo-ai)

### Exposed APIs

#### Console
```typescript
// Subscribe to console messages
{ action: "console.subscribe" }

// Evaluate in console
{ action: "console.eval", code: "1 + 1" }

// Get console history
{ action: "console.history", level?: "error" | "warn" | "log" }
```

#### DOM
```typescript
// Get accessibility snapshot
{ action: "dom.snapshot" }

// Query selector
{ action: "dom.query", selector: ".button" }

// Click element
{ action: "dom.click", selector: "#submit" }
```

#### Network
```typescript
// Subscribe to network events
{ action: "network.subscribe" }

// Intercept requests
{ action: "network.intercept", pattern: "*/api/*" }

// Mock response
{ action: "network.mock", url: "/api/user", response: { name: "Test" } }
```

#### DevTools
```typescript
// Set breakpoint
{ action: "debugger.breakpoint", url: "app.js", line: 42 }

// Step through code
{ action: "debugger.step" }

// Get call stack
{ action: "debugger.stack" }
```

## VS Code Extension

### Installation
```bash
code --install-extension hanzo.hanzo-ai
```

### Exposed APIs

#### Files
```typescript
// Open file
{ action: "file.open", path: "/src/main.ts", line?: 42 }

// Save file
{ action: "file.save", path?: "/src/main.ts" }

// Close file
{ action: "file.close", path?: "/src/main.ts" }

// List open files
{ action: "file.list" }
```

#### Editor
```typescript
// Get selection
{ action: "editor.selection" }

// Set selection
{ action: "editor.select", line: 10, column: 5, endLine: 10, endColumn: 15 }

// Insert text
{ action: "editor.insert", text: "// TODO", line: 10 }

// Replace text
{ action: "editor.replace", text: "newCode", line: 10, column: 0, endLine: 12, endColumn: 0 }
```

#### Navigation
```typescript
// Go to definition
{ action: "nav.definition", line: 10, column: 5 }

// Find references
{ action: "nav.references", line: 10, column: 5 }

// Go to symbol
{ action: "nav.symbol", query: "MyClass" }
```

#### Refactoring
```typescript
// Rename symbol
{ action: "refactor.rename", line: 10, column: 5, newName: "betterName" }

// Format document
{ action: "refactor.format" }

// Organize imports
{ action: "refactor.imports" }

// Extract function
{ action: "refactor.extract", type: "function", line: 10, endLine: 20 }
```

#### Diagnostics
```typescript
// Get diagnostics
{ action: "diagnostics.get", severity?: "error" | "warning" }

// Apply quick fix
{ action: "diagnostics.fix", line: 10, column: 5, index?: 0 }
```

#### Terminal
```typescript
// Create terminal
{ action: "terminal.create", name?: "Build" }

// Send to terminal
{ action: "terminal.send", command: "npm test", name?: "Build" }

// Get terminal output
{ action: "terminal.output", name?: "Build" }
```

#### Commands
```typescript
// Execute VS Code command
{ action: "command.execute", command: "workbench.action.togglePanel" }

// List available commands
{ action: "command.list", filter?: "workbench" }
```

## Message Format

All messages use JSON-RPC 2.0:

### Request
```json
{
  "jsonrpc": "2.0",
  "id": "unique-id",
  "method": "action",
  "params": { ... }
}
```

### Response
```json
{
  "jsonrpc": "2.0",
  "id": "unique-id",
  "result": { ... }
}
```

### Error
```json
{
  "jsonrpc": "2.0",
  "id": "unique-id",
  "error": {
    "code": -32600,
    "message": "Invalid Request"
  }
}
```

### Event (no id)
```json
{
  "jsonrpc": "2.0",
  "method": "event",
  "params": {
    "type": "console.message",
    "data": { "level": "log", "text": "Hello" }
  }
}
```

## Security

- Extensions only accept connections from localhost
- Optional authentication via shared secret
- Sandboxed execution (no arbitrary code without user consent)
- Rate limiting on sensitive operations
- User must enable "AI Control" in extension settings

## Development

### Building Browser Extension
```bash
cd extensions/browser
npm install
npm run build
# Load unpacked extension from dist/
```

### Building VS Code Extension
```bash
cd extensions/vscode
npm install
npm run build
code --install-extension hanzo-ai-*.vsix
```

### Testing
```bash
# Run integration tests
npm test

# Manual testing
curl -X POST http://localhost:9224 \
  -H "Content-Type: application/json" \
  -d '{"action": "status"}'
```
