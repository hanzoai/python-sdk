# VS Code Integration

Set up hanzo-mcp with VS Code, Cursor, and other MCP-compatible editors.

## VS Code with Continue

[Continue](https://continue.dev) is an open-source AI code assistant that supports MCP.

### Installation

1. Install Continue extension from VS Code marketplace
2. Configure MCP in `~/.continue/config.json`:

```json
{
  "models": [...],
  "mcpServers": [
    {
      "name": "hanzo",
      "command": "uvx",
      "args": ["hanzo-mcp"]
    }
  ]
}
```

3. Restart VS Code

## Cursor

Cursor has built-in MCP support.

### Configuration

Add to Cursor settings (`~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "hanzo": {
      "command": "uvx",
      "args": ["hanzo-mcp", "--allow-path", "~"]
    }
  }
}
```

## Windsurf (Codeium)

### Configuration

Add to `~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "hanzo": {
      "command": "uvx",
      "args": ["hanzo-mcp"]
    }
  }
}
```

## Generic MCP Client

For any MCP-compatible client:

### stdio Transport

```json
{
  "command": "uvx",
  "args": ["hanzo-mcp", "--transport", "stdio"]
}
```

### SSE Transport

Start the server:

```bash
hanzo-mcp --transport sse --port 8888
```

Connect to: `http://localhost:8888/sse`

## Project-Specific Configuration

Create `.hanzo/config.json` in your project root:

```json
{
  "name": "my-project",
  "rules": [
    "Use TypeScript",
    "Follow existing patterns"
  ],
  "enabled_tools": {
    "shell": true,
    "browser": false
  }
}
```

The MCP server will automatically detect and apply project settings.

## Recommended Extensions

### VS Code

- **Continue** - AI assistant with MCP support
- **Claude Dev** - Claude integration
- **GitLens** - Git integration (works well with hanzo tools)

### Cursor

Built-in AI features work with hanzo-mcp out of the box.

## Troubleshooting

### Server Not Starting

```bash
# Check if hanzo-mcp is installed
uvx hanzo-mcp --version

# Test manually
uvx hanzo-mcp --transport sse --port 8888
# Then open http://localhost:8888 in browser
```

### Permission Errors

Ensure paths are allowed:

```json
{
  "args": ["hanzo-mcp", "--allow-path", "/path/to/project"]
}
```

### Tool Not Available

Some tools require additional dependencies:

```bash
# Full installation with all tools
pip install hanzo-mcp[tools-all]

# Or specific tools
pip install hanzo-mcp[browser]  # Playwright
pip install hanzo-mcp[llm]      # LiteLLM
```

### Logs and Debugging

For SSE transport, logs appear in terminal. For stdio:

```bash
# Redirect stderr to file
hanzo-mcp 2>/tmp/hanzo-mcp.log
```

## Performance Tips

1. **Use uvx** - Faster startup than pip-installed version
2. **Limit paths** - Only allow necessary directories
3. **Disable unused tools** - Reduces memory usage
4. **Use project config** - Faster tool discovery

## Browser Extension Integration

The Hanzo Browser Extension enables AI control of browser tabs through the browser tool.

### Installation

1. Install the browser extension from the Chrome/Firefox store (or build from source)
2. Start the CDP bridge server:

```bash
python -m hanzo_tools.browser.cdp_bridge_server
# Runs on ws://localhost:9223 by default
```

3. The extension automatically connects to the bridge

### How It Works

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│   hanzo-mcp     │────▶│  CDP Bridge      │────▶│  Browser Extension  │
│  browser tool   │◀────│  Server (9223)   │◀────│  (CDP Provider)     │
└─────────────────┘     └──────────────────┘     └─────────────────────┘
                              ▲
                              │ WebSocket
                              │
                        ┌─────┴─────┐
                        │  Chrome   │
                        │  Tabs     │
                        └───────────┘
```

### Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `HANZO_CDP_BRIDGE_HOST` | `localhost` | Bridge server host |
| `HANZO_CDP_BRIDGE_PORT` | `9223` | Bridge server port |

### Usage with MCP

Once connected, the browser tool can control tabs through the extension:

```python
# In your AI/MCP context
browser(action="navigate", url="https://example.com")
browser(action="click", selector="#login-button")
browser(action="fill", selector="#email", text="user@example.com")
browser(action="screenshot")
```

### Programmatic Usage

```python
from hanzo_tools.browser import CDPBridgeClient

# Connect to the bridge
client = CDPBridgeClient(port=9223)
await client.connect()

# Control browser
await client.navigate("https://example.com")
await client.click("#submit")
screenshot = await client.screenshot(full_page=True)
```

### Debugging

If the extension isn't connecting:

1. Check extension is installed and enabled
2. Verify bridge server is running: `curl http://localhost:9223/health`
3. Check browser console for errors (F12 → Console)
4. Ensure `debugger` permission is granted in extension settings

## See Also

- [Quickstart](quickstart.md) - Getting started
- [Configuration](configuration.md) - All configuration options
- [Tools Reference](../tools/index.md) - Available tools
