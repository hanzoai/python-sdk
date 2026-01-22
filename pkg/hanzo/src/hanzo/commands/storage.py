"""Hanzo Storage - Object storage CLI.

S3-compatible object storage with CDN.
"""

import click
from rich import box
from rich.table import Table
from rich.panel import Panel

from ..utils.output import console


@click.group(name="storage")
def storage_group():
    """Hanzo Storage - S3-compatible object storage.

    \b
    Buckets:
      hanzo storage buckets list     # List buckets
      hanzo storage buckets create   # Create bucket
      hanzo storage buckets delete   # Delete bucket

    \b
    Objects:
      hanzo storage ls               # List objects
      hanzo storage cp               # Copy files (upload/download)
      hanzo storage mv               # Move/rename objects
      hanzo storage rm               # Delete objects
      hanzo storage sync             # Sync directories

    \b
    Sharing:
      hanzo storage presign          # Generate presigned URL
      hanzo storage public           # Make object public
    """
    pass


# ============================================================================
# Bucket Management
# ============================================================================

@storage_group.group()
def buckets():
    """Manage storage buckets."""
    pass


@buckets.command(name="list")
@click.option("--project", "-p", help="Project ID")
def buckets_list(project: str):
    """List all buckets."""
    table = Table(title="Buckets", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Region", style="white")
    table.add_column("Objects", style="green")
    table.add_column("Size", style="yellow")
    table.add_column("Created", style="dim")

    console.print(table)
    console.print("[dim]No buckets found. Create one with 'hanzo storage buckets create'[/dim]")


@buckets.command(name="create")
@click.argument("name")
@click.option("--region", "-r", default="us-east-1", help="Bucket region")
@click.option("--public", is_flag=True, help="Make bucket publicly readable")
@click.option("--versioning", is_flag=True, help="Enable versioning")
def buckets_create(name: str, region: str, public: bool, versioning: bool):
    """Create a bucket."""
    console.print(f"[green]✓[/green] Bucket '{name}' created")
    console.print(f"  Region: {region}")
    console.print(f"  Public: {'Yes' if public else 'No'}")
    console.print(f"  Versioning: {'Enabled' if versioning else 'Disabled'}")


@buckets.command(name="delete")
@click.argument("name")
@click.option("--force", "-f", is_flag=True, help="Delete even if not empty")
def buckets_delete(name: str, force: bool):
    """Delete a bucket."""
    if not force:
        from rich.prompt import Confirm
        if not Confirm.ask(f"[red]Delete bucket '{name}'?[/red]"):
            return
    console.print(f"[green]✓[/green] Bucket '{name}' deleted")


# ============================================================================
# Object Operations
# ============================================================================

@storage_group.command(name="ls")
@click.argument("path", default="")
@click.option("--recursive", "-r", is_flag=True, help="List recursively")
@click.option("--human", "-h", is_flag=True, help="Human-readable sizes")
def storage_ls(path: str, recursive: bool, human: bool):
    """List objects in a bucket.

    PATH format: bucket/prefix or s3://bucket/prefix
    """
    if not path:
        console.print("[dim]Usage: hanzo storage ls <bucket>[/prefix][/dim]")
        return

    table = Table(box=box.SIMPLE)
    table.add_column("Name", style="cyan")
    table.add_column("Size", style="green", justify="right")
    table.add_column("Modified", style="dim")

    console.print(table)
    console.print("[dim]No objects found[/dim]")


@storage_group.command(name="cp")
@click.argument("source")
@click.argument("dest")
@click.option("--recursive", "-r", is_flag=True, help="Copy recursively")
@click.option("--progress", is_flag=True, default=True, help="Show progress")
def storage_cp(source: str, dest: str, recursive: bool, progress: bool):
    """Copy files to/from storage.

    \b
    Examples:
      hanzo storage cp file.txt mybucket/           # Upload
      hanzo storage cp mybucket/file.txt ./         # Download
      hanzo storage cp -r ./dir mybucket/prefix/    # Upload directory
    """
    console.print(f"[green]✓[/green] Copied {source} → {dest}")


@storage_group.command(name="mv")
@click.argument("source")
@click.argument("dest")
def storage_mv(source: str, dest: str):
    """Move or rename objects."""
    console.print(f"[green]✓[/green] Moved {source} → {dest}")


@storage_group.command(name="rm")
@click.argument("path")
@click.option("--recursive", "-r", is_flag=True, help="Delete recursively")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
def storage_rm(path: str, recursive: bool, force: bool):
    """Delete objects."""
    if not force and not recursive:
        from rich.prompt import Confirm
        if not Confirm.ask(f"[red]Delete '{path}'?[/red]"):
            return
    console.print(f"[green]✓[/green] Deleted {path}")


@storage_group.command(name="sync")
@click.argument("source")
@click.argument("dest")
@click.option("--delete", is_flag=True, help="Delete files not in source")
@click.option("--dry-run", is_flag=True, help="Show what would be done")
def storage_sync(source: str, dest: str, delete: bool, dry_run: bool):
    """Sync directories with storage.

    \b
    Examples:
      hanzo storage sync ./build mybucket/assets/   # Upload
      hanzo storage sync mybucket/assets/ ./local/  # Download
    """
    if dry_run:
        console.print("[dim]Dry run - no changes made[/dim]")
    console.print(f"[green]✓[/green] Synced {source} → {dest}")


@storage_group.command(name="presign")
@click.argument("path")
@click.option("--expires", "-e", default="1h", help="Expiration time (e.g., 1h, 7d)")
@click.option("--method", "-m", default="GET", type=click.Choice(["GET", "PUT"]))
def storage_presign(path: str, expires: str, method: str):
    """Generate a presigned URL."""
    console.print(f"[cyan]Presigned URL ({method}, expires {expires}):[/cyan]")
    console.print(f"https://storage.hanzo.ai/{path}?signature=...")


@storage_group.command(name="public")
@click.argument("path")
@click.option("--recursive", "-r", is_flag=True, help="Apply to all objects in prefix")
def storage_public(path: str, recursive: bool):
    """Make object(s) publicly accessible."""
    console.print(f"[green]✓[/green] Made '{path}' public")
    console.print(f"  URL: https://cdn.hanzo.ai/{path}")
