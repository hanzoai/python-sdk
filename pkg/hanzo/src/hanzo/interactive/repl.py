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
        cli_commands = ["chat", "ask", "agent", "node", "mcp", "network", 
                       "auth", "config", "tools", "miner", "serve", "net", 
                       "dev", "router"]
        completer = WordCompleter(
            list(self.commands.keys()) + cli_commands,
            ignore_case=True,
        )

        while self.running:
            try:
                # Get input with simple prompt
                command = await self.session.prompt_async(
                    "> ", completer=completer
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
                elif cmd in ["chat", "ask", "agent", "node", "mcp", "network", "auth", "config", "tools", "miner", "serve", "net", "dev", "router"]:
                    # Execute known CLI commands
                    await self.execute_command(cmd, args)
                else:
                    # Treat as chat message if not a known command
                    await self.chat_with_ai(command)

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
- `node status` - Check node status
- `mcp tools` - List MCP tools
- `network agents` - List network agents

## Examples:
```
hanzo> chat How do I create a Python web server?
hanzo> agent list
hanzo> node start --models llama-3.2-3b
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
            "node": await self.check_node_status(),
            "agents": await self.count_agents(),
            "auth": self.check_auth_status(),
        }

        self.console.print("[cyan]System Status:[/cyan]")
        self.console.print(f"  Node: {status['node']}")
        self.console.print(f"  Agents: {status['agents']}")
        self.console.print(f"  Auth: {status['auth']}")

    async def execute_command(self, cmd: str, args: str):
        """Execute a CLI command."""
        import os
        import sys
        import shutil
        import subprocess

        # Find hanzo executable
        hanzo_cmd = shutil.which("hanzo")
        if not hanzo_cmd:
            # Try using Python module directly
            hanzo_cmd = sys.executable
            argv = [hanzo_cmd, "-m", "hanzo", cmd]
        else:
            argv = [hanzo_cmd, cmd]
        
        if args:
            import shlex
            argv.extend(shlex.split(args))

        # Execute as subprocess to avoid context issues
        try:
            result = subprocess.run(
                argv,
                capture_output=True,
                text=True,
                timeout=30,
                env=os.environ.copy()  # Pass environment variables
            )
            
            if result.stdout:
                self.console.print(result.stdout.rstrip())
            if result.stderr and result.returncode != 0:
                self.console.print(f"[red]{result.stderr.rstrip()}[/red]")
                
        except subprocess.TimeoutExpired:
            self.console.print("[red]Command timed out[/red]")
        except FileNotFoundError:
            self.console.print("[red]Command not found. Make sure 'hanzo' is installed.[/red]")
        except Exception as e:
            self.console.print(f"[red]Command error: {e}[/red]")

    async def check_node_status(self) -> str:
        """Check if node is running."""
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
    
    async def chat_with_ai(self, message: str):
        """Chat with AI when user types natural language."""
        # For natural language input, try to use it as a chat message
        # Default to cloud mode to avoid needing local server
        await self.execute_command("ask", f"--cloud {message}")
