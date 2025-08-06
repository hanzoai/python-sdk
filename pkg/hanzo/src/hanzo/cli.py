"""Main CLI entry point for Hanzo."""

import asyncio
import sys
from typing import Optional

import click
from rich.console import Console

from .commands import agent, auth, chat, cluster, config, mcp, miner, network, repl, tools
from .interactive.repl import HanzoREPL
from .utils.output import console

# Version
__version__ = "0.2.4"


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="hanzo")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--json", is_flag=True, help="JSON output format")
@click.option("--config", "-c", type=click.Path(), help="Config file path")
@click.pass_context
def cli(ctx, verbose: bool, json: bool, config: Optional[str]):
    """Hanzo AI - Unified CLI for local, private, and free AI.
    
    Run without arguments to enter interactive mode.
    """
    # Ensure context object exists
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["json"] = json
    ctx.obj["config"] = config
    ctx.obj["console"] = console
    
    # If no subcommand, enter interactive mode or start compute node
    if ctx.invoked_subcommand is None:
        # Check if we should start as a compute node
        import os
        if os.environ.get("HANZO_COMPUTE_NODE") == "1":
            # Start as a compute node
            from .commands import network
            asyncio.run(start_compute_node(ctx))
        else:
            # Enter interactive REPL mode
            console.print("[bold cyan]Hanzo AI - Interactive Mode[/bold cyan]")
            console.print("Type 'help' for commands, 'exit' to quit\n")
            try:
                repl = HanzoREPL(console=console)
                asyncio.run(repl.run())
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted[/yellow]")
            except EOFError:
                console.print("\n[yellow]Goodbye![/yellow]")


# Register command groups
cli.add_command(agent.agent_group)
cli.add_command(auth.auth_group)
cli.add_command(cluster.cluster_group)
cli.add_command(mcp.mcp_group)
cli.add_command(miner.miner_group)
cli.add_command(chat.chat_command)
cli.add_command(repl.repl_group)
cli.add_command(tools.tools_group)
cli.add_command(network.network_group)
cli.add_command(config.config_group)


# Quick aliases
@cli.command()
@click.argument("prompt", nargs=-1, required=True)
@click.option("--model", "-m", default="llama-3.2-3b", help="Model to use")
@click.option("--local/--cloud", default=True, help="Use local or cloud model")
@click.pass_context
def ask(ctx, prompt: tuple, model: str, local: bool):
    """Quick question to AI (alias for 'hanzo chat --once')."""
    prompt_text = " ".join(prompt)
    asyncio.run(chat.ask_once(ctx, prompt_text, model, local))


@cli.command()
@click.option("--name", "-n", default="hanzo-local", help="Cluster name")
@click.option("--port", "-p", default=8000, help="API port")
@click.pass_context
def serve(ctx, name: str, port: int):
    """Start local AI cluster (alias for 'hanzo cluster start')."""
    asyncio.run(cluster.start_cluster(ctx, name, port))


@cli.command()
@click.option("--name", "-n", help="Node name (auto-generated if not provided)")
@click.option("--port", "-p", default=7860, help="Node port")
@click.option("--network", default="mainnet", help="Network to join (mainnet/testnet/local)")
@click.option("--models", "-m", multiple=True, help="Models to serve")
@click.option("--max-jobs", type=int, default=10, help="Max concurrent jobs")
@click.pass_context
def node(ctx, name: str, port: int, network: str, models: tuple, max_jobs: int):
    """Start as a compute node for the Hanzo network."""
    asyncio.run(start_compute_node(ctx, name, port, network, models, max_jobs))


async def start_compute_node(ctx, name: str = None, port: int = 7860, 
                            network: str = "mainnet", models: tuple = None, 
                            max_jobs: int = 10):
    """Start this instance as a compute node."""
    console = ctx.obj.get("console", Console())
    
    console.print("[bold cyan]Starting Hanzo Compute Node[/bold cyan]")
    console.print(f"Network: {network}")
    console.print(f"Port: {port}")
    
    try:
        from hanzo_network import ComputeNode
        
        # Generate node name if not provided
        if not name:
            import socket
            import uuid
            hostname = socket.gethostname()
            node_id = str(uuid.uuid4())[:8]
            name = f"{hostname}-{node_id}"
        
        # Initialize compute node
        node = ComputeNode(
            name=name,
            port=port,
            network=network,
            models=list(models) if models else None,
            max_concurrent_jobs=max_jobs
        )
        
        console.print(f"\n[green]✓[/green] Node '{name}' initialized")
        console.print(f"  ID: {node.id}")
        console.print(f"  Models: {', '.join(node.available_models) if node.available_models else 'auto-detect'}")
        console.print(f"  Max jobs: {max_jobs}")
        console.print("\n[yellow]Joining network...[/yellow]")
        
        await node.connect()
        
        console.print(f"[green]✓[/green] Connected to {network} network")
        console.print(f"  Peers: {len(node.peers)}")
        console.print(f"  Status: {node.status}")
        
        console.print("\n[bold green]Compute node is running![/bold green]")
        console.print("Press Ctrl+C to stop\n")
        
        # Run the node
        await node.run()
        
    except ImportError:
        console.print("[red]Error:[/red] hanzo-network not installed")
        console.print("Install with: pip install hanzo[network]")
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down node...[/yellow]")
        if 'node' in locals():
            await node.shutdown()
        console.print("[green]✓[/green] Node stopped")
    except Exception as e:
        console.print(f"[red]Error starting compute node: {e}[/red]")


@cli.command()
@click.pass_context
def dashboard(ctx):
    """Open interactive dashboard."""
    from .interactive.dashboard import run_dashboard
    run_dashboard()


def main():
    """Main entry point."""
    try:
        cli(auto_envvar_prefix="HANZO")
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()