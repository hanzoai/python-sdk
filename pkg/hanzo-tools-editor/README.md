# hanzo-tools-editor

Neovim integration tools for Hanzo MCP.

## Installation

```bash
pip install hanzo-tools-editor
```

## Tools

### neovim_edit - Edit Files in Neovim
```python
neovim_edit(file="/path/to/file.py", line=10)
```

### neovim_command - Run Neovim Commands
```python
neovim_command(command=":w")  # Save
neovim_command(command=":q!")  # Quit without saving
neovim_command(command=":%s/old/new/g")  # Search replace
```

### neovim_session - Manage Sessions
```python
neovim_session(action="list")  # List sessions
neovim_session(action="connect", name="main")
neovim_session(action="disconnect")
```

## Requirements

- Neovim with remote plugin support
- `pynvim` package (installed automatically)

## Configuration

Set Neovim socket path:

```bash
NVIM_LISTEN_ADDRESS=/tmp/nvim.sock nvim
```

Or connect to existing session:

```python
neovim_session(action="connect", socket="/tmp/nvim.sock")
```

## License

MIT
