"""Beautiful Textual-based REPL interface for Hanzo."""

import asyncio
import time
from datetime import datetime
from typing import Optional, List, Dict, Any

from textual import events
from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.widgets import Static, Input, Label, RichLog
from textual.reactive import reactive
from textual.css.query import NoMatches
from rich.text import Text
from rich.console import Console
from rich.markdown import Markdown

from hanzo_mcp.server import HanzoMCPServer
from .llm_client import LLMClient
from .tool_executor import ToolExecutor
from .command_palette import CommandPalette, CommandSelected
from .command_suggestions import CommandSuggestions
from .backends import BackendManager


class StatusBar(Static):
    """Animated status bar showing thinking state."""
    
    elapsed_time = reactive(0)
    token_count = reactive(0)
    is_thinking = reactive(False)
    status_text = reactive("Ready")
    
    SPINNERS = ["✦", "✧", "✶", "✷", "✸", "✹", "✺", "✻", "✼", "✽"]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.start_time = None
        self.spinner_index = 0
        
    def on_mount(self) -> None:
        """Start the timer."""
        self.set_interval(0.1, self.update_status)
        
    def update_status(self) -> None:
        """Update the status display."""
        if self.is_thinking and self.start_time:
            self.elapsed_time = int(time.time() - self.start_time)
            self.spinner_index = (self.spinner_index + 1) % len(self.SPINNERS)
            
    def start_thinking(self, text: str = "Bonding") -> None:
        """Start the thinking animation."""
        self.is_thinking = True
        self.status_text = text
        self.start_time = time.time()
        self.token_count = 0
        
    def stop_thinking(self) -> None:
        """Stop the thinking animation."""
        self.is_thinking = False
        self.start_time = None
        
    def update_tokens(self, count: int) -> None:
        """Update token count."""
        self.token_count = count
        
    def render(self) -> Text:
        """Render the status bar."""
        if self.is_thinking:
            spinner = self.SPINNERS[self.spinner_index]
            return Text(
                f"{spinner} {self.status_text}… ({self.elapsed_time}s · ↑ {self.token_count} tokens · esc to interrupt)",
                style="bright_yellow"
            )
        return Text("")


class ContextIndicator(Static):
    """Shows context usage."""
    
    context_percent = reactive(10)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def render(self) -> Text:
        """Render context indicator."""
        return Text(
            f"Context left until auto-compact: {self.context_percent}%",
            style="dim yellow"
        )


class MessageArea(ScrollableContainer):
    """Scrollable area for messages."""
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield RichLog(id="messages", wrap=True, markup=True, auto_scroll=True)


class HanzoTextualREPL(App):
    """Main Textual application for Hanzo REPL."""
    
    CSS = """
    Screen {
        background: $background;
    }
    
    MessageArea {
        height: 1fr;
        border: none;
        padding: 1 2;
    }
    
    #messages {
        background: $background;
        scrollbar-size: 1 1;
    }
    
    #input-box {
        height: 3;
        margin: 0 1;
        border: tall $secondary;
        background: $panel;
    }
    
    #input {
        dock: top;
        background: transparent;
        border: none;
        padding: 0 1;
    }
    
    #status-bar {
        dock: top;
        height: 1;
        padding: 0 2;
        background: transparent;
    }
    
    #bottom-bar {
        dock: bottom;
        height: 1;
        background: transparent;
        padding: 0 2;
    }
    
    #permissions {
        text-align: right;
    }
    
    #hint {
        color: $text-muted;
        padding: 0 2;
    }
    """
    
    BINDINGS = [
        ("escape", "interrupt", "Interrupt"),
        ("ctrl+c", "quit", "Quit"),
        ("ctrl+l", "clear", "Clear"),
        ("ctrl+k", "command_palette", "Commands"),
        ("up", "history_up", "Previous"),
        ("down", "history_down", "Next"),
        ("ctrl+r", "verbose", "Verbose"),
        ("!", "bash_mode", "Bash Mode"),
        ("?", "shortcuts", "Shortcuts"),
        ("/", "slash_commands", "Commands"),
        ("@", "file_complete", "Files"),
        ("#", "memorize", "Memorize"),
    ]
    
    def __init__(self):
        super().__init__()
        self.mcp_server = None
        self.llm_client = None
        self.backend_manager = None
        self.tool_executor = None
        self.history = []
        self.history_index = 0
        self.bash_mode = False
        self.context_usage = 10
        self.verbose_mode = False
        self.memory = {}  # For memorized snippets
        self.command_suggestions = None
        
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        # Status bar at top
        yield StatusBar(id="status-bar")
        
        # Message area
        yield MessageArea()
        
        # Input area
        with Vertical(id="input-box"):
            yield Input(
                placeholder="Press up to edit queued messages",
                id="input"
            )
        
        # Hint text
        yield Label("? for shortcuts", id="hint")
        
        # Bottom bar
        with Horizontal(id="bottom-bar"):
            yield Static(Text("Bypassing Permissions", style="yellow"))
            yield ContextIndicator(id="permissions")
    
    async def on_mount(self) -> None:
        """Initialize when app mounts."""
        await self.initialize_services()
        
        # Focus input
        self.query_one("#input", Input).focus()
        
        # Show welcome message
        messages = self.query_one("#messages", RichLog)
        messages.write(Text("● Welcome to Hanzo REPL", style="bold cyan"))
        messages.write(Text("● Type '?' for shortcuts, '!' for bash mode", style="dim"))
        messages.write("")
    
    async def initialize_services(self) -> None:
        """Initialize MCP and LLM services."""
        try:
            # Initialize MCP server
            self.mcp_server = HanzoMCPServer()
            await self.mcp_server.initialize()
            
            # Initialize LLM client (for embedded backend)
            self.llm_client = LLMClient()
            
            # Initialize backend manager
            self.backend_manager = BackendManager(self.llm_client)
            
            # Show backend info
            messages = self.query_one("#messages", RichLog)
            backend_name = self.backend_manager.current_backend
            backend = self.backend_manager.get_backend()
            
            messages.write(Text(f"● Backend: {backend_name}", style="green"))
            
            # Show specific info based on backend
            if backend_name == "claude":
                if hasattr(backend, 'authenticated') and backend.authenticated:
                    messages.write(Text("● Using Claude personal account", style="cyan"))
                else:
                    messages.write(Text("● Claude Code (not authenticated - using API)", style="yellow"))
            elif backend_name == "embedded":
                messages.write(Text(f"● Model: {self.llm_client.current_model}", style="green"))
            
            # Initialize tool executor with backend
            self.tool_executor = ToolExecutor(self.mcp_server, self.backend_manager)
            
            # List available backends
            backends = self.backend_manager.list_backends()
            available = [name for name, avail in backends.items() if avail]
            messages.write(Text(f"● Available backends: {', '.join(available)}", style="dim"))
            
        except Exception as e:
            self.show_error(f"Initialization error: {e}")
    
    def show_message(self, message: str, style: str = "white") -> None:
        """Show a message in the chat area."""
        messages = self.query_one("#messages", RichLog)
        messages.write(Text(f"● {message}", style=style))
    
    def show_error(self, message: str) -> None:
        """Show an error message."""
        messages = self.query_one("#messages", RichLog)
        messages.write(Text(f"● {message}", style="red"))
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        input_widget = self.query_one("#input", Input)
        value = event.value.strip()
        
        # Check if command suggestions are visible and handle selection
        try:
            suggestions = self.query_one("#command-suggestions", CommandSuggestions)
            selected_command = suggestions.get_selected_command()
            if selected_command:
                # Use selected command
                value = selected_command
                input_widget.value = ""
                # Remove suggestions
                suggestions.remove()
        except NoMatches:
            pass
        
        if not value:
            return
            
        # Clear input
        input_widget.value = ""
        
        # Add to history
        self.history.append(value)
        self.history_index = len(self.history)
        
        # Show user message
        self.show_message(value, "bright_white")
        
        # Handle special input first
        if await self.handle_special_input(value):
            return
        
        # Handle special commands
        if value.startswith("!"):
            # Bash mode
            await self.execute_bash(value[1:].strip())
        elif value == "?":
            self.action_shortcuts()
        else:
            # Regular chat mode
            await self.process_chat(value)
    
    async def process_chat(self, message: str) -> None:
        """Process a chat message."""
        # Start thinking animation
        status = self.query_one("#status-bar", StatusBar)
        status.start_thinking()
        
        try:
            # Execute with tools
            response = await self.tool_executor.execute_with_tools(message)
            
            # Stop animation
            status.stop_thinking()
            
            # Show response
            messages = self.query_one("#messages", RichLog)
            messages.write("")
            
            # Format as markdown
            console = Console()
            with console.capture() as capture:
                console.print(Markdown(response))
            
            for line in capture.get().split("\n"):
                if line.strip():
                    messages.write(f"● {line}")
            
            messages.write("")
            
            # Update context usage (mock)
            self.context_usage = max(5, self.context_usage - 2)
            context_indicator = self.query_one("#permissions", ContextIndicator)
            context_indicator.context_percent = self.context_usage
            
        except Exception as e:
            status.stop_thinking()
            self.show_error(f"Error: {e}")
    
    async def execute_bash(self, command: str) -> None:
        """Execute a bash command."""
        if not command:
            self.show_message("Entering bash mode. Type commands to execute.", "yellow")
            self.bash_mode = True
            return
        
        # Show command
        messages = self.query_one("#messages", RichLog)
        messages.write(Text(f"Bash({command})", style="yellow"))
        messages.write(Text("  └─ Running…", style="dim"))
        
        try:
            # Execute command
            tool = self.mcp_server.tools.get("run_command")
            if tool:
                result = await tool.execute(command=command)
                # Show output
                if result:
                    for line in str(result).split("\n"):
                        if line.strip():
                            messages.write(f"  {line}")
                messages.write("")
        except Exception as e:
            self.show_error(f"Command failed: {e}")
    
    def action_interrupt(self) -> None:
        """Interrupt current operation."""
        status = self.query_one("#status-bar", StatusBar)
        if status.is_thinking:
            status.stop_thinking()
            self.show_message("Interrupted", "yellow")
    
    def action_clear(self) -> None:
        """Clear the message area."""
        messages = self.query_one("#messages", RichLog)
        messages.clear()
    
    def action_history_up(self) -> None:
        """Navigate to previous command or move selection in suggestions."""
        # Check if command suggestions are visible
        try:
            suggestions = self.query_one("#command-suggestions", CommandSuggestions)
            suggestions.move_selection_up()
            return
        except NoMatches:
            pass
            
        # Normal history navigation
        if self.history and self.history_index > 0:
            self.history_index -= 1
            input_widget = self.query_one("#input", Input)
            input_widget.value = self.history[self.history_index]
    
    def action_history_down(self) -> None:
        """Navigate to next command or move selection in suggestions."""
        # Check if command suggestions are visible
        try:
            suggestions = self.query_one("#command-suggestions", CommandSuggestions)
            suggestions.move_selection_down()
            return
        except NoMatches:
            pass
            
        # Normal history navigation
        if self.history and self.history_index < len(self.history) - 1:
            self.history_index += 1
            input_widget = self.query_one("#input", Input)
            input_widget.value = self.history[self.history_index]
        elif self.history_index == len(self.history) - 1:
            self.history_index = len(self.history)
            input_widget = self.query_one("#input", Input)
            input_widget.value = ""
    
    def action_shortcuts(self) -> None:
        """Show shortcuts."""
        messages = self.query_one("#messages", RichLog)
        messages.write("")
        
        # Input box with shortcuts
        messages.write(Text("╭─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮", style="dim"))
        messages.write(Text("│ !                                                                                                                           │", style="dim"))
        messages.write(Text("╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯", style="dim"))
        
        # Shortcuts in two columns
        shortcuts_left = [
            ("! for bash mode", "Execute shell commands directly"),
            ("/ for commands", "Access MCP tool commands"),  
            ("@ for file paths", "Quick file path completion"),
            ("# to memorize", "Save snippet for later recall"),
        ]
        
        shortcuts_right = [
            ("double tap esc to clear input", ""),
            ("shift + tab to auto-accept edits", ""),
            ("ctrl + r for verbose output", ""),
            ("shift + ⏎ for newline", ""),
        ]
        
        # Display shortcuts
        for left, right in zip(shortcuts_left, shortcuts_right):
            left_text = f"  {left[0]:<35}"
            right_text = right[0]
            messages.write(Text(left_text + right_text, style="cyan"))
        
        messages.write("")
    
    def action_command_palette(self) -> None:
        """Show command palette."""
        if self.mcp_server and self.mcp_server.tools:
            palette = CommandPalette(self.mcp_server.tools)
            self.mount(palette)
    
    async def on_command_selected(self, message: CommandSelected) -> None:
        """Handle command selection from palette."""
        command = message.command
        
        # Handle special commands
        if command.name == "clear":
            self.action_clear()
        elif command.name == "help":
            self.action_shortcuts()
        elif command.name == "model":
            await self.show_model_selector()
        elif command.name == "ai_complete":
            # AI completion of partial command
            await self.process_chat(command.description[4:])  # Remove "AI: " prefix
        else:
            # Execute MCP tool
            await self.execute_tool(command.name, command.parameters)
    
    async def execute_tool(self, tool_name: str, parameters: Optional[Dict] = None) -> None:
        """Execute an MCP tool."""
        self.show_message(f"Executing: {tool_name}", "cyan")
        
        # Start thinking animation
        status = self.query_one("#status-bar", StatusBar)
        status.start_thinking(f"Running {tool_name}")
        
        try:
            tool = self.mcp_server.tools.get(tool_name)
            if not tool:
                self.show_error(f"Tool not found: {tool_name}")
                return
            
            # Get parameters if needed
            if parameters and any(p.get("required", False) for p in parameters.get("properties", {}).values()):
                # TODO: Show parameter input dialog
                self.show_message("Tool requires parameters. Using defaults.", "yellow")
                params = {}
            else:
                params = {}
            
            # Execute tool
            result = await tool.execute(**params)
            
            # Stop animation
            status.stop_thinking()
            
            # Show result
            messages = self.query_one("#messages", RichLog)
            if isinstance(result, str):
                for line in result.split("\n"):
                    if line.strip():
                        messages.write(f"  {line}")
            else:
                messages.write(f"  Result: {result}")
            
            messages.write("")
            
        except Exception as e:
            status.stop_thinking()
            self.show_error(f"Tool execution failed: {e}")
    
    def action_slash_commands(self) -> None:
        """Show slash commands menu."""
        self.show_message("/ commands:", "cyan")
        commands = [
            "/search <query> - Search for content",
            "/file <path> - Open file",
            "/run <command> - Run shell command",
            "/voice - Enable voice mode",
            "/model <name> - Change AI model",
        ]
        messages = self.query_one("#messages", RichLog)
        for cmd in commands:
            messages.write(f"  {cmd}")
        messages.write("")
    
    def action_file_complete(self) -> None:
        """File path completion."""
        input_widget = self.query_one("#input", Input)
        current_value = input_widget.value
        
        # Add @ prefix if not present
        if not current_value.startswith("@"):
            input_widget.value = "@" + current_value
        
        self.show_message("File completion: Start typing a path after @", "cyan")
    
    def action_memorize(self) -> None:
        """Memorize current input or last message."""
        input_widget = self.query_one("#input", Input)
        current_value = input_widget.value
        
        if current_value:
            # Memorize current input
            key = f"snippet_{len(self.memory) + 1}"
            self.memory[key] = current_value
            self.show_message(f"Memorized as {key}: {current_value[:50]}...", "green")
        else:
            # Show memorized items
            if self.memory:
                self.show_message("Memorized snippets:", "cyan")
                messages = self.query_one("#messages", RichLog)
                for key, value in self.memory.items():
                    messages.write(f"  {key}: {value[:50]}...")
                messages.write("")
            else:
                self.show_message("No memorized snippets. Type something and press # to memorize.", "yellow")
    
    def action_verbose(self) -> None:
        """Toggle verbose mode."""
        self.verbose_mode = not self.verbose_mode
        mode = "enabled" if self.verbose_mode else "disabled"
        self.show_message(f"Verbose mode {mode}", "cyan")
    
    async def handle_special_input(self, value: str) -> bool:
        """Handle special input patterns."""
        # Voice command
        if value == "/voice":
            await self.toggle_voice_mode()
            return True
        
        # File path with @
        if value.startswith("@"):
            file_path = value[1:].strip()
            if file_path:
                await self.execute_tool("read_file", {"file_path": file_path})
            return True
        
        # Search with /
        if value.startswith("/") and len(value) > 1:
            parts = value[1:].split(maxsplit=1)
            command = parts[0]
            arg = parts[1] if len(parts) > 1 else ""
            
            if command == "search" and arg:
                await self.execute_tool("search", {"query": arg})
                return True
            elif command == "model" and arg:
                if self.backend_manager.current_backend == "embedded":
                    self.llm_client.set_model(arg)
                    self.show_message(f"Model changed to: {arg}", "green")
                else:
                    self.show_message("Model selection only available for embedded backend", "yellow")
                return True
            elif command == "auth":
                await self.handle_auth_command()
                return True
            elif command == "backend":
                await self.handle_backend_command(arg)
                return True
            elif command == "logout":
                await self.handle_logout_command()
                return True
            elif command == "status":
                await self.show_backend_status()
                return True
            elif command == "exit" or command == "quit":
                self.exit()
                return True
            elif command == "clear":
                self.action_clear()
                return True
            elif command == "help":
                self.action_shortcuts()
                return True
            elif command == "tools":
                await self.show_tools()
                return True
        
        # Memorize with #
        if value.startswith("#"):
            content = value[1:].strip()
            if content:
                key = f"snippet_{len(self.memory) + 1}"
                self.memory[key] = content
                self.show_message(f"Memorized as {key}", "green")
            return True
        
        return False
    
    async def toggle_voice_mode(self) -> None:
        """Toggle voice mode on/off."""
        try:
            from .voice_mode import VoiceMode, VoiceCommands, VOICE_AVAILABLE
            
            if not VOICE_AVAILABLE:
                self.show_error("Voice mode not available. Install: pip install speechrecognition pyttsx3 pyaudio")
                return
            
            if not hasattr(self, 'voice_mode'):
                self.voice_mode = VoiceMode()
                self.voice_commands = VoiceCommands()
            
            if self.voice_mode.is_active:
                # Stop voice mode
                self.voice_mode.stop()
                self.show_message("Voice mode deactivated", "yellow")
            else:
                # Start voice mode
                def on_speech(text: str):
                    # Process voice input
                    processed, should_stop = self.voice_commands.process_voice_input(text)
                    
                    if should_stop:
                        self.call_from_thread(self.toggle_voice_mode)
                    elif processed:
                        # Show what was heard
                        self.call_from_thread(self.show_message, f"Heard: {text}", "dim")
                        # Process the command
                        self.call_from_thread(self.process_voice_command, processed)
                
                self.voice_mode.start(on_speech)
                self.show_message("Voice mode activated. Say 'Hey Hanzo' followed by your command.", "green")
                
        except Exception as e:
            self.show_error(f"Voice mode error: {e}")
    
    async def process_voice_command(self, command: str) -> None:
        """Process a voice command."""
        # Simulate input
        input_widget = self.query_one("#input", Input)
        input_widget.value = command
        
        # Submit it
        await self.on_input_submitted(Input.Submitted(input_widget, command))
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes to show command suggestions."""
        value = event.value
        
        # Show command suggestions when typing "/"
        if value.startswith("/") and len(value) >= 1:
            # Remove existing suggestions if any
            try:
                self.query_one("#command-suggestions").remove()
            except NoMatches:
                pass
            
            # Create and mount suggestions
            self.command_suggestions = CommandSuggestions(value)
            self.mount(self.command_suggestions, after="#input-box")
        else:
            # Remove suggestions if not typing a command
            try:
                self.query_one("#command-suggestions").remove()
            except NoMatches:
                pass
            
        # Update existing suggestions
        if self.command_suggestions and value.startswith("/"):
            self.command_suggestions.update_query(value)
    
    async def show_model_selector(self) -> None:
        """Show model selection dialog."""
        models = self.llm_client.get_available_models()
        self.show_message("Available models:", "cyan")
        messages = self.query_one("#messages", RichLog)
        for i, model in enumerate(models, 1):
            current = " (current)" if model == self.llm_client.current_model else ""
            messages.write(f"  {i}. {model}{current}")
        messages.write("")
        self.show_message("Use /model <name> to change model", "dim")
    
    async def handle_auth_command(self) -> None:
        """Handle /auth command."""
        backend = self.backend_manager.get_backend()
        
        if self.backend_manager.current_backend == "claude":
            if hasattr(backend, 'authenticate'):
                self.show_message("Authenticating with Claude...", "yellow")
                try:
                    success = await backend.authenticate()
                    if success:
                        self.show_message("Successfully authenticated with Claude!", "green")
                        self.show_message("You can now use your personal Claude account without API keys.", "cyan")
                    else:
                        self.show_error("Authentication failed. Please try again.")
                except Exception as e:
                    self.show_error(f"Authentication error: {e}")
            else:
                self.show_message("Claude backend doesn't support authentication", "yellow")
        else:
            self.show_message(f"Authentication not available for {self.backend_manager.current_backend} backend", "yellow")
            self.show_message("Use /backend claude to switch to Claude Code", "dim")
    
    async def handle_backend_command(self, backend_name: str) -> None:
        """Handle /backend command."""
        if not backend_name:
            # Show available backends
            backends = self.backend_manager.list_backends()
            self.show_message("Available backends:", "cyan")
            messages = self.query_one("#messages", RichLog)
            
            for name, available in backends.items():
                status = "✓" if available else "✗"
                current = " (current)" if name == self.backend_manager.current_backend else ""
                style = "green" if available else "red"
                messages.write(Text(f"  {status} {name}{current}", style=style))
            
            messages.write("")
            self.show_message("Use /backend <name> to switch backend", "dim")
        else:
            # Switch backend
            try:
                self.backend_manager.set_backend(backend_name)
                self.show_message(f"Switched to {backend_name} backend", "green")
                
                # Reinitialize tool executor with new backend
                self.tool_executor = ToolExecutor(self.mcp_server, self.backend_manager)
                
                # Show backend-specific info
                backend = self.backend_manager.get_backend()
                if backend_name == "claude" and hasattr(backend, 'authenticated'):
                    if backend.authenticated:
                        self.show_message("Using Claude personal account", "cyan")
                    else:
                        self.show_message("Not authenticated. Use /auth to login with personal account", "yellow")
                        
            except ValueError as e:
                self.show_error(str(e))
    
    async def handle_logout_command(self) -> None:
        """Handle /logout command."""
        backend = self.backend_manager.get_backend()
        
        if self.backend_manager.current_backend == "claude" and hasattr(backend, 'logout'):
            await backend.logout()
            self.show_message("Logged out from Claude account", "yellow")
        else:
            self.show_message("No active authentication session", "dim")
    
    async def show_backend_status(self) -> None:
        """Show current backend status."""
        backend_name = self.backend_manager.current_backend
        backend = self.backend_manager.get_backend()
        
        self.show_message("Backend Status:", "cyan")
        messages = self.query_one("#messages", RichLog)
        
        messages.write(f"  Current backend: {backend_name}")
        messages.write(f"  Config file: {backend.get_config_file()}")
        
        if backend_name == "claude":
            auth_status = "Authenticated" if hasattr(backend, 'authenticated') and backend.authenticated else "Not authenticated"
            messages.write(f"  Auth status: {auth_status}")
        elif backend_name == "embedded":
            messages.write(f"  Model: {self.llm_client.current_model}")
            messages.write(f"  Provider: {self.llm_client.current_provider}")
        
        # Load config if available
        config = await self.backend_manager.load_config()
        if config:
            messages.write("")
            messages.write("  Configuration loaded from: " + backend.get_config_file())
        
        messages.write("")
    
    async def show_tools(self) -> None:
        """Show available MCP tools."""
        if not self.mcp_server or not self.mcp_server.tools:
            self.show_error("MCP tools not initialized")
            return
            
        from rich.table import Table
        
        table = Table(title="Available MCP Tools")
        table.add_column("Tool", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")
        table.add_column("Category", style="green")
        
        for tool_name, tool in sorted(self.mcp_server.tools.items()):
            category = tool.__class__.__module__.split('.')[-1]
            table.add_row(tool_name, tool.description[:60] + "...", category)
        
        console = Console()
        with console.capture() as capture:
            console.print(table)
        
        messages = self.query_one("#messages", RichLog)
        for line in capture.get().split("\n"):
            if line.strip():
                messages.write(line)
        
        messages.write("")
        self.show_message(f"Total tools: {len(self.mcp_server.tools)}", "dim")


def main():
    """Run the Textual REPL."""
    app = HanzoTextualREPL()
    app.run()


if __name__ == "__main__":
    main()