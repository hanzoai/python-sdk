# hanzo-repl

Interactive REPL (Read-Eval-Print Loop) for Hanzo AI.

## Installation

```bash
pip install hanzo-repl
```

## Overview

hanzo-repl provides an interactive command-line interface for AI agents with:

- **Multiple Backends** - IPython, Textual, and standard REPL
- **Voice Mode** - Speech-to-text input
- **Command Palette** - Quick access to commands
- **Command Suggestions** - Context-aware suggestions
- **LLM Integration** - Direct AI assistant access

## Quick Start

```bash
# Start the REPL
hanzo-repl

# Or with Python
python -m hanzo_repl
```

## Features

### Standard REPL

```python
from hanzo_repl import REPL

# Create and run REPL
repl = REPL()
repl.run()
```

### IPython Backend

Enhanced REPL with IPython features:

```python
from hanzo_repl import IPythonREPL

repl = IPythonREPL()
repl.run()
```

Features:
- Tab completion
- Syntax highlighting
- Magic commands
- History persistence

### Textual Backend

Modern TUI (Text User Interface) REPL:

```python
from hanzo_repl import TextualREPL

repl = TextualREPL()
repl.run()
```

Features:
- Rich UI components
- Multiple panes
- Mouse support
- Keyboard shortcuts

## Voice Mode

Enable voice input:

```python
from hanzo_repl import REPL, VoiceMode

repl = REPL()
voice = VoiceMode()

# Enable voice
repl.enable_voice(voice)

# Start listening
repl.run()
```

### Voice Commands

| Command | Action |
|---------|--------|
| "Hey Hanzo" | Activate voice input |
| "Stop" | Cancel current input |
| "Execute" | Run current command |
| "Clear" | Clear screen |

## Command Palette

Quick access to common commands:

```python
from hanzo_repl import CommandPalette

palette = CommandPalette()

# Add custom commands
palette.add_command("build", "npm run build", category="dev")
palette.add_command("test", "pytest", category="dev")

# Open palette (Ctrl+Shift+P)
palette.show()
```

### Default Commands

| Category | Commands |
|----------|----------|
| File | Open, Save, Close |
| Edit | Cut, Copy, Paste, Undo |
| View | Zoom In, Zoom Out, Toggle Panel |
| Git | Status, Commit, Push, Pull |
| Run | Execute, Debug, Profile |

## Command Suggestions

Context-aware suggestions:

```python
from hanzo_repl import CommandSuggestions

suggestions = CommandSuggestions()

# Get suggestions based on context
ctx = {"language": "python", "file": "main.py"}
sugg = suggestions.get(ctx)

# Returns relevant commands like:
# - python main.py
# - pytest
# - black main.py
```

## LLM Integration

Direct AI assistant access:

```python
from hanzo_repl import LLMClient

client = LLMClient()

# Ask the AI
response = await client.ask("How do I sort a list in Python?")
print(response)

# With context
response = await client.ask(
    "Explain this code",
    context=code_snippet,
)
```

### Configuration

```python
LLMClient(
    model="gpt-4",
    temperature=0.7,
    max_tokens=1000,
)
```

## CLI Options

```bash
# Choose backend
hanzo-repl --backend ipython
hanzo-repl --backend textual
hanzo-repl --backend standard

# Enable voice
hanzo-repl --voice

# Set LLM model
hanzo-repl --model claude-3

# Debug mode
hanzo-repl --debug
```

## Keyboard Shortcuts

### Navigation

| Shortcut | Action |
|----------|--------|
| `Ctrl+C` | Cancel/interrupt |
| `Ctrl+D` | Exit REPL |
| `Ctrl+L` | Clear screen |
| `Ctrl+R` | Search history |
| `Tab` | Complete command |

### Editing

| Shortcut | Action |
|----------|--------|
| `Ctrl+A` | Beginning of line |
| `Ctrl+E` | End of line |
| `Ctrl+K` | Kill to end of line |
| `Ctrl+U` | Kill to start of line |
| `Ctrl+W` | Delete word backward |

### Command Palette

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+P` | Open command palette |
| `Ctrl+P` | Quick open file |
| `Ctrl+Shift+F` | Search in files |

## Configuration

### Config File

Create `~/.hanzo/repl.yaml`:

```yaml
backend: ipython
voice:
  enabled: true
  wake_word: "hey hanzo"
llm:
  model: claude-3
  temperature: 0.7
theme: dark
history:
  size: 10000
  file: ~/.hanzo/history
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `HANZO_REPL_BACKEND` | Default backend |
| `HANZO_REPL_VOICE` | Enable voice (true/false) |
| `HANZO_REPL_MODEL` | LLM model |
| `HANZO_REPL_THEME` | Color theme |

## Custom Commands

Register custom commands:

```python
from hanzo_repl import REPL, command

@command("hello")
def hello_command(args):
    """Say hello"""
    name = args.get("name", "World")
    print(f"Hello, {name}!")

repl = REPL()
repl.register_command(hello_command)
repl.run()
```

## Plugins

Extend the REPL with plugins:

```python
from hanzo_repl import Plugin, REPL

class MyPlugin(Plugin):
    name = "my-plugin"

    def on_load(self, repl):
        print("Plugin loaded!")

    def on_command(self, cmd):
        # Process commands
        pass

repl = REPL()
repl.load_plugin(MyPlugin())
```

## API Reference

### REPL Class

| Method | Description |
|--------|-------------|
| `run()` | Start the REPL |
| `eval(code)` | Evaluate code |
| `register_command(cmd)` | Add custom command |
| `enable_voice(mode)` | Enable voice input |
| `load_plugin(plugin)` | Load a plugin |

### LLMClient Class

| Method | Description |
|--------|-------------|
| `ask(prompt, context)` | Ask the AI |
| `stream(prompt)` | Stream response |
| `set_model(model)` | Change model |

### VoiceMode Class

| Method | Description |
|--------|-------------|
| `start()` | Start listening |
| `stop()` | Stop listening |
| `set_wake_word(word)` | Set activation word |
