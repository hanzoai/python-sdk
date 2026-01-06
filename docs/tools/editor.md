# Editor Tools

The editor tools (`hanzo-tools-editor`) provide integration with external code editors, currently focused on Neovim.

## Overview

These tools enable opening files in your preferred editor with precise cursor positioning, split modes, and session management.

## Neovim Integration

### neovim_edit - Open Files

Open files in Neovim with advanced options:

```python
# Basic file open
neovim_edit(file_path="main.py")

# Open at specific line
neovim_edit(file_path="main.py", line_number=42)

# Open at specific line and column
neovim_edit(file_path="main.py", line_number=42, column_number=10)

# Open in read-only mode
neovim_edit(file_path="config.json", read_only=True)

# Open in vertical split
neovim_edit(file_path="test.py", split="vsplit")

# Open in new tab
neovim_edit(file_path="README.md", split="tab")
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `file_path` | str | required | Path to the file |
| `line_number` | int | - | Line to jump to |
| `column_number` | int | - | Column to jump to |
| `read_only` | bool | `False` | Open in view mode |
| `split` | str | - | `vsplit`, `split`, or `tab` |
| `wait` | bool | `True` | Wait for editor to close |
| `in_terminal` | bool | `True` | Open in terminal window |

#### Split Modes

| Mode | Description |
|------|-------------|
| `vsplit` | Vertical split (side by side) |
| `split` | Horizontal split (top/bottom) |
| `tab` | New tab |

### neovim_command - Execute Commands

Execute Neovim Ex commands:

```python
# Run command in current buffer
neovim_command(command=":w")

# Search and replace
neovim_command(command=":%s/old/new/g")

# Run Lua code
neovim_command(command=":lua print('Hello')")

# Source configuration
neovim_command(command=":source ~/.config/nvim/init.lua")
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `command` | str | required | Ex command to execute |
| `file_path` | str | - | File to run command on |

### neovim_session - Manage Sessions

Manage Neovim sessions for persistent workspaces:

```python
# Save current session
neovim_session(action="save", name="project-alpha")

# Load session
neovim_session(action="load", name="project-alpha")

# List sessions
neovim_session(action="list")

# Delete session
neovim_session(action="delete", name="old-session")
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `action` | str | required | `save`, `load`, `list`, `delete` |
| `name` | str | - | Session name |

## Installation

```bash
# Basic install
pip install hanzo-tools-editor

# With Neovim support
pip install hanzo-tools-editor[neovim]
```

## Requirements

- **Neovim** must be installed and available in PATH
- Installation varies by platform:

```bash
# macOS
brew install neovim

# Ubuntu/Debian
sudo apt install neovim

# Arch Linux
sudo pacman -S neovim

# Windows (Chocolatey)
choco install neovim
```

## Terminal Integration

On macOS, the tool integrates with:
- **iTerm2** (preferred if installed)
- **Terminal.app** (fallback)

On Linux:
- **gnome-terminal**
- **xterm** (fallback)

## Best Practices

### 1. Use Line/Column for Error Navigation

```python
# Jump directly to error location
neovim_edit(file_path="src/main.py", line_number=42, column_number=15)
```

### 2. Use Splits for Comparison

```python
# Open original and new file side by side
neovim_edit(file_path="original.py")
neovim_edit(file_path="modified.py", split="vsplit")
```

### 3. Use Sessions for Projects

```python
# Save state when switching projects
neovim_session(action="save", name="current-work")

# Restore when returning
neovim_session(action="load", name="current-work")
```

### 4. Read-Only for Config Files

```python
# Prevent accidental changes
neovim_edit(file_path="/etc/config", read_only=True)
```
