"""Hanzo CLI — KMS subcommands for secret management.

Usage:
    hanzo kms list <project> <env>                — List secrets
    hanzo kms get <project> <env> <name>          — Get secret value
    hanzo kms set <project> <env> <name> <value>  — Create or update secret
    hanzo kms delete <project> <env> <name>       — Delete a secret
    hanzo kms inject <project> <env>              — Print export statements
"""

from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table

console = Console()


def _get_kms_client():
    """Build a KMS client from environment or stored auth."""
    import os

    from hanzo_kms import ClientSettings, KMSClient

    # KMS has its own auth (Universal Auth with client_id/secret)
    # Check for dedicated KMS env vars first
    kms_url = os.getenv("HANZO_KMS_URL", "https://kms.hanzo.ai")
    client_id = os.getenv("HANZO_KMS_CLIENT_ID", "")
    client_secret = os.getenv("HANZO_KMS_CLIENT_SECRET", "")

    if client_id and client_secret:
        from hanzo_kms import AuthenticationOptions, UniversalAuthMethod

        settings = ClientSettings(
            site_url=kms_url,
            auth=AuthenticationOptions(
                universal_auth=UniversalAuthMethod(
                    client_id=client_id,
                    client_secret=client_secret,
                )
            ),
        )
        return KMSClient(settings=settings)

    # Fall back to default env-based construction
    return KMSClient()


@click.group()
def kms() -> None:
    """Manage secrets via Hanzo KMS."""


@kms.command("list")
@click.argument("project")
@click.argument("env")
@click.option("--path", default="/", help="Secret path prefix.")
def list_secrets(project: str, env: str, path: str) -> None:
    """List all secrets in a project environment."""
    client = _get_kms_client()
    try:
        secrets = client.list_secrets(
            project_id=project,
            environment=env,
            path=path,
        )
    finally:
        client.close()

    if not secrets:
        console.print("[yellow]No secrets found.[/yellow]")
        return

    table = Table(title=f"Secrets: {project} / {env} ({path})")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="dim")
    table.add_column("Version", style="white", justify="right")
    table.add_column("Updated", style="white")

    for s in secrets:
        # Mask the value — show first 4 chars then ***
        val = s.secret_value
        masked = f"{val[:4]}***" if len(val) > 4 else "***"
        updated = str(s.updated_at)[:19] if s.updated_at else "—"
        table.add_row(s.secret_key, masked, str(s.version), updated)

    console.print(table)


@kms.command("get")
@click.argument("project")
@click.argument("env")
@click.argument("name")
@click.option("--path", default="/", help="Secret path prefix.")
@click.option("--reveal", is_flag=True, help="Show full value (default: masked).")
def get_secret(project: str, env: str, name: str, path: str, reveal: bool) -> None:
    """Get a single secret's value."""
    client = _get_kms_client()
    try:
        secret = client.get_secret(
            project_id=project,
            environment=env,
            secret_name=name,
            path=path,
        )
    finally:
        client.close()

    if reveal:
        console.print(secret.secret_value)
    else:
        val = secret.secret_value
        masked = f"{val[:4]}***" if len(val) > 4 else "***"
        table = Table(title=f"{name}")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")
        table.add_row("Key", secret.secret_key)
        table.add_row("Value", masked)
        table.add_row("Version", str(secret.version))
        table.add_row("Type", secret.type)
        table.add_row("Environment", secret.environment)
        if secret.secret_comment:
            table.add_row("Comment", secret.secret_comment)
        console.print(table)


@kms.command("set")
@click.argument("project")
@click.argument("env")
@click.argument("name")
@click.argument("value", required=False)
@click.option("--path", default="/", help="Secret path prefix.")
@click.option("--comment", default=None, help="Secret comment.")
def set_secret(
    project: str,
    env: str,
    name: str,
    value: str | None,
    path: str,
    comment: str | None,
) -> None:
    """Create or update a secret. Prompts for value if not given."""
    if not value:
        value = click.prompt("Secret value", hide_input=True)

    client = _get_kms_client()
    try:
        # Try update first, create if it doesn't exist
        try:
            secret = client.update_secret(
                project_id=project,
                environment=env,
                secret_name=name,
                secret_value=value,
            )
            console.print(f"[green]Updated[/green] {name} (v{secret.version})")
        except Exception:
            kwargs = {}
            if comment:
                kwargs["secret_comment"] = comment
            secret = client.create_secret(
                project_id=project,
                environment=env,
                secret_name=name,
                secret_value=value,
                **kwargs,
            )
            console.print(f"[green]Created[/green] {name}")
    finally:
        client.close()


@kms.command("delete")
@click.argument("project")
@click.argument("env")
@click.argument("name")
@click.option("--path", default="/", help="Secret path prefix.")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation.")
def delete_secret(project: str, env: str, name: str, path: str, yes: bool) -> None:
    """Delete a secret."""
    if not yes:
        click.confirm(f"Delete secret '{name}' from {project}/{env}?", abort=True)

    client = _get_kms_client()
    try:
        client.delete_secret(
            project_id=project,
            environment=env,
            secret_name=name,
            path=path,
        )
    finally:
        client.close()

    console.print(f"[green]Deleted[/green] {name}")


@kms.command("inject")
@click.argument("project")
@click.argument("env")
@click.option("--path", default="/", help="Secret path prefix.")
@click.option("--format", "fmt", type=click.Choice(["export", "dotenv", "json"]), default="export")
def inject_secrets(project: str, env: str, path: str, fmt: str) -> None:
    """Print secrets as export statements, dotenv, or JSON.

    Pipe to `eval` or redirect to .env file:
        hanzo kms inject myproject production | source /dev/stdin
        hanzo kms inject myproject production --format dotenv > .env
    """
    import json

    client = _get_kms_client()
    try:
        secrets = client.list_secrets(
            project_id=project,
            environment=env,
            path=path,
        )
    finally:
        client.close()

    if not secrets:
        return

    if fmt == "export":
        for s in secrets:
            # Shell-safe quoting
            val = s.secret_value.replace("'", "'\\''")
            click.echo(f"export {s.secret_key}='{val}'")
    elif fmt == "dotenv":
        for s in secrets:
            val = s.secret_value.replace('"', '\\"')
            click.echo(f'{s.secret_key}="{val}"')
    elif fmt == "json":
        data = {s.secret_key: s.secret_value for s in secrets}
        click.echo(json.dumps(data, indent=2))
