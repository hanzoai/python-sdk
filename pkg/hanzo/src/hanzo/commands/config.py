"""Configuration management commands."""

import json

import yaml
import click
from rich.syntax import Syntax

from ..utils.output import console


@click.group(name="config")
def config_group():
    """Manage Hanzo configuration."""
    pass


@config_group.command()
@click.option("--global", "is_global", is_flag=True, help="Show global config")
@click.option("--local", "is_local", is_flag=True, help="Show local config")
@click.option("--system", is_flag=True, help="Show system config")
@click.pass_context
def show(ctx, is_global: bool, is_local: bool, system: bool):
    """Show configuration."""
    from ..utils.config import load_config, get_config_paths

    # Determine which configs to show
    show_all = not (is_global or is_local or system)

    configs = {}
    paths = get_config_paths()

    if show_all or system:
        if paths["system"].exists():
            configs["System"] = (paths["system"], load_config(paths["system"]))

    if show_all or is_global:
        if paths["global"].exists():
            configs["Global"] = (paths["global"], load_config(paths["global"]))

    if show_all or is_local:
        if paths["local"].exists():
            configs["Local"] = (paths["local"], load_config(paths["local"]))

    # Merge and show
    if configs:
        for name, (path, config) in configs.items():
            console.print(f"[cyan]{name} Config:[/cyan] {path}")

            # Pretty print config
            if config:
                syntax = Syntax(
                    yaml.dump(config, default_flow_style=False),
                    "yaml",
                    theme="monokai",
                    line_numbers=False,
                )
                console.print(syntax)
            else:
                console.print("[dim]Empty[/dim]")
            console.print()
    else:
        console.print("[yellow]No configuration found[/yellow]")
        console.print("Create one with: hanzo config set <key> <value>")


@config_group.command()
@click.argument("key")
@click.argument("value")
@click.option("--global", "is_global", is_flag=True, help="Set in global config")
@click.option("--local", "is_local", is_flag=True, help="Set in local config")
@click.pass_context
def set(ctx, key: str, value: str, is_global: bool, is_local: bool):
    """Set configuration value."""
    from ..utils.config import load_config, save_config, get_config_paths

    # Determine target config
    paths = get_config_paths()

    if is_local:
        config_path = paths["local"]
        config_name = "local"
    else:  # Default to global
        config_path = paths["global"]
        config_name = "global"

    # Load existing config
    config = load_config(config_path) if config_path.exists() else {}

    # Parse value
    try:
        # Try to parse as JSON first
        parsed_value = json.loads(value)
    except json.JSONDecodeError:
        # Check for boolean strings
        if value.lower() == "true":
            parsed_value = True
        elif value.lower() == "false":
            parsed_value = False
        else:
            # Keep as string
            parsed_value = value

    # Set value (support nested keys with dot notation)
    keys = key.split(".")
    current = config

    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        current = current[k]

    current[keys[-1]] = parsed_value

    # Save config
    save_config(config_path, config)

    console.print(
        f"[green]✓[/green] Set {key} = {parsed_value} in {config_name} config"
    )


@config_group.command()
@click.argument("key")
@click.option("--global", "is_global", is_flag=True, help="Get from global config")
@click.option("--local", "is_local", is_flag=True, help="Get from local config")
@click.pass_context
def get(ctx, key: str, is_global: bool, is_local: bool):
    """Get configuration value."""
    from ..utils.config import get_config_value

    scope = "local" if is_local else ("global" if is_global else None)
    value = get_config_value(key, scope=scope)

    if value is not None:
        if isinstance(value, (dict, list)):
            console.print_json(data=value)
        else:
            console.print(value)
    else:
        console.print(f"[yellow]Key not found: {key}[/yellow]")


@config_group.command()
@click.argument("key")
@click.option("--global", "is_global", is_flag=True, help="Unset from global config")
@click.option("--local", "is_local", is_flag=True, help="Unset from local config")
@click.pass_context
def unset(ctx, key: str, is_global: bool, is_local: bool):
    """Unset configuration value."""
    from ..utils.config import load_config, save_config, get_config_paths

    # Determine target config
    paths = get_config_paths()

    if is_local:
        config_path = paths["local"]
        config_name = "local"
    else:  # Default to global
        config_path = paths["global"]
        config_name = "global"

    if not config_path.exists():
        console.print(f"[yellow]No {config_name} config found[/yellow]")
        return

    # Load config
    config = load_config(config_path)

    # Remove value (support nested keys)
    keys = key.split(".")
    current = config

    try:
        for k in keys[:-1]:
            current = current[k]

        if keys[-1] in current:
            del current[keys[-1]]
            save_config(config_path, config)
            console.print(f"[green]✓[/green] Unset {key} from {config_name} config")
        else:
            console.print(f"[yellow]Key not found: {key}[/yellow]")
    except KeyError:
        console.print(f"[yellow]Key not found: {key}[/yellow]")


@config_group.command()
@click.option("--system", is_flag=True, help="Edit system config")
@click.option("--global", "is_global", is_flag=True, help="Edit global config")
@click.option("--local", "is_local", is_flag=True, help="Edit local config")
@click.pass_context
def edit(ctx, system: bool, is_global: bool, is_local: bool):
    """Edit configuration file in editor."""
    import os
    import subprocess

    from ..utils.config import get_config_paths

    # Determine which config to edit
    paths = get_config_paths()

    if system:
        config_path = paths["system"]
    elif is_local:
        config_path = paths["local"]
    else:  # Default to global
        config_path = paths["global"]

    # Ensure file exists
    if not config_path.exists():
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text("# Hanzo configuration\n")

    # Get editor
    editor = os.environ.get("EDITOR", "vi")

    # Open in editor
    try:
        subprocess.run([editor, str(config_path)], check=True)
        console.print(f"[green]✓[/green] Edited {config_path}")
    except subprocess.CalledProcessError:
        console.print(f"[red]Failed to open editor[/red]")
    except FileNotFoundError:
        console.print(f"[red]Editor not found: {editor}[/red]")
        console.print("Set EDITOR environment variable to specify editor")


@config_group.command()
@click.pass_context
def init(ctx):
    """Initialize configuration."""
    from ..utils.config import init_config

    try:
        paths = init_config()
        console.print("[green]✓[/green] Initialized configuration")
        console.print(f"  Global: {paths['global']}")
        console.print(f"  Local: {paths.get('local', 'Not in project')}")
    except Exception as e:
        console.print(f"[red]Failed to initialize config: {e}[/red]")
