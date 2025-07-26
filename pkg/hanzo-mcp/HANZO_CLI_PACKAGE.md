# hanzo-cli Package Design

The `hanzo-cli` package provides a unified command-line interface to the entire Hanzo AI ecosystem, exposing all SDK functionality through a single `hanzo` command.

## Package Structure

```
pkg/hanzo-cli/
├── pyproject.toml
├── README.md
├── src/
│   └── hanzo_cli/
│       ├── __init__.py
│       ├── __main__.py         # Entry point for python -m hanzo
│       ├── cli.py              # Main CLI using Click/Typer
│       ├── commands/
│       │   ├── __init__.py
│       │   ├── agent.py        # Agent management commands
│       │   ├── cluster.py      # Cluster commands
│       │   ├── mcp.py          # MCP server commands
│       │   ├── miner.py        # Mining commands
│       │   ├── chat.py         # Interactive chat
│       │   ├── tools.py        # Tool execution
│       │   ├── network.py      # Network commands
│       │   └── config.py       # Configuration
│       ├── interactive/
│       │   ├── __init__.py
│       │   ├── repl.py         # Interactive REPL
│       │   ├── chat.py         # Chat interface
│       │   └── dashboard.py    # TUI dashboard
│       └── utils/
│           ├── __init__.py
│           ├── output.py       # Rich output formatting
│           ├── config.py       # Config management
│           └── auth.py         # Authentication
├── completions/
│   ├── hanzo.bash
│   ├── hanzo.zsh
│   └── hanzo.fish
└── tests/
    └── test_cli.py
```

## pyproject.toml Configuration

```toml
[project]
name = "hanzo-cli"
version = "1.0.0"
description = "Unified CLI for Hanzo AI"
dependencies = [
    "hanzoai>=1.0.0",
    "hanzo-cluster>=0.1.0",
    "hanzo-miner>=0.1.0",
    "hanzo-mcp>=0.1.0",
    "hanzo-agents>=0.1.0",
    "hanzo-network>=0.1.0",
    "hanzo-a2a>=0.1.0",
    "click>=8.0.0",
    "rich>=13.0.0",
    "typer>=0.9.0",
    "prompt-toolkit>=3.0.0",
    "httpx>=0.23.0",
    "pydantic>=2.0.0",
]

[project.scripts]
hanzo = "hanzo_cli.cli:main"

[project.urls]
Homepage = "https://hanzo.ai"
Repository = "https://github.com/hanzoai/python-sdk"
Documentation = "https://docs.hanzo.ai/cli"

# Publish as both hanzo-cli and hanzo
[tool.hatch.build]
packages = ["src/hanzo_cli"]

[tool.hatch.build.targets.wheel]
packages = ["src/hanzo_cli"]

# Additional metadata for PyPI
[project.keywords]
keywords = ["ai", "cli", "hanzo", "agents", "llm", "mcp"]

[project.classifiers]
classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Environment :: Console",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: Apache Software License",
    "Programming Language :: Python :: 3.8",
    "Topic :: Software Development :: Libraries :: Python Modules",
]
```

## Main CLI Structure (cli.py)

```python
import click
import asyncio
from rich.console import Console
from rich.table import Table
from typing import Optional
import sys

from hanzo_cli.commands import agent, cluster, mcp, miner, chat, tools, network, config
from hanzo_cli.interactive import repl
from hanzo_cli.utils import output

console = Console()

@click.group(invoke_without_command=True)
@click.version_option(version="1.0.0", prog_name="hanzo")
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.option('--json', is_flag=True, help='JSON output format')
@click.pass_context
def cli(ctx, verbose, json):
    """Hanzo AI - Unified CLI for local, private, and free AI.
    
    Run without arguments to enter interactive mode.
    """
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['json'] = json
    ctx.obj['console'] = console
    
    if ctx.invoked_subcommand is None:
        # No subcommand - enter interactive mode
        console.print("[bold cyan]Welcome to Hanzo AI CLI[/bold cyan]")
        console.print("Type 'help' for available commands or 'exit' to quit.\n")
        asyncio.run(repl.start())

# Register command groups
cli.add_command(agent.agent_group)
cli.add_command(cluster.cluster_group)
cli.add_command(mcp.mcp_group)
cli.add_command(miner.miner_group)
cli.add_command(chat.chat_command)
cli.add_command(tools.tools_group)
cli.add_command(network.network_group)
cli.add_command(config.config_group)

# Quick aliases
@cli.command()
@click.argument('prompt', nargs=-1)
@click.option('--model', '-m', default='llama-3.2-3b', help='Model to use')
@click.option('--local/--cloud', default=True, help='Use local or cloud model')
def ask(prompt, model, local):
    """Quick question to AI (alias for 'hanzo chat --once')."""
    prompt_text = ' '.join(prompt)
    asyncio.run(chat.ask_once(prompt_text, model, local))

@cli.command()
def serve():
    """Start local AI cluster (alias for 'hanzo cluster start')."""
    asyncio.run(cluster.start_cluster())

def main():
    """Main entry point."""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)

if __name__ == '__main__':
    main()
```

## Command Examples

### Agent Commands (commands/agent.py)
```python
import click
from rich.table import Table
from hanzo_agents import create_agent, create_network

@click.group(name='agent')
def agent_group():
    """Manage AI agents."""
    pass

@agent_group.command()
@click.option('--name', '-n', required=True, help='Agent name')
@click.option('--model', '-m', default='llama-3.2-3b', help='Model to use')
@click.option('--local/--cloud', default=True, help='Use local or cloud')
def create(name, model, local):
    """Create a new agent."""
    agent = create_agent(
        name=name,
        model=model,
        base_url="http://localhost:8000" if local else None
    )
    console.print(f"[green]Created agent: {name}[/green]")

@agent_group.command()
def list():
    """List available agents."""
    # Would connect to agent registry
    table = Table(title="Available Agents")
    table.add_column("Name", style="cyan")
    table.add_column("Model", style="green")
    table.add_column("Status", style="yellow")
    
    # Add agents to table
    table.add_row("helper", "llama-3.2-3b", "active")
    table.add_row("coder", "codellama-7b", "idle")
    
    console.print(table)

@agent_group.command()
@click.argument('agents', nargs=-1, required=True)
@click.option('--task', '-t', required=True, help='Task to execute')
def run(agents, task):
    """Run a task with specified agents."""
    # Create network and run task
    network = create_network(agents=list(agents))
    result = asyncio.run(network.run(task))
    console.print(result)
```

### Cluster Commands (commands/cluster.py)
```python
@click.group(name='cluster')
def cluster_group():
    """Manage local AI cluster."""
    pass

@cluster_group.command()
@click.option('--name', '-n', default='hanzo-local', help='Cluster name')
@click.option('--port', '-p', default=8000, help='API port')
@click.option('--models', '-m', multiple=True, help='Models to load')
async def start(name, port, models):
    """Start local AI cluster."""
    from hanzo_cluster import start_local_cluster
    
    with console.status("[bold green]Starting cluster..."):
        cluster = await start_local_cluster(
            name=name,
            port=port,
            models=list(models) if models else None
        )
    
    console.print(f"[green]✓[/green] Cluster started at http://localhost:{port}")
    console.print("Press Ctrl+C to stop")
    
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        await cluster.stop()

@cluster_group.command()
def status():
    """Show cluster status."""
    # Check if cluster is running
    import httpx
    try:
        response = httpx.get("http://localhost:8000/health")
        if response.status_code == 200:
            console.print("[green]✓[/green] Cluster is running")
            # Show loaded models, memory usage, etc.
        else:
            console.print("[red]✗[/red] Cluster is not responding")
    except:
        console.print("[yellow]![/yellow] Cluster is not running")
```

### Interactive Chat (commands/chat.py)
```python
@click.command(name='chat')
@click.option('--model', '-m', default='llama-3.2-3b', help='Model to use')
@click.option('--local/--cloud', default=True, help='Use local or cloud')
@click.option('--once', is_flag=True, help='Single question mode')
@click.argument('prompt', nargs=-1)
async def chat_command(model, local, once, prompt):
    """Interactive AI chat."""
    if once or prompt:
        # Single question mode
        await ask_once(' '.join(prompt), model, local)
    else:
        # Interactive chat
        from hanzo_cli.interactive.chat import InteractiveChat
        chat = InteractiveChat(model=model, local=local)
        await chat.run()

async def ask_once(prompt: str, model: str, local: bool):
    """Ask a single question."""
    from hanzoai import completion
    
    if local:
        # Use local cluster
        response = await completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            base_url="http://localhost:8000"
        )
    else:
        # Use cloud
        response = completion(
            model=f"anthropic/{model}" if "claude" in model else model,
            messages=[{"role": "user", "content": prompt}]
        )
    
    console.print(response)
```

### MCP Commands (commands/mcp.py)
```python
@click.group(name='mcp')
def mcp_group():
    """Manage MCP servers and tools."""
    pass

@mcp_group.command()
@click.option('--name', '-n', default='hanzo-mcp', help='Server name')
@click.option('--transport', '-t', type=click.Choice(['stdio', 'sse']), default='stdio')
@click.option('--allow-path', '-p', multiple=True, help='Allowed paths')
def serve(name, transport, allow_path):
    """Start MCP server."""
    from hanzo_mcp import run_mcp_server
    
    console.print(f"[cyan]Starting MCP server ({transport})...[/cyan]")
    
    run_mcp_server(
        name=name,
        transport=transport,
        allowed_paths=list(allow_path) or ['.']
    )

@mcp_group.command()
def tools():
    """List available MCP tools."""
    from hanzo_mcp import create_server
    
    server = create_server()
    tools = asyncio.run(server.mcp.list_tools())
    
    table = Table(title="MCP Tools")
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="white")
    
    for tool in tools:
        table.add_row(tool.name, tool.description)
    
    console.print(table)

@mcp_group.command()
@click.argument('tool')
@click.option('--arg', '-a', multiple=True, help='Tool arguments (key=value)')
def run(tool, arg):
    """Run an MCP tool."""
    # Parse arguments
    args = {}
    for a in arg:
        key, value = a.split('=', 1)
        args[key] = value
    
    # Run tool
    from hanzo_mcp import create_server
    server = create_server()
    result = asyncio.run(server.run_tool(tool, **args))
    
    console.print(result)
```

### Mining Commands (commands/miner.py)
```python
@click.group(name='miner')
def miner_group():
    """Manage mining operations."""
    pass

@miner_group.command()
@click.option('--wallet', '-w', required=True, help='Wallet address')
@click.option('--max-ram', type=int, help='Max RAM to use (GB)')
@click.option('--max-gpu', type=int, help='Max GPU memory (GB)')
async def start(wallet, max_ram, max_gpu):
    """Start mining."""
    from hanzo_miner import join_mining_network
    
    with console.status("[bold yellow]Joining mining network..."):
        miner = await join_mining_network(
            wallet_address=wallet,
            max_ram=max_ram,
            max_vram=max_gpu
        )
    
    console.print(f"[green]✓[/green] Mining started")
    console.print(f"Wallet: {wallet}")
    
    # Show mining stats periodically
    while True:
        await asyncio.sleep(60)
        stats = miner.get_stats()
        console.print(f"Compute: {stats['compute_contributed']}")
        console.print(f"Rewards: {stats['rewards_earned']}")

@miner_group.command()
def stats():
    """Show mining statistics."""
    # Connect to miner and show stats
    pass
```

## Interactive REPL (interactive/repl.py)

```python
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
import shlex

class HanzoREPL:
    """Interactive REPL for Hanzo CLI."""
    
    def __init__(self):
        self.commands = {
            'help': self.help,
            'exit': self.exit,
            'agent': self.agent_commands,
            'cluster': self.cluster_commands,
            'chat': self.chat,
            'tools': self.tools,
            # ... more commands
        }
        
        self.completer = WordCompleter(
            list(self.commands.keys()),
            ignore_case=True
        )
        
        self.session = PromptSession(
            history=FileHistory('.hanzo_history'),
            auto_suggest=AutoSuggestFromHistory(),
            completer=self.completer
        )
    
    async def run(self):
        """Run the REPL."""
        console.print("[cyan]Hanzo Interactive Mode[/cyan]")
        console.print("Type 'help' for commands, 'exit' to quit\n")
        
        while True:
            try:
                # Get input
                line = await self.session.prompt_async('hanzo> ')
                
                if not line.strip():
                    continue
                
                # Parse command
                parts = shlex.split(line)
                cmd = parts[0]
                args = parts[1:]
                
                # Execute command
                if cmd in self.commands:
                    await self.commands[cmd](args)
                else:
                    # Try to run as shell command
                    await self.shell_command(line)
                    
            except KeyboardInterrupt:
                continue
            except EOFError:
                break
    
    async def help(self, args):
        """Show help."""
        console.print("""
Available commands:
  agent    - Manage agents
  cluster  - Manage local cluster
  chat     - Start chat session
  tools    - Run tools
  miner    - Mining operations
  network  - Network operations
  config   - Configuration
  help     - Show this help
  exit     - Exit REPL
        """)
    
    async def exit(self, args):
        """Exit REPL."""
        console.print("[yellow]Goodbye![/yellow]")
        raise EOFError
```

## Dashboard TUI (interactive/dashboard.py)

```python
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, DataTable
from textual.containers import Container, Horizontal, Vertical

class HanzoDashboard(App):
    """TUI dashboard for Hanzo."""
    
    CSS = """
    .box {
        border: solid green;
        padding: 1;
        margin: 1;
    }
    """
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Horizontal(
                Vertical(
                    Static("Cluster Status", classes="box"),
                    Static("Models: llama-3.2-3b", classes="box"),
                    id="cluster"
                ),
                Vertical(
                    Static("Active Agents", classes="box"),
                    DataTable(id="agents"),
                    id="agents-panel"
                ),
            ),
            Horizontal(
                Vertical(
                    Static("Mining Stats", classes="box"),
                    Static("Rate: 0 H/s", id="mining-rate"),
                    Static("Rewards: 0", id="rewards"),
                    id="mining"
                ),
                Vertical(
                    Static("Recent Tasks", classes="box"),
                    DataTable(id="tasks"),
                    id="tasks-panel"
                ),
            ),
        )
        yield Footer()
    
    def on_mount(self) -> None:
        # Start updating stats
        self.set_interval(1.0, self.update_stats)
    
    async def update_stats(self) -> None:
        # Update dashboard with latest stats
        pass
```

## Usage Examples

```bash
# Quick AI question
hanzo ask "What is the capital of France?"

# Start local cluster
hanzo serve

# Interactive chat
hanzo chat

# Chat with specific model
hanzo chat -m codellama-7b

# Create and run agent
hanzo agent create -n helper -m llama-3.2-3b
hanzo agent run helper -t "Write a Python hello world"

# Start mining
hanzo miner start -w 0x1234...

# Run MCP server
hanzo mcp serve --allow-path /workspace

# List MCP tools
hanzo mcp tools

# Run specific tool
hanzo mcp run search -a pattern=TODO -a path=.

# Interactive mode
hanzo
> chat
Starting chat session...
You: Hello!
AI: Hello! How can I help you today?
You: exit
> cluster status
✓ Cluster is running
> exit
Goodbye!

# Dashboard
hanzo dashboard
```

## Shell Completions

The package includes shell completion scripts for bash, zsh, and fish that enable tab completion for all commands and options.

## Configuration

Configuration stored in `~/.config/hanzo/config.yaml`:

```yaml
default_model: llama-3.2-3b
prefer_local: true
cluster:
  port: 8000
  models:
    - llama-3.2-3b
    - codellama-7b
mining:
  wallet: "0x..."
  max_ram: 16
  max_gpu: 8
```

## Benefits

1. **Unified Interface**: Single CLI for entire Hanzo ecosystem
2. **Intuitive Commands**: Logical command structure
3. **Interactive Mode**: REPL for exploration
4. **Rich Output**: Beautiful formatted output
5. **Shell Integration**: Tab completion support
6. **Flexible**: Use as one-off commands or interactive
7. **Discoverable**: Built-in help and examples