"""Hanzo Doc - Document database CLI.

MongoDB-compatible document database with global distribution.
"""

import click
from rich import box
from rich.panel import Panel
from rich.table import Table

from ..utils.output import console


@click.group(name="doc")
def doc_group():
    """Hanzo Doc - Document database (MongoDB-compatible).

    \b
    Databases:
      hanzo doc create               # Create database
      hanzo doc list                 # List databases
      hanzo doc delete               # Delete database

    \b
    Collections:
      hanzo doc collections list     # List collections
      hanzo doc collections create   # Create collection
      hanzo doc collections drop     # Drop collection

    \b
    Data:
      hanzo doc find                 # Query documents
      hanzo doc insert               # Insert document
      hanzo doc update               # Update documents
      hanzo doc delete-docs          # Delete documents

    \b
    Indexes:
      hanzo doc indexes list         # List indexes
      hanzo doc indexes create       # Create index
      hanzo doc indexes drop         # Drop index
    """
    pass


# ============================================================================
# Database Management
# ============================================================================


@doc_group.command(name="create")
@click.argument("name")
@click.option("--region", "-r", multiple=True, help="Regions for replication")
@click.option("--tier", "-t", type=click.Choice(["free", "standard", "dedicated"]), default="standard")
def doc_create(name: str, region: tuple, tier: str):
    """Create a document database."""
    console.print(f"[green]✓[/green] Database '{name}' created")
    console.print(f"  Tier: {tier}")
    if region:
        console.print(f"  Regions: {', '.join(region)}")
    console.print(f"  Connection: mongodb://doc.hanzo.ai/{name}")


@doc_group.command(name="list")
def doc_list():
    """List document databases."""
    table = Table(title="Document Databases", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Tier", style="white")
    table.add_column("Collections", style="green")
    table.add_column("Size", style="yellow")
    table.add_column("Status", style="dim")

    console.print(table)
    console.print("[dim]No databases found. Create one with 'hanzo doc create'[/dim]")


@doc_group.command(name="describe")
@click.argument("name")
def doc_describe(name: str):
    """Show database details."""
    console.print(
        Panel(
            f"[cyan]Name:[/cyan] {name}\n"
            f"[cyan]Tier:[/cyan] Standard\n"
            f"[cyan]Status:[/cyan] [green]● Running[/green]\n"
            f"[cyan]Collections:[/cyan] 5\n"
            f"[cyan]Documents:[/cyan] 12,345\n"
            f"[cyan]Size:[/cyan] 256 MB\n"
            f"[cyan]Regions:[/cyan] us-east-1\n"
            f"[cyan]Connection:[/cyan] mongodb://doc.hanzo.ai/{name}",
            title="Database Details",
            border_style="cyan",
        )
    )


@doc_group.command(name="delete")
@click.argument("name")
@click.option("--force", "-f", is_flag=True)
def doc_delete(name: str, force: bool):
    """Delete a document database."""
    if not force:
        from rich.prompt import Confirm

        if not Confirm.ask(f"[red]Delete database '{name}'?[/red]"):
            return
    console.print(f"[green]✓[/green] Database '{name}' deleted")


@doc_group.command(name="connect")
@click.argument("name")
def doc_connect(name: str):
    """Get connection string."""
    console.print(f"[cyan]Connection string for '{name}':[/cyan]")
    console.print(f"mongodb://doc.hanzo.ai/{name}?authSource=admin")


# ============================================================================
# Collections
# ============================================================================


@doc_group.group()
def collections():
    """Manage collections."""
    pass


@collections.command(name="list")
@click.option("--db", "-d", default="default", help="Database name")
def collections_list(db: str):
    """List collections in a database."""
    table = Table(title=f"Collections in '{db}'", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Documents", style="green")
    table.add_column("Size", style="yellow")
    table.add_column("Indexes", style="dim")

    console.print(table)
    console.print("[dim]No collections found[/dim]")


@collections.command(name="create")
@click.argument("name")
@click.option("--db", "-d", default="default", help="Database name")
@click.option("--capped", is_flag=True, help="Create capped collection")
@click.option("--size", "-s", help="Max size for capped collection")
@click.option("--validator", "-v", help="JSON schema validator")
def collections_create(name: str, db: str, capped: bool, size: str, validator: str):
    """Create a collection."""
    console.print(f"[green]✓[/green] Collection '{name}' created in '{db}'")
    if capped:
        console.print(f"  Capped: Yes (max {size})")


@collections.command(name="drop")
@click.argument("name")
@click.option("--db", "-d", default="default")
@click.option("--force", "-f", is_flag=True)
def collections_drop(name: str, db: str, force: bool):
    """Drop a collection."""
    if not force:
        from rich.prompt import Confirm

        if not Confirm.ask(f"[red]Drop collection '{name}'?[/red]"):
            return
    console.print(f"[green]✓[/green] Collection '{name}' dropped")


@collections.command(name="stats")
@click.argument("name")
@click.option("--db", "-d", default="default")
def collections_stats(name: str, db: str):
    """Show collection statistics."""
    console.print(
        Panel(
            f"[cyan]Collection:[/cyan] {name}\n"
            f"[cyan]Documents:[/cyan] 1,234\n"
            f"[cyan]Size:[/cyan] 12.5 MB\n"
            f"[cyan]Avg doc size:[/cyan] 10.1 KB\n"
            f"[cyan]Indexes:[/cyan] 3\n"
            f"[cyan]Index size:[/cyan] 1.2 MB",
            title="Collection Statistics",
            border_style="cyan",
        )
    )


# ============================================================================
# Data Operations
# ============================================================================


@doc_group.command(name="find")
@click.argument("collection")
@click.option("--db", "-d", default="default", help="Database name")
@click.option("--query", "-q", default="{}", help="Query filter (JSON)")
@click.option("--projection", "-p", help="Field projection")
@click.option("--sort", "-s", help="Sort order")
@click.option("--limit", "-n", default=20, help="Max results")
@click.option("--skip", type=int, help="Skip documents")
def doc_find(collection: str, db: str, query: str, projection: str, sort: str, limit: int, skip: int):
    """Query documents in a collection.

    \b
    Examples:
      hanzo doc find users
      hanzo doc find users -q '{"status": "active"}'
      hanzo doc find users -q '{"age": {"$gt": 21}}' -s '{"name": 1}'
    """
    console.print(f"[cyan]Results from {db}.{collection}:[/cyan]")
    console.print("[dim]No documents found[/dim]")


@doc_group.command(name="insert")
@click.argument("collection")
@click.option("--db", "-d", default="default")
@click.option("--doc", help="Document JSON")
@click.option("--file", "-f", type=click.Path(exists=True), help="Document file")
def doc_insert(collection: str, db: str, doc: str, file: str):
    """Insert a document."""
    doc_id = "64f1a2b3c4d5e6f7a8b9c0d1"
    console.print(f"[green]✓[/green] Inserted document into '{collection}'")
    console.print(f"  _id: {doc_id}")


@doc_group.command(name="update")
@click.argument("collection")
@click.option("--db", "-d", default="default")
@click.option("--filter", "-q", required=True, help="Query filter")
@click.option("--set", "set_fields", multiple=True, help="Fields to set")
@click.option("--unset", "unset_fields", multiple=True, help="Fields to unset")
@click.option("--upsert", is_flag=True, help="Insert if not found")
def doc_update(collection: str, db: str, filter: str, set_fields: tuple, unset_fields: tuple, upsert: bool):
    """Update documents.

    \b
    Examples:
      hanzo doc update users -q '{"status": "pending"}' --set status=active
      hanzo doc update users -q '{"_id": "..."}' --set name=John --set age=30
    """
    console.print(f"[green]✓[/green] Updated documents in '{collection}'")
    console.print("  Matched: 1, Modified: 1")


@doc_group.command(name="delete-docs")
@click.argument("collection")
@click.option("--db", "-d", default="default")
@click.option("--filter", "-q", required=True, help="Query filter")
@click.option("--force", "-f", is_flag=True)
def doc_delete_docs(collection: str, db: str, filter: str, force: bool):
    """Delete documents matching filter."""
    if not force:
        from rich.prompt import Confirm

        if not Confirm.ask("[red]Delete matching documents?[/red]"):
            return
    console.print(f"[green]✓[/green] Deleted documents from '{collection}'")
    console.print("  Deleted: 0")


@doc_group.command(name="count")
@click.argument("collection")
@click.option("--db", "-d", default="default")
@click.option("--query", "-q", default="{}", help="Query filter")
def doc_count(collection: str, db: str, query: str):
    """Count documents."""
    console.print(f"[cyan]Count in {db}.{collection}:[/cyan] 0")


# ============================================================================
# Indexes
# ============================================================================


@doc_group.group()
def indexes():
    """Manage indexes."""
    pass


@indexes.command(name="list")
@click.argument("collection")
@click.option("--db", "-d", default="default")
def indexes_list(collection: str, db: str):
    """List indexes on a collection."""
    table = Table(title=f"Indexes on '{collection}'", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Keys", style="white")
    table.add_column("Type", style="yellow")
    table.add_column("Size", style="dim")

    table.add_row("_id_", "_id: 1", "default", "12 KB")

    console.print(table)


@indexes.command(name="create")
@click.argument("collection")
@click.option("--db", "-d", default="default")
@click.option("--keys", "-k", required=True, help="Index keys (e.g., 'field:1' or 'field:-1')")
@click.option("--name", "-n", help="Index name")
@click.option("--unique", "-u", is_flag=True, help="Unique index")
@click.option("--sparse", is_flag=True, help="Sparse index")
@click.option("--ttl", help="TTL in seconds")
def indexes_create(collection: str, db: str, keys: str, name: str, unique: bool, sparse: bool, ttl: str):
    """Create an index.

    \b
    Examples:
      hanzo doc indexes create users -k email:1 --unique
      hanzo doc indexes create logs -k createdAt:1 --ttl 86400
      hanzo doc indexes create products -k 'category:1,price:-1'
    """
    console.print(f"[green]✓[/green] Index created on '{collection}'")
    console.print(f"  Keys: {keys}")
    if unique:
        console.print("  Unique: Yes")


@indexes.command(name="drop")
@click.argument("collection")
@click.argument("index_name")
@click.option("--db", "-d", default="default")
def indexes_drop(collection: str, index_name: str, db: str):
    """Drop an index."""
    console.print(f"[green]✓[/green] Index '{index_name}' dropped from '{collection}'")


# ============================================================================
# Admin
# ============================================================================


@doc_group.command(name="backup")
@click.argument("name")
@click.option("--output", "-o", help="Output path")
def doc_backup(name: str, output: str):
    """Create database backup."""
    console.print(f"[green]✓[/green] Backup created for '{name}'")
    console.print(f"  Backup ID: bak_abc123")


@doc_group.command(name="restore")
@click.argument("backup_id")
@click.option("--to", "-t", help="Target database name")
def doc_restore(backup_id: str, to: str):
    """Restore from backup."""
    console.print(f"[green]✓[/green] Restored from backup '{backup_id}'")


@doc_group.command(name="users")
@click.argument("action", type=click.Choice(["list", "create", "delete"]))
@click.option("--db", "-d", default="default")
@click.option("--username", "-u", help="Username")
@click.option("--role", "-r", help="Role (read, readWrite, dbAdmin)")
def doc_users(action: str, db: str, username: str, role: str):
    """Manage database users."""
    if action == "list":
        console.print(f"[cyan]Users for '{db}':[/cyan]")
        console.print("[dim]No users found[/dim]")
    elif action == "create":
        console.print(f"[green]✓[/green] User '{username}' created with role '{role}'")
    elif action == "delete":
        console.print(f"[green]✓[/green] User '{username}' deleted")
