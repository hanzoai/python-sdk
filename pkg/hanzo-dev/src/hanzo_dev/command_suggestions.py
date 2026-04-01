"""Command suggestions widget for slash commands."""

from dataclasses import dataclass
from typing import List, Optional

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import Static


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
        SlashCommand("/auto", "Execute prompt autonomously with tools"),
        SlashCommand("/backend", "Switch AI backend (claude/openai/embedded)"),
        SlashCommand("/bug", "Submit feedback about Hanzo REPL"),
        SlashCommand("/clear", "Clear session history and start fresh"),
        SlashCommand("/code", "Implement with consensus from multiple review passes"),
        SlashCommand("/compact", "Compact session keeping a summary in context"),
        SlashCommand("/config", "Show loaded configuration files", ["theme"]),
        SlashCommand("/cost", "Show total cost and duration of current session"),
        SlashCommand("/doctor", "Check the health of your Hanzo installation"),
        SlashCommand("/exit", "Exit the REPL", ["quit"]),
        SlashCommand("/export", "Export conversation to file"),
        SlashCommand("/fast", "Toggle fast/standard mode"),
        SlashCommand("/file", "Read or open a file"),
        SlashCommand("/help", "Show help and available commands"),
        SlashCommand("/history", "Show command history"),
        SlashCommand("/import", "Import conversation from file"),
        SlashCommand("/init", "Create starter CLAUDE.md in cwd"),
        SlashCommand("/login", "Authenticate via PKCE flow"),
        SlashCommand("/logout", "Logout from Claude account"),
        SlashCommand("/loop", "Run prompt on interval (e.g. /loop 10 check status)"),
        SlashCommand("/memorize", "Save a snippet for later recall"),
        SlashCommand("/memory", "Show loaded instruction files"),
        SlashCommand("/model", "Show or switch active AI model"),
        SlashCommand("/permissions", "Show/switch permission mode"),
        SlashCommand("/plan", "Planning agent - create a detailed plan"),
        SlashCommand("/providers", "List available LLM providers"),
        SlashCommand("/remote-control", "Start WebSocket server for remote control"),
        SlashCommand("/reset", "Reset conversation context"),
        SlashCommand("/resume", "Load saved session from JSON file"),
        SlashCommand("/run", "Run a shell command"),
        SlashCommand("/search", "Search for content using MCP tools"),
        SlashCommand("/session", "List or switch saved sessions"),
        SlashCommand("/solve", "Race multiple approaches, present best solution"),
        SlashCommand("/status", "Model, session info, token usage"),
        SlashCommand("/tools", "Show available MCP tools"),
        SlashCommand("/version", "Show version info"),
        SlashCommand("/voice", "Enable voice mode for bidirectional communication"),
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
                cmd for cmd in self.COMMANDS if cmd.matches(query)
            ]
        self.selected_index = 0

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        # Header
        yield Static(
            Text(
                "╭─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮\n"
                f"│ > {self.query:<121}│\n"
                "╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯",
                style="dim",
            ),
            classes="suggestion-header",
        )

        # Commands list
        for i, cmd in enumerate(self.filtered_commands[:10]):  # Show max 10
            selected = "selected" if i == self.selected_index else ""

            # Format command and description
            cmd_text = f"{cmd.command:<20}"
            desc_text = cmd.description[:80]

            yield Static(
                Text(
                    f"  {cmd_text}{desc_text}",
                    style="bright_white" if selected else "white",
                ),
                classes=f"suggestion-item {selected}",
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
