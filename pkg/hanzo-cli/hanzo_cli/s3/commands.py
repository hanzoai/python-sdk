"""Hanzo CLI — S3 subcommands for object storage.

Wraps the ``hanzo_s3`` client (S3-compatible, backed by hanzoai/s3) at
s3.hanzo.ai.
Credentials come from the environment — inject them from KMS, never store
them in plaintext:

    eval "$(hanzo kms inject myproject production)"   # exports HANZO_S3_*

Usage:
    hanzo s3 buckets                          — List buckets
    hanzo s3 mb <bucket>                       — Make a bucket
    hanzo s3 rb <bucket> [--yes]               — Remove a bucket
    hanzo s3 ls <bucket> [--prefix p]          — List objects
    hanzo s3 stat <bucket> <object>            — Object metadata
    hanzo s3 rm <bucket> <object> [--yes]      — Remove an object
    hanzo s3 presign <bucket> <object>         — Presigned GET URL
"""

from __future__ import annotations

import os

import click
from rich.console import Console
from rich.table import Table

console = Console()


def _get_s3_client():
    """Build an S3 client from environment credentials."""
    from hanzo_s3 import S3Client

    endpoint = os.getenv("HANZO_S3_ENDPOINT", "s3.hanzo.ai")
    access_key = os.getenv("HANZO_S3_ACCESS_KEY") or os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("HANZO_S3_SECRET_KEY") or os.getenv("AWS_SECRET_ACCESS_KEY")
    secure = os.getenv("HANZO_S3_SECURE", "true").lower() not in ("0", "false", "no")

    if not access_key or not secret_key:
        raise click.ClickException(
            "Missing S3 credentials. Set HANZO_S3_ACCESS_KEY and HANZO_S3_SECRET_KEY "
            "(inject from KMS: eval \"$(hanzo kms inject <project> <env>)\")."
        )

    return S3Client(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)


@click.group()
def s3() -> None:
    """Manage S3-compatible object storage."""


@s3.command("buckets")
def list_buckets() -> None:
    """List all buckets."""
    client = _get_s3_client()
    buckets = list(client.list_buckets())
    if not buckets:
        console.print("[yellow]No buckets found.[/yellow]")
        return

    table = Table(title="Buckets")
    table.add_column("Name", style="cyan")
    table.add_column("Created", style="white")
    for b in buckets:
        table.add_row(b.name, str(b.creation_date)[:19] if b.creation_date else "—")
    console.print(table)


@s3.command("mb")
@click.argument("bucket")
def make_bucket(bucket: str) -> None:
    """Make a bucket."""
    client = _get_s3_client()
    client.make_bucket(bucket)
    console.print(f"[green]Created[/green] bucket {bucket}")


@s3.command("rb")
@click.argument("bucket")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation.")
def remove_bucket(bucket: str, yes: bool) -> None:
    """Remove a bucket (must be empty)."""
    if not yes:
        click.confirm(f"Remove bucket '{bucket}'?", abort=True)
    client = _get_s3_client()
    client.remove_bucket(bucket)
    console.print(f"[green]Removed[/green] bucket {bucket}")


@s3.command("ls")
@click.argument("bucket")
@click.option("--prefix", default="", help="Object key prefix.")
@click.option("--recursive", "-r", is_flag=True, help="Recurse into prefixes.")
def list_objects(bucket: str, prefix: str, recursive: bool) -> None:
    """List objects in a bucket."""
    client = _get_s3_client()
    objects = list(client.list_objects(bucket, prefix=prefix, recursive=recursive))
    if not objects:
        console.print("[yellow]No objects found.[/yellow]")
        return

    table = Table(title=f"Objects: {bucket}/{prefix}")
    table.add_column("Key", style="cyan")
    table.add_column("Size", style="white", justify="right")
    table.add_column("Modified", style="white")
    for o in objects:
        size = "—" if o.is_dir else str(o.size)
        modified = str(o.last_modified)[:19] if o.last_modified else "—"
        table.add_row(o.object_name, size, modified)
    console.print(table)


@s3.command("stat")
@click.argument("bucket")
@click.argument("object_name")
def stat_object(bucket: str, object_name: str) -> None:
    """Show object metadata."""
    client = _get_s3_client()
    obj = client.stat_object(bucket, object_name)
    table = Table(title=f"{bucket}/{object_name}")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")
    table.add_row("Size", str(obj.size))
    table.add_row("ETag", obj.etag or "—")
    table.add_row("Content-Type", obj.content_type or "—")
    table.add_row("Modified", str(obj.last_modified)[:19] if obj.last_modified else "—")
    console.print(table)


@s3.command("rm")
@click.argument("bucket")
@click.argument("object_name")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation.")
def remove_object(bucket: str, object_name: str, yes: bool) -> None:
    """Remove an object."""
    if not yes:
        click.confirm(f"Remove '{bucket}/{object_name}'?", abort=True)
    client = _get_s3_client()
    client.remove_object(bucket, object_name)
    console.print(f"[green]Removed[/green] {bucket}/{object_name}")


@s3.command("presign")
@click.argument("bucket")
@click.argument("object_name")
@click.option("--expires", default=3600, help="URL lifetime in seconds.")
def presign(bucket: str, object_name: str, expires: int) -> None:
    """Generate a presigned GET URL for an object."""
    from datetime import timedelta

    client = _get_s3_client()
    url = client.presigned_get_object(
        bucket, object_name, expires=timedelta(seconds=expires)
    )
    click.echo(url)
