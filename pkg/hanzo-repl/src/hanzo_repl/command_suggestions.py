"""Command suggestions widget for slash commands."""

from typing import List, Dict, Optional
from dataclasses import dataclass

from textual import events
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static, Label
from textual.reactive import reactive
from textual.message import Message
from rich.text import Text
from rich.table import Table


@dataclass 
class SlashCommand:
    """Represents a slash command."""
    command: str
    description: str
    aliases: List[str] = None
    
    def matches(self, query: str) -> bool:
        """Check if command matches query."""
        query = query.lower()
        if self.command.lower().startswith(query):
            return True
        if self.aliases:
            return any(alias.lower().startswith(query) for alias in self.aliases)
        return False


class CommandSuggestions(Vertical):
    """Command suggestions dropdown widget."""
    
    CSS = """
    CommandSuggestions {
        layer: overlay;
        width: auto;
        max-width: 100;
        height: auto;
        max-height: 20;
        background: $panel;
        border: tall $primary;
        padding: 0 1;
        offset-y: -100%;
        margin-bottom: 1;
    }
    
    .suggestion-header {
        padding: 1 0;
        border-bottom: solid $secondary;
        margin-bottom: 1;
    }
    
    .suggestion-item {
        padding: 0 1;
        height: 2;
    }
    
    .suggestion-item.selected {
        background: $boost;
    }
    
    .command-name {
        color: $primary;
        text-style: bold;
    }
    
    .command-desc {
        color: $text-muted;
    }
    """
    
    COMMANDS = [
        SlashCommand("/add-dir", "Add a new working directory"),
        SlashCommand("/auth", "Authenticate with Claude personal account"),
        SlashCommand("/backend", "Switch AI backend (claude/openai/embedded)"),
        SlashCommand("/bug", "Submit feedback about Hanzo REPL"),
        SlashCommand("/clear", "Clear conversation history and free up context"),
        SlashCommand("/compact", "Clear conversation history but keep a summary in context"),
        SlashCommand("/config", "Open config panel", ["theme"]),
        SlashCommand("/cost", "Show the total cost and duration of the current session"),
        SlashCommand("/doctor", "Checks the health of your Hanzo installation"),
        SlashCommand("/exit", "Exit the REPL", ["quit"]),
        SlashCommand("/help", "Show help and available commands"),
        SlashCommand("/logout", "Logout from Claude account"),
        SlashCommand("/model", "Change the AI model"),
        SlashCommand("/voice", "Enable voice mode for bidirectional communication"),
        SlashCommand("/search", "Search for content using MCP tools"),
        SlashCommand("/file", "Read or open a file"),
        SlashCommand("/run", "Run a shell command"),
        SlashCommand("/memorize", "Save a snippet for later recall"),
        SlashCommand("/tools", "Show available MCP tools"),
        SlashCommand("/history", "Show command history"),
        SlashCommand("/export", "Export conversation to file"),
        SlashCommand("/import", "Import conversation from file"),
        SlashCommand("/reset", "Reset the current session"),
        SlashCommand("/status", "Show current backend and auth status"),
    ]
    
    selected_index = reactive(0)
    filtered_commands = reactive(COMMANDS)
    
    def __init__(self, query: str = ""):
        super().__init__(id="command-suggestions")
        self.query = query
        self._filter_commands()
        
    def _filter_commands(self) -> None:
        """Filter commands based on query."""
        if not self.query or self.query == "/":
            self.filtered_commands = self.COMMANDS
        else:
            query = self.query[1:] if self.query.startswith("/") else self.query
            self.filtered_commands = [
                cmd for cmd in self.COMMANDS
                if cmd.matches(query)
            ]
        self.selected_index = 0
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        # Header
        yield Static(
            Text("╭─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮\n"
                 f"│ > {self.query:<121}│\n"
                 "╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯",
                 style="dim"),
            classes="suggestion-header"
        )
        
        # Commands list
        for i, cmd in enumerate(self.filtered_commands[:10]):  # Show max 10
            selected = "selected" if i == self.selected_index else ""
            
            # Format command and description
            cmd_text = f"{cmd.command:<20}"
            desc_text = cmd.description[:80]
            
            yield Static(
                Text(f"  {cmd_text}{desc_text}", 
                     style="bright_white" if selected else "white"),
                classes=f"suggestion-item {selected}"
            )
    
    def on_mount(self) -> None:
        """Focus when mounted."""
        self.refresh()
    
    def update_query(self, query: str) -> None:
        """Update the search query."""
        self.query = query
        self._filter_commands()
        self.refresh()
    
    def move_selection_up(self) -> None:
        """Move selection up."""
        if self.selected_index > 0:
            self.selected_index -= 1
            self.refresh()
    
    def move_selection_down(self) -> None:
        """Move selection down."""
        if self.selected_index < len(self.filtered_commands) - 1:
            self.selected_index += 1
            self.refresh()
    
    def get_selected_command(self) -> Optional[str]:
        """Get the selected command."""
        if 0 <= self.selected_index < len(self.filtered_commands):
            return self.filtered_commands[self.selected_index].command
        return None