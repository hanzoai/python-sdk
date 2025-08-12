"""Agent management commands."""

import asyncio
from typing import Optional

import click
from rich.table import Table

from ..utils.output import console, handle_errors


@click.group(name="agent")
def agent_group():
    """Manage AI agents."""
    pass


@agent_group.command()
@click.option("--name", "-n", required=True, help="Agent name")
@click.option("--model", "-m", default="llama-3.2-3b", help="Model to use")
@click.option("--description", "-d", help="Agent description")
@click.option("--local/--cloud", default=True, help="Use local or cloud model")
@click.pass_context
@handle_errors
async def create(ctx, name: str, model: str, description: Optional[str], local: bool):
    """Create a new agent."""
    try:
        from hanzoai.agents import create_agent
    except ImportError:
        console.print("[red]Error:[/red] hanzo-agents not installed")
        console.print("Install with: pip install hanzo[agents]")
        return

    base_url = "http://localhost:8000" if local else None

    with console.status(f"Creating agent '{name}'..."):
        agent = create_agent(name=name, model=model, base_url=base_url)

    console.print(f"[green]✓[/green] Created agent: {name}")
    console.print(f"  Model: {model}")
    console.print(f"  Mode: {'local' if local else 'cloud'}")


@agent_group.command()
@click.pass_context
def list(ctx):
    """List available agents."""
    # TODO: Connect to agent registry
    table = Table(title="Available Agents")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Model", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Description")

    # Mock data for now
    agents = [
        ("helper", "llama-3.2-3b", "active", "General purpose assistant"),
        ("coder", "codellama-7b", "idle", "Code generation specialist"),
        ("researcher", "llama-3.2-3b", "idle", "Research and analysis"),
    ]

    for name, model, status, desc in agents:
        table.add_row(name, model, status, desc)

    console.print(table)


@agent_group.command()
@click.argument("agents", nargs=-1, required=True)
@click.option("--task", "-t", required=True, help="Task to execute")
@click.option("--parallel", "-p", is_flag=True, help="Run agents in parallel")
@click.option("--timeout", type=int, help="Timeout in seconds")
@click.pass_context
@handle_errors
async def run(ctx, agents: tuple, task: str, parallel: bool, timeout: Optional[int]):
    """Run a task with specified agents."""
    try:
        from hanzoai.agents import create_network
    except ImportError:
        console.print("[red]Error:[/red] hanzo-agents not installed")
        console.print("Install with: pip install hanzo[agents]")
        return

    agent_list = list(agents)

    with console.status(f"Running task with {len(agent_list)} agents..."):
        # Create network with agents
        network = create_network(agents=agent_list)

        # Run task
        result = (
            await asyncio.wait_for(network.run(task), timeout=timeout)
            if timeout
            else await network.run(task)
        )

    console.print("[green]Task completed![/green]")
    console.print(result)


@agent_group.command()
@click.argument("agent")
@click.pass_context
def delete(ctx, agent: str):
    """Delete an agent."""
    if click.confirm(f"Delete agent '{agent}'?"):
        console.print(f"[yellow]Deleted agent: {agent}[/yellow]")
    else:
        console.print("Cancelled")
