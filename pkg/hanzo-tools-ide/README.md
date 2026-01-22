# hanzo-tools-ide

IDE integration tool for VS Code, Cursor, Windsurf, JetBrains, and LSP-compatible editors.

## Features

- **Multi-IDE support**: VS Code, Cursor, Windsurf, JetBrains, Neovim
- **Full editor control**: Open, edit, navigate, refactor
- **Terminal integration**: Create and send commands to terminals
- **Diagnostics**: Access errors, warnings, and quick fixes
- **Agent-friendly**: Designed for AI agent workflows

## Installation

```bash
pip install hanzo-tools-ide
```

## Requirements

Install the Hanzo extension in your IDE:
- **VS Code/Cursor/Windsurf**: Install "Hanzo AI" extension
- **JetBrains**: Install "Hanzo AI" plugin
- **Neovim**: Install hanzo.nvim plugin

## Usage

```python
from hanzo_tools.ide import IdeTool

ide = IdeTool()

# Connect to IDE (auto-detects)
await ide.call(action="connect")

# Open file
await ide.call(action="open", path="/src/main.py", line=42)

# Insert text
await ide.call(action="insert", text="# TODO: fix", line=10)

# Go to definition
await ide.call(action="go_to_definition", line=15, column=8)

# Rename symbol
await ide.call(action="rename", new_name="betterName", line=10, column=5)

# Run in terminal
await ide.call(action="terminal", command="npm test")

# Get diagnostics
await ide.call(action="diagnostics", severity="error")

# Execute VS Code command
await ide.call(action="command", command="editor.action.formatDocument")
```

## Actions

| Action | Description | Parameters |
|--------|-------------|------------|
| connect | Connect to IDE | ide?: vscode\|cursor\|jetbrains |
| status | Check connection | - |
| open | Open file | path, line? |
| close | Close file | path? |
| save | Save file | path? |
| files | List open files | - |
| select | Set selection | line, column, end_line?, end_column? |
| insert | Insert text | text, line, column? |
| replace | Replace text | text, line, column, end_line, end_column |
| get_text | Get text | line?, end_line? |
| go_to_definition | Navigate | line, column |
| find_references | Find refs | line, column |
| rename | Rename symbol | new_name, line, column |
| format | Format doc | - |
| diagnostics | Get errors | severity? |
| quick_fix | Apply fix | line, column, index? |
| command | Execute cmd | command, args? |
| terminal | Terminal | command?, name? |
| search | Search | query, include?, exclude? |

## License

MIT - Hanzo Industries Inc
