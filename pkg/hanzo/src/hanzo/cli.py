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
    
    # If no subcommand, enter interactive mode
    if ctx.invoked_subcommand is None:
        console.print("[bold cyan]Welcome to Hanzo AI CLI[/bold cyan]")
        console.print("Type 'help' for available commands or 'exit' to quit.\n")
        try:
            repl = HanzoREPL()
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
@click.pass_context
def dashboard(ctx):
    """Open interactive dashboard."""
    from hanzo_cli.interactive.dashboard import run_dashboard
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