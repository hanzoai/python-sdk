"""CLI for hanzo-agents."""

import asyncio
import sys

import click
from rich.console import Console
from rich.table import Table

from . import __version__

console = Console()


@click.group(invoke_without_command=True)
@click.option("--version", "-v", is_flag=True, help="Show version")
@click.pass_context
def main(ctx, version):
    """Hanzo Agents - Multi-agent orchestration CLI.

    Run and orchestrate AI agents including Claude, Codex, Gemini, Grok, and more.

    Examples:
        hanzo-agents run claude "Explain this code"
        hanzo-agents list
        hanzo-agents status claude
    """
    if version:
        console.print(f"hanzo-agents {__version__}")
        return

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@main.command()
@click.argument("agent", required=False)
@click.argument("prompt", required=False)
@click.option("--timeout", "-t", default=300, help="Timeout in seconds")
def run(agent, prompt, timeout):
    """Run an agent with a prompt.

    Examples:
        hanzo-agents run claude "Explain this code"
        hanzo-agents run gemini "Review this PR"
    """
    if not agent:
        console.print("[yellow]Usage: hanzo-agents run <agent> <prompt>[/yellow]")
        console.print("\nAvailable agents: claude, codex, gemini, grok, qwen, vibe")
        return

    if not prompt:
        console.print("[yellow]Please provide a prompt[/yellow]")
        return

    try:
        from hanzo_tools.agent import AgentTool

        tool = AgentTool()
        result = asyncio.run(
            tool.call(None, action="run", name=agent, prompt=prompt, timeout=timeout)
        )
        console.print(result)
    except ImportError:
        console.print("[red]hanzo-tools-agent not installed[/red]")
        console.print("Run: pip install hanzo-tools-agent")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@main.command("list")
def list_agents():
    """List available agents."""
    table = Table(title="Available Agents")
    table.add_column("Agent", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Status", style="green")

    agents = [
        ("claude", "Anthropic Claude Code CLI", "✓"),
        ("codex", "OpenAI Codex CLI", "✓"),
        ("gemini", "Google Gemini CLI", "✓"),
        ("grok", "xAI Grok CLI", "✓"),
        ("qwen", "Alibaba Qwen CLI", "✓"),
        ("vibe", "Vibe coding agent", "✓"),
    ]

    for name, desc, status in agents:
        table.add_row(name, desc, status)

    console.print(table)


@main.command()
@click.argument("agent", required=False)
def status(agent):
    """Check agent status and availability."""
    try:
        from hanzo_tools.agent import AgentTool

        tool = AgentTool()
        if agent:
            result = asyncio.run(tool.call(None, action="status", name=agent))
        else:
            result = asyncio.run(tool.call(None, action="list"))
        console.print(result)
    except ImportError:
        console.print("[red]hanzo-tools-agent not installed[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@main.command()
def config():
    """Show agent configuration."""
    try:
        from hanzo_tools.agent import AgentTool

        tool = AgentTool()
        result = asyncio.run(tool.call(None, action="config"))
        console.print(result)
    except ImportError:
        console.print("[red]hanzo-tools-agent not installed[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
