"""Main CLI entry point for Hanzo."""

import os
import sys
import signal
import asyncio
import subprocess
from typing import Optional

import click
from rich.console import Console

from .commands import (
    mcp,
    auth,
    chat,
    node,
    repl,
    agent,
    miner,
    tools,
    config,
    router,
    network,
)
from .utils.output import console
from .interactive.repl import HanzoREPL
from .interactive.enhanced_repl import EnhancedHanzoREPL
from .ui.startup import show_startup

# Version
__version__ = "0.3.23"


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
            # Show startup UI (unless in quiet mode)
            if not ctx.obj.get("quiet") and not os.environ.get("HANZO_NO_STARTUP"):
                show_startup(minimal=os.environ.get("HANZO_MINIMAL_UI") == "1")
            
            # Enter interactive REPL mode
            try:
                # Use enhanced REPL if available, otherwise fallback
                use_enhanced = os.environ.get("HANZO_ENHANCED_REPL", "1") == "1"
                if use_enhanced:
                    repl = EnhancedHanzoREPL(console=console)
                else:
                    repl = HanzoREPL(console=console)
                asyncio.run(repl.run())
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted[/yellow]")
            except EOFError:
                console.print("\n[yellow]Goodbye![/yellow]")


# Register command groups
cli.add_command(agent.agent_group)
cli.add_command(auth.auth_group)
cli.add_command(node.cluster)
cli.add_command(mcp.mcp_group)
cli.add_command(miner.miner_group)
cli.add_command(chat.chat_command)
cli.add_command(repl.repl_group)
cli.add_command(tools.tools_group)
cli.add_command(network.network_group)
cli.add_command(config.config_group)
cli.add_command(router.router_group)


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
@click.option("--name", "-n", default="hanzo-local", help="Node name")
@click.option("--port", "-p", default=8000, help="API port")
@click.pass_context
def serve(ctx, name: str, port: int):
    """Start local AI node (alias for 'hanzo node start')."""
    asyncio.run(node.start_node(ctx, name, port))


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
    try:
        asyncio.run(start_compute_node(ctx, name, port, network, models, max_jobs))
    except KeyboardInterrupt:
        # Already handled in start_compute_node
        pass


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
    try:
        asyncio.run(start_compute_node(ctx, name, port, network, models, max_jobs))
    except KeyboardInterrupt:
        # Already handled in start_compute_node
        pass


@cli.command()
@click.option("--workspace", default="~/.hanzo/dev", help="Workspace directory")
@click.option(
    "--orchestrator",
    default="gpt-5",
    help="Orchestrator: gpt-5, router:gpt-4o, direct:claude, codex, gpt-5-pro-codex, cost-optimized",
)
@click.option(
    "--orchestrator-mode",
    type=click.Choice(["router", "direct", "codex", "hybrid", "local"]),
    default=None,
    help="Force orchestrator mode (router via hanzo-router, direct API, codex, hybrid, local)",
)
@click.option(
    "--router-endpoint",
    default=None,
    help="Hanzo router endpoint (default: http://localhost:4000)",
)
@click.option("--claude-path", help="Path to Claude Code executable")
@click.option("--monitor", is_flag=True, help="Start in monitor mode")
@click.option("--repl", is_flag=True, help="Start REPL interface (default)")
@click.option("--instances", type=int, default=2, help="Number of worker agents")
@click.option("--mcp-tools", is_flag=True, default=True, help="Enable all MCP tools")
@click.option(
    "--network-mode", is_flag=True, default=True, help="Network agents together"
)
@click.option(
    "--guardrails", is_flag=True, default=True, help="Enable code quality guardrails"
)
@click.option(
    "--use-network/--no-network", default=True, help="Use hanzo-network if available"
)
@click.option(
    "--use-hanzo-net",
    is_flag=True,
    help="Use hanzo/net for local AI (auto-enabled with local: models)",
)
@click.option(
    "--hanzo-net-port",
    type=int,
    default=52415,
    help="Port for hanzo/net (default: 52415)",
)
@click.pass_context
def dev(
    ctx,
    workspace: str,
    orchestrator: str,
    orchestrator_mode: str,
    router_endpoint: str,
    claude_path: str,
    monitor: bool,
    repl: bool,
    instances: int,
    mcp_tools: bool,
    network_mode: bool,
    guardrails: bool,
    use_network: bool,
    use_hanzo_net: bool,
    hanzo_net_port: int,
):
    """Start Hanzo Dev - AI Coding OS with configurable orchestrator.

    This creates a multi-agent system where:
    - Configurable orchestrator (GPT-5, GPT-4, Claude, or LOCAL) manages the network
    - Local AI via hanzo/net for cost-effective orchestration
    - Worker agents (Claude + local) handle code implementation
    - Critic agents review and improve code (System 2 thinking)
    - Cost-optimized routing (local models for simple tasks)
    - All agents can use MCP tools
    - Agents can call each other recursively
    - Guardrails prevent code degradation
    - Auto-recovery from failures

    Examples:
        hanzo dev                                    # GPT-5 orchestrator (default)
        hanzo dev --orchestrator gpt-4               # GPT-4 orchestrator
        hanzo dev --orchestrator claude-3-5-sonnet   # Claude orchestrator
        hanzo dev --orchestrator local:llama3.2      # Local Llama 3.2 via hanzo/net
        hanzo dev --use-hanzo-net                    # Enable local AI workers
        hanzo dev --instances 4                      # More worker agents
        hanzo dev --monitor                          # Auto-monitor and restart mode
    """
    from .dev import run_dev_orchestrator
    from .orchestrator_config import OrchestratorMode, get_orchestrator_config

    # Get orchestrator configuration
    orch_config = get_orchestrator_config(orchestrator)

    # Override mode if specified
    if orchestrator_mode:
        orch_config.mode = OrchestratorMode(orchestrator_mode)

    # Override router endpoint if specified
    if router_endpoint and orch_config.router:
        orch_config.router.endpoint = router_endpoint

    # Auto-enable hanzo net if using local orchestrator
    if orchestrator.startswith("local:") or orch_config.mode == OrchestratorMode.LOCAL:
        use_hanzo_net = True

    # Show configuration
    console.print(f"[bold cyan]Orchestrator Configuration[/bold cyan]")
    console.print(f"  Mode: {orch_config.mode.value}")
    console.print(f"  Primary Model: {orch_config.primary_model}")
    if orch_config.router:
        console.print(f"  Router Endpoint: {orch_config.router.endpoint}")
    if orch_config.codex:
        console.print(f"  Codex Model: {orch_config.codex.model}")
    console.print(
        f"  Cost Optimization: {'Enabled' if orch_config.enable_cost_optimization else 'Disabled'}"
    )
    console.print()

    asyncio.run(
        run_dev_orchestrator(
            workspace=workspace,
            orchestrator_model=orchestrator,
            orchestrator_config=orch_config,  # Pass the config
            claude_path=claude_path,
            monitor=monitor,
            repl=repl or not monitor,  # Default to REPL if not monitoring
            instances=instances,
            mcp_tools=mcp_tools,
            network_mode=network_mode,
            guardrails=guardrails,
            use_network=use_network,
            use_hanzo_net=use_hanzo_net,
            hanzo_net_port=hanzo_net_port,
            console=ctx.obj.get("console", console),
        )
    )


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

                # Set up signal handlers for async version
                stop_event = asyncio.Event()

                def async_signal_handler(signum, frame):
                    console.print("\n[yellow]Stopping hanzo net...[/yellow]")
                    stop_event.set()

                signal.signal(signal.SIGINT, async_signal_handler)
                signal.signal(signal.SIGTERM, async_signal_handler)

                # Run net with proper signal handling
                try:
                    net_task = asyncio.create_task(net_run())
                    stop_task = asyncio.create_task(stop_event.wait())

                    # Wait for either net to complete or stop signal
                    done, pending = await asyncio.wait(
                        [net_task, stop_task], return_when=asyncio.FIRST_COMPLETED
                    )

                    # Cancel pending tasks
                    for task in pending:
                        task.cancel()
                        try:
                            await task
                        except asyncio.CancelledError:
                            pass

                    # Check if we stopped due to signal
                    if stop_task in done:
                        console.print("[green]✓[/green] Node stopped gracefully")
                except asyncio.CancelledError:
                    console.print("[yellow]Cancelled[/yellow]")
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

                # Run net command with detected python in a more signal-friendly way
                # Create new process group for better signal handling
                process = subprocess.Popen(
                    cmd_args,
                    env=env,
                    preexec_fn=os.setsid if hasattr(os, "setsid") else None,
                )

                # Set up signal handlers to forward to subprocess group
                def signal_handler(signum, frame):
                    if process.poll() is None:  # Process is still running
                        console.print("\n[yellow]Stopping hanzo net...[/yellow]")
                        try:
                            # Send signal to entire process group
                            if hasattr(os, "killpg"):
                                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                            else:
                                process.terminate()
                            process.wait(timeout=5)  # Wait up to 5 seconds
                        except subprocess.TimeoutExpired:
                            console.print("[yellow]Force stopping...[/yellow]")
                            if hasattr(os, "killpg"):
                                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                            else:
                                process.kill()
                            process.wait()
                        except ProcessLookupError:
                            pass  # Process already terminated
                    raise KeyboardInterrupt

                # Register signal handlers
                signal.signal(signal.SIGINT, signal_handler)
                signal.signal(signal.SIGTERM, signal_handler)

                # Wait for process to complete
                returncode = process.wait()

                if returncode != 0 and returncode != -2:  # -2 is Ctrl+C
                    console.print(f"[red]Net exited with code {returncode}[/red]")

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
