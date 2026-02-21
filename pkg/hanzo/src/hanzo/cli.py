"""Main CLI entry point for Hanzo."""

import os
import sys
import shutil
import subprocess
from typing import Optional
from pathlib import Path

import click
from rich.console import Console

from .commands import (
    cx,
    fn,
    kv,
    ml,
    doc,
    env,
    iam,
    k8s,
    mcp,
    run,
    auth,
    auto,
    base,
    chat,
    flow,
    jobs,
    node,
    o11y,
    agent,
    cloud,
    miner,
    tasks,
    tools,
    config,
    events,
    growth,
    pubsub,
    queues,
    router,
    search,
    vector,
    install,
    network,
    secrets,
    storage,
    platform,
    git_provider,
)
from .utils.output import console

# Version
__version__ = "0.3.48"

HANZO_BIN = Path.home() / ".hanzo" / "bin"


def _find_binary(*names: str) -> str | None:
    """Search PATH and ~/.hanzo/bin for the first matching binary."""
    for name in names:
        path = shutil.which(name)
        if path:
            return path
        candidate = HANZO_BIN / name
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


def _auto_install_npm(package: str) -> bool:
    """Install an npm package globally. Returns True on success."""
    npm = shutil.which("npm") or shutil.which("pnpm")
    if not npm:
        return False
    try:
        console.print(f"[cyan]Installing {package}...[/cyan]")
        subprocess.run(
            [npm, "install", "-g", package],
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
        console.print(f"[green]Installed {package}[/green]")
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False


def _auto_install_pip(package: str) -> bool:
    """Install a Python package via uv or pip. Returns True on success."""
    uv = shutil.which("uv")
    if uv:
        cmd = [uv, "pip", "install", package]
    else:
        pip = shutil.which("pip3") or shutil.which("pip")
        if not pip:
            return False
        cmd = [pip, "install", package]
    try:
        console.print(f"[cyan]Installing {package}...[/cyan]")
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=120)
        console.print(f"[green]Installed {package}[/green]")
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False


def _passthrough(binary: str, args: tuple[str, ...]) -> None:
    """Replace the current process with the given binary."""
    os.execvp(binary, [binary] + list(args))


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="hanzo")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--json", is_flag=True, help="JSON output format")
@click.option("--config", "-c", type=click.Path(), help="Config file path")
@click.pass_context
def cli(ctx, verbose: bool, json: bool, config: Optional[str]):
    """Hanzo AI - Unified CLI for infrastructure, deployments, and services."""
    # Ensure context object exists
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["json"] = json
    ctx.obj["config"] = config
    ctx.obj["console"] = console

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# Register command groups
cli.add_command(agent.agent_group)
cli.add_command(auth.auth_group)
cli.add_command(auto.auto_group)
cli.add_command(base.base_group)
cli.add_command(node.cluster)
cli.add_command(cloud.cloud_group)
cli.add_command(config.config_group)
cli.add_command(cx.cx_group)
cli.add_command(doc.doc_group)
cli.add_command(env.env_group)
cli.add_command(events.events_group)
cli.add_command(flow.flow_group)
cli.add_command(fn.fn_group)
cli.add_command(git_provider.git_group)
cli.add_command(growth.growth_group)
cli.add_command(iam.iam_group)
cli.add_command(install.install_group)
cli.add_command(jobs.jobs_group)
cli.add_command(k8s.k8s_group)
cli.add_command(kv.kv_group)
cli.add_command(mcp.mcp_group)
cli.add_command(miner.miner_group)
cli.add_command(ml.ml_group)
cli.add_command(chat.chat_command)
cli.add_command(network.network_group)
cli.add_command(o11y.o11y_group)
cli.add_command(platform.platform_group)
cli.add_command(pubsub.pubsub_group)
cli.add_command(queues.queues_group)
cli.add_command(router.router_group)
cli.add_command(run.run_group)
cli.add_command(search.search_group)
cli.add_command(secrets.secrets_group)
cli.add_command(storage.storage_group)  # primary: hanzo s3
cli.add_command(storage.storage_group, name="storage")  # alias: hanzo storage
cli.add_command(tasks.tasks_group)
cli.add_command(tools.tools_group)
cli.add_command(vector.vector_group)

# Aliases
cli.add_command(doc.doc_group, name="docdb")  # docdb alias for doc
cli.add_command(fn.fn_group, name="fn")  # fn alias for function


# Quick aliases
@cli.command()
@click.argument("prompt", nargs=-1, required=True)
@click.option("--model", "-m", default="llama-3.2-3b", help="Model to use")
@click.option("--local/--cloud", default=True, help="Use local or cloud model")
@click.pass_context
def ask(ctx, prompt: tuple, model: str, local: bool):
    """Quick question to AI (alias for 'hanzo chat --once')."""
    import asyncio

    prompt_text = " ".join(prompt)
    asyncio.run(chat.ask_once(ctx, prompt_text, model, local))


# Observability quick commands
@cli.command()
@click.argument("query", required=False)
@click.option("--source", "-s", help="Log source/service")
@click.option("--follow", "-f", is_flag=True, help="Follow logs")
@click.option("--level", "-l", type=click.Choice(["debug", "info", "warn", "error"]))
@click.option("--limit", "-n", default=100, help="Max results")
def log(query: str, source: str, follow: bool, level: str, limit: int):
    """View service logs (shortcut for 'hanzo o11y log').

    \b
    Examples:
      hanzo log                     # Show recent logs
      hanzo log "error" -s my-api   # Search for errors
      hanzo log -f -s my-api        # Tail logs
    """
    if follow:
        console.print(
            f"[cyan]Tailing log{' for ' + source if source else ''}...[/cyan]"
        )
        console.print("[dim]Press Ctrl+C to stop[/dim]")
    elif query:
        console.print(f"[cyan]Searching log for '{query}'...[/cyan]")
    else:
        console.print("[cyan]Recent log entries:[/cyan]")
    console.print("[dim]No log entries found[/dim]")


@cli.command()
@click.argument("query", required=False)
@click.option("--service", "-s", help="Filter by service")
@click.option("--range", "-r", default="1h", help="Time range")
def metric(query: str, service: str, range: str):
    """View service metric (shortcut for 'hanzo o11y metric').

    \b
    Examples:
      hanzo metric                          # Show key metric
      hanzo metric "http_requests_total"    # Query specific metric
      hanzo metric -s my-api -r 24h         # Service metric for 24h
    """
    console.print(
        f"[cyan]Metric{' for ' + service if service else ''} (last {range}):[/cyan]"
    )
    console.print("[dim]No metric found[/dim]")


@cli.command()
@click.argument("trace_id", required=False)
@click.option("--service", "-s", help="Filter by service")
@click.option("--min-duration", "-d", help="Min duration (e.g., 100ms)")
def trace(trace_id: str, service: str, min_duration: str):
    """View distributed trace (shortcut for 'hanzo o11y trace').

    \b
    Examples:
      hanzo trace                     # Recent trace
      hanzo trace abc123              # Show specific trace
      hanzo trace -s my-api -d 1s     # Slow trace for service
    """
    if trace_id:
        console.print(f"[cyan]Trace {trace_id}:[/cyan]")
    else:
        console.print(
            f"[cyan]Recent trace{' for ' + service if service else ''}:[/cyan]"
        )
    console.print("[dim]No trace found[/dim]")


# Top-level login/logout shortcuts
@cli.command()
@click.option("--email", "-e", help="Email address")
@click.option("--password", "-p", help="Password (not recommended, use prompt)")
@click.option("--api-key", "-k", help="API key for direct authentication")
@click.option("--web", "-w", is_flag=True, help="Login via browser (device code flow)")
@click.option("--headless", is_flag=True, help="Headless mode - don't open browser")
@click.pass_context
def login(ctx, email, password, api_key, web, headless):
    """Login to Hanzo AI (shortcut for 'hanzo auth login').

    \b
    Examples:
      hanzo login              # Interactive device code flow
      hanzo login --web        # Open browser for authentication
      hanzo login -k sk-xxx   # Direct API key authentication
      hanzo login -e user@example.com  # Email/password login
    """
    ctx.invoke(
        auth.login,
        email=email,
        password=password,
        api_key=api_key,
        web=web,
        headless=headless,
    )


@cli.command()
@click.pass_context
def logout(ctx):
    """Logout from Hanzo AI (shortcut for 'hanzo auth logout')."""
    ctx.invoke(auth.logout)


@cli.command()
@click.pass_context
def whoami(ctx):
    """Show current user (shortcut for 'hanzo auth whoami')."""
    ctx.invoke(auth.whoami)


# Alias observe -> o11y
cli.add_command(o11y.o11y_group, name="observe")


# Alias deploy -> run
cli.add_command(run.run_group, name="deploy")


@cli.command()
@click.option("--name", "-n", default="hanzo-local", help="Node name")
@click.option("--port", "-p", default=8000, help="API port")
@click.pass_context
def serve(ctx, name: str, port: int):
    """Start local AI node (alias for 'hanzo node start')."""
    import asyncio

    asyncio.run(node.start_node(ctx, name, port))


@cli.command(
    context_settings={
        "ignore_unknown_options": True,
        "allow_extra_args": True,
        "allow_interspersed_args": False,
    },
)
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def net(args: tuple[str, ...]):
    """Start a Hanzo Network compute node (delegates to hanzod).

    All arguments are passed through to the hanzod binary.

    \b
    Examples:
        hanzo net                      Start compute node
        hanzo net --port 8080          Start on custom port
        hanzo net --help               Show hanzod help
    """
    binary = _find_binary("hanzod")
    if not binary:
        console.print("[yellow]hanzod not found. Installing...[/yellow]")
        if _auto_install_npm("@hanzo/hanzod"):
            binary = _find_binary("hanzod")
        if not binary:
            console.print("[red]Failed to install hanzod.[/red]")
            console.print("Install manually: curl -fsSL https://hanzo.sh | bash")
            raise SystemExit(1)
    _passthrough(binary, args)


@cli.command(
    context_settings={
        "ignore_unknown_options": True,
        "allow_extra_args": True,
        "allow_interspersed_args": False,
    },
)
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def dev(args: tuple[str, ...]):
    """Hanzo Dev — AI coding assistant (delegates to @hanzo/dev).

    All arguments are passed through to the hanzo-dev binary.

    \b
    Examples:
        hanzo dev                      Start Hanzo Dev
        hanzo dev mcp list             List MCP servers
        hanzo dev mcp add <name>       Add MCP server
        hanzo dev mcp remove <name>    Remove MCP server
        hanzo dev --help               Show dev binary help
    """
    binary = _find_binary("dev", "hanzo-dev")
    if not binary:
        console.print("[yellow]hanzo-dev not found. Installing @hanzo/dev...[/yellow]")
        if _auto_install_npm("@hanzo/dev"):
            binary = _find_binary("dev", "hanzo-dev")
        if not binary:
            console.print("[red]Failed to install @hanzo/dev.[/red]")
            console.print("Install manually: npm install -g @hanzo/dev")
            console.print("  or: curl -fsSL https://hanzo.sh | bash")
            raise SystemExit(1)
    _passthrough(binary, args)


cli.add_command(net, name="node")  # hanzo node = hanzo net


@cli.command()
@click.pass_context
def dashboard(ctx):
    """Open interactive dashboard."""
    from .interactive.dashboard import run_dashboard

    run_dashboard()


@cli.command()
@click.option("--json", "json_output", is_flag=True, help="JSON output format")
@click.pass_context
def doctor(ctx, json_output: bool):
    """Show installed Hanzo tools, versions, and system info.

    Checks all Hanzo CLI tools installed via uv, cargo, npm, or homebrew.
    """
    import shutil
    import platform

    from rich.panel import Panel
    from rich.table import Table

    console = ctx.obj.get("console", Console())

    if json_output:
        import json as json_module

        result = {"tools": [], "system": {}}

    # System info
    console.print(
        Panel.fit(
            f"[bold cyan]Hanzo Doctor[/bold cyan]\n[dim]System: {platform.system()} {platform.machine()}[/dim]",
            border_style="cyan",
        )
    )
    console.print()

    # Check uv tools
    tools_found = []

    console.print("[bold]Python Tools (uv):[/bold]")
    try:
        result_uv = subprocess.run(
            ["uv", "tool", "list"], capture_output=True, text=True, timeout=10
        )
        if result_uv.returncode == 0:
            table = Table(show_header=True, header_style="bold")
            table.add_column("Package", style="cyan")
            table.add_column("Version", style="green")
            table.add_column("Path", style="dim")

            for line in result_uv.stdout.strip().split("\n"):
                if line.startswith("hanzo"):
                    parts = line.split()
                    if len(parts) >= 2:
                        name, version = parts[0], parts[1]
                        path = shutil.which(name) or f"~/.local/bin/{name}"
                        table.add_row(name, version, path)
                        tools_found.append(
                            {
                                "name": name,
                                "version": version,
                                "path": path,
                                "source": "uv",
                            }
                        )

            if tools_found:
                console.print(table)
            else:
                console.print("  [dim](none installed)[/dim]")
        else:
            console.print("  [dim](uv not available)[/dim]")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        console.print("  [dim](uv not installed)[/dim]")

    console.print()

    # Check for other AI CLI tools
    console.print("[bold]AI CLI Tools:[/bold]")
    ai_tools = [
        ("claude", "Claude Code"),
        ("gemini", "Gemini CLI"),
        ("codex", "OpenAI Codex"),
        ("cursor", "Cursor"),
        ("aider", "Aider"),
    ]

    ai_table = Table(show_header=True, header_style="bold")
    ai_table.add_column("Tool", style="cyan")
    ai_table.add_column("Version", style="green")
    ai_table.add_column("Path", style="dim")

    ai_found = False
    for cmd, name in ai_tools:
        path = shutil.which(cmd)
        if path:
            ai_found = True
            try:
                ver_result = subprocess.run(
                    [cmd, "--version"], capture_output=True, text=True, timeout=5
                )
                version = (
                    ver_result.stdout.strip().split("\n")[0]
                    if ver_result.returncode == 0
                    else "?"
                )
            except Exception:
                version = "?"
            ai_table.add_row(name, version, path)

    if ai_found:
        console.print(ai_table)
    else:
        console.print("  [dim](none detected)[/dim]")

    console.print()

    # Check API keys
    console.print("[bold]API Keys:[/bold]")
    api_keys = [
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "GOOGLE_API_KEY",
        "GEMINI_API_KEY",
        "XAI_API_KEY",
        "GROQ_API_KEY",
        "GITHUB_TOKEN",
        "HF_TOKEN",
    ]

    keys_found = []
    for key in api_keys:
        if os.environ.get(key):
            keys_found.append(key)
            console.print(f"  [green]✓[/green] {key}")

    if not keys_found:
        console.print("  [dim](none set)[/dim]")

    console.print()
    console.print("[bold green]✓[/bold green] Doctor check complete")

    if json_output:
        result["tools"] = tools_found
        result["system"] = {
            "platform": platform.system(),
            "arch": platform.machine(),
            "python": platform.python_version(),
        }
        print(json_module.dumps(result, indent=2))


@cli.command()
@click.option("--all", "upgrade_all", is_flag=True, help="Upgrade all Hanzo tools")
@click.option("--force", "-f", is_flag=True, help="Force reinstall")
@click.argument("packages", nargs=-1)
@click.pass_context
def update(ctx, upgrade_all: bool, force: bool, packages: tuple):
    """Update Hanzo CLI tools to latest versions.

    \b
    Examples:
      hanzo update              # Update hanzo and hanzo-mcp
      hanzo update --all        # Update all Hanzo tools
      hanzo update hanzo-mcp    # Update specific package
      hanzo update --force      # Force reinstall
    """
    console = ctx.obj.get("console", Console())

    # Default packages to update
    default_packages = ["hanzo", "hanzo-mcp"]
    all_packages = [
        "hanzo",
        "hanzo-mcp",
        "hanzo-agents",
        "hanzo-memory",
        "hanzo-network",
    ]

    if packages:
        to_update = list(packages)
    elif upgrade_all:
        to_update = all_packages
    else:
        to_update = default_packages

    console.print("[bold cyan]Updating Hanzo CLI tools...[/bold cyan]")
    console.print()

    # Check if uv is available
    import shutil

    if not shutil.which("uv"):
        console.print("[red]Error:[/red] uv is not installed")
        console.print("Install with: curl -LsSf https://astral.sh/uv/install.sh | sh")
        return

    success = []
    failed = []

    for pkg in to_update:
        console.print(f"  Updating [cyan]{pkg}[/cyan]...", end=" ")
        try:
            cmd = ["uv", "tool", "upgrade" if not force else "install", pkg]
            if force:
                cmd.append("--force")

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if result.returncode == 0:
                # Get new version
                ver_result = subprocess.run(
                    ["uv", "tool", "list"], capture_output=True, text=True, timeout=10
                )
                version = "?"
                for line in ver_result.stdout.split("\n"):
                    if line.startswith(pkg + " "):
                        version = line.split()[1] if len(line.split()) > 1 else "?"
                        break

                console.print(f"[green]✓[/green] {version}")
                success.append(pkg)
            else:
                # Try install if upgrade failed (package not installed)
                if "not installed" in result.stderr.lower():
                    install_result = subprocess.run(
                        ["uv", "tool", "install", pkg],
                        capture_output=True,
                        text=True,
                        timeout=120,
                    )
                    if install_result.returncode == 0:
                        console.print("[green]✓[/green] installed")
                        success.append(pkg)
                    else:
                        console.print(f"[red]✗[/red] {install_result.stderr.strip()}")
                        failed.append(pkg)
                else:
                    console.print(f"[red]✗[/red] {result.stderr.strip()}")
                    failed.append(pkg)

        except subprocess.TimeoutExpired:
            console.print("[red]✗[/red] timeout")
            failed.append(pkg)
        except Exception as e:
            console.print(f"[red]✗[/red] {e}")
            failed.append(pkg)

    console.print()
    if success:
        console.print(f"[bold green]✓[/bold green] Updated: {', '.join(success)}")
    if failed:
        console.print(f"[bold red]✗[/bold red] Failed: {', '.join(failed)}")


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
