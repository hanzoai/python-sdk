# hanzo-tools-config

Configuration and development mode management for Hanzo AI.

## Installation

```bash
pip install hanzo-tools-config
```

Or as part of the full toolkit:

```bash
pip install hanzo-mcp[tools-all]
```

## Overview

`hanzo-tools-config` provides:

- **config** - Git-style configuration management
- **mode** - Development mode/persona switching

## Config Tool

Manage settings with git-style configuration.

### Quick Start

```python
# Get a value
config(action="get", key="user.name")

# Set a value
config(action="set", key="user.name", value="Alice")

# List all settings
config(action="list")

# Delete a setting
config(action="delete", key="user.name")
```

### Actions

#### get

Get a configuration value.

```python
config(action="get", key="editor.theme")
config(action="get", key="tools.timeout")
```

#### set

Set a configuration value.

```python
config(action="set", key="editor.theme", value="dark")
config(action="set", key="tools.timeout", value="30")
```

#### list

List all configuration values.

```python
config(action="list")
```

**Response:**
```json
{
  "settings": {
    "user.name": "Alice",
    "editor.theme": "dark",
    "tools.timeout": "30"
  }
}
```

#### delete

Remove a configuration value.

```python
config(action="delete", key="editor.theme")
```

### Configuration Scopes

| Scope | Location | Priority |
|-------|----------|----------|
| Session | Memory | Highest |
| Project | `.hanzo/config` | Medium |
| Global | `~/.hanzo/config` | Lowest |

## Mode Tool

Switch between development modes/personas.

### Quick Start

```python
# List available modes
mode(action="list")

# Activate a mode
mode(action="activate", name="guido")

# Show current mode
mode(action="current")

# Show mode details
mode(action="show", name="linus")
```

### Actions

#### list

List all available development modes.

```python
mode(action="list")
```

**Response:**
```json
{
  "modes": [
    {"name": "guido", "description": "Guido van Rossum - Python creator"},
    {"name": "linus", "description": "Linus Torvalds - Linux/Git creator"},
    {"name": "rob", "description": "Rob Pike - Go language designer"}
  ]
}
```

#### activate

Activate a development mode.

```python
mode(action="activate", name="guido")
```

This changes:
- Code style preferences
- Review approach
- Communication style
- Tool recommendations

#### current

Show the currently active mode.

```python
mode(action="current")
```

#### show

Show details of a specific mode.

```python
mode(action="show", name="linus")
```

**Response:**
```json
{
  "name": "linus",
  "description": "Linus Torvalds - Linux/Git creator",
  "principles": [
    "Simple is better than complex",
    "Make it work, make it right, make it fast",
    "Read the code"
  ],
  "preferences": {
    "language": "C",
    "style": "kernel",
    "testing": "rigorous"
  }
}
```

### Available Modes

The mode system includes 700+ programmer personas loaded from `hanzo-persona`:

| Category | Examples |
|----------|----------|
| Language Creators | guido (Python), linus (Linux/C), rob (Go), rich (Clojure) |
| Industry Leaders | jeff (AWS), kelsey (Kubernetes), mitchellh (HashiCorp) |
| Framework Authors | dan (React), evan (Vue), taylor (Laravel) |
| Scientists | alan (Turing), grace (Hopper), ada (Lovelace) |

Each persona includes:
- OCEAN personality traits
- Behavioral patterns
- Cognitive style
- Communication preferences
- Tool recommendations

## Examples

### Project Setup

```python
# Set project-specific config
config(action="set", key="project.language", value="python")
config(action="set", key="project.style", value="black")
config(action="set", key="tools.lsp", value="pyright")

# Activate appropriate mode
mode(action="activate", name="guido")
```

### Switching Contexts

```python
# Working on Go project
mode(action="activate", name="rob")
config(action="set", key="project.language", value="go")

# Later, switching to Rust
mode(action="activate", name="steve")  # Steve Klabnik
config(action="set", key="project.language", value="rust")
```

### Checking Configuration

```python
# See all settings
config(action="list")

# Check specific setting
timeout = config(action="get", key="tools.timeout")

# Check current mode
current = mode(action="current")
```

## Best Practices

1. **Use hierarchical keys** - `category.setting` format
2. **Set project config locally** - Use `.hanzo/config` for project-specific
3. **Match mode to project** - Python project → guido mode
4. **Review mode on start** - Check persona fits your current task
