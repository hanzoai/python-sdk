"""Main REPL implementation for Hanzo MCP testing."""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from hanzo_mcp.server import HanzoMCPServer
from hanzoai.config import ConfigLoader, RuntimeConfig
from hanzoai.protocols import ModelPricing, PermissionMode, PermissionPolicy, UsageTracker
from hanzoai.session import (
    CompactionConfig,
    Session as HanzoSession,
    compact_session,
    estimate_session_tokens,
    should_compact,
)
from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from .llm_client import LLMClient
from .tool_executor import ToolExecutor

__version__ = "0.1.0"

# Default pricing for cost estimates (Claude 3.5 Sonnet tier)
_DEFAULT_PRICING = ModelPricing(
    input_price_per_token=3.0e-6,
    output_price_per_token=15.0e-6,
    cache_creation_price_per_token=3.75e-6,
    cache_read_price_per_token=0.3e-6,
)


class HanzoREPL:
    """Interactive REPL for testing Hanzo MCP tools."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.console = Console()
        self.config = config or {}
        self.mcp_server = None
        self.llm_client = None
        self.tool_executor = None
        self.session = None
        self.history_file = os.path.expanduser("~/.hanzo_dev_history")

        # Hierarchical config
        self.runtime_config: RuntimeConfig = self._load_runtime_config()

        # Session persistence
        self._session_path = Path.home() / ".hanzo" / "session.json"
        self._sessions_dir = Path.home() / ".hanzo" / "sessions"
        self.hanzo_session = HanzoSession()
        self.compaction_config = CompactionConfig()

        # Mode flags
        self.permission_mode = PermissionMode.Allow
        self.fast_mode = False

        # REPL commands
        self.commands = {
            "/help": self.show_help,
            "/tools": self.list_tools,
            "/exit": self.exit_repl,
            "/quit": self.exit_repl,
            "/clear": self.cmd_clear,
            "/providers": self.list_providers,
            "/model": self.set_model,
            "/permissions": self.cmd_permissions,
            "/context": self.show_context,
            "/reset": self.reset_context,
            "/test": self.run_tests,
            "/status": self.show_status,
            "/cost": self.show_cost,
            "/compact": self.run_compact,
            "/config": self.show_config,
            "/version": self.show_version,
            "/login": self.do_login,
            "/loop": self.do_loop,
            "/resume": self.cmd_resume,
            "/memory": self.cmd_memory,
            "/init": self.cmd_init,
            "/export": self.cmd_export,
            "/session": self.cmd_session,
            "/plan": self.cmd_plan,
            "/solve": self.cmd_solve,
            "/code": self.cmd_code,
            "/auto": self.cmd_auto,
            "/fast": self.cmd_fast,
            "/remote-control": self.cmd_remote_control,
        }

    def _load_runtime_config(self) -> RuntimeConfig:
        """Load hierarchical config via ConfigLoader."""
        loader = ConfigLoader.default_for(Path.cwd())
        return loader.load()

    async def initialize(self):
        """Initialize MCP server and LLM client."""
        self.console.print("[bold green]Initializing Hanzo REPL...[/bold green]")

        # Initialize MCP server
        self.console.print("Loading MCP server...")
        self.mcp_server = HanzoMCPServer()
        await self.mcp_server.initialize()

        # Initialize LLM client
        self.console.print("Detecting available LLM providers...")
        self.llm_client = LLMClient()

        # Apply model from config if present
        cfg_model = self.runtime_config.get("model")
        if cfg_model and isinstance(cfg_model, str):
            try:
                self.llm_client.set_model(cfg_model)
                self.console.print(f"[green]Model from config: {cfg_model}[/green]")
            except ValueError:
                pass

        available_providers = self.llm_client.get_available_providers()

        if not available_providers:
            self.console.print("[bold red]No LLM API keys detected![/bold red]")
            self.console.print("Please set one of the following environment variables:")
            self.console.print("- OPENAI_API_KEY")
            self.console.print("- ANTHROPIC_API_KEY")
            self.console.print("- GROQ_API_KEY")
            self.console.print("- etc.")
            sys.exit(1)

        self.console.print(
            f"[green]Available providers: {', '.join(available_providers)}[/green]"
        )

        # Initialize tool executor with permission policy
        self.tool_executor = ToolExecutor(
            self.mcp_server,
            self.llm_client,
            permission_policy=PermissionPolicy(default_mode=PermissionMode.Allow),
        )

        # Connect to MCP servers defined in config
        mcp_servers = self.runtime_config.mcp_servers()
        for name, cfg in mcp_servers.items():
            if hasattr(cfg, "command"):
                cmd = [cfg.command] + list(cfg.args)
                count = await self.tool_executor.register_mcp_server(
                    name, cmd, env=cfg.env or None,
                )
                if count:
                    self.console.print(f"[green]MCP {name}: {count} tools[/green]")

        # Load persisted session if exists
        if self._session_path.is_file():
            try:
                self.hanzo_session = HanzoSession.load(self._session_path)
                est = estimate_session_tokens(self.hanzo_session)
                self.console.print(
                    f"[dim]Restored session: {len(self.hanzo_session.messages)} messages, ~{est:,} tokens[/dim]"
                )
            except Exception:
                self.hanzo_session = HanzoSession()

        # Initialize prompt session
        tool_names = [tool.name for tool in self.mcp_server.tools.values()]
        completer = WordCompleter(
            list(self.commands.keys()) + tool_names, ignore_case=True
        )
        self.session = PromptSession(
            history=FileHistory(self.history_file),
            auto_suggest=AutoSuggestFromHistory(),
            completer=completer,
        )

        self.console.print("[bold green]REPL initialized successfully![/bold green]")
        self.console.print(f"Using model: [cyan]{self.llm_client.current_model}[/cyan]")
        self.console.print("Type [bold]/help[/bold] for available commands.")

    async def run(self):
        """Run the main REPL loop."""
        await self.initialize()

        while True:
            try:
                # Get user input
                user_input = await self.session.prompt_async("hanzo> ", multiline=False)

                if not user_input.strip():
                    continue

                # Check for commands
                if user_input.startswith("/"):
                    command = user_input.split()[0]
                    if command in self.commands:
                        await self.commands[command](user_input)
                    else:
                        self.console.print(f"[red]Unknown command: {command}[/red]")
                    continue

                # Process as chat with MCP tools
                await self.process_chat(user_input)

            except KeyboardInterrupt:
                self.console.print("\n[yellow]Use /exit to quit[/yellow]")
            except EOFError:
                await self.exit_repl("")
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")
                if self.config.get("debug"):
                    self.console.print_exception()

    async def process_chat(self, message: str):
        """Process a chat message with MCP tool support."""
        self.console.print()

        # Send to LLM with available tools
        try:
            response = await self.tool_executor.execute_with_tools(message)

            # Display response
            if isinstance(response, str):
                self.console.print(Markdown(response))
            else:
                self.console.print(response)

        except Exception as e:
            self.console.print(f"[red]Error processing chat: {e}[/red]")
            if self.config.get("debug"):
                self.console.print_exception()

    async def show_help(self, _):
        """Show help information."""
        help_text = """
# Hanzo REPL Commands

## Session
- **/clear** - Clear session history (new session)
- **/compact** - Compact session keeping summary
- **/resume [path]** - Load saved session from JSON
- **/session [list|switch id]** - Manage saved sessions
- **/export [file]** - Export conversation to file
- **/memory** - Show loaded instruction files
- **/init** - Create starter CLAUDE.md in cwd

## Model & Config
- **/model [name]** - Show or switch active model
- **/permissions [mode]** - Show/switch permission mode
- **/config** - Show loaded configuration files
- **/fast** - Toggle fast/standard mode
- **/providers** - List available LLM providers
- **/status** - Model, session info, token usage
- **/cost** - Accumulated cost estimate
- **/version** - Show version info

## Agents
- **/plan [prompt]** - Planning agent
- **/solve [prompt]** - Multi-approach solver
- **/code [prompt]** - Consensus code review
- **/auto [prompt]** - Autonomous execution

## Other
- **/login** - Authenticate via PKCE flow
- **/loop <sec> <prompt>** - Run prompt on interval
- **/tools** - List available MCP tools
- **/context** - Show conversation context
- **/reset** - Reset conversation context
- **/test** - Run MCP tool tests
- **/remote-control** - Start WebSocket remote bridge
- **/exit** or **/quit** - Exit the REPL
"""
        self.console.print(Markdown(help_text))

    async def list_tools(self, _):
        """List available MCP tools."""
        table = Table(title="Available MCP Tools")
        table.add_column("Tool", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")
        table.add_column("Category", style="green")

        for tool_name, tool in sorted(self.mcp_server.tools.items()):
            category = tool.__class__.__module__.split(".")[-1]
            table.add_row(tool_name, tool.description[:60] + "...", category)

        self.console.print(table)
        self.console.print(f"\nTotal tools: [bold]{len(self.mcp_server.tools)}[/bold]")

    async def list_providers(self, _):
        """List available LLM providers."""
        providers = self.llm_client.get_available_providers()
        models = self.llm_client.get_available_models()

        table = Table(title="Available LLM Providers")
        table.add_column("Provider", style="cyan")
        table.add_column("Models", style="white")
        table.add_column("Status", style="green")

        for provider in providers:
            provider_models = [m for m in models if m.startswith(provider)]
            status = "Active" if provider == self.llm_client.current_provider else ""
            table.add_row(
                provider,
                ", ".join(provider_models[:3])
                + ("..." if len(provider_models) > 3 else ""),
                status,
            )

        self.console.print(table)
        self.console.print(
            f"\nCurrent model: [bold cyan]{self.llm_client.current_model}[/bold cyan]"
        )

    async def set_model(self, command: str):
        """Set the LLM model to use."""
        parts = command.split(maxsplit=1)
        if len(parts) < 2:
            self.console.print("[red]Usage: /model <model_name>[/red]")
            self.console.print("Available models:")
            for model in self.llm_client.get_available_models():
                self.console.print(f"  - {model}")
            return

        model = parts[1]
        try:
            self.llm_client.set_model(model)
            self.console.print(f"[green]Model set to: {model}[/green]")
        except ValueError as e:
            self.console.print(f"[red]Error: {e}[/red]")

    async def show_context(self, _):
        """Show current conversation context."""
        context = self.tool_executor.get_context()
        if not context:
            self.console.print("[yellow]No conversation context yet[/yellow]")
            return

        self.console.print(
            Panel(
                json.dumps(context, indent=2),
                title="Conversation Context",
                border_style="blue",
            )
        )

    async def reset_context(self, _):
        """Reset conversation context."""
        self.tool_executor.reset_context()
        self.console.print("[green]Conversation context reset[/green]")

    async def run_tests(self, _):
        """Run MCP tool tests."""
        self.console.print("[bold]Running MCP tool tests...[/bold]")

        # Import and run tests
        from .tests import run_tool_tests

        await run_tool_tests(self.console, self.mcp_server, self.tool_executor)

    async def cmd_clear(self, _):
        """Clear session history and start fresh."""
        self.hanzo_session = HanzoSession()
        self.tool_executor.reset_context()
        os.system("cls" if os.name == "nt" else "clear")  # noqa: S605
        self.console.print("[green]Session cleared.[/green]")

    async def cmd_permissions(self, command: str):
        """Show or switch permission mode."""
        parts = command.split(maxsplit=1)
        modes = {"read-only": PermissionMode.Deny, "workspace-write": PermissionMode.Ask, "full-access": PermissionMode.Allow}
        if len(parts) < 2:
            current = {v: k for k, v in modes.items()}.get(self.permission_mode, "full-access")
            self.console.print(f"[cyan]Permission mode:[/cyan] {current}")
            self.console.print(f"  Options: {', '.join(modes.keys())}")
            return
        name = parts[1].strip()
        if name not in modes:
            self.console.print(f"[red]Unknown mode. Use: {', '.join(modes.keys())}[/red]")
            return
        self.permission_mode = modes[name]
        self.tool_executor.permission_policy = PermissionPolicy(default_mode=self.permission_mode)
        self.console.print(f"[green]Permission mode: {name}[/green]")

    async def cmd_resume(self, command: str):
        """Load saved session from JSON file."""
        parts = command.split(maxsplit=1)
        path = Path(parts[1].strip()) if len(parts) > 1 else self._session_path
        if not path.is_file():
            self.console.print(f"[red]No session file at {path}[/red]")
            return
        self.hanzo_session = HanzoSession.load(path)
        est = estimate_session_tokens(self.hanzo_session)
        self.console.print(f"[green]Loaded: {len(self.hanzo_session.messages)} messages, ~{est:,} tokens[/green]")

    async def cmd_memory(self, _):
        """Show loaded instruction files."""
        self.console.print("[cyan]Loaded instruction files:[/cyan]")
        for entry in self.runtime_config.loaded_entries:
            self.console.print(f"  [{entry.source.name}] {entry.path}")
        if not self.runtime_config.loaded_entries:
            self.console.print("  [dim]None[/dim]")

    async def cmd_init(self, _):
        """Create starter CLAUDE.md in cwd."""
        target = Path.cwd() / "CLAUDE.md"
        if target.exists():
            self.console.print(f"[yellow]Already exists: {target}[/yellow]")
            return
        target.write_text("# Project Instructions\n\nAdd project-specific instructions here.\n")
        self.console.print(f"[green]Created {target}[/green]")

    async def cmd_export(self, command: str):
        """Export conversation to file."""
        parts = command.split(maxsplit=1)
        outpath = Path(parts[1].strip()) if len(parts) > 1 else Path("hanzo-export.md")
        lines = [f"# Hanzo Session Export ({datetime.now().isoformat()})\n"]
        for msg in self.hanzo_session.messages:
            role = msg.role.value if hasattr(msg.role, "value") else str(msg.role)
            text = "".join(b.text for b in msg.content if hasattr(b, "text"))
            lines.append(f"## {role}\n\n{text}\n")
        outpath.write_text("\n".join(lines))
        self.console.print(f"[green]Exported {len(self.hanzo_session.messages)} messages to {outpath}[/green]")

    async def cmd_session(self, command: str):
        """List or switch saved sessions."""
        parts = command.split(maxsplit=2)
        self._sessions_dir.mkdir(parents=True, exist_ok=True)
        if len(parts) < 2 or parts[1] == "list":
            sessions = sorted(self._sessions_dir.glob("*.json"))
            if not sessions:
                self.console.print("[yellow]No saved sessions.[/yellow]")
                return
            for s in sessions:
                self.console.print(f"  {s.stem}")
            return
        if parts[1] == "switch" and len(parts) > 2:
            target = self._sessions_dir / f"{parts[2]}.json"
            if not target.is_file():
                self.console.print(f"[red]Session not found: {parts[2]}[/red]")
                return
            self.hanzo_session = HanzoSession.load(target)
            self.console.print(f"[green]Switched to session: {parts[2]}[/green]")
            return
        self.console.print("[red]Usage: /session [list|switch <id>][/red]")

    async def _agent_chat(self, system_prefix: str, command: str, label: str):
        """Send a prompt with a system prefix for agent commands."""
        parts = command.split(maxsplit=1)
        if len(parts) < 2:
            self.console.print(f"[red]Usage: /{label} <prompt>[/red]")
            return
        prompt = f"{system_prefix}\n\nUser request: {parts[1]}"
        await self.process_chat(prompt)

    async def cmd_plan(self, command: str):
        """Planning agent."""
        await self._agent_chat("You are a planning agent. Create a detailed plan.", command, "plan")

    async def cmd_solve(self, command: str):
        """Multi-approach solver."""
        await self._agent_chat("Race multiple approaches. Present the best solution.", command, "solve")

    async def cmd_code(self, command: str):
        """Consensus code review."""
        await self._agent_chat("Implement this with consensus from multiple review passes.", command, "code")

    async def cmd_auto(self, command: str):
        """Autonomous execution."""
        await self._agent_chat("Execute this task autonomously. Use tools as needed.", command, "auto")

    async def cmd_fast(self, _):
        """Toggle fast/standard mode."""
        self.fast_mode = not self.fast_mode
        state = "fast" if self.fast_mode else "standard"
        self.console.print(f"[cyan]Mode: {state}[/cyan]")

    async def cmd_remote_control(self, _):
        """Start WebSocket server for remote control."""
        try:
            import websockets  # noqa: F401
        except ImportError:
            self.console.print("[red]Install websockets: pip install websockets[/red]")
            return
        port = 9229
        self.console.print(f"[cyan]Remote control bridge: ws://localhost:{port}[/cyan]")
        self.console.print("[yellow]Send JSON messages: {{\"type\": \"prompt\", \"text\": \"...\"}}[/yellow]")
        self.console.print("[dim]Press Ctrl+C to stop.[/dim]")

        async def handler(ws):
            async for raw in ws:
                try:
                    msg = json.loads(raw)
                    if msg.get("type") == "prompt":
                        await self.process_chat(msg["text"])
                        await ws.send(json.dumps({"type": "done"}))
                except Exception as e:
                    await ws.send(json.dumps({"type": "error", "message": str(e)}))

        import websockets
        try:
            async with websockets.serve(handler, "localhost", port):
                await asyncio.Future()  # run forever
        except KeyboardInterrupt:
            self.console.print("[yellow]Remote control stopped.[/yellow]")

    async def show_status(self, _):
        """Show model, session info, and token usage."""
        tracker = self.tool_executor.usage_tracker if self.tool_executor else UsageTracker()
        cum = tracker.cumulative_usage()
        est_tokens = estimate_session_tokens(self.hanzo_session)

        table = Table(title="Status")
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="white")
        table.add_row("Model", self.llm_client.current_model if self.llm_client else "n/a")
        table.add_row("Provider", self.llm_client.current_provider if self.llm_client else "n/a")
        table.add_row("Turns", str(tracker.turns))
        table.add_row("Input tokens", f"{cum.input_tokens:,}")
        table.add_row("Output tokens", f"{cum.output_tokens:,}")
        table.add_row("Session tokens (est)", f"{est_tokens:,}")
        table.add_row("Session messages", str(len(self.hanzo_session.messages)))
        table.add_row("Config files loaded", str(len(self.runtime_config.loaded_entries)))
        self.console.print(table)

    async def show_cost(self, _):
        """Show accumulated cost estimate."""
        tracker = self.tool_executor.usage_tracker if self.tool_executor else UsageTracker()
        cum = tracker.cumulative_usage()
        cost = _DEFAULT_PRICING.cost(cum)
        self.console.print(
            f"[cyan]Cost estimate:[/cyan] ${cost:.6f} "
            f"({cum.input_tokens:,} in / {cum.output_tokens:,} out, {tracker.turns} turns)"
        )

    async def run_compact(self, _):
        """Compact the session to reclaim context."""
        est = estimate_session_tokens(self.hanzo_session)
        result = compact_session(self.hanzo_session, self.compaction_config)
        if result.removed_message_count == 0:
            self.console.print("[yellow]Session too small to compact.[/yellow]")
            return
        self.hanzo_session = result.compacted_session
        new_est = estimate_session_tokens(self.hanzo_session)
        self.console.print(
            f"[green]Compacted: removed {result.removed_message_count} messages, "
            f"{est:,} -> {new_est:,} est tokens.[/green]"
        )

    async def show_config(self, _):
        """Show loaded configuration."""
        if not self.runtime_config.loaded_entries:
            self.console.print("[yellow]No config files loaded.[/yellow]")
            return
        for entry in self.runtime_config.loaded_entries:
            self.console.print(f"  [{entry.source.name}] {entry.path}")
        mcp_servers = self.runtime_config.mcp_servers()
        if mcp_servers:
            self.console.print(f"\n  MCP servers: {', '.join(mcp_servers.keys())}")

    async def show_version(self, _):
        """Show version info."""
        from hanzoai._version import __version__ as hanzoai_version
        self.console.print(f"  hanzo-dev  {__version__}")
        self.console.print(f"  hanzoai     {hanzoai_version}")

    async def do_login(self, _):
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

        self.console.print("[yellow]Starting PKCE login flow...[/yellow]")
        try:
            token_set = await auth.login_with_pkce(**kwargs)
            self.console.print(f"[green]Logged in. Scopes: {', '.join(token_set.scopes)}[/green]")
        except Exception as e:
            self.console.print(f"[red]Login failed: {e}[/red]")

    async def do_loop(self, command: str):
        """Run a prompt on a recurring interval. Usage: /loop <seconds> <prompt>"""
        parts = command.split(maxsplit=2)
        if len(parts) < 3:
            self.console.print("[red]Usage: /loop <seconds> <prompt>[/red]")
            return
        try:
            interval = int(parts[1])
        except ValueError:
            self.console.print("[red]Interval must be an integer (seconds).[/red]")
            return
        prompt = parts[2]
        self.console.print(f"[yellow]Looping every {interval}s: {prompt}[/yellow]")
        try:
            while True:
                await self.process_chat(prompt)
                await asyncio.sleep(interval)
        except KeyboardInterrupt:
            self.console.print("[yellow]Loop stopped.[/yellow]")

    async def exit_repl(self, _):
        """Exit the REPL, saving session."""
        # Persist session
        self._session_path.parent.mkdir(parents=True, exist_ok=True)
        self.hanzo_session.save(self._session_path)
        self.console.print("[yellow]Goodbye![/yellow]")
        sys.exit(0)


async def main():
    """Main entry point."""
    repl = HanzoREPL()
    await repl.run()


if __name__ == "__main__":
    asyncio.run(main())
