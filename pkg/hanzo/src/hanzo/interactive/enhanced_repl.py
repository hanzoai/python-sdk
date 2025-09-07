"""Enhanced REPL with model selection and authentication."""

import os
import json
import httpx
import asyncio
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.formatted_text import HTML

try:
    from ..tools.detector import ToolDetector, AITool
except ImportError:
    ToolDetector = None
    AITool = None

try:
    from .model_selector import QuickModelSelector, BackgroundTaskManager
except ImportError:
    QuickModelSelector = None
    BackgroundTaskManager = None

try:
    from .todo_manager import TodoManager
except ImportError:
    TodoManager = None


class EnhancedHanzoREPL:
    """Enhanced REPL with model selection and authentication."""

    # Available models
    MODELS = {
        # OpenAI
        "gpt-4": "OpenAI GPT-4",
        "gpt-4-turbo": "OpenAI GPT-4 Turbo",
        "gpt-3.5-turbo": "OpenAI GPT-3.5 Turbo",
        
        # Anthropic
        "claude-3-opus": "Anthropic Claude 3 Opus",
        "claude-3-sonnet": "Anthropic Claude 3 Sonnet", 
        "claude-3-haiku": "Anthropic Claude 3 Haiku",
        "claude-2.1": "Anthropic Claude 2.1",
        
        # Google
        "gemini-pro": "Google Gemini Pro",
        "gemini-pro-vision": "Google Gemini Pro Vision",
        
        # Meta
        "llama2-70b": "Meta Llama 2 70B",
        "llama2-13b": "Meta Llama 2 13B",
        "llama2-7b": "Meta Llama 2 7B",
        "codellama-34b": "Meta Code Llama 34B",
        
        # Mistral
        "mistral-medium": "Mistral Medium",
        "mistral-small": "Mistral Small",
        "mixtral-8x7b": "Mixtral 8x7B",
        
        # Local models
        "local:llama2": "Local Llama 2",
        "local:mistral": "Local Mistral",
        "local:phi-2": "Local Phi-2",
    }
    
    def get_all_models(self):
        """Get all available models including detected tools."""
        models = dict(self.MODELS)
        
        # Add detected tools as models
        if self.detected_tools:
            for tool in self.detected_tools:
                models[f"tool:{tool.name}"] = f"{tool.display_name} (Tool)"
        
        return models

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.config_dir = Path.home() / ".hanzo"
        self.config_file = self.config_dir / "config.json"
        self.auth_file = self.config_dir / "auth.json"
        
        # Load configuration
        self.config = self.load_config()
        self.auth = self.load_auth()
        
        # Initialize tool detector
        self.tool_detector = ToolDetector(console) if ToolDetector else None
        self.detected_tools = []
        self.current_tool = None
        self.failed_tools = set()  # Track tools that have failed this session
        
        # Initialize background task manager
        self.task_manager = BackgroundTaskManager(console) if BackgroundTaskManager else None
        
        # Initialize todo manager
        self.todo_manager = TodoManager(console) if TodoManager else None
        
        # Detect available tools and set default
        if self.tool_detector:
            self.detected_tools = self.tool_detector.detect_all()
            default_tool = self.tool_detector.get_default_tool()
            
            # If Claude Code is available, use it as default
            if default_tool:
                self.current_model = f"tool:{default_tool.name}"
                self.current_tool = default_tool
                self.console.print(f"[green]✓ Detected {default_tool.display_name} as default AI assistant[/green]")
            else:
                # Fallback to regular models
                self.current_model = self.config.get("default_model", "gpt-3.5-turbo")
        else:
            # No tool detector, use regular models
            self.current_model = self.config.get("default_model", "gpt-3.5-turbo")
        
        # Setup session
        self.session = PromptSession(
            history=FileHistory(str(self.config_dir / ".repl_history")),
            auto_suggest=AutoSuggestFromHistory(),
        )
        
        # Commands
        self.commands = {
            "help": self.show_help,
            "exit": self.exit_repl,
            "quit": self.exit_repl,
            "clear": self.clear_screen,
            "status": self.show_status,
            "model": self.change_model,
            "models": self.list_models,
            "tools": self.list_tools,
            "agents": self.list_tools,  # Alias for tools
            "login": self.login,
            "logout": self.logout,
            "config": self.show_config,
            "tasks": self.show_tasks,
            "kill": self.kill_task,
            "quick": self.quick_model_select,
            "todo": self.manage_todos,
            "todos": self.manage_todos,  # Alias
        }
        
        self.running = False

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                return json.loads(self.config_file.read_text())
            except:
                pass
        return {}

    def save_config(self):
        """Save configuration to file."""
        self.config_dir.mkdir(exist_ok=True)
        self.config_file.write_text(json.dumps(self.config, indent=2))

    def load_auth(self) -> Dict[str, Any]:
        """Load authentication data."""
        if self.auth_file.exists():
            try:
                return json.loads(self.auth_file.read_text())
            except:
                pass
        return {}

    def save_auth(self):
        """Save authentication data."""
        self.config_dir.mkdir(exist_ok=True)
        self.auth_file.write_text(json.dumps(self.auth, indent=2))

    def get_prompt(self) -> str:
        """Get the simple prompt."""
        # We'll use a simple > prompt, the box is handled by prompt_toolkit
        return "> "

    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        # Check for API key
        if os.getenv("HANZO_API_KEY"):
            return True
        
        # Check auth file
        if self.auth.get("api_key"):
            return True
            
        # Check if logged in
        if self.auth.get("logged_in"):
            return True
            
        return False

    def get_model_info(self):
        """Get current model info string."""
        model = self.current_model
        
        # Check if using a tool
        if model.startswith("tool:"):
            if self.current_tool:
                return f"[dim cyan]agent: {self.current_tool.display_name}[/dim cyan]"
            else:
                tool_name = model.replace("tool:", "")
                return f"[dim cyan]agent: {tool_name}[/dim cyan]"
        
        # Determine provider from model name
        if model.startswith("gpt"):
            provider = "openai"
        elif model.startswith("claude"):
            provider = "anthropic"
        elif model.startswith("gemini"):
            provider = "google"
        elif model.startswith("llama") or model.startswith("codellama"):
            provider = "meta"
        elif model.startswith("mistral") or model.startswith("mixtral"):
            provider = "mistral"
        elif model.startswith("local:"):
            provider = "local"
        else:
            provider = "unknown"
        
        return f"[dim]model: {provider}/{model}[/dim]"
    
    async def run(self):
        """Run the enhanced REPL."""
        self.running = True
        
        # Setup completer
        commands = list(self.commands.keys())
        models = list(self.MODELS.keys())
        cli_commands = ["chat", "ask", "agent", "node", "mcp", "network", 
                       "auth", "config", "tools", "miner", "serve", "net", 
                       "dev", "router"]
        
        completer = WordCompleter(
            commands + models + cli_commands,
            ignore_case=True,
        )

        while self.running:
            try:
                # Show model info above prompt
                self.console.print(self.get_model_info())
                
                # Get input with simple prompt
                command = await self.session.prompt_async(
                    self.get_prompt(),
                    completer=completer,
                    vi_mode=True  # Enable vi mode for better navigation
                )

                if not command.strip():
                    continue

                # Handle slash commands
                if command.startswith("/"):
                    await self.handle_slash_command(command[1:])
                    continue

                # Parse command
                parts = command.strip().split(maxsplit=1)
                cmd = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""

                # Execute command
                if cmd in self.commands:
                    await self.commands[cmd](args)
                elif cmd in cli_commands:
                    await self.execute_command(cmd, args)
                else:
                    # Treat as chat message
                    await self.chat_with_ai(command)

            except KeyboardInterrupt:
                continue
            except EOFError:
                break
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")

    async def handle_slash_command(self, command: str):
        """Handle slash commands like /model, /status, etc."""
        parts = command.strip().split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        # Map slash commands to regular commands
        slash_map = {
            "m": "model",
            "s": "status",
            "h": "help",
            "q": "quit",
            "c": "clear",
            "models": "models",
            "login": "login",
            "logout": "logout",
            "todo": "todo",
            "todos": "todos",
            "t": "todo",  # Shortcut for todo
        }
        
        mapped_cmd = slash_map.get(cmd, cmd)
        
        if mapped_cmd in self.commands:
            await self.commands[mapped_cmd](args)
        else:
            self.console.print(f"[yellow]Unknown command: /{cmd}[/yellow]")
            self.console.print("[dim]Type /help for available commands[/dim]")

    async def show_status(self, args: str = ""):
        """Show comprehensive status."""
        # Create status table
        table = Table(title="System Status", box=box.ROUNDED)
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details", style="dim")
        
        # Authentication status
        if self.is_authenticated():
            auth_status = "✅ Authenticated"
            auth_details = self.auth.get("email", "API Key configured")
        else:
            auth_status = "❌ Not authenticated"
            auth_details = "Run /login to authenticate"
        table.add_row("Authentication", auth_status, auth_details)
        
        # Current model
        model_name = self.MODELS.get(self.current_model, self.current_model)
        table.add_row("Current Model", f"🤖 {self.current_model}", model_name)
        
        # Router status
        try:
            response = httpx.get("http://localhost:4000/health", timeout=1)
            router_status = "✅ Running" if response.status_code == 200 else "⚠️ Unhealthy"
            router_details = "Port 4000"
        except:
            router_status = "❌ Offline"
            router_details = "Run 'hanzo router start'"
        table.add_row("Router", router_status, router_details)
        
        # Node status
        try:
            response = httpx.get("http://localhost:3690/health", timeout=1)
            node_status = "✅ Running" if response.status_code == 200 else "⚠️ Unhealthy"
            node_details = "Port 3690"
        except:
            node_status = "❌ Offline"
            node_details = "Run 'hanzo node start'"
        table.add_row("Node", node_status, node_details)
        
        # API endpoints
        if os.getenv("HANZO_API_KEY"):
            api_status = "✅ Configured"
            api_details = "Using Hanzo Cloud API"
        else:
            api_status = "⚠️ Not configured"
            api_details = "Set HANZO_API_KEY environment variable"
        table.add_row("Cloud API", api_status, api_details)
        
        self.console.print(table)
        
        # Show additional info
        if self.auth.get("last_login"):
            self.console.print(f"\n[dim]Last login: {self.auth['last_login']}[/dim]")

    async def change_model(self, args: str = ""):
        """Change the current model or tool."""
        if not args:
            # Show model selection menu
            await self.list_models("")
            self.console.print("\n[cyan]Enter model/tool name or number:[/cyan]")
            
            # Get selection
            try:
                selection = await self.session.prompt_async("> ")
                
                # Handle numeric selection
                if selection.isdigit():
                    num = int(selection)
                    
                    # Check if it's a tool selection
                    if self.detected_tools and num <= len(self.detected_tools):
                        tool = self.detected_tools[num - 1]
                        args = f"tool:{tool.name}"
                    else:
                        # It's a model selection
                        model_idx = num - len(self.detected_tools) - 1 if self.detected_tools else num - 1
                        models_list = list(self.MODELS.keys())
                        if 0 <= model_idx < len(models_list):
                            args = models_list[model_idx]
                        else:
                            self.console.print("[red]Invalid selection[/red]")
                            return
                else:
                    args = selection
            except (KeyboardInterrupt, EOFError):
                return
        
        # Check if it's a tool
        if args.startswith("tool:") or args in [t.name for t in self.detected_tools] if self.detected_tools else False:
            # Handle tool selection
            tool_name = args.replace("tool:", "") if args.startswith("tool:") else args
            
            # Find the tool
            tool = None
            for t in self.detected_tools:
                if t.name == tool_name or t.display_name.lower() == tool_name.lower():
                    tool = t
                    break
            
            if tool:
                self.current_model = f"tool:{tool.name}"
                self.current_tool = tool
                self.config["default_model"] = self.current_model
                self.save_config()
                self.console.print(f"[green]✅ Switched to {tool.display_name}[/green]")
            else:
                self.console.print(f"[red]Tool not found: {tool_name}[/red]")
                self.console.print("[dim]Use /tools to see available tools[/dim]")
        
        # Regular model
        elif args in self.MODELS or args.startswith("local:"):
            self.current_model = args
            self.current_tool = None
            self.config["default_model"] = args
            self.save_config()
            
            model_name = self.MODELS.get(args, args)
            self.console.print(f"[green]✅ Switched to {model_name}[/green]")
        
        else:
            self.console.print(f"[red]Unknown model or tool: {args}[/red]")
            self.console.print("[dim]Use /models or /tools to see available options[/dim]")

    async def list_tools(self, args: str = ""):
        """List available AI tools."""
        if self.tool_detector:
            self.tool_detector.show_available_tools()
        else:
            self.console.print("[yellow]Tool detection not available[/yellow]")
    
    async def list_models(self, args: str = ""):
        """List available models."""
        # Show tools first if available
        if self.detected_tools:
            self.console.print("[bold cyan]AI Coding Assistants (Detected):[/bold cyan]")
            for i, tool in enumerate(self.detected_tools, 1):
                marker = "→" if self.current_model == f"tool:{tool.name}" else " "
                self.console.print(f"  {marker} {i}. {tool.display_name} ({tool.provider})")
            self.console.print()
        
        table = Table(title="Language Models", box=box.ROUNDED)
        table.add_column("#", style="dim")
        table.add_column("Model ID", style="cyan")
        table.add_column("Name", style="white")
        table.add_column("Provider", style="yellow")
        
        start_idx = len(self.detected_tools) + 1 if self.detected_tools else 1
        for i, (model_id, model_name) in enumerate(self.MODELS.items(), start_idx):
            # Extract provider
            if model_id.startswith("gpt"):
                provider = "OpenAI"
            elif model_id.startswith("claude"):
                provider = "Anthropic"
            elif model_id.startswith("gemini"):
                provider = "Google"
            elif model_id.startswith("llama") or model_id.startswith("codellama"):
                provider = "Meta"
            elif model_id.startswith("mistral") or model_id.startswith("mixtral"):
                provider = "Mistral"
            elif model_id.startswith("local:"):
                provider = "Local"
            else:
                provider = "Other"
            
            # Highlight current model
            if model_id == self.current_model:
                table.add_row(
                    str(i),
                    f"[bold green]→ {model_id}[/bold green]",
                    f"[bold]{model_name}[/bold]",
                    provider
                )
            else:
                table.add_row(str(i), model_id, model_name, provider)
        
        self.console.print(table)
        self.console.print("\n[dim]Use /model <name> or /model <number> to switch[/dim]")

    async def login(self, args: str = ""):
        """Login to Hanzo."""
        self.console.print("[cyan]Hanzo Authentication[/cyan]\n")
        
        # Check if already logged in
        if self.is_authenticated():
            self.console.print("[yellow]Already authenticated[/yellow]")
            if self.auth.get("email"):
                self.console.print(f"Logged in as: {self.auth['email']}")
            return
        
        # Get credentials
        try:
            # Email
            email = await self.session.prompt_async("Email: ")
            
            # Password (hidden)
            from prompt_toolkit import prompt
            password = prompt("Password: ", is_password=True)
            
            # Attempt login
            self.console.print("\n[dim]Authenticating...[/dim]")
            
            # TODO: Implement actual authentication
            # For now, simulate successful login
            await asyncio.sleep(1)
            
            # Save auth
            self.auth["email"] = email
            self.auth["logged_in"] = True
            self.auth["last_login"] = datetime.now().isoformat()
            self.save_auth()
            
            self.console.print("[green]✅ Successfully logged in![/green]")
            
        except (KeyboardInterrupt, EOFError):
            self.console.print("\n[yellow]Login cancelled[/yellow]")

    async def logout(self, args: str = ""):
        """Logout from Hanzo."""
        if not self.is_authenticated():
            self.console.print("[yellow]Not logged in[/yellow]")
            return
        
        # Clear auth
        self.auth = {}
        self.save_auth()
        
        # Clear environment variable if set
        if "HANZO_API_KEY" in os.environ:
            del os.environ["HANZO_API_KEY"]
        
        self.console.print("[green]✅ Successfully logged out[/green]")

    async def show_config(self, args: str = ""):
        """Show current configuration."""
        config_text = json.dumps(self.config, indent=2)
        self.console.print(Panel(config_text, title="Configuration", box=box.ROUNDED))

    async def show_help(self, args: str = ""):
        """Show enhanced help."""
        help_text = """
# Hanzo Enhanced REPL

## Slash Commands:
- `/todo [cmd]` - Manage todos (see `/todo help`)
- `/model [name]` - Change AI model (or `/m`)
- `/models` - List available models
- `/tools` - List available AI tools
- `/quick` - Quick model selector (arrow keys)
- `/tasks` - Show background tasks
- `/kill [id]` - Kill background task
- `/status` - Show system status (or `/s`)
- `/login` - Login to Hanzo Cloud
- `/logout` - Logout from Hanzo
- `/config` - Show configuration
- `/help` - Show this help (or `/h`)
- `/clear` - Clear screen (or `/c`)
- `/quit` - Exit REPL (or `/q`)

## Quick Model Selection:
- Press ↓ arrow key for quick model selector
- Use ↑/↓ to navigate, Enter to select
- Esc to cancel

## Model Selection:
- Use `/model gpt-4` to switch to GPT-4
- Use `/model 3` to select model by number
- Current model shown in prompt: `hanzo [gpt] >`

## Authentication:
- 🔓 = Authenticated (logged in or API key set)
- 🔒 = Not authenticated
- Use `/login` to authenticate with Hanzo Cloud

## Tips:
- Type any message to chat with current model
- Use Tab for command completion
- Use Up/Down arrows for history
"""
        self.console.print(Markdown(help_text))

    async def clear_screen(self, args: str = ""):
        """Clear the screen."""
        self.console.clear()

    async def exit_repl(self, args: str = ""):
        """Exit the REPL."""
        self.running = False
        self.console.print("[yellow]Goodbye! 👋[/yellow]")

    async def execute_command(self, cmd: str, args: str):
        """Execute a CLI command."""
        # Import here to avoid circular imports
        import subprocess
        
        full_cmd = f"hanzo {cmd} {args}".strip()
        self.console.print(f"[dim]Executing: {full_cmd}[/dim]")
        
        try:
            result = subprocess.run(
                full_cmd,
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.stdout:
                self.console.print(result.stdout)
            if result.stderr:
                self.console.print(f"[red]{result.stderr}[/red]")
                
        except Exception as e:
            self.console.print(f"[red]Error executing command: {e}[/red]")

    async def chat_with_ai(self, message: str):
        """Chat with AI using current model or tool."""
        # Check if using a tool
        if self.current_model.startswith("tool:") and self.current_tool:
            # Skip if this tool has already failed this session
            if self.current_tool.name in self.failed_tools:
                # Automatically use the first working tool
                for tool in self.detected_tools:
                    if tool.name not in self.failed_tools:
                        self.current_tool = tool
                        self.current_model = f"tool:{tool.name}"
                        self.console.print(f"[yellow]Switched to {tool.display_name}[/yellow]")
                        break
            
            # Try the current tool
            if self.current_tool.name not in self.failed_tools:
                self.console.print(f"[dim]Using {self.current_tool.display_name}...[/dim]")
                success, output = self.tool_detector.execute_with_tool(self.current_tool, message)
                
                if success:
                    self.console.print(output)
                    return
                else:
                    # Mark this tool as failed for the session
                    self.failed_tools.add(self.current_tool.name)
                    self.console.print(f"[red]Error: {output}[/red]")
            
            # Try to find next available tool
            found_working = False
            if self.tool_detector and self.tool_detector.detected_tools:
                for fallback_tool in self.tool_detector.detected_tools:
                    if fallback_tool.name not in self.failed_tools:
                        self.console.print(f"[yellow]Trying {fallback_tool.display_name}...[/yellow]")
                        success, output = self.tool_detector.execute_with_tool(fallback_tool, message)
                        if success:
                            self.console.print(output)
                            # Automatically switch to this working tool
                            self.current_tool = fallback_tool
                            self.current_model = f"tool:{fallback_tool.name}"
                            self.config["default_model"] = self.current_model
                            self.save_config()
                            self.console.print(f"\n[green]Switched to {fallback_tool.display_name} (now default)[/green]")
                            found_working = True
                            return
                        else:
                            # Mark as failed
                            self.failed_tools.add(fallback_tool.name)
                            self.console.print(f"[red]{fallback_tool.display_name} also failed[/red]")
            
            if not found_working:
                # Final fallback to cloud model
                self.console.print(f"[yellow]Falling back to cloud model...[/yellow]")
                await self.execute_command("ask", f"--cloud --model gpt-3.5-turbo {message}")
        else:
            # Use regular model through hanzo ask
            await self.execute_command("ask", f"--cloud --model {self.current_model} {message}")
    
    async def quick_model_select(self, args: str = ""):
        """Quick model selector with arrow keys."""
        if not QuickModelSelector:
            self.console.print("[yellow]Quick selector not available[/yellow]")
            return
        
        # Prepare tools and models
        tools = [(f"tool:{t.name}", t.display_name) for t in self.detected_tools] if self.detected_tools else []
        models = list(self.MODELS.items())
        
        selector = QuickModelSelector(models, tools, self.current_model)
        selected = await selector.run()
        
        if selected:
            # Change to selected model
            await self.change_model(selected)
    
    async def show_tasks(self, args: str = ""):
        """Show background tasks."""
        if self.task_manager:
            self.task_manager.list_tasks()
        else:
            self.console.print("[yellow]Task manager not available[/yellow]")
    
    async def kill_task(self, args: str = ""):
        """Kill a background task."""
        if not self.task_manager:
            self.console.print("[yellow]Task manager not available[/yellow]")
            return
        
        if args:
            if args.lower() == "all":
                self.task_manager.kill_all()
            else:
                self.task_manager.kill_task(args)
        else:
            # Show tasks and prompt for selection
            self.task_manager.list_tasks()
            self.console.print("\n[cyan]Enter task ID to kill (or 'all' for all tasks):[/cyan]")
            try:
                task_id = await self.session.prompt_async("> ")
                if task_id:
                    if task_id.lower() == "all":
                        self.task_manager.kill_all()
                    else:
                        self.task_manager.kill_task(task_id)
            except (KeyboardInterrupt, EOFError):
                pass
    
    async def manage_todos(self, args: str = ""):
        """Manage todos."""
        if not self.todo_manager:
            self.console.print("[yellow]Todo manager not available[/yellow]")
            return
        
        # Parse command
        parts = args.strip().split(maxsplit=1)
        
        if not parts:
            # Show todos
            self.todo_manager.display_todos()
            return
        
        subcommand = parts[0].lower()
        rest = parts[1] if len(parts) > 1 else ""
        
        # Handle subcommands
        if subcommand in ["add", "a", "+"]:
            # Add todo
            if rest:
                # Quick add
                try:
                    todo = self.todo_manager.quick_add(rest)
                    self.console.print(f"[green]✅ Added todo: {todo.title} (ID: {todo.id})[/green]")
                except ValueError as e:
                    self.console.print(f"[red]Error: {e}[/red]")
            else:
                # Interactive add
                await self.add_todo_interactive()
        
        elif subcommand in ["list", "ls", "l"]:
            # List todos with optional filter
            filter_parts = rest.split()
            status = None
            priority = None
            tag = None
            
            for i in range(0, len(filter_parts), 2):
                if i + 1 < len(filter_parts):
                    key = filter_parts[i]
                    value = filter_parts[i + 1]
                    
                    if key in ["status", "s"]:
                        status = value
                    elif key in ["priority", "p"]:
                        priority = value
                    elif key in ["tag", "t"]:
                        tag = value
            
            todos = self.todo_manager.list_todos(status=status, priority=priority, tag=tag)
            title = "Filtered Todos" if (status or priority or tag) else "All Todos"
            self.todo_manager.display_todos(todos, title)
        
        elif subcommand in ["done", "d", "complete", "finish"]:
            # Mark as done
            if rest:
                todo = self.todo_manager.update_todo(rest, status="done")
                if todo:
                    self.console.print(f"[green]✅ Marked as done: {todo.title}[/green]")
                else:
                    self.console.print(f"[red]Todo not found: {rest}[/red]")
            else:
                self.console.print("[yellow]Usage: /todo done <id>[/yellow]")
        
        elif subcommand in ["start", "begin", "progress"]:
            # Mark as in progress
            if rest:
                todo = self.todo_manager.update_todo(rest, status="in_progress")
                if todo:
                    self.console.print(f"[cyan]🔄 Started: {todo.title}[/cyan]")
                else:
                    self.console.print(f"[red]Todo not found: {rest}[/red]")
            else:
                self.console.print("[yellow]Usage: /todo start <id>[/yellow]")
        
        elif subcommand in ["cancel", "x"]:
            # Cancel todo
            if rest:
                todo = self.todo_manager.update_todo(rest, status="cancelled")
                if todo:
                    self.console.print(f"[red]❌ Cancelled: {todo.title}[/red]")
                else:
                    self.console.print(f"[red]Todo not found: {rest}[/red]")
            else:
                self.console.print("[yellow]Usage: /todo cancel <id>[/yellow]")
        
        elif subcommand in ["delete", "del", "rm", "remove"]:
            # Delete todo
            if rest:
                if self.todo_manager.delete_todo(rest):
                    self.console.print(f"[green]✅ Deleted todo: {rest}[/green]")
                else:
                    self.console.print(f"[red]Todo not found: {rest}[/red]")
            else:
                self.console.print("[yellow]Usage: /todo delete <id>[/yellow]")
        
        elif subcommand in ["view", "show", "detail"]:
            # View todo detail
            if rest:
                todo = self.todo_manager.get_todo(rest)
                if todo:
                    self.todo_manager.display_todo_detail(todo)
                else:
                    self.console.print(f"[red]Todo not found: {rest}[/red]")
            else:
                self.console.print("[yellow]Usage: /todo view <id>[/yellow]")
        
        elif subcommand in ["stats", "statistics"]:
            # Show statistics
            self.todo_manager.display_statistics()
        
        elif subcommand in ["clear", "reset"]:
            # Clear all todos (with confirmation)
            try:
                confirm = await self.session.prompt_async("Are you sure you want to delete ALL todos? (yes/no): ")
                if confirm.lower() in ["yes", "y"]:
                    self.todo_manager.todos = []
                    self.todo_manager.save_todos()
                    self.console.print("[green]✅ All todos cleared[/green]")
                else:
                    self.console.print("[yellow]Cancelled[/yellow]")
            except (KeyboardInterrupt, EOFError):
                self.console.print("[yellow]Cancelled[/yellow]")
        
        elif subcommand in ["help", "h", "?"]:
            # Show todo help
            self.show_todo_help()
        
        else:
            # Unknown subcommand, treat as quick add
            try:
                todo = self.todo_manager.quick_add(args)
                self.console.print(f"[green]✅ Added todo: {todo.title} (ID: {todo.id})[/green]")
            except ValueError:
                self.console.print(f"[yellow]Unknown todo command: {subcommand}[/yellow]")
                self.console.print("[dim]Use /todo help for available commands[/dim]")
    
    async def add_todo_interactive(self):
        """Add todo interactively."""
        try:
            # Get title
            title = await self.session.prompt_async("Title: ")
            if not title:
                self.console.print("[yellow]Cancelled[/yellow]")
                return
            
            # Get description
            description = await self.session.prompt_async("Description (optional): ")
            
            # Get priority
            priority = await self.session.prompt_async("Priority (low/medium/high/urgent) [medium]: ")
            if not priority:
                priority = "medium"
            
            # Get tags
            tags_input = await self.session.prompt_async("Tags (comma-separated, optional): ")
            tags = [t.strip() for t in tags_input.split(",") if t.strip()] if tags_input else []
            
            # Get due date
            due_date = await self.session.prompt_async("Due date (optional): ")
            
            # Add todo
            todo = self.todo_manager.add_todo(
                title=title,
                description=description,
                priority=priority,
                tags=tags,
                due_date=due_date if due_date else None
            )
            
            self.console.print(f"[green]✅ Added todo: {todo.title} (ID: {todo.id})[/green]")
            
        except (KeyboardInterrupt, EOFError):
            self.console.print("[yellow]Cancelled[/yellow]")
    
    def show_todo_help(self):
        """Show todo help."""
        help_text = """
[bold cyan]Todo Management[/bold cyan]

[bold]Quick Add:[/bold]
  /todo Buy milk #shopping !high @tomorrow
  Format: title #tag1 #tag2 !priority @due_date

[bold]Commands:[/bold]
  /todo                  - List all todos
  /todo add <text>       - Quick add todo
  /todo list [filters]   - List with filters
  /todo done <id>        - Mark as done
  /todo start <id>       - Mark as in progress
  /todo cancel <id>      - Cancel todo
  /todo delete <id>      - Delete todo
  /todo view <id>        - View todo details
  /todo stats            - Show statistics
  /todo clear            - Clear all todos
  /todo help             - Show this help

[bold]List Filters:[/bold]
  /todo list status todo
  /todo list priority high
  /todo list tag work

[bold]Shortcuts:[/bold]
  /todo a    = add
  /todo ls   = list
  /todo d    = done
  /todo rm   = delete
"""
        self.console.print(help_text)