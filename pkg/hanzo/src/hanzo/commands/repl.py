"""REPL command for interactive AI sessions."""

import os
import sys

import click

from ..utils.output import console


@click.group(name="repl")
def repl_group():
    """Interactive REPL for AI and MCP tools."""
    pass


@repl_group.command()
@click.option("--model", "-m", help="Default model to use")
@click.option("--local/--cloud", default=False, help="Use local cluster")
@click.option("--ipython", is_flag=True, help="Use IPython interface")
@click.option("--tui", is_flag=True, help="Use TUI interface")
@click.option("--voice", is_flag=True, help="Enable voice mode")
@click.pass_context
def start(ctx, model: str, local: bool, ipython: bool, tui: bool, voice: bool):
    """Start interactive REPL (like Claude Code in terminal)."""
    try:
        # Set up environment
        if model:
            os.environ["HANZO_DEFAULT_MODEL"] = model
        if local:
            os.environ["HANZO_USE_LOCAL"] = "true"
        if voice:
            os.environ["HANZO_ENABLE_VOICE"] = "true"

        if ipython:
            from hanzo_repl.ipython_repl import main
        elif tui:
            from hanzo_repl.textual_repl import main
        else:
            from hanzo_repl.cli import main

        console.print("[cyan]Starting Hanzo REPL...[/cyan]")
        console.print("All MCP tools available. Type 'help' for commands.\n")

        sys.exit(main())

    except ImportError:
        console.print("[red]Error:[/red] hanzo-repl not installed")
        console.print("Install with: pip install hanzo[repl]")
        console.print("\nFeatures:")
        console.print("  • Direct access to 70+ MCP tools")
        console.print("  • Chat with AI that can use tools")
        console.print("  • IPython magic commands")
        console.print("  • Beautiful TUI interface")
        console.print("  • Voice mode (optional)")


@repl_group.command()
@click.pass_context
def info(ctx):
    """Show REPL information and status."""
    try:
        import hanzo_mcp
        from hanzo_repl import __version__

        console.print("[cyan]Hanzo REPL[/cyan]")
        console.print(f"  Version: {__version__}")
        console.print(f"  MCP Tools: {len(hanzo_mcp.get_all_tools())}")

        # Check available interfaces
        interfaces = []
        try:
            import IPython

            interfaces.append("IPython")
        except ImportError:
            pass

        try:
            import textual

            interfaces.append("TUI")
        except ImportError:
            pass

        try:
            import speech_recognition

            interfaces.append("Voice")
        except ImportError:
            pass

        console.print(f"  Interfaces: {', '.join(interfaces) or 'Basic'}")

        # Check LLM providers
        providers = []
        if os.environ.get("OPENAI_API_KEY"):
            providers.append("OpenAI")
        if os.environ.get("ANTHROPIC_API_KEY"):
            providers.append("Anthropic")
        if os.environ.get("HANZO_API_KEY"):
            providers.append("Hanzo AI")

        console.print(f"  Providers: {', '.join(providers) or 'None configured'}")

        if not providers:
            console.print("\n[yellow]No LLM providers configured[/yellow]")
            console.print(
                "Set one of: OPENAI_API_KEY, ANTHROPIC_API_KEY, HANZO_API_KEY"
            )

    except ImportError:
        console.print("[red]Error:[/red] hanzo-repl not installed")


@repl_group.command()
@click.option(
    "--interface", type=click.Choice(["all", "ipython", "tui", "voice"]), default="all"
)
@click.pass_context
def install_extras(ctx, interface: str):
    """Install optional REPL components."""
    import subprocess

    packages = {
        "ipython": ["ipython>=8.0.0", "jupyter>=1.0.0"],
        "tui": ["textual>=0.41.0", "textual-dev>=1.2.0"],
        "voice": ["speechrecognition>=3.10.0", "pyttsx3>=2.90", "pyaudio>=0.2.11"],
    }

    if interface == "all":
        to_install = []
        for pkgs in packages.values():
            to_install.extend(pkgs)
    else:
        to_install = packages.get(interface, [])

    if to_install:
        console.print(f"[cyan]Installing {interface} components...[/cyan]")
        cmd = [sys.executable, "-m", "pip", "install"] + to_install

        try:
            subprocess.run(cmd, check=True)
            console.print(f"[green]✓[/green] Installed {interface} components")
        except subprocess.CalledProcessError:
            console.print(f"[red]Failed to install components[/red]")
            console.print("Try manually: pip install hanzo-repl[voice]")


@repl_group.command()
@click.argument("command", nargs=-1, required=True)
@click.option("--model", "-m", help="Model to use")
@click.pass_context
def exec(ctx, command: tuple, model: str):
    """Execute a command in REPL and exit."""
    try:
        import asyncio

        from hanzo_repl import create_repl

        repl = create_repl(model=model)
        command_str = " ".join(command)

        async def run():
            result = await repl.execute(command_str)
            console.print(result)

        asyncio.run(run())

    except ImportError as e:
        console.print(f"[red]Import Error:[/red] {e}")
        console.print(
            "[yellow]Note:[/yellow] hanzo-repl may not be installed correctly"
        )
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@repl_group.command()
@click.pass_context
def demo(ctx):
    """Run REPL demo showcasing features."""
    try:
        from hanzo_repl.demos import run_demo

        console.print("[cyan]Running Hanzo REPL demo...[/cyan]\n")
        run_demo()

    except ImportError:
        console.print("[red]Error:[/red] hanzo-repl not installed")
        console.print("\nThe demo would show:")
        console.print("  • File operations with MCP tools")
        console.print("  • Code search and analysis")
        console.print("  • AI chat with tool usage")
        console.print("  • IPython magic commands")
        console.print("  • Voice interaction (if available)")
