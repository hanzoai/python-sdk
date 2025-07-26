"""Main REPL implementation for Hanzo MCP testing."""

import asyncio
import json
import os
import sys
from typing import Any, Dict, List, Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from hanzo_mcp.server import HanzoMCPServer
from hanzo_mcp.tools.llm import UnifiedLLMTool
from .llm_client import LLMClient
from .tool_executor import ToolExecutor


class HanzoREPL:
    """Interactive REPL for testing Hanzo MCP tools."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.console = Console()
        self.config = config or {}
        self.mcp_server = None
        self.llm_client = None
        self.tool_executor = None
        self.session = None
        self.history_file = os.path.expanduser("~/.hanzo_repl_history")
        
        # REPL commands
        self.commands = {
            "/help": self.show_help,
            "/tools": self.list_tools,
            "/exit": self.exit_repl,
            "/quit": self.exit_repl,
            "/clear": self.clear_screen,
            "/providers": self.list_providers,
            "/model": self.set_model,
            "/context": self.show_context,
            "/reset": self.reset_context,
            "/test": self.run_tests,
        }
        
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
        available_providers = self.llm_client.get_available_providers()
        
        if not available_providers:
            self.console.print("[bold red]No LLM API keys detected![/bold red]")
            self.console.print("Please set one of the following environment variables:")
            self.console.print("- OPENAI_API_KEY")
            self.console.print("- ANTHROPIC_API_KEY")
            self.console.print("- GROQ_API_KEY")
            self.console.print("- etc.")
            sys.exit(1)
            
        self.console.print(f"[green]Available providers: {', '.join(available_providers)}[/green]")
        
        # Initialize tool executor
        self.tool_executor = ToolExecutor(self.mcp_server, self.llm_client)
        
        # Initialize prompt session
        tool_names = [tool.name for tool in self.mcp_server.tools.values()]
        completer = WordCompleter(
            list(self.commands.keys()) + tool_names,
            ignore_case=True
        )
        self.session = PromptSession(
            history=FileHistory(self.history_file),
            auto_suggest=AutoSuggestFromHistory(),
            completer=completer
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
                user_input = await self.session.prompt_async(
                    "hanzo> ",
                    multiline=False
                )
                
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

- **/help** - Show this help message
- **/tools** - List available MCP tools
- **/providers** - List available LLM providers
- **/model <model>** - Set the LLM model to use
- **/context** - Show current conversation context
- **/reset** - Reset conversation context
- **/test** - Run MCP tool tests
- **/clear** - Clear the screen
- **/exit** or **/quit** - Exit the REPL

## Usage

Simply type your message and the REPL will:
1. Send it to the configured LLM
2. Execute any MCP tools the LLM requests
3. Display the results

## Examples

- "Read the file README.md"
- "Search for Python files containing 'async'"
- "Run the command 'ls -la'"
- "Create a new file called test.txt with 'Hello World'"
"""
        self.console.print(Markdown(help_text))
    
    async def list_tools(self, _):
        """List available MCP tools."""
        table = Table(title="Available MCP Tools")
        table.add_column("Tool", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")
        table.add_column("Category", style="green")
        
        for tool_name, tool in sorted(self.mcp_server.tools.items()):
            category = tool.__class__.__module__.split('.')[-1]
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
                ", ".join(provider_models[:3]) + ("..." if len(provider_models) > 3 else ""),
                status
            )
        
        self.console.print(table)
        self.console.print(f"\nCurrent model: [bold cyan]{self.llm_client.current_model}[/bold cyan]")
    
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
        
        self.console.print(Panel(
            json.dumps(context, indent=2),
            title="Conversation Context",
            border_style="blue"
        ))
    
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
    
    async def clear_screen(self, _):
        """Clear the screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    async def exit_repl(self, _):
        """Exit the REPL."""
        self.console.print("[yellow]Goodbye![/yellow]")
        sys.exit(0)


async def main():
    """Main entry point."""
    repl = HanzoREPL()
    await repl.run()


if __name__ == "__main__":
    asyncio.run(main())