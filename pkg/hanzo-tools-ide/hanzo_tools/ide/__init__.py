"""
hanzo-tools-ide: IDE integration for VS Code, JetBrains, and LSP editors.

Provides AI agents with direct control over IDEs:
- File operations (open, save, close)
- Editor operations (select, insert, replace)
- Navigation (go to definition, find references)
- Refactoring (rename, extract, format)
- Terminal control (create, send commands)
- Diagnostics (errors, warnings, quick fixes)

Usage:
    ide(action="open", path="/path/to/file.py")
    ide(action="insert", text="# comment", line=10)
    ide(action="go_to_definition", line=15, column=8)
    ide(action="rename", new_name="better_name", line=10, column=5)
    ide(action="terminal", command="npm test")
"""

from .ide_tool import IdeTool, IdeConnection

TOOLS = [IdeTool()]

__all__ = ["IdeTool", "IdeConnection", "TOOLS"]
