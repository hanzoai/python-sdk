"""Interactive REPL for Hanzo CLI."""

from typing import Optional
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory


class HanzoREPL:
    """Interactive REPL for Hanzo CLI."""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.session = PromptSession(
            history=FileHistory(".hanzo_repl_history"),
            auto_suggest=AutoSuggestFromHistory(),
        )
        self.commands = {
            "help": self.show_help,
            "exit": self.exit_repl,
            "quit": self.exit_repl,
            "clear": self.clear_screen,
            "status": self.show_status,
        }
        self.running = False

    async def run(self):
        """Run the REPL."""
        self.running = True
        # Don't print welcome message here since it's already printed in cli.py

        # Set up command completer
        completer = WordCompleter(
            list(self.commands.keys()) + ["chat", "agent", "cluster", "mcp", "network"],
            ignore_case=True,
        )

        while self.running:
            try:
                # Get input
                command = await self.session.prompt_async(
                    "hanzo> ", completer=completer
                )

                if not command.strip():
                    continue

                # Parse command
                parts = command.strip().split(maxsplit=1)
                cmd = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""

                # Execute command
                if cmd in self.commands:
                    await self.commands[cmd](args)
                else:
                    await self.execute_command(cmd, args)

            except KeyboardInterrupt:
                continue
            except EOFError:
                break
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")

    async def show_help(self, args: str = ""):
        """Show help message."""
        help_text = """
# Hanzo Interactive Mode

## Built-in Commands:
- `help` - Show this help message
- `exit/quit` - Exit interactive mode
- `clear` - Clear the screen
- `status` - Show system status

## CLI Commands:
All Hanzo CLI commands are available:
- `chat <message>` - Chat with AI
- `agent start` - Start an agent
- `cluster status` - Check cluster status
- `mcp tools` - List MCP tools
- `network agents` - List network agents

## Examples:
```
hanzo> chat How do I create a Python web server?
hanzo> agent list
hanzo> cluster start --models llama-3.2-3b
hanzo> mcp run read_file --arg path=README.md
```

## Tips:
- Use Tab for command completion
- Use ↑/↓ for command history
- Use Ctrl+R for reverse search
"""
        self.console.print(Markdown(help_text))

    def exit_repl(self, args: str = ""):
        """Exit the REPL."""
        self.running = False
        self.console.print("\n[yellow]Goodbye![/yellow]")

    def clear_screen(self, args: str = ""):
        """Clear the screen."""
        self.console.clear()

    async def show_status(self, args: str = ""):
        """Show system status."""
        status = {
            "cluster": await self.check_cluster_status(),
            "agents": await self.count_agents(),
            "auth": self.check_auth_status(),
        }

        self.console.print("[cyan]System Status:[/cyan]")
        self.console.print(f"  Cluster: {status['cluster']}")
        self.console.print(f"  Agents: {status['agents']}")
        self.console.print(f"  Auth: {status['auth']}")

    async def execute_command(self, cmd: str, args: str):
        """Execute a CLI command."""
        # Import here to avoid circular imports
        import sys

        import click

        from .. import cli

        # Build command line
        argv = [cmd]
        if args:
            import shlex

            argv.extend(shlex.split(args))

        # Create a new context
        try:
            # Save original argv
            orig_argv = sys.argv
            sys.argv = ["hanzo"] + argv

            # Execute command
            ctx = click.Context(cli.cli)
            cli.cli.invoke(ctx)

        except SystemExit:
            # Catch exit from commands
            pass
        except Exception as e:
            self.console.print(f"[red]Command error: {e}[/red]")
        finally:
            # Restore argv
            sys.argv = orig_argv

    async def check_cluster_status(self) -> str:
        """Check if cluster is running."""
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8000/health", timeout=1.0)
                return "running" if response.status_code == 200 else "not responding"
        except Exception:
            return "not running"

    async def count_agents(self) -> int:
        """Count running agents."""
        # This would check actual agent status
        return 0

    def check_auth_status(self) -> str:
        """Check authentication status."""
        import os

        if os.environ.get("HANZO_API_KEY"):
            return "authenticated (API key)"
        elif (Path.home() / ".hanzo" / "auth.json").exists():
            return "authenticated (saved)"
        else:
            return "not authenticated"
