"""Command palette widget for MCP tool selection."""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass

from textual import events
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Input, ListView, ListItem, Label
from textual.reactive import reactive
from textual.message import Message
from rich.text import Text


@dataclass
class Command:
    """Represents a command/tool."""
    name: str
    description: str
    category: str
    icon: str = "⚡"
    usage_count: int = 0
    parameters: Optional[Dict[str, Any]] = None


class CommandSelected(Message):
    """Message sent when a command is selected."""
    def __init__(self, command: Command) -> None:
        self.command = command
        super().__init__()


class CommandItem(ListItem):
    """A command item in the list."""
    
    def __init__(self, command: Command) -> None:
        super().__init__()
        self.command = command
        
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        with Horizontal(classes="command-item"):
            # Icon and category
            yield Static(f"{self.command.icon} [{self.command.category}]", classes="command-icon")
            
            # Name and description
            with Vertical(classes="command-info"):
                yield Static(self.command.name, classes="command-name")
                yield Static(self.command.description[:60] + "...", classes="command-desc")


class CommandPalette(Vertical):
    """Command palette overlay widget."""
    
    CSS = """
    CommandPalette {
        layer: overlay;
        width: 80%;
        height: 60%;
        background: $panel;
        border: thick $primary;
        padding: 1;
        align: center middle;
        offset: 10% 20%;
    }
    
    #palette-input {
        dock: top;
        height: 3;
        margin-bottom: 1;
        background: $background;
        border: tall $secondary;
        padding: 0 1;
    }
    
    #palette-list {
        height: 1fr;
        background: $background;
        border: none;
        overflow-y: auto;
    }
    
    .command-item {
        padding: 0 1;
        height: 3;
    }
    
    .command-item:hover {
        background: $boost;
    }
    
    .command-icon {
        width: 20;
        color: $primary;
    }
    
    .command-info {
        width: 1fr;
    }
    
    .command-name {
        text-style: bold;
    }
    
    .command-desc {
        color: $text-muted;
        text-style: italic;
    }
    
    #palette-hint {
        dock: bottom;
        height: 1;
        color: $text-muted;
        text-align: center;
        margin-top: 1;
    }
    """
    
    commands = reactive([], always_update=True)
    filtered_commands = reactive([], always_update=True)
    
    def __init__(self, tools: Dict[str, Any]) -> None:
        super().__init__(id="command-palette")
        self.all_commands = self._build_commands(tools)
        self.commands = self.all_commands
        self.filtered_commands = self.all_commands
        
    def _build_commands(self, tools: Dict[str, Any]) -> List[Command]:
        """Build command list from MCP tools."""
        commands = []
        
        # Tool categories with icons
        category_icons = {
            "file": "📁",
            "search": "🔍",
            "shell": "💻",
            "agent": "🤖",
            "llm": "🧠",
            "editor": "✏️",
            "todo": "✅",
            "vector": "🔗",
            "database": "🗄️",
        }
        
        for name, tool in sorted(tools.items()):
            # Determine category from tool module
            category = "general"
            if hasattr(tool, "__module__"):
                parts = tool.__module__.split(".")
                if len(parts) > 2:
                    category = parts[-1]
            
            icon = category_icons.get(category, "⚡")
            
            commands.append(Command(
                name=name,
                description=tool.description,
                category=category,
                icon=icon,
                parameters=tool.get_schema() if hasattr(tool, "get_schema") else None
            ))
        
        # Add some special commands
        commands.extend([
            Command("clear", "Clear the chat history", "system", "🗑️"),
            Command("help", "Show help and shortcuts", "system", "❓"),
            Command("model", "Change AI model", "system", "🔄"),
            Command("theme", "Change theme", "system", "🎨"),
        ])
        
        return commands
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Input(
            placeholder="Search commands... (fuzzy matching enabled)",
            id="palette-input"
        )
        yield ListView(id="palette-list")
        yield Label("↑↓ Navigate · ⏎ Select · esc Close · ⇥ Complete", id="palette-hint")
    
    def on_mount(self) -> None:
        """Focus input when mounted."""
        self.query_one("#palette-input", Input).focus()
        self._update_list()
    
    def _fuzzy_match(self, query: str, text: str) -> bool:
        """Simple fuzzy matching."""
        query = query.lower()
        text = text.lower()
        
        # Direct substring match
        if query in text:
            return True
        
        # Character-by-character fuzzy match
        query_idx = 0
        for char in text:
            if query_idx < len(query) and char == query[query_idx]:
                query_idx += 1
        
        return query_idx == len(query)
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Filter commands as user types."""
        query = event.value.strip()
        
        if not query:
            self.filtered_commands = self.all_commands
        else:
            # Fuzzy filter
            filtered = []
            for cmd in self.all_commands:
                if (self._fuzzy_match(query, cmd.name) or 
                    self._fuzzy_match(query, cmd.description) or
                    self._fuzzy_match(query, cmd.category)):
                    filtered.append(cmd)
            
            # Sort by relevance (prefer name matches)
            filtered.sort(key=lambda c: (
                not c.name.lower().startswith(query.lower()),
                not query.lower() in c.name.lower(),
                -c.usage_count
            ))
            
            self.filtered_commands = filtered
        
        self._update_list()
    
    def _update_list(self) -> None:
        """Update the command list."""
        list_view = self.query_one("#palette-list", ListView)
        list_view.clear()
        
        for cmd in self.filtered_commands[:20]:  # Limit to 20 items
            list_view.append(CommandItem(cmd))
    
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle command selection."""
        if isinstance(event.item, CommandItem):
            self.post_message(CommandSelected(event.item.command))
            self.remove()
    
    def on_key(self, event: events.Key) -> None:
        """Handle keyboard shortcuts."""
        if event.key == "escape":
            self.remove()
        elif event.key == "tab":
            # Auto-complete to first match
            if self.filtered_commands:
                input_widget = self.query_one("#palette-input", Input)
                input_widget.value = self.filtered_commands[0].name
        elif event.key == "enter":
            # Execute first match or AI complete
            input_widget = self.query_one("#palette-input", Input)
            value = input_widget.value.strip()
            
            if self.filtered_commands:
                # Use first match
                self.post_message(CommandSelected(self.filtered_commands[0]))
            elif value:
                # Try AI completion
                ai_cmd = Command(
                    name="ai_complete",
                    description=f"AI: {value}",
                    category="ai",
                    icon="✨"
                )
                self.post_message(CommandSelected(ai_cmd))
            
            self.remove()