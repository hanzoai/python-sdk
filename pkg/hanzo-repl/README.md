# Hanzo REPL

Interactive REPL for Hanzo AI - Like Claude Code in your terminal.

## Features

- 🎯 **Direct MCP Access**: All 70+ MCP tools available as Python functions
- 💬 **Integrated Chat**: Chat with AI that can use MCP tools
- 🔧 **IPython Magic**: Advanced features with tab completion and magic commands
- 🎨 **Beautiful TUI**: Textual-based terminal UI with syntax highlighting
- 🔄 **Live Editing**: Edit code and see results immediately
- 🎤 **Voice Mode**: Speak to AI and hear responses (optional)

## Quick Start

```bash
# Install
pip install hanzo-repl

# Start interactive REPL (recommended)
hanzo-repl

# Start IPython REPL (advanced)
hanzo-repl-ipython

# Start TUI mode (beautiful interface)
hanzo-repl-tui
```

## Usage

### Basic CLI Usage

The REPL integrates seamlessly with the Hanzo CLI:

```bash
# Interactive chat mode
hanzo chat

# Quick questions
hanzo ask "What files are in the current directory?"

# With specific model
hanzo ask "Explain this code" --model claude-3-opus
```

### REPL Commands

```python
# Direct tool access
>>> read_file(file_path="README.md")
>>> write_file(file_path="test.py", content="print('Hello')")
>>> search(query="def main", path=".")

# Chat with AI
>>> chat("Create a Python script that fetches weather data")

# AI will use tools automatically
>>> chat("Find all TODO comments in the codebase and create a summary")
```

### IPython Magic Commands

```python
# Quick chat
%chat What is 2+2?

# Multi-line chat
%%ai
Help me refactor this function to be more efficient.
It should handle edge cases better.

# List tools
%tools

# Change model
%model claude-3.5-sonnet

# Execute tool
%tool read_file {"file_path": "config.json"}
```

### TUI Mode Features

- **Split panes**: Code editor, chat, and output
- **Syntax highlighting**: Full language support
- **Tool palette**: Visual tool selection
- **History**: Navigate previous commands
- **Themes**: Dark/light mode support

## Environment Setup

Set at least one LLM provider:

```bash
export ANTHROPIC_API_KEY=your-key  # For Claude
export OPENAI_API_KEY=your-key     # For GPT
export HANZO_API_KEY=your-key      # For Hanzo AI
```

## Advanced Features

### Voice Mode

Install voice dependencies:

```bash
pip install hanzo-repl[voice]
```

Enable in REPL:

```python
>>> enable_voice()
>>> chat("Hello")  # Speak your message
```

### Custom Tools

Create custom tools on the fly:

```python
@register_tool
def my_tool(param: str) -> str:
    """My custom tool."""
    return f"Processed: {param}"

# Now available to AI
>>> chat("Use my_tool to process 'hello'")
```

### Scripting

Use the REPL in scripts:

```python
from hanzo_repl import create_repl

async def main():
    repl = create_repl()
    result = await repl.chat("Analyze the project structure")
    print(result)
```

## Integration with Hanzo Ecosystem

### With Hanzo MCP

All MCP tools are automatically available:

- File operations
- Code search and analysis
- Process management
- Git operations
- And 60+ more tools

### With Hanzo Agents

Create and manage agents:

```python
>>> agent = create_agent("researcher")
>>> agent.run("Research best practices for API design")
```

### With Hanzo Network

Dispatch to agent networks:

```python
>>> network.dispatch("Solve this problem", agents=5)
```

## Tips

1. **Tab Completion**: Use Tab to explore available tools and parameters
2. **Help System**: Use `?` after any function for documentation
3. **History**: Use up/down arrows to navigate command history
4. **Shortcuts**: Ctrl+R for reverse search, Ctrl+L to clear screen
5. **Output**: Results are automatically pretty-printed with Rich

## Troubleshooting

### No LLM Response

Ensure you have set API keys:

```bash
echo $ANTHROPIC_API_KEY  # Should show your key
```

### Tool Errors

Check tool permissions:

```python
>>> mcp.get_allowed_paths()
>>> mcp.add_allowed_path("/path/to/allow")
```

### Performance

For better performance:

```python
>>> set_model("gpt-3.5-turbo")  # Faster model
>>> set_streaming(True)  # Stream responses
```

## Contributing

The REPL is part of the Hanzo Python SDK. See the main repository for contribution guidelines.

## License

BSD-3-Clause - see LICENSE file for details.