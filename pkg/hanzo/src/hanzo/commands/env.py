"""Hanzo Env - Environment management CLI.

Environment configuration and switching.
"""

import click
from rich import box
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax

from ..utils.output import console


@click.group(name="env")
def env_group():
    """Hanzo Env - Environment management.

    \b
    Environments:
      hanzo env list                 # List environments
      hanzo env create               # Create environment
      hanzo env use                  # Switch environment
      hanzo env current              # Show current environment
      hanzo env delete               # Delete environment

    \b
    Variables:
      hanzo env vars                 # List env variables
      hanzo env set                  # Set variable
      hanzo env unset                # Unset variable
      hanzo env diff                 # Compare environments
    """
    pass


# ============================================================================
# Environment Management
# ============================================================================


@env_group.command(name="list")
@click.option("--project", "-p", help="Project ID")
def env_list(project: str):
    """List all environments."""
    table = Table(title="Environments", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("URL", style="dim")
    table.add_column("Variables", style="yellow")
    table.add_column("Updated", style="dim")

    table.add_row(
        "development", "[green]●[/green] active", "dev.app.hanzo.ai", "12", "2024-01-15"
    )
    table.add_row(
        "staging", "[yellow]●[/yellow] idle", "staging.app.hanzo.ai", "12", "2024-01-14"
    )
    table.add_row(
        "production", "[green]●[/green] active", "app.hanzo.ai", "15", "2024-01-13"
    )

    console.print(table)


@env_group.command(name="create")
@click.argument("name")
@click.option("--from", "from_env", help="Clone from existing environment")
@click.option("--description", "-d", help="Environment description")
def env_create(name: str, from_env: str, description: str):
    """Create a new environment."""
    console.print(f"[green]✓[/green] Environment '{name}' created")
    if from_env:
        console.print(f"  Cloned from: {from_env}")
    console.print(f"  URL: {name}.app.hanzo.ai")


@env_group.command(name="use")
@click.argument("name")
def env_use(name: str):
    """Switch to an environment."""
    console.print(f"[green]✓[/green] Switched to environment '{name}'")


@env_group.command(name="current")
def env_current():
    """Show current environment."""
    console.print(
        Panel(
            "[cyan]Environment:[/cyan] development\n"
            "[cyan]Project:[/cyan] my-app\n"
            "[cyan]URL:[/cyan] dev.app.hanzo.ai\n"
            "[cyan]Variables:[/cyan] 12",
            title="Current Environment",
            border_style="cyan",
        )
    )


@env_group.command(name="delete")
@click.argument("name")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
def env_delete(name: str, force: bool):
    """Delete an environment."""
    if name == "production":
        console.print("[red]Error: Cannot delete production environment[/red]")
        return
    if not force:
        from rich.prompt import Confirm

        if not Confirm.ask(f"[red]Delete environment '{name}'?[/red]"):
            return
    console.print(f"[green]✓[/green] Environment '{name}' deleted")


# ============================================================================
# Environment Variables
# ============================================================================


@env_group.command(name="vars")
@click.option("--env", "-e", default="development", help="Environment name")
@click.option("--reveal", "-r", is_flag=True, help="Show secret values")
def env_vars(env: str, reveal: bool):
    """List environment variables."""
    table = Table(title=f"Variables: {env}", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Value", style="white")
    table.add_column("Source", style="dim")

    table.add_row(
        "DATABASE_URL", "●●●●●●●●" if not reveal else "postgres://...", "secret"
    )
    table.add_row("API_KEY", "●●●●●●●●" if not reveal else "sk-...", "secret")
    table.add_row("LOG_LEVEL", "debug", "config")
    table.add_row("NODE_ENV", "development", "config")

    console.print(table)


@env_group.command(name="set")
@click.argument("name")
@click.argument("value")
@click.option("--env", "-e", default="development", help="Environment name")
@click.option("--secret", "-s", is_flag=True, help="Mark as secret")
def env_set(name: str, value: str, env: str, secret: bool):
    """Set an environment variable."""
    console.print(f"[green]✓[/green] Set {name}={value if not secret else '●●●●●●●●'}")
    console.print(f"  Environment: {env}")


@env_group.command(name="unset")
@click.argument("name")
@click.option("--env", "-e", default="development", help="Environment name")
def env_unset(name: str, env: str):
    """Unset an environment variable."""
    console.print(f"[green]✓[/green] Unset {name}")
    console.print(f"  Environment: {env}")


@env_group.command(name="diff")
@click.argument("env1")
@click.argument("env2")
def env_diff(env1: str, env2: str):
    """Compare two environments."""
    console.print(f"[cyan]Comparing {env1} vs {env2}:[/cyan]\n")

    table = Table(box=box.SIMPLE)
    table.add_column("Variable", style="cyan")
    table.add_column(env1, style="green")
    table.add_column(env2, style="yellow")
    table.add_column("Status", style="white")

    table.add_row("LOG_LEVEL", "debug", "info", "[yellow]changed[/yellow]")
    table.add_row("FEATURE_FLAG", "true", "false", "[yellow]changed[/yellow]")
    table.add_row("NEW_VAR", "-", "value", "[green]added[/green]")
    table.add_row("OLD_VAR", "value", "-", "[red]removed[/red]")

    console.print(table)


@env_group.command(name="push")
@click.option("--from", "from_env", required=True, help="Source environment")
@click.option("--to", "to_env", required=True, help="Target environment")
@click.option("--vars", "-v", multiple=True, help="Specific variables to push")
@click.option("--dry-run", is_flag=True, help="Show what would be pushed")
def env_push(from_env: str, to_env: str, vars: tuple, dry_run: bool):
    """Push variables from one environment to another."""
    if dry_run:
        console.print(f"[dim]Dry run - would push from {from_env} to {to_env}[/dim]")
        return
    console.print(f"[green]✓[/green] Pushed variables from {from_env} to {to_env}")
