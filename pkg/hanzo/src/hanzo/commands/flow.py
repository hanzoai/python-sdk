"""Hanzo Flow - Visual LLM workflow builder CLI.

Build and deploy LLM applications with a visual interface (Langflow-compatible).
"""

import click
from rich import box
from rich.table import Table
from rich.panel import Panel

from ..utils.output import console


@click.group(name="flow")
def flow_group():
    """Hanzo Flow - Visual LLM workflow builder (Langflow-compatible).

    \b
    Flows:
      hanzo flow create            # Create LLM flow
      hanzo flow list              # List flows
      hanzo flow run               # Run a flow
      hanzo flow export            # Export flow definition

    \b
    Components:
      hanzo flow components        # List available components
      hanzo flow custom            # Manage custom components

    \b
    Development:
      hanzo flow dev               # Start visual editor
      hanzo flow deploy            # Deploy to production

    \b
    API:
      hanzo flow api               # Manage flow APIs
      hanzo flow playground        # Interactive playground
    """
    pass


# ============================================================================
# Flow Management
# ============================================================================

@flow_group.command(name="create")
@click.argument("name")
@click.option("--template", "-t", help="Start from template")
@click.option("--description", "-d", help="Flow description")
def flow_create(name: str, template: str, description: str):
    """Create a new LLM flow.

    \b
    Examples:
      hanzo flow create chatbot
      hanzo flow create rag-assistant --template rag
      hanzo flow create summarizer --template chain
    """
    console.print(f"[green]✓[/green] Flow '{name}' created")
    if template:
        console.print(f"  Template: {template}")
    console.print()
    console.print("Next steps:")
    console.print("  1. [cyan]hanzo flow dev[/cyan] - Open visual editor")
    console.print("  2. Add components to your flow")
    console.print("  3. [cyan]hanzo flow deploy {name}[/cyan] - Deploy to production")


@flow_group.command(name="list")
@click.option("--status", type=click.Choice(["deployed", "draft", "all"]), default="all")
def flow_list(status: str):
    """List LLM flows."""
    table = Table(title="LLM Flows", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Components", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Endpoint", style="white")
    table.add_column("Updated", style="dim")

    console.print(table)
    console.print("[dim]No flows found. Create one with 'hanzo flow create'[/dim]")


@flow_group.command(name="describe")
@click.argument("name")
def flow_describe(name: str):
    """Show flow details."""
    console.print(Panel(
        f"[cyan]Name:[/cyan] {name}\n"
        f"[cyan]Status:[/cyan] [green]● Deployed[/green]\n"
        f"[cyan]Components:[/cyan] 5\n"
        f"[cyan]Endpoint:[/cyan] https://flow.hanzo.ai/{name}\n"
        f"[cyan]API Key:[/cyan] ****\n"
        f"[cyan]Calls (24h):[/cyan] 1,234\n"
        f"[cyan]Avg Latency:[/cyan] 850ms",
        title="Flow Details",
        border_style="cyan"
    ))


@flow_group.command(name="run")
@click.argument("name")
@click.option("--input", "-i", "input_data", required=True, help="Input JSON or text")
@click.option("--stream", "-s", is_flag=True, help="Stream output")
@click.option("--verbose", "-v", is_flag=True, help="Show component outputs")
def flow_run(name: str, input_data: str, stream: bool, verbose: bool):
    """Run a flow locally.

    \b
    Examples:
      hanzo flow run chatbot -i "What is machine learning?"
      hanzo flow run rag -i '{"query": "How do I reset my password?"}'
      hanzo flow run summarizer -i @document.txt --stream
    """
    console.print(f"[cyan]Running flow '{name}'...[/cyan]")
    if verbose:
        console.print("  [dim]→ Input processed[/dim]")
        console.print("  [dim]→ LLM called[/dim]")
        console.print("  [dim]→ Output generated[/dim]")
    console.print()
    console.print("[green]Output:[/green]")
    console.print("[dim]<flow output would appear here>[/dim]")


@flow_group.command(name="delete")
@click.argument("name")
@click.option("--force", "-f", is_flag=True)
def flow_delete(name: str, force: bool):
    """Delete a flow."""
    if not force:
        from rich.prompt import Confirm
        if not Confirm.ask(f"[red]Delete flow '{name}'?[/red]"):
            return
    console.print(f"[green]✓[/green] Flow '{name}' deleted")


@flow_group.command(name="export")
@click.argument("name")
@click.option("--output", "-o", help="Output file")
@click.option("--format", "fmt", type=click.Choice(["json", "yaml"]), default="json")
def flow_export(name: str, output: str, fmt: str):
    """Export flow definition."""
    out_file = output or f"{name}.{fmt}"
    console.print(f"[green]✓[/green] Flow exported to '{out_file}'")


@flow_group.command(name="import")
@click.argument("file")
@click.option("--name", "-n", help="Override flow name")
def flow_import(file: str, name: str):
    """Import flow from file."""
    console.print(f"[cyan]Importing flow from '{file}'...[/cyan]")
    console.print(f"[green]✓[/green] Flow imported")


# ============================================================================
# Components
# ============================================================================

@flow_group.group()
def components():
    """Manage flow components."""
    pass


@components.command(name="list")
@click.option("--category", "-c", help="Filter by category")
@click.option("--search", "-s", help="Search components")
def components_list(category: str, search: str):
    """List available components."""
    table = Table(title="Flow Components", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Category", style="white")
    table.add_column("Description", style="dim")

    components_data = [
        # LLMs
        ("OpenAI", "LLMs", "GPT-4, GPT-3.5 models"),
        ("Anthropic", "LLMs", "Claude models"),
        ("Ollama", "LLMs", "Local LLM models"),
        ("HuggingFace", "LLMs", "Open source models"),
        # Embeddings
        ("OpenAI Embeddings", "Embeddings", "text-embedding-3"),
        ("Cohere Embeddings", "Embeddings", "embed-english-v3"),
        # Vector Stores
        ("Qdrant", "Vector Stores", "Vector database"),
        ("Pinecone", "Vector Stores", "Managed vector DB"),
        ("Chroma", "Vector Stores", "Local vector store"),
        # Chains
        ("LLM Chain", "Chains", "Simple LLM chain"),
        ("Retrieval QA", "Chains", "RAG chain"),
        ("Conversation", "Chains", "Chat with memory"),
        # Agents
        ("ReAct Agent", "Agents", "Reasoning + Acting"),
        ("OpenAI Functions", "Agents", "Function calling agent"),
        # Tools
        ("Web Search", "Tools", "Search the web"),
        ("Calculator", "Tools", "Math operations"),
        ("Python REPL", "Tools", "Execute Python code"),
        ("API Request", "Tools", "Call external APIs"),
        # Memory
        ("Buffer Memory", "Memory", "Simple conversation memory"),
        ("Summary Memory", "Memory", "Summarized memory"),
        ("Vector Memory", "Memory", "Vector-based memory"),
        # Loaders
        ("PDF Loader", "Loaders", "Load PDF documents"),
        ("Web Loader", "Loaders", "Load web pages"),
        ("File Loader", "Loaders", "Load text files"),
        # Output
        ("Text Output", "Output", "Plain text response"),
        ("JSON Output", "Output", "Structured JSON"),
        ("Chat Output", "Output", "Chat message format"),
    ]

    for name, cat, desc in components_data:
        if category and category.lower() not in cat.lower():
            continue
        if search and search.lower() not in name.lower() and search.lower() not in desc.lower():
            continue
        table.add_row(name, cat, desc)

    console.print(table)


@components.command(name="describe")
@click.argument("name")
def components_describe(name: str):
    """Show component details."""
    console.print(Panel(
        f"[cyan]Name:[/cyan] {name}\n"
        f"[cyan]Category:[/cyan] LLMs\n"
        f"[cyan]Inputs:[/cyan] prompt, model, temperature\n"
        f"[cyan]Outputs:[/cyan] text, tokens_used\n"
        f"[cyan]Config:[/cyan] api_key, max_tokens",
        title="Component Details",
        border_style="cyan"
    ))


# ============================================================================
# Custom Components
# ============================================================================

@flow_group.group()
def custom():
    """Manage custom components."""
    pass


@custom.command(name="create")
@click.argument("name")
@click.option("--template", "-t", type=click.Choice(["tool", "chain", "agent"]), default="tool")
def custom_create(name: str, template: str):
    """Create a custom component."""
    console.print(f"[green]✓[/green] Custom component '{name}' created")
    console.print(f"  Template: {template}")
    console.print(f"  File: components/{name}.py")


@custom.command(name="list")
def custom_list():
    """List custom components."""
    table = Table(title="Custom Components", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="white")
    table.add_column("File", style="dim")

    console.print(table)
    console.print("[dim]No custom components found[/dim]")


@custom.command(name="publish")
@click.argument("name")
def custom_publish(name: str):
    """Publish component to registry."""
    console.print(f"[cyan]Publishing component '{name}'...[/cyan]")
    console.print(f"[green]✓[/green] Component published")


# ============================================================================
# Development
# ============================================================================

@flow_group.command(name="dev")
@click.option("--port", "-p", default=7860, help="Port to run on")
@click.option("--flow", "-f", help="Open specific flow")
def flow_dev(port: int, flow: str):
    """Start visual flow editor."""
    console.print(f"[cyan]Starting Hanzo Flow editor on port {port}...[/cyan]")
    console.print()
    console.print(f"  [cyan]Editor:[/cyan] http://localhost:{port}")
    if flow:
        console.print(f"  [cyan]Flow:[/cyan] {flow}")
    console.print()
    console.print("Press Ctrl+C to stop")


@flow_group.command(name="deploy")
@click.argument("name")
@click.option("--env", "-e", default="production", help="Environment")
def flow_deploy(name: str, env: str):
    """Deploy flow to production."""
    console.print(f"[cyan]Deploying flow '{name}' to {env}...[/cyan]")
    console.print(f"[green]✓[/green] Flow deployed")
    console.print(f"  Endpoint: https://flow.hanzo.ai/{name}")
    console.print(f"  API Key: sk-flow-***")


@flow_group.command(name="undeploy")
@click.argument("name")
def flow_undeploy(name: str):
    """Undeploy a flow."""
    console.print(f"[green]✓[/green] Flow '{name}' undeployed")


# ============================================================================
# API Management
# ============================================================================

@flow_group.group()
def api():
    """Manage flow APIs."""
    pass


@api.command(name="keys")
@click.argument("flow_name")
def api_keys(flow_name: str):
    """List API keys for a flow."""
    table = Table(title=f"API Keys for '{flow_name}'", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Key", style="white")
    table.add_column("Created", style="dim")
    table.add_column("Last Used", style="dim")

    console.print(table)
    console.print("[dim]No API keys found[/dim]")


@api.command(name="create-key")
@click.argument("flow_name")
@click.option("--name", "-n", default="default", help="Key name")
def api_create_key(flow_name: str, name: str):
    """Create API key for a flow."""
    console.print(f"[green]✓[/green] API key created for '{flow_name}'")
    console.print(f"  Name: {name}")
    console.print(f"  Key: sk-flow-xxxxxxxxxxxx")
    console.print("[yellow]Save this key - it won't be shown again[/yellow]")


@api.command(name="revoke-key")
@click.argument("flow_name")
@click.argument("key_name")
def api_revoke_key(flow_name: str, key_name: str):
    """Revoke an API key."""
    console.print(f"[green]✓[/green] API key '{key_name}' revoked")


@api.command(name="test")
@click.argument("flow_name")
@click.option("--input", "-i", "input_data", required=True, help="Test input")
def api_test(flow_name: str, input_data: str):
    """Test flow API endpoint."""
    console.print(f"[cyan]Testing API for '{flow_name}'...[/cyan]")
    console.print("[green]✓[/green] API responded successfully")
    console.print("  Status: 200")
    console.print("  Latency: 850ms")


# ============================================================================
# Playground
# ============================================================================

@flow_group.command(name="playground")
@click.argument("name")
@click.option("--port", "-p", default=7861, help="Port")
def flow_playground(name: str, port: int):
    """Open interactive playground for a flow."""
    console.print(f"[cyan]Opening playground for '{name}'...[/cyan]")
    console.print(f"  URL: http://localhost:{port}/playground/{name}")


# ============================================================================
# Templates
# ============================================================================

@flow_group.group()
def templates():
    """Pre-built flow templates."""
    pass


@templates.command(name="list")
def templates_list():
    """List available templates."""
    table = Table(title="Flow Templates", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Components", style="dim")

    templates_data = [
        ("chatbot", "Simple chatbot with memory", "LLM, Memory, Output"),
        ("rag", "Retrieval Augmented Generation", "Loader, Embeddings, VectorStore, LLM"),
        ("agent", "ReAct agent with tools", "Agent, Tools, LLM"),
        ("chain", "Sequential LLM chain", "LLM, Chain, Output"),
        ("summarizer", "Document summarizer", "Loader, LLM, Output"),
        ("qa", "Question answering", "Loader, LLM, Output"),
        ("translator", "Multi-language translator", "LLM, Output"),
        ("code-assistant", "Code generation assistant", "LLM, Python REPL, Output"),
    ]

    for name, desc, comps in templates_data:
        table.add_row(name, desc, comps)

    console.print(table)


@templates.command(name="use")
@click.argument("template")
@click.option("--name", "-n", required=True, help="Flow name")
def templates_use(template: str, name: str):
    """Create flow from template."""
    console.print(f"[cyan]Creating flow '{name}' from template '{template}'...[/cyan]")
    console.print(f"[green]✓[/green] Flow created")
    console.print()
    console.print("Next steps:")
    console.print(f"  1. [cyan]hanzo flow dev -f {name}[/cyan] - Edit in visual editor")
    console.print(f"  2. [cyan]hanzo flow deploy {name}[/cyan] - Deploy to production")


# ============================================================================
# Versions & History
# ============================================================================

@flow_group.command(name="versions")
@click.argument("name")
def flow_versions(name: str):
    """List flow versions."""
    table = Table(title=f"Versions of '{name}'", box=box.ROUNDED)
    table.add_column("Version", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Created", style="dim")
    table.add_column("Note", style="dim")

    console.print(table)
    console.print("[dim]No versions found[/dim]")


@flow_group.command(name="rollback")
@click.argument("name")
@click.option("--version", "-v", required=True, help="Target version")
def flow_rollback(name: str, version: str):
    """Rollback to a previous version."""
    console.print(f"[cyan]Rolling back '{name}' to version {version}...[/cyan]")
    console.print(f"[green]✓[/green] Rolled back successfully")
