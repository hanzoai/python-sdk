"""Hanzo CLI — KMS subcommands for secret management.

A secret is (org, path, name, env). The org comes from HANZO_KMS_ORG
(default: hanzo); env defaults to "default".

Usage:
    hanzo kms list --path providers/lux --env prod     — List secret names
    hanzo kms get providers/lux deploy-mnemonic        — Get a secret value
    hanzo kms set providers/lux deploy-mnemonic VALUE  — Create or replace
    hanzo kms delete providers/lux deploy-mnemonic     — Delete a secret
    hanzo kms inject --path providers/lux              — Print export statements
"""

from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table

console = Console()

DEFAULT_ENV = "default"


def _get_kms_client():
    """Build a KMS client from the environment.

    KMSClient() reads HANZO_KMS_URL / _ORG / _CLIENT_ID / _CLIENT_SECRET /
    _TOKEN itself — see hanzo_kms.settings_from_env.
    """
    from hanzo_kms import KMSClient

    return KMSClient()


def _masked(value: str) -> str:
    return f"{value[:4]}***" if len(value) > 4 else "***"


@click.group()
def kms() -> None:
    """Manage secrets via Hanzo KMS."""


@kms.command("list")
@click.option("--path", default="", help="Secret path, e.g. providers/lux.")
@click.option("--env", default=DEFAULT_ENV, help="Environment bucket.")
def list_secrets(path: str, env: str) -> None:
    """List the secret names at a path.

    Names only — the server's list route returns names, not values.
    """
    client = _get_kms_client()
    try:
        names = client.list_secrets(path, env)
    finally:
        client.close()

    if not names:
        console.print("[yellow]No secrets found.[/yellow]")
        return

    table = Table(title=f"Secrets: {path or '/'} ({env})")
    table.add_column("Name", style="cyan")
    for name in names:
        table.add_row(name)
    console.print(table)


@kms.command("get")
@click.argument("path")
@click.argument("name")
@click.option("--env", default=DEFAULT_ENV, help="Environment bucket.")
@click.option("--reveal", is_flag=True, help="Show full value (default: masked).")
def get_secret(path: str, name: str, env: str, reveal: bool) -> None:
    """Get a single secret's value."""
    client = _get_kms_client()
    try:
        value = client.get_secret(path, name, env)
    finally:
        client.close()

    console.print(value if reveal else _masked(value))


@kms.command("set")
@click.argument("path")
@click.argument("name")
@click.argument("value", required=False)
@click.option("--env", default=DEFAULT_ENV, help="Environment bucket.")
def set_secret(path: str, name: str, value: str | None, env: str) -> None:
    """Create or replace a secret. Prompts for the value if not given.

    One upsert — KMS holds exactly one value per (path, name, env).
    """
    if not value:
        value = click.prompt("Secret value", hide_input=True)

    client = _get_kms_client()
    try:
        client.put_secret(path, name, value, env)
    finally:
        client.close()

    console.print(f"[green]Set[/green] {path}/{name} ({env})")


@kms.command("delete")
@click.argument("path")
@click.argument("name")
@click.option("--env", default=DEFAULT_ENV, help="Environment bucket.")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation.")
def delete_secret(path: str, name: str, env: str, yes: bool) -> None:
    """Delete a secret."""
    if not yes:
        click.confirm(f"Delete secret '{path}/{name}' from {env}?", abort=True)

    client = _get_kms_client()
    try:
        client.delete_secret(path, name, env)
    finally:
        client.close()

    console.print(f"[green]Deleted[/green] {path}/{name} ({env})")


@kms.command("inject")
@click.option("--path", default="", help="Secret path.")
@click.option("--env", default=DEFAULT_ENV, help="Environment bucket.")
@click.option(
    "--format", "fmt", type=click.Choice(["export", "dotenv", "json"]), default="export"
)
def inject_secrets(path: str, env: str, fmt: str) -> None:
    """Print secrets as export statements, dotenv, or JSON.

    Pipe to `eval` or redirect to a .env file:
        hanzo kms inject --path providers/lux | source /dev/stdin
        hanzo kms inject --path providers/lux --format dotenv > .env

    Costs one list request plus one read per secret — the server's list
    route returns names, not values.
    """
    import json

    client = _get_kms_client()
    try:
        values = {
            name: client.get_secret(path, name, env)
            for name in client.list_secrets(path, env)
        }
    finally:
        client.close()

    if not values:
        return

    if fmt == "json":
        click.echo(json.dumps(values, indent=2))
        return

    for name, value in values.items():
        if fmt == "export":
            shell_safe = value.replace("'", "'\\''")
            click.echo(f"export {name}='{shell_safe}'")
        else:  # dotenv
            dotenv_safe = value.replace('"', '\\"')
            click.echo(f'{name}="{dotenv_safe}"')
