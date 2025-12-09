"""MCP (Model Context Protocol) commands."""

import json

import click
from rich.table import Table

from ..utils.output import console


@click.group(name="mcp")
def mcp_group():
    """Manage MCP servers and tools."""
    pass


@mcp_group.command()
@click.option("--name", "-n", default="hanzo-mcp", help="Server name")
@click.option(
    "--transport",
    "-t",
    type=click.Choice(["stdio", "sse"]),
    default="stdio",
    help="Transport protocol",
)
@click.option("--allow-path", "-p", multiple=True, help="Allowed paths")
@click.option("--enable-agent", is_flag=True, help="Enable agent tools")
@click.option("--host", default="127.0.0.1", help="Host for SSE transport")
@click.option("--port", default=3000, type=int, help="Port for SSE transport")
@click.pass_context
def serve(
    ctx,
    name: str,
    transport: str,
    allow_path: tuple,
    enable_agent: bool,
    host: str,
    port: int,
):
    """Start MCP server."""
    try:
        from hanzoai.mcp import run_mcp_server
    except ImportError:
        console.print("[red]Error:[/red] hanzo-mcp not installed")
        console.print("Install with: pip install hanzo[mcp]")
        return

    allowed_paths = list(allow_path) if allow_path else ["."]

    console.print(f"[cyan]Starting MCP server[/cyan]")
    console.print(f"  Name: {name}")
    console.print(f"  Transport: {transport}")
    console.print(f"  Allowed paths: {', '.join(allowed_paths)}")

    if transport == "sse":
        console.print(f"  Endpoint: http://{host}:{port}")

    try:
        run_mcp_server(
            name=name,
            transport=transport,
            allowed_paths=allowed_paths,
            enable_agent_tool=enable_agent,
            host=host,
            port=port,
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped[/yellow]")


@mcp_group.command()
@click.option("--category", "-c", help="Filter by category")
@click.pass_context
async def tools(ctx, category: str):
    """List available MCP tools."""
    try:
        from hanzoai.mcp import create_server
    except ImportError:
        console.print("[red]Error:[/red] hanzo-mcp not installed")
        console.print("Install with: pip install hanzo[mcp]")
        return

    with console.status("Loading tools..."):
        server = create_server(enable_all_tools=True)
        tools_list = await server.mcp.list_tools()

    # Group by category if available
    categories = {}
    for tool in tools_list:
        cat = getattr(tool, "category", "general")
        if category and cat != category:
            continue
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(tool)

    # Display tools
    for cat, tools in sorted(categories.items()):
        table = Table(
            title=f"{cat.title()} Tools" if len(categories) > 1 else "MCP Tools"
        )
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Description")

        for tool in sorted(tools, key=lambda t: t.name):
            table.add_row(tool.name, tool.description)

        console.print(table)
        if len(categories) > 1:
            console.print()


@mcp_group.command()
@click.argument("tool")
@click.option("--arg", "-a", multiple=True, help="Tool arguments (key=value)")
@click.option("--json-args", "-j", help="JSON arguments")
@click.pass_context
async def run(ctx, tool: str, arg: tuple, json_args: str):
    """Run an MCP tool."""
    try:
        from hanzoai.mcp import create_server
    except ImportError:
        console.print("[red]Error:[/red] hanzo-mcp not installed")
        console.print("Install with: pip install hanzo[mcp]")
        return

    # Parse arguments
    args = {}

    if json_args:
        try:
            args = json.loads(json_args)
        except json.JSONDecodeError as e:
            console.print(f"[red]Invalid JSON: {e}[/red]")
            return
    else:
        for a in arg:
            if "=" not in a:
                console.print(f"[red]Invalid argument format: {a}[/red]")
                console.print("Use: --arg key=value")
                return
            key, value = a.split("=", 1)

            # Try to parse value as JSON first
            try:
                args[key] = json.loads(value)
            except Exception:
                args[key] = value

    # Create server and run tool
    with console.status(f"Running tool '{tool}'..."):
        server = create_server(enable_all_tools=True)

        # Find tool
        tools_list = await server.mcp.list_tools()
        tool_obj = None
        for t in tools_list:
            if t.name == tool:
                tool_obj = t
                break

        if not tool_obj:
            console.print(f"[red]Tool not found: {tool}[/red]")
            console.print("Use 'hanzo mcp tools' to list available tools")
            return

        # Run tool
        try:
            # Mock context for now
            from mcp.server.fastmcp import Context

            context = Context()

            # Get tool function
            tool_func = server.mcp._tool_map.get(tool)
            if tool_func:
                result = await tool_func(**args)
            else:
                console.print(f"[red]Tool function not found: {tool}[/red]")
                return

        except Exception as e:
            console.print(f"[red]Tool error: {e}[/red]")
            return

    # Display result
    if isinstance(result, str):
        try:
            # Try to parse as JSON for pretty printing
            data = json.loads(result)
            console.print_json(data=data)
        except Exception:
            # Display as text
            console.print(result)
    else:
        console.print(result)


@mcp_group.command()
@click.option(
    "--path",
    "-p",
    default="~/.config/claude/claude_desktop_config.json",
    help="Config file path",
)
@click.pass_context
def install(ctx, path: str):
    """Install MCP server in Claude Desktop."""
    try:
        import hanzoai.mcp
    except ImportError:
        console.print("[red]Error:[/red] hanzo-mcp not installed")
        console.print("Install with: pip install hanzo[mcp]")
        return

    import os
    import json
    from pathlib import Path

    config_path = Path(os.path.expanduser(path))

    # Create config
    config = {
        "mcpServers": {
            "hanzo-mcp": {
                "command": "hanzo",
                "args": ["mcp", "serve", "--transport", "stdio"],
            }
        }
    }

    # Check if file exists
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                existing = json.load(f)

            if "mcpServers" not in existing:
                existing["mcpServers"] = {}

            existing["mcpServers"]["hanzo-mcp"] = config["mcpServers"]["hanzo-mcp"]
            config = existing
        except Exception as e:
            console.print(
                f"[yellow]Warning: Could not read existing config: {e}[/yellow]"
            )

    # Write config
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    console.print(f"[green]✓[/green] Installed hanzo-mcp in Claude Desktop")
    console.print(f"  Config: {config_path}")
    console.print("\nRestart Claude Desktop for changes to take effect")
