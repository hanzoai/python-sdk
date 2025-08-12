"""Main CLI entry point for Hanzo."""

import sys
import asyncio
from typing import Optional

import click
from rich.console import Console

from .commands import (
    mcp,
    auth,
    chat,
    repl,
    agent,
    miner,
    tools,
    config,
    cluster,
    network,
)
from .utils.output import console
from .interactive.repl import HanzoREPL

# Version
__version__ = "0.2.10"


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
@click.option(
    "--port", "-p", default=52415, help="Node port (default: 52415 for hanzo/net)"
)
@click.option(
    "--network", default="local", help="Network to join (mainnet/testnet/local)"
)
@click.option(
    "--models", "-m", multiple=True, help="Models to serve (e.g., llama-3.2-3b)"
)
@click.option("--max-jobs", type=int, default=10, help="Max concurrent jobs")
@click.pass_context
def net(ctx, name: str, port: int, network: str, models: tuple, max_jobs: int):
    """Start the Hanzo Network distributed AI compute node."""
    asyncio.run(start_compute_node(ctx, name, port, network, models, max_jobs))


@cli.command()
@click.option("--name", "-n", help="Node name (auto-generated if not provided)")
@click.option(
    "--port", "-p", default=52415, help="Node port (default: 52415 for hanzo/net)"
)
@click.option(
    "--network", default="local", help="Network to join (mainnet/testnet/local)"
)
@click.option(
    "--models", "-m", multiple=True, help="Models to serve (e.g., llama-3.2-3b)"
)
@click.option("--max-jobs", type=int, default=10, help="Max concurrent jobs")
@click.pass_context
def node(ctx, name: str, port: int, network: str, models: tuple, max_jobs: int):
    """Alias for 'hanzo net' - Start as a compute node for the Hanzo network."""
    asyncio.run(start_compute_node(ctx, name, port, network, models, max_jobs))


async def start_compute_node(
    ctx,
    name: str = None,
    port: int = 52415,
    network: str = "mainnet",
    models: tuple = None,
    max_jobs: int = 10,
):
    """Start this instance as a compute node using hanzo/net."""
    from .utils.net_check import check_net_installation

    console = ctx.obj.get("console", Console())

    console.print("[bold cyan]Starting Hanzo Net Compute Node[/bold cyan]")
    console.print(f"Network: {network}")
    console.print(f"Port: {port}")

    # Check hanzo/net availability
    is_available, net_path, python_exe = check_net_installation()

    if not is_available:
        console.print("[red]Error:[/red] hanzo-net is not installed")
        console.print("\nTo install hanzo-net from PyPI:")
        console.print("  pip install hanzo-net")
        console.print("\nOr for development, clone from GitHub:")
        console.print("  git clone https://github.com/hanzoai/net.git ~/work/hanzo/net")
        console.print("  cd ~/work/hanzo/net && pip install -e .")
        return

    try:
        import os
        import sys
        import subprocess

        # Use the checked net_path and python_exe
        if not net_path:
            # net is installed as a package
            console.print("[green]✓[/green] Using installed hanzo/net")

            # Set up sys.argv for net's argparse
            original_argv = sys.argv.copy()
            try:
                # Build argv for net
                sys.argv = ["hanzo-net"]  # Program name

                # Add options
                if port != 52415:
                    sys.argv.extend(["--chatgpt-api-port", str(port)])
                if name:
                    sys.argv.extend(["--node-id", name])
                if network != "local":
                    sys.argv.extend(["--discovery-module", network])
                if models:
                    sys.argv.extend(["--default-model", models[0]])

                # Import and run net
                from net.main import run as net_run

                console.print(f"\n[green]✓[/green] Node initialized")
                console.print(f"  Port: {port}")
                console.print(
                    f"  Models: {', '.join(models) if models else 'auto-detect'}"
                )
                console.print("\n[bold green]Hanzo Net is running![/bold green]")
                console.print("WebUI: http://localhost:52415")
                console.print("API: http://localhost:52415/v1/chat/completions")
                console.print("\nPress Ctrl+C to stop\n")

                # Run net
                await net_run()
            finally:
                sys.argv = original_argv
        else:
            # Run from source directory using the detected python_exe
            console.print(f"[green]✓[/green] Using hanzo/net from {net_path}")
            if python_exe != sys.executable:
                console.print(f"[green]✓[/green] Using hanzo/net venv")
            else:
                console.print("[yellow]⚠[/yellow] Using system Python")

            # Change to net directory and run
            original_cwd = os.getcwd()
            try:
                os.chdir(net_path)

                # Set up environment
                env = os.environ.copy()
                if models:
                    env["NET_MODELS"] = ",".join(models)
                if name:
                    env["NET_NODE_NAME"] = name
                env["PYTHONPATH"] = (
                    os.path.join(net_path, "src") + ":" + env.get("PYTHONPATH", "")
                )

                console.print(f"\n[green]✓[/green] Starting net node")
                console.print(f"  Port: {port}")
                console.print(
                    f"  Models: {', '.join(models) if models else 'auto-detect'}"
                )
                console.print("\n[bold green]Hanzo Net is running![/bold green]")
                console.print("WebUI: http://localhost:52415")
                console.print("API: http://localhost:52415/v1/chat/completions")
                console.print("\nPress Ctrl+C to stop\n")

                # Build command line args
                cmd_args = [python_exe, "-m", "net.main"]
                if port != 52415:
                    cmd_args.extend(["--chatgpt-api-port", str(port)])
                if name:
                    cmd_args.extend(["--node-id", name])
                if network != "local":
                    cmd_args.extend(["--discovery-module", network])
                if models:
                    cmd_args.extend(["--default-model", models[0]])

                # Run net command with detected python
                process = subprocess.run(cmd_args, env=env, check=False)

                if process.returncode != 0 and process.returncode != -2:  # -2 is Ctrl+C
                    console.print(
                        f"[red]Net exited with code {process.returncode}[/red]"
                    )

            finally:
                os.chdir(original_cwd)

    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down node...[/yellow]")
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
