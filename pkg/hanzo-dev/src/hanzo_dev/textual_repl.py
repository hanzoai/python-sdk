"""Beautiful Textual-based REPL interface for Hanzo."""

import contextlib
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from hanzo_mcp.server import HanzoMCPServer
from hanzoai.config import ConfigLoader, RuntimeConfig
from hanzoai.protocols import (
    ModelPricing,
    PermissionMode,
    PermissionPolicy,
    UsageTracker,
)
from hanzoai.session import (
    CompactionConfig,
    Session as HanzoSession,
    compact_session,
    estimate_session_tokens,
)
from rich.console import Console
from rich.markdown import Markdown
from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.css.query import NoMatches
from textual.reactive import reactive
from textual.widgets import Input, Label, RichLog, Static

from .backends import BackendManager
from .command_palette import CommandPalette, CommandSelected
from .command_suggestions import CommandSuggestions
from .llm_client import LLMClient
from .tool_executor import ToolExecutor

# Default pricing for cost display (Claude 3.5 Sonnet tier)
_DEFAULT_PRICING = ModelPricing(
    input_price_per_token=3.0e-6,
    output_price_per_token=15.0e-6,
    cache_creation_price_per_token=3.75e-6,
    cache_read_price_per_token=0.3e-6,
)


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
                style="bright_yellow",
            )
        return Text("")


class ContextIndicator(Static):
    """Shows context usage based on estimate_session_tokens()."""

    context_percent = reactive(100)

    def __init__(self, max_tokens: int = 200_000, **kwargs):
        super().__init__(**kwargs)
        self.max_tokens = max_tokens

    def update_from_session(self, session: HanzoSession) -> None:
        """Recompute percentage from live session token estimate."""
        used = estimate_session_tokens(session)
        remaining = max(0, self.max_tokens - used)
        self.context_percent = int((remaining / self.max_tokens) * 100)

    def render(self) -> Text:
        """Render context indicator."""
        return Text(
            f"Context left until auto-compact: {self.context_percent}%",
            style="dim yellow",
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
        self.fast_mode = False
        self.permission_mode = PermissionMode.Allow

        # hanzoai core wiring
        loader = ConfigLoader.default_for(Path.cwd())
        self.runtime_config: RuntimeConfig = loader.load()
        self.hanzo_session = HanzoSession()
        self.compaction_config = CompactionConfig()
        self._session_path = Path.home() / ".hanzo" / "session.json"
        self._sessions_dir = Path.home() / ".hanzo" / "sessions"

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        # Status bar at top
        yield StatusBar(id="status-bar")

        # Message area
        yield MessageArea()

        # Input area
        with Vertical(id="input-box"):
            yield Input(placeholder="Press up to edit queued messages", id="input")

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

            # Apply model from config if present
            cfg_model = self.runtime_config.get("model")
            if cfg_model and isinstance(cfg_model, str):
                try:
                    self.llm_client.set_model(cfg_model)
                except ValueError:
                    pass

            # Initialize backend manager
            self.backend_manager = BackendManager(self.llm_client)

            # Show backend info
            messages = self.query_one("#messages", RichLog)
            backend_name = self.backend_manager.current_backend
            backend = self.backend_manager.get_backend()

            messages.write(Text(f"● Backend: {backend_name}", style="green"))

            # Show specific info based on backend
            if backend_name == "claude":
                if hasattr(backend, "authenticated") and backend.authenticated:
                    messages.write(
                        Text("● Using Claude personal account", style="cyan")
                    )
                else:
                    messages.write(
                        Text(
                            "● Claude Code (not authenticated - using API)",
                            style="yellow",
                        )
                    )
            elif backend_name == "embedded":
                messages.write(
                    Text(f"● Model: {self.llm_client.current_model}", style="green")
                )

            # Initialize tool executor with backend + permission policy
            self.tool_executor = ToolExecutor(
                self.mcp_server,
                self.backend_manager,
                permission_policy=PermissionPolicy(default_mode=PermissionMode.Allow),
            )

            # Connect to MCP servers from config
            mcp_servers = self.runtime_config.mcp_servers()
            for name, cfg in mcp_servers.items():
                if hasattr(cfg, "command"):
                    cmd = [cfg.command] + list(cfg.args)
                    count = await self.tool_executor.register_mcp_server(
                        name, cmd, env=cfg.env or None,
                    )
                    if count:
                        messages.write(Text(f"● MCP {name}: {count} tools", style="green"))

            # Load persisted session
            if self._session_path.is_file():
                try:
                    self.hanzo_session = HanzoSession.load(self._session_path)
                    est = estimate_session_tokens(self.hanzo_session)
                    messages.write(
                        Text(f"● Restored session: {len(self.hanzo_session.messages)} msgs, ~{est:,} tokens", style="dim")
                    )
                except Exception:
                    self.hanzo_session = HanzoSession()

            # Update context indicator from session
            context_indicator = self.query_one("#permissions", ContextIndicator)
            context_indicator.update_from_session(self.hanzo_session)

            # List available backends
            backends = self.backend_manager.list_backends()
            available = [name for name, avail in backends.items() if avail]
            messages.write(
                Text(f"● Available backends: {', '.join(available)}", style="dim")
            )

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
        from hanzoai.session import ConversationMessage, TextBlock

        # Start thinking animation
        status = self.query_one("#status-bar", StatusBar)
        status.start_thinking()

        try:
            # Track user message in session
            self.hanzo_session.messages.append(ConversationMessage.user_text(message))

            # Execute with tools
            response = await self.tool_executor.execute_with_tools(message)

            # Track assistant response in session
            self.hanzo_session.messages.append(
                ConversationMessage.assistant([TextBlock(text=response or "")])
            )

            # Stop animation
            status.stop_thinking()

            # Update token count on status bar
            if self.tool_executor:
                cum = self.tool_executor.usage_tracker.cumulative_usage()
                status.update_tokens(cum.total_tokens())

            # Show response
            msgs_widget = self.query_one("#messages", RichLog)
            msgs_widget.write("")

            # Format as markdown
            console = Console()
            with console.capture() as capture:
                console.print(Markdown(response))

            for line in capture.get().split("\n"):
                if line.strip():
                    msgs_widget.write(f"● {line}")

            msgs_widget.write("")

            # Update context indicator from real session token estimate
            context_indicator = self.query_one("#permissions", ContextIndicator)
            context_indicator.update_from_session(self.hanzo_session)

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
        messages.write(
            Text(
                "╭─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮",
                style="dim",
            )
        )
        messages.write(
            Text(
                "│ !                                                                                                                           │",
                style="dim",
            )
        )
        messages.write(
            Text(
                "╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯",
                style="dim",
            )
        )

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

    async def execute_tool(
        self, tool_name: str, parameters: Optional[Dict] = None
    ) -> None:
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
            params = {}
            if parameters and any(
                p.get("required", False)
                for p in parameters.get("properties", {}).values()
            ):
                self.show_message(
                    "Tool requires parameters - use CLI for full control", "yellow"
                )

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
            "/help              Show shortcuts",
            "/status            Model, session info, token usage",
            "/cost              Accumulated cost estimate",
            "/clear             Clear session history",
            "/compact           Compact session, keep summary",
            "/model [name]      Show or switch AI model",
            "/permissions [m]   Show/switch permission mode",
            "/fast              Toggle fast/standard mode",
            "/config            Show loaded config files",
            "/memory            Show loaded instruction files",
            "/init              Create starter CLAUDE.md",
            "/resume [path]     Load saved session",
            "/export [file]     Export conversation",
            "/session [list|..]  Manage saved sessions",
            "/plan <prompt>     Planning agent",
            "/solve <prompt>    Multi-approach solver",
            "/code <prompt>     Consensus code review",
            "/auto <prompt>     Autonomous execution",
            "/login             Authenticate via PKCE",
            "/loop <s> <msg>    Run prompt on interval",
            "/backend <name>    Switch backend",
            "/tools             List MCP tools",
            "/remote-control    WebSocket remote bridge",
            "/version           Show version info",
            "/exit              Quit",
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
                self.show_message(
                    "No memorized snippets. Type something and press # to memorize.",
                    "yellow",
                )

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
            if command == "model" and arg:
                if self.backend_manager.current_backend == "embedded":
                    self.llm_client.set_model(arg)
                    self.show_message(f"Model changed to: {arg}", "green")
                else:
                    self.show_message(
                        "Model selection only available for embedded backend", "yellow"
                    )
                return True
            if command == "model" and not arg:
                await self.show_model_selector()
                return True
            if command == "auth":
                await self.handle_auth_command()
                return True
            if command == "backend":
                await self.handle_backend_command(arg)
                return True
            if command == "logout":
                await self.handle_logout_command()
                return True
            if command == "status":
                await self.handle_status_command()
                return True
            if command == "cost":
                await self.handle_cost_command()
                return True
            if command == "compact":
                await self.handle_compact_command()
                return True
            if command == "config":
                await self.handle_config_command()
                return True
            if command == "version":
                await self.handle_version_command()
                return True
            if command == "login":
                await self.handle_login_command()
                return True
            if command == "loop":
                await self.handle_loop_command(arg)
                return True
            if command == "permissions":
                await self.handle_permissions_command(arg)
                return True
            if command == "resume":
                await self.handle_resume_command(arg)
                return True
            if command == "memory":
                await self.handle_memory_command()
                return True
            if command == "init":
                await self.handle_init_command()
                return True
            if command == "export":
                await self.handle_export_command(arg)
                return True
            if command == "session":
                await self.handle_session_command(arg)
                return True
            if command == "plan":
                await self.handle_agent_command("You are a planning agent. Create a detailed plan.", arg, "plan")
                return True
            if command == "solve":
                await self.handle_agent_command("Race multiple approaches. Present the best solution.", arg, "solve")
                return True
            if command == "code":
                await self.handle_agent_command("Implement this with consensus from multiple review passes.", arg, "code")
                return True
            if command == "auto":
                await self.handle_agent_command("Execute this task autonomously. Use tools as needed.", arg, "auto")
                return True
            if command == "fast":
                self.fast_mode = not self.fast_mode
                self.show_message(f"Mode: {'fast' if self.fast_mode else 'standard'}", "cyan")
                return True
            if command == "remote-control":
                self.show_message("Remote control: ws://localhost:9229", "cyan")
                self.show_message("Install websockets and run from CLI REPL for full support.", "yellow")
                return True
            if command == "exit" or command == "quit":
                # Save session before exit
                self._session_path.parent.mkdir(parents=True, exist_ok=True)
                self.hanzo_session.save(self._session_path)
                self.exit()
                return True
            if command == "clear":
                self.hanzo_session = HanzoSession()
                if self.tool_executor:
                    self.tool_executor.reset_context()
                self.action_clear()
                self.show_message("Session cleared.", "green")
                return True
            if command == "help":
                self.action_shortcuts()
                return True
            if command == "tools":
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
            from .voice_mode import VOICE_AVAILABLE, VoiceCommands, VoiceMode

            if not VOICE_AVAILABLE:
                self.show_error(
                    "Voice mode not available. Install: pip install speechrecognition pyttsx3 pyaudio"
                )
                return

            if not hasattr(self, "voice_mode"):
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
                    processed, should_stop = self.voice_commands.process_voice_input(
                        text
                    )

                    if should_stop:
                        self.call_from_thread(self.toggle_voice_mode)
                    elif processed:
                        # Show what was heard
                        self.call_from_thread(
                            self.show_message, f"Heard: {text}", "dim"
                        )
                        # Process the command
                        self.call_from_thread(self.process_voice_command, processed)

                self.voice_mode.start(on_speech)
                self.show_message(
                    "Voice mode activated. Say 'Hey Hanzo' followed by your command.",
                    "green",
                )

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
            with contextlib.suppress(NoMatches):
                self.query_one("#command-suggestions").remove()

            # Create and mount suggestions
            self.command_suggestions = CommandSuggestions(value)
            self.mount(self.command_suggestions, after="#input-box")
        else:
            # Remove suggestions if not typing a command
            with contextlib.suppress(NoMatches):
                self.query_one("#command-suggestions").remove()

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
            if hasattr(backend, "authenticate"):
                self.show_message("Authenticating with Claude...", "yellow")
                try:
                    success = await backend.authenticate()
                    if success:
                        self.show_message(
                            "Successfully authenticated with Claude!", "green"
                        )
                        self.show_message(
                            "You can now use your personal Claude account without API keys.",
                            "cyan",
                        )
                    else:
                        self.show_error("Authentication failed. Please try again.")
                except Exception as e:
                    self.show_error(f"Authentication error: {e}")
            else:
                self.show_message(
                    "Claude backend doesn't support authentication", "yellow"
                )
        else:
            self.show_message(
                f"Authentication not available for {self.backend_manager.current_backend} backend",
                "yellow",
            )
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
                current = (
                    " (current)" if name == self.backend_manager.current_backend else ""
                )
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
                if backend_name == "claude" and hasattr(backend, "authenticated"):
                    if backend.authenticated:
                        self.show_message("Using Claude personal account", "cyan")
                    else:
                        self.show_message(
                            "Not authenticated. Use /auth to login with personal account",
                            "yellow",
                        )

            except ValueError as e:
                self.show_error(str(e))

    async def handle_logout_command(self) -> None:
        """Handle /logout command."""
        backend = self.backend_manager.get_backend()

        if self.backend_manager.current_backend == "claude" and hasattr(
            backend, "logout"
        ):
            await backend.logout()
            self.show_message("Logged out from Claude account", "yellow")
        else:
            self.show_message("No active authentication session", "dim")

    async def handle_status_command(self) -> None:
        """Show model, session info, token usage."""
        messages = self.query_one("#messages", RichLog)
        tracker = self.tool_executor.usage_tracker if self.tool_executor else UsageTracker()
        cum = tracker.cumulative_usage()
        est = estimate_session_tokens(self.hanzo_session)
        model = self.llm_client.current_model if self.llm_client else "n/a"
        provider = self.llm_client.current_provider if self.llm_client else "n/a"
        backend = self.backend_manager.current_backend if self.backend_manager else "n/a"

        messages.write(Text("Status:", style="cyan"))
        messages.write(f"  Backend:            {backend}")
        messages.write(f"  Model:              {model}")
        messages.write(f"  Provider:           {provider}")
        messages.write(f"  Turns:              {tracker.turns}")
        messages.write(f"  Input tokens:       {cum.input_tokens:,}")
        messages.write(f"  Output tokens:      {cum.output_tokens:,}")
        messages.write(f"  Session tokens:     ~{est:,}")
        messages.write(f"  Session messages:   {len(self.hanzo_session.messages)}")
        messages.write(f"  Config files:       {len(self.runtime_config.loaded_entries)}")
        messages.write("")

    async def handle_cost_command(self) -> None:
        """Show accumulated cost estimate."""
        tracker = self.tool_executor.usage_tracker if self.tool_executor else UsageTracker()
        cum = tracker.cumulative_usage()
        cost = _DEFAULT_PRICING.cost(cum)
        self.show_message(
            f"Cost: ${cost:.6f} ({cum.input_tokens:,} in / {cum.output_tokens:,} out, {tracker.turns} turns)",
            "cyan",
        )

    async def handle_compact_command(self) -> None:
        """Compact the session to reclaim context."""
        est_before = estimate_session_tokens(self.hanzo_session)
        result = compact_session(self.hanzo_session, self.compaction_config)
        if result.removed_message_count == 0:
            self.show_message("Session too small to compact.", "yellow")
            return
        self.hanzo_session = result.compacted_session
        est_after = estimate_session_tokens(self.hanzo_session)
        self.show_message(
            f"Compacted: removed {result.removed_message_count} messages, "
            f"{est_before:,} -> {est_after:,} est tokens.",
            "green",
        )
        # Update context indicator
        context_indicator = self.query_one("#permissions", ContextIndicator)
        context_indicator.update_from_session(self.hanzo_session)

    async def handle_config_command(self) -> None:
        """Show loaded configuration files."""
        messages = self.query_one("#messages", RichLog)
        if not self.runtime_config.loaded_entries:
            self.show_message("No config files loaded.", "yellow")
            return
        messages.write(Text("Config:", style="cyan"))
        for entry in self.runtime_config.loaded_entries:
            messages.write(f"  [{entry.source.name}] {entry.path}")
        mcp_servers = self.runtime_config.mcp_servers()
        if mcp_servers:
            messages.write(f"  MCP servers: {', '.join(mcp_servers.keys())}")
        messages.write("")

    async def handle_version_command(self) -> None:
        """Show version info."""
        from hanzoai._version import __version__ as hanzoai_version
        from hanzo_dev import __version__ as dev_version
        messages = self.query_one("#messages", RichLog)
        messages.write(Text("Version:", style="cyan"))
        messages.write(f"  hanzo-dev  {dev_version}")
        messages.write(f"  hanzoai     {hanzoai_version}")
        messages.write("")

    async def handle_login_command(self) -> None:
        """Login via PKCE flow."""
        from hanzoai.auth import HanzoAuth

        auth = HanzoAuth()
        oauth_cfg = self.runtime_config.oauth()

        kwargs: Dict[str, Any] = {}
        if oauth_cfg:
            kwargs["authorize_url"] = oauth_cfg.authorize_url
            kwargs["token_url"] = oauth_cfg.token_url
            kwargs["client_id"] = oauth_cfg.client_id
            if oauth_cfg.scopes:
                kwargs["scopes"] = oauth_cfg.scopes
            if oauth_cfg.callback_port:
                kwargs["redirect_port"] = oauth_cfg.callback_port

        self.show_message("Starting PKCE login flow...", "yellow")
        try:
            token_set = await auth.login_with_pkce(**kwargs)
            self.show_message(f"Logged in. Scopes: {', '.join(token_set.scopes)}", "green")
        except Exception as e:
            self.show_error(f"Login failed: {e}")

    async def handle_loop_command(self, arg: str) -> None:
        """Run a prompt on a recurring interval. Usage: /loop <seconds> <prompt>"""
        import asyncio

        parts = arg.split(maxsplit=1)
        if len(parts) < 2:
            self.show_error("Usage: /loop <seconds> <prompt>")
            return
        try:
            interval = int(parts[0])
        except ValueError:
            self.show_error("Interval must be an integer (seconds).")
            return
        prompt = parts[1]
        self.show_message(f"Looping every {interval}s: {prompt}", "yellow")
        try:
            while True:
                await self.process_chat(prompt)
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            self.show_message("Loop stopped.", "yellow")

    async def handle_permissions_command(self, arg: str) -> None:
        """Show or switch permission mode."""
        modes = {"read-only": PermissionMode.Deny, "workspace-write": PermissionMode.Ask, "full-access": PermissionMode.Allow}
        if not arg:
            current = {v: k for k, v in modes.items()}.get(self.permission_mode, "full-access")
            self.show_message(f"Permission mode: {current}", "cyan")
            self.show_message(f"Options: {', '.join(modes.keys())}", "dim")
            return
        if arg not in modes:
            self.show_error(f"Unknown mode. Use: {', '.join(modes.keys())}")
            return
        self.permission_mode = modes[arg]
        if self.tool_executor:
            self.tool_executor.permission_policy = PermissionPolicy(default_mode=self.permission_mode)
        self.show_message(f"Permission mode: {arg}", "green")

    async def handle_resume_command(self, arg: str) -> None:
        """Load saved session from JSON file."""
        path = Path(arg.strip()) if arg else self._session_path
        if not path.is_file():
            self.show_error(f"No session file at {path}")
            return
        self.hanzo_session = HanzoSession.load(path)
        est = estimate_session_tokens(self.hanzo_session)
        self.show_message(f"Loaded: {len(self.hanzo_session.messages)} messages, ~{est:,} tokens", "green")

    async def handle_memory_command(self) -> None:
        """Show loaded instruction files."""
        messages = self.query_one("#messages", RichLog)
        messages.write(Text("Loaded instruction files:", style="cyan"))
        for entry in self.runtime_config.loaded_entries:
            messages.write(f"  [{entry.source.name}] {entry.path}")
        if not self.runtime_config.loaded_entries:
            messages.write("  (none)")
        messages.write("")

    async def handle_init_command(self) -> None:
        """Create starter CLAUDE.md in cwd."""
        target = Path.cwd() / "CLAUDE.md"
        if target.exists():
            self.show_message(f"Already exists: {target}", "yellow")
            return
        target.write_text("# Project Instructions\n\nAdd project-specific instructions here.\n")
        self.show_message(f"Created {target}", "green")

    async def handle_export_command(self, arg: str) -> None:
        """Export conversation to file."""
        outpath = Path(arg.strip()) if arg else Path("hanzo-export.md")
        lines = [f"# Hanzo Session Export ({datetime.now().isoformat()})\n"]
        for msg in self.hanzo_session.messages:
            role = msg.role.value if hasattr(msg.role, "value") else str(msg.role)
            text = "".join(b.text for b in msg.content if hasattr(b, "text"))
            lines.append(f"## {role}\n\n{text}\n")
        outpath.write_text("\n".join(lines))
        self.show_message(f"Exported {len(self.hanzo_session.messages)} messages to {outpath}", "green")

    async def handle_session_command(self, arg: str) -> None:
        """List or switch saved sessions."""
        self._sessions_dir.mkdir(parents=True, exist_ok=True)
        parts = arg.split(maxsplit=1) if arg else []
        if not parts or parts[0] == "list":
            sessions = sorted(self._sessions_dir.glob("*.json"))
            if not sessions:
                self.show_message("No saved sessions.", "yellow")
                return
            messages = self.query_one("#messages", RichLog)
            for s in sessions:
                messages.write(f"  {s.stem}")
            messages.write("")
            return
        if parts[0] == "switch" and len(parts) > 1:
            target = self._sessions_dir / f"{parts[1]}.json"
            if not target.is_file():
                self.show_error(f"Session not found: {parts[1]}")
                return
            self.hanzo_session = HanzoSession.load(target)
            self.show_message(f"Switched to session: {parts[1]}", "green")
            return
        self.show_error("Usage: /session [list|switch <id>]")

    async def handle_agent_command(self, system_prefix: str, arg: str, label: str) -> None:
        """Send a prompt with a system prefix for agent commands."""
        if not arg:
            self.show_error(f"Usage: /{label} <prompt>")
            return
        prompt = f"{system_prefix}\n\nUser request: {arg}"
        await self.process_chat(prompt)

    async def show_backend_status(self) -> None:
        """Show current backend status."""
        backend_name = self.backend_manager.current_backend
        backend = self.backend_manager.get_backend()

        self.show_message("Backend Status:", "cyan")
        messages = self.query_one("#messages", RichLog)

        messages.write(f"  Current backend: {backend_name}")
        messages.write(f"  Config file: {backend.get_config_file()}")

        if backend_name == "claude":
            auth_status = (
                "Authenticated"
                if hasattr(backend, "authenticated") and backend.authenticated
                else "Not authenticated"
            )
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
            category = tool.__class__.__module__.split(".")[-1]
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
