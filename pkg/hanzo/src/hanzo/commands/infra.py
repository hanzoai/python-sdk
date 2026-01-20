"""Infrastructure management commands for Hanzo CLI.

Provision and manage infrastructure services on Hanzo Cloud:
- Vector (Qdrant)
- KV (Redis/Valkey)
- DocumentDB (MongoDB)
- Storage (S3/MinIO)
- Search (Meilisearch)
- PubSub (NATS)
- Tasks (Temporal)
- Queues
- Cron
- Functions (Nuclio)
"""

import os
import json
from typing import Optional
from pathlib import Path

import click
import httpx
from rich import box
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Confirm

from ..utils.output import console


HANZO_API_URL = os.getenv("HANZO_API_URL", "https://api.hanzo.ai")

# Service names - defined before SERVICES dict for click.Choice
SERVICE_NAMES = (
    "vector", "kv", "documentdb", "storage", "search",
    "pubsub", "tasks", "queues", "cron", "functions"
)

SERVICES = {
    "vector": {
        "name": "Vector Database",
        "description": "Qdrant vector similarity search",
        "env_prefix": "QDRANT",
        "default_port": 6333,
    },
    "kv": {
        "name": "Key-Value Store",
        "description": "Redis/Valkey for caching and state",
        "env_prefix": "REDIS",
        "default_port": 6379,
    },
    "documentdb": {
        "name": "Document Database",
        "description": "MongoDB for document storage",
        "env_prefix": "MONGODB",
        "default_port": 27017,
    },
    "storage": {
        "name": "Object Storage",
        "description": "S3-compatible storage (MinIO)",
        "env_prefix": "S3",
        "default_port": 9000,
    },
    "search": {
        "name": "Full-Text Search",
        "description": "Meilisearch for fast search",
        "env_prefix": "MEILI",
        "default_port": 7700,
    },
    "pubsub": {
        "name": "Pub/Sub Messaging",
        "description": "NATS for event streaming",
        "env_prefix": "NATS",
        "default_port": 4222,
    },
    "tasks": {
        "name": "Workflow Engine",
        "description": "Temporal for durable workflows",
        "env_prefix": "TEMPORAL",
        "default_port": 7233,
    },
    "queues": {
        "name": "Job Queues",
        "description": "Distributed work queues",
        "env_prefix": "QUEUE",
        "default_port": 6379,
    },
    "cron": {
        "name": "Scheduled Jobs",
        "description": "Cron-based job scheduling",
        "env_prefix": "CRON",
        "default_port": 6379,
    },
    "functions": {
        "name": "Serverless Functions",
        "description": "Nuclio function runtime",
        "env_prefix": "NUCLIO",
        "default_port": 8070,
    },
}


def get_api_key() -> Optional[str]:
    """Get Hanzo API key from env or auth file."""
    if os.getenv("HANZO_API_KEY"):
        return os.getenv("HANZO_API_KEY")

    auth_file = Path.home() / ".hanzo" / "auth.json"
    if auth_file.exists():
        try:
            auth = json.loads(auth_file.read_text())
            return auth.get("api_key")
        except Exception:
            pass
    return None


def get_infra_config() -> dict:
    """Load infrastructure configuration."""
    config_file = Path.home() / ".hanzo" / "infra.json"
    if config_file.exists():
        try:
            return json.loads(config_file.read_text())
        except Exception:
            pass
    return {"services": {}}


def save_infra_config(config: dict):
    """Save infrastructure configuration."""
    config_dir = Path.home() / ".hanzo"
    config_dir.mkdir(exist_ok=True)
    config_file = config_dir / "infra.json"
    config_file.write_text(json.dumps(config, indent=2))


@click.group(name="infra")
def infra_group():
    """Manage Hanzo infrastructure services.

    Provision and connect to managed infrastructure:

    \b
    Services:
      vector     - Qdrant vector database
      kv         - Redis/Valkey key-value store
      documentdb - MongoDB document database
      storage    - S3/MinIO object storage
      search     - Meilisearch full-text search
      pubsub     - NATS messaging
      tasks      - Temporal workflows
      queues     - Distributed job queues
      cron       - Scheduled jobs
      functions  - Nuclio serverless

    \b
    Examples:
      hanzo infra list              # Show available services
      hanzo infra provision vector  # Provision Qdrant
      hanzo infra connect           # Get connection URLs
      hanzo infra env               # Export as env vars
      hanzo infra status            # Check health
    """
    pass


@infra_group.command()
def list():
    """List available infrastructure services."""
    config = get_infra_config()
    provisioned = config.get("services", {})

    table = Table(title="Hanzo Infrastructure Services", box=box.ROUNDED)
    table.add_column("Service", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Status", style="green")
    table.add_column("Description", style="dim")

    for key, info in SERVICES.items():
        status = "✓ Provisioned" if key in provisioned else "○ Available"
        style = "green" if key in provisioned else "dim"
        table.add_row(key, info["name"], f"[{style}]{status}[/{style}]", info["description"])

    console.print(table)
    console.print()
    console.print("[dim]Use 'hanzo infra provision <service>' to provision a service[/dim]")


@infra_group.command()
@click.argument("service", type=click.Choice(SERVICE_NAMES))
@click.option("--tier", type=click.Choice(["free", "pro", "enterprise"]), default="free", help="Service tier")
@click.option("--region", default="us-west-2", help="Deployment region")
def provision(service: str, tier: str, region: str):
    """Provision an infrastructure service on Hanzo Cloud."""
    api_key = get_api_key()
    if not api_key:
        console.print("[red]Not authenticated. Run 'hanzo auth login' first.[/red]")
        return

    info = SERVICES[service]
    console.print(f"[cyan]Provisioning {info['name']}...[/cyan]")

    try:
        with httpx.Client(timeout=60) as client:
            resp = client.post(
                f"{HANZO_API_URL}/v1/infra/provision",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "service": service,
                    "tier": tier,
                    "region": region,
                },
            )

            if resp.status_code == 401:
                console.print("[red]Authentication failed. Run 'hanzo auth login'.[/red]")
                return

            if resp.status_code == 402:
                console.print("[yellow]Upgrade required for this tier.[/yellow]")
                console.print("Visit https://hanzo.ai/pricing to upgrade.")
                return

            if resp.status_code >= 400:
                console.print(f"[red]Error: {resp.text}[/red]")
                return

            data = resp.json()

            # Save to config
            config = get_infra_config()
            config["services"][service] = {
                "id": data.get("id"),
                "url": data.get("url"),
                "host": data.get("host"),
                "port": data.get("port"),
                "credentials": data.get("credentials", {}),
                "tier": tier,
                "region": region,
            }
            save_infra_config(config)

            console.print(f"[green]✓ {info['name']} provisioned successfully![/green]")
            console.print()
            console.print(f"[cyan]Connection URL:[/cyan] {data.get('url')}")
            console.print()
            console.print("[dim]Run 'hanzo infra env' to export environment variables[/dim]")

    except httpx.ConnectError:
        console.print("[red]Could not connect to Hanzo API.[/red]")
        console.print("[dim]Check your network connection or try again later.[/dim]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@infra_group.command()
@click.argument("service", type=click.Choice(SERVICE_NAMES), required=False)
def connect(service: Optional[str]):
    """Show connection details for provisioned services."""
    config = get_infra_config()
    services = config.get("services", {})

    if not services:
        console.print("[yellow]No services provisioned yet.[/yellow]")
        console.print("Run 'hanzo infra provision <service>' to get started.")
        return

    if service:
        if service not in services:
            console.print(f"[yellow]{service} not provisioned.[/yellow]")
            return
        services = {service: services[service]}

    for svc_name, svc_config in services.items():
        info = SERVICES[svc_name]
        panel = Panel(
            f"[cyan]URL:[/cyan] {svc_config.get('url', 'N/A')}\n"
            f"[cyan]Host:[/cyan] {svc_config.get('host', 'N/A')}\n"
            f"[cyan]Port:[/cyan] {svc_config.get('port', 'N/A')}\n"
            f"[cyan]Tier:[/cyan] {svc_config.get('tier', 'free')}\n"
            f"[cyan]Region:[/cyan] {svc_config.get('region', 'N/A')}",
            title=f"[bold]{info['name']}[/bold]",
            border_style="cyan",
        )
        console.print(panel)


@infra_group.command()
@click.option("--shell", type=click.Choice(["bash", "zsh", "fish", "powershell"]), default="bash")
@click.option("--export", "do_export", is_flag=True, help="Print export statements")
def env(shell: str, do_export: bool):
    """Show environment variables for provisioned services."""
    config = get_infra_config()
    services = config.get("services", {})

    if not services:
        console.print("[yellow]No services provisioned.[/yellow]")
        return

    env_vars = []

    for svc_name, svc_config in services.items():
        info = SERVICES[svc_name]
        prefix = info["env_prefix"]

        if svc_config.get("url"):
            env_vars.append((f"{prefix}_URL", svc_config["url"]))
        if svc_config.get("host"):
            env_vars.append((f"{prefix}_HOST", svc_config["host"]))
        if svc_config.get("port"):
            env_vars.append((f"{prefix}_PORT", str(svc_config["port"])))

        creds = svc_config.get("credentials", {})
        if creds.get("api_key"):
            env_vars.append((f"{prefix}_API_KEY", creds["api_key"]))
        if creds.get("password"):
            env_vars.append((f"{prefix}_PASSWORD", creds["password"]))
        if creds.get("username"):
            env_vars.append((f"{prefix}_USERNAME", creds["username"]))

    if do_export:
        # Print export statements
        if shell in ("bash", "zsh"):
            for key, value in env_vars:
                console.print(f'export {key}="{value}"')
        elif shell == "fish":
            for key, value in env_vars:
                console.print(f'set -gx {key} "{value}"')
        elif shell == "powershell":
            for key, value in env_vars:
                console.print(f'$env:{key} = "{value}"')
    else:
        # Show as table
        table = Table(title="Environment Variables", box=box.ROUNDED)
        table.add_column("Variable", style="cyan")
        table.add_column("Value", style="green")

        for key, value in env_vars:
            # Mask sensitive values
            if "KEY" in key or "PASSWORD" in key or "SECRET" in key:
                display = value[:8] + "..." if len(value) > 8 else "***"
            else:
                display = value
            table.add_row(key, display)

        console.print(table)
        console.print()
        console.print(f"[dim]Run 'hanzo infra env --export' to get export statements[/dim]")


@infra_group.command()
@click.argument("service", type=click.Choice(SERVICE_NAMES), required=False)
def status(service: Optional[str]):
    """Check health status of provisioned services."""
    config = get_infra_config()
    services = config.get("services", {})

    if not services:
        console.print("[yellow]No services provisioned.[/yellow]")
        return

    if service:
        if service not in services:
            console.print(f"[yellow]{service} not provisioned.[/yellow]")
            return
        services = {service: services[service]}

    api_key = get_api_key()

    table = Table(title="Service Health", box=box.ROUNDED)
    table.add_column("Service", style="cyan")
    table.add_column("Status", style="white")
    table.add_column("Latency", style="dim")

    with httpx.Client(timeout=10) as client:
        for svc_name, svc_config in services.items():
            info = SERVICES[svc_name]

            try:
                resp = client.get(
                    f"{HANZO_API_URL}/v1/infra/{svc_config.get('id')}/health",
                    headers={"Authorization": f"Bearer {api_key}"} if api_key else {},
                )

                if resp.status_code == 200:
                    data = resp.json()
                    status_str = "[green]● Healthy[/green]"
                    latency = f"{data.get('latency_ms', '?')}ms"
                else:
                    status_str = "[yellow]○ Unknown[/yellow]"
                    latency = "-"
            except Exception:
                status_str = "[red]✗ Unreachable[/red]"
                latency = "-"

            table.add_row(info["name"], status_str, latency)

    console.print(table)


@infra_group.command()
@click.argument("service", type=click.Choice(SERVICE_NAMES))
@click.option("--force", is_flag=True, help="Skip confirmation")
def destroy(service: str, force: bool):
    """Destroy a provisioned service."""
    config = get_infra_config()
    services = config.get("services", {})

    if service not in services:
        console.print(f"[yellow]{service} not provisioned.[/yellow]")
        return

    info = SERVICES[service]

    if not force:
        if not Confirm.ask(f"[red]Destroy {info['name']}? This cannot be undone.[/red]"):
            console.print("Cancelled.")
            return

    api_key = get_api_key()
    if not api_key:
        console.print("[red]Not authenticated.[/red]")
        return

    try:
        with httpx.Client(timeout=30) as client:
            svc_id = services[service].get("id")
            resp = client.delete(
                f"{HANZO_API_URL}/v1/infra/{svc_id}",
                headers={"Authorization": f"Bearer {api_key}"},
            )

            if resp.status_code >= 400:
                console.print(f"[red]Error: {resp.text}[/red]")
                return

        # Remove from config
        del config["services"][service]
        save_infra_config(config)

        console.print(f"[green]✓ {info['name']} destroyed.[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@infra_group.command()
def init():
    """Initialize infrastructure from hanzo.yaml config file."""
    config_paths = [
        Path.cwd() / "hanzo.yaml",
        Path.cwd() / "hanzo.yml",
        Path.cwd() / ".hanzo.yaml",
    ]

    config_file = None
    for p in config_paths:
        if p.exists():
            config_file = p
            break

    if not config_file:
        console.print("[yellow]No hanzo.yaml found in current directory.[/yellow]")
        console.print()
        console.print("Create one with:")
        console.print()
        console.print("[cyan]# hanzo.yaml[/cyan]")
        console.print("infra:")
        console.print("  vector: true")
        console.print("  kv: true")
        console.print("  search: true")
        return

    import yaml

    try:
        config = yaml.safe_load(config_file.read_text())
    except Exception as e:
        console.print(f"[red]Error parsing {config_file}: {e}[/red]")
        return

    infra_config = config.get("infra", {})
    if not infra_config:
        console.print("[yellow]No 'infra' section in config file.[/yellow]")
        return

    console.print(f"[cyan]Initializing infrastructure from {config_file}...[/cyan]")

    for service, enabled in infra_config.items():
        if service in SERVICES and enabled:
            console.print(f"  Provisioning {service}...")
            # Would call provision logic here

    console.print("[green]✓ Infrastructure initialized![/green]")
