"""Tools management commands."""

import click
from rich.table import Table
from rich.syntax import Syntax

from ..utils.output import console


@click.group(name="tools")
def tools_group():
    """Manage Hanzo tools and plugins."""
    pass


@tools_group.command(name="list")
@click.option("--category", "-c", help="Filter by category")
@click.option("--installed", is_flag=True, help="Show only installed tools")
@click.pass_context
async def list_tools(ctx, category: str, installed: bool):
    """List available tools."""
    try:
        from hanzo_tools import get_tool_registry
    except ImportError:
        console.print("[red]Error:[/red] hanzo-tools not installed")
        console.print("Install with: pip install hanzo[tools]")
        return

    registry = get_tool_registry()

    with console.status("Loading tools..."):
        try:
            tools = await registry.list_tools(
                category=category, installed_only=installed
            )
        except Exception as e:
            console.print(f"[red]Failed to load tools: {e}[/red]")
            return

    if not tools:
        console.print("[yellow]No tools found[/yellow]")
        return

    # Group by category
    categories = {}
    for tool in tools:
        cat = tool.get("category", "uncategorized")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(tool)

    # Display tools
    for cat, cat_tools in sorted(categories.items()):
        table = Table(title=f"{cat.title()} Tools")
        table.add_column("Name", style="cyan")
        table.add_column("Version", style="green")
        table.add_column("Description", style="white")
        table.add_column("Status", style="yellow")

        for tool in sorted(cat_tools, key=lambda t: t["name"]):
            table.add_row(
                tool["name"],
                tool.get("version", "latest"),
                tool.get("description", ""),
                "installed" if tool.get("installed") else "available",
            )

        console.print(table)
        if len(categories) > 1:
            console.print()


@tools_group.command()
@click.argument("tool_name")
@click.option("--version", "-v", help="Specific version to install")
@click.pass_context
async def install(ctx, tool_name: str, version: str):
    """Install a tool."""
    try:
        from hanzo_tools import get_tool_registry
    except ImportError:
        console.print("[red]Error:[/red] hanzo-tools not installed")
        return

    registry = get_tool_registry()

    with console.status(f"Installing {tool_name}..."):
        try:
            result = await registry.install_tool(name=tool_name, version=version)

            console.print(
                f"[green]✓[/green] Installed {tool_name} v{result['version']}"
            )

            if deps := result.get("dependencies_installed"):
                console.print(f"  Dependencies: {', '.join(deps)}")

            if config := result.get("post_install_message"):
                console.print(f"\n[yellow]Configuration:[/yellow]")
                console.print(config)

        except Exception as e:
            console.print(f"[red]Failed to install {tool_name}: {e}[/red]")


@tools_group.command()
@click.argument("tool_name")
@click.pass_context
async def uninstall(ctx, tool_name: str):
    """Uninstall a tool."""
    try:
        from hanzo_tools import get_tool_registry
    except ImportError:
        console.print("[red]Error:[/red] hanzo-tools not installed")
        return

    registry = get_tool_registry()

    if click.confirm(f"Uninstall {tool_name}?"):
        with console.status(f"Uninstalling {tool_name}..."):
            try:
                await registry.uninstall_tool(tool_name)
                console.print(f"[green]✓[/green] Uninstalled {tool_name}")
            except Exception as e:
                console.print(f"[red]Failed to uninstall {tool_name}: {e}[/red]")


@tools_group.command()
@click.argument("tool_name")
@click.option("--version", "-v", help="Target version")
@click.pass_context
async def update(ctx, tool_name: str, version: str):
    """Update a tool."""
    try:
        from hanzo_tools import get_tool_registry
    except ImportError:
        console.print("[red]Error:[/red] hanzo-tools not installed")
        return

    registry = get_tool_registry()

    with console.status(f"Updating {tool_name}..."):
        try:
            result = await registry.update_tool(name=tool_name, version=version)

            console.print(f"[green]✓[/green] Updated {tool_name}")
            console.print(f"  Previous: v{result['previous_version']}")
            console.print(f"  Current: v{result['current_version']}")

        except Exception as e:
            console.print(f"[red]Failed to update {tool_name}: {e}[/red]")


@tools_group.command()
@click.argument("tool_name")
@click.pass_context
async def info(ctx, tool_name: str):
    """Show tool information."""
    try:
        from hanzo_tools import get_tool_registry
    except ImportError:
        console.print("[red]Error:[/red] hanzo-tools not installed")
        return

    registry = get_tool_registry()

    with console.status(f"Loading {tool_name} info..."):
        try:
            info = await registry.get_tool_info(tool_name)
        except Exception as e:
            console.print(f"[red]Failed to get info: {e}[/red]")
            return

    console.print(f"[cyan]{info['name']}[/cyan]")
    console.print(f"  Version: {info['version']}")
    console.print(f"  Category: {info['category']}")
    console.print(f"  Author: {info.get('author', 'Unknown')}")
    console.print(f"  License: {info.get('license', 'Unknown')}")

    if desc := info.get("description"):
        console.print(f"\n{desc}")

    if features := info.get("features"):
        console.print("\n[cyan]Features:[/cyan]")
        for feature in features:
            console.print(f"  • {feature}")

    if deps := info.get("dependencies"):
        console.print("\n[cyan]Dependencies:[/cyan]")
        for dep in deps:
            console.print(f"  • {dep}")

    if usage := info.get("usage_example"):
        console.print("\n[cyan]Usage Example:[/cyan]")
        syntax = Syntax(usage, "python", theme="monokai", line_numbers=False)
        console.print(syntax)


@tools_group.command()
@click.argument("tool_name")
@click.argument("args", nargs=-1)
@click.option("--json", "-j", is_flag=True, help="Output as JSON")
@click.pass_context
async def run(ctx, tool_name: str, args: tuple, json: bool):
    """Run a tool directly."""
    try:
        from hanzo_tools import run_tool
    except ImportError:
        console.print("[red]Error:[/red] hanzo-tools not installed")
        return

    # Parse arguments
    tool_args = {}
    for arg in args:
        if "=" in arg:
            key, value = arg.split("=", 1)
            tool_args[key] = value
        else:
            console.print(f"[red]Invalid argument format: {arg}[/red]")
            console.print("Use: key=value")
            return

    with console.status(f"Running {tool_name}..."):
        try:
            result = await run_tool(name=tool_name, args=tool_args)

            if json:
                console.print_json(data=result)
            else:
                if isinstance(result, str):
                    console.print(result)
                elif isinstance(result, dict):
                    for key, value in result.items():
                        console.print(f"{key}: {value}")
                else:
                    console.print(result)

        except Exception as e:
            console.print(f"[red]Tool execution failed: {e}[/red]")


@tools_group.command()
@click.option("--check", is_flag=True, help="Check for updates only")
@click.pass_context
async def upgrade(ctx, check: bool):
    """Upgrade all tools."""
    try:
        from hanzo_tools import get_tool_registry
    except ImportError:
        console.print("[red]Error:[/red] hanzo-tools not installed")
        return

    registry = get_tool_registry()

    with console.status("Checking for updates..."):
        try:
            updates = await registry.check_updates()
        except Exception as e:
            console.print(f"[red]Failed to check updates: {e}[/red]")
            return

    if not updates:
        console.print("[green]✓[/green] All tools are up to date")
        return

    # Show available updates
    table = Table(title="Available Updates")
    table.add_column("Tool", style="cyan")
    table.add_column("Current", style="yellow")
    table.add_column("Latest", style="green")
    table.add_column("Changes", style="white")

    for update in updates:
        table.add_row(
            update["name"],
            update["current_version"],
            update["latest_version"],
            update.get("changelog_summary", ""),
        )

    console.print(table)

    if check:
        return

    # Perform updates
    if click.confirm(f"Update {len(updates)} tools?"):
        for update in updates:
            with console.status(f"Updating {update['name']}..."):
                try:
                    await registry.update_tool(update["name"])
                    console.print(f"[green]✓[/green] Updated {update['name']}")
                except Exception as e:
                    console.print(f"[red]Failed to update {update['name']}: {e}[/red]")


@tools_group.command()
@click.argument("name")
@click.option("--template", "-t", help="Tool template to use")
@click.pass_context
async def create(ctx, name: str, template: str):
    """Create a new custom tool."""
    try:
        from hanzo_tools import create_tool_template
    except ImportError:
        console.print("[red]Error:[/red] hanzo-tools not installed")
        return

    with console.status(f"Creating tool '{name}'..."):
        try:
            path = await create_tool_template(name=name, template=template or "basic")

            console.print(f"[green]✓[/green] Created tool template at: {path}")
            console.print("\nNext steps:")
            console.print("1. Edit the tool implementation")
            console.print("2. Test with: hanzo tools run {name}")
            console.print("3. Package with: hanzo tools package {name}")

        except Exception as e:
            console.print(f"[red]Failed to create tool: {e}[/red]")
