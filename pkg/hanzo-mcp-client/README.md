# Hanzo MCP Client

MCP (Model Context Protocol) client library for connecting to MCP servers.

This library provides the client-side implementation for connecting to MCP servers and using their tools.

## Installation

```bash
pip install hanzo-mcp-client
```

## Usage

```python
from hanzo_mcp_client import MCPClient, add_mcp_tools_to_agent

# Create a client
client = MCPClient()

# Connect to an MCP server
await client.connect("stdio", command="hanzo-mcp")

# List available tools
tools = await client.list_tools()
```