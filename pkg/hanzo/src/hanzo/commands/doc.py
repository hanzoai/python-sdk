"""Hanzo Doc - Document database CLI.

MongoDB-compatible document database with global distribution.
"""

import os
import json

import click
import httpx
from rich import box
from rich.panel import Panel
from rich.table import Table

from .base import check_response, service_request
from ..utils.output import console

DOC_URL = os.getenv("HANZO_DOC_URL", "https://doc.hanzo.ai")


def _request(method: str, path: str, **kwargs) -> httpx.Response:
    return service_request(DOC_URL, method, path, **kwargs)


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
    payload = {"name": name, "tier": tier}
    if region:
        payload["regions"] = list(region)

    resp = _request("post", "/v1/databases", json=payload)
    data = check_response(resp)

    console.print(f"[green]✓[/green] Database '{name}' created")
    console.print(f"  ID: {data.get('id', '-')}")
    console.print(f"  Tier: {tier}")
    if region:
        console.print(f"  Regions: {', '.join(region)}")
    console.print(f"  Connection: {data.get('connection_string', f'mongodb://doc.hanzo.ai/{name}')}")


@doc_group.command(name="list")
def doc_list():
    """List document databases."""
    resp = _request("get", "/v1/databases")
    data = check_response(resp)
    dbs = data.get("databases", data.get("items", []))

    table = Table(title="Document Databases", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Tier", style="white")
    table.add_column("Collections", style="green")
    table.add_column("Size", style="yellow")
    table.add_column("Status", style="dim")

    for db in dbs:
        status = db.get("status", "unknown")
        style = "green" if status == "running" else "yellow"
        table.add_row(
            db.get("name", ""),
            db.get("tier", "-"),
            str(db.get("collection_count", 0)),
            db.get("size", "0 B"),
            f"[{style}]● {status}[/{style}]",
        )

    console.print(table)
    if not dbs:
        console.print("[dim]No databases found. Create one with 'hanzo doc create'[/dim]")


@doc_group.command(name="describe")
@click.argument("name")
def doc_describe(name: str):
    """Show database details."""
    resp = _request("get", f"/v1/databases/{name}")
    data = check_response(resp)

    status = data.get("status", "unknown")
    style = "green" if status == "running" else "yellow"

    console.print(
        Panel(
            f"[cyan]Name:[/cyan] {data.get('name', name)}\n"
            f"[cyan]Tier:[/cyan] {data.get('tier', '-')}\n"
            f"[cyan]Status:[/cyan] [{style}]● {status}[/{style}]\n"
            f"[cyan]Collections:[/cyan] {data.get('collection_count', 0)}\n"
            f"[cyan]Documents:[/cyan] {data.get('document_count', 0):,}\n"
            f"[cyan]Size:[/cyan] {data.get('size', '0 B')}\n"
            f"[cyan]Regions:[/cyan] {', '.join(data.get('regions', ['-']))}\n"
            f"[cyan]Connection:[/cyan] {data.get('connection_string', f'mongodb://doc.hanzo.ai/{name}')}",
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

    resp = _request("delete", f"/v1/databases/{name}")
    check_response(resp)
    console.print(f"[green]✓[/green] Database '{name}' deleted")


@doc_group.command(name="connect")
@click.argument("name")
def doc_connect(name: str):
    """Get connection string."""
    resp = _request("get", f"/v1/databases/{name}")
    data = check_response(resp)
    conn = data.get("connection_string", f"mongodb://doc.hanzo.ai/{name}?authSource=admin")
    console.print(f"[cyan]Connection string for '{name}':[/cyan]")
    console.print(conn)


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
    resp = _request("get", f"/v1/databases/{db}/collections")
    data = check_response(resp)
    items = data.get("collections", data.get("items", []))

    table = Table(title=f"Collections in '{db}'", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Documents", style="green")
    table.add_column("Size", style="yellow")
    table.add_column("Indexes", style="dim")

    for c in items:
        table.add_row(
            c.get("name", ""),
            str(c.get("document_count", 0)),
            c.get("size", "0 B"),
            str(c.get("index_count", 0)),
        )

    console.print(table)
    if not items:
        console.print("[dim]No collections found[/dim]")


@collections.command(name="create")
@click.argument("name")
@click.option("--db", "-d", default="default", help="Database name")
@click.option("--capped", is_flag=True, help="Create capped collection")
@click.option("--size", "-s", help="Max size for capped collection")
@click.option("--validator", "-v", help="JSON schema validator")
def collections_create(name: str, db: str, capped: bool, size: str, validator: str):
    """Create a collection."""
    payload = {"name": name}
    if capped:
        payload["capped"] = True
        if size:
            payload["max_size"] = size
    if validator:
        payload["validator"] = json.loads(validator)

    resp = _request("post", f"/v1/databases/{db}/collections", json=payload)
    check_response(resp)

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

    resp = _request("delete", f"/v1/databases/{db}/collections/{name}")
    check_response(resp)
    console.print(f"[green]✓[/green] Collection '{name}' dropped")


@collections.command(name="stats")
@click.argument("name")
@click.option("--db", "-d", default="default")
def collections_stats(name: str, db: str):
    """Show collection statistics."""
    resp = _request("get", f"/v1/databases/{db}/collections/{name}/stats")
    data = check_response(resp)

    console.print(
        Panel(
            f"[cyan]Collection:[/cyan] {data.get('name', name)}\n"
            f"[cyan]Documents:[/cyan] {data.get('document_count', 0):,}\n"
            f"[cyan]Size:[/cyan] {data.get('size', '0 B')}\n"
            f"[cyan]Avg doc size:[/cyan] {data.get('avg_doc_size', '0 B')}\n"
            f"[cyan]Indexes:[/cyan] {data.get('index_count', 0)}\n"
            f"[cyan]Index size:[/cyan] {data.get('index_size', '0 B')}",
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
    payload = {"filter": json.loads(query), "limit": limit}
    if projection:
        payload["projection"] = json.loads(projection)
    if sort:
        payload["sort"] = json.loads(sort)
    if skip:
        payload["skip"] = skip

    resp = _request("post", f"/v1/databases/{db}/collections/{collection}/find", json=payload)
    data = check_response(resp)
    docs = data.get("documents", data.get("items", []))

    console.print(f"[cyan]Results from {db}.{collection}:[/cyan]")
    for doc in docs:
        console.print(json.dumps(doc, indent=2, default=str))

    total = data.get("total", len(docs))
    if not docs:
        console.print("[dim]No documents found[/dim]")
    else:
        console.print(f"\n[dim]{total} total, showing {len(docs)}[/dim]")


@doc_group.command(name="insert")
@click.argument("collection")
@click.option("--db", "-d", default="default")
@click.option("--doc", help="Document JSON")
@click.option("--file", "-f", type=click.Path(exists=True), help="Document file")
def doc_insert(collection: str, db: str, doc: str, file: str):
    """Insert a document."""
    if file:
        from pathlib import Path

        document = json.loads(Path(file).read_text())
    elif doc:
        document = json.loads(doc)
    else:
        raise click.ClickException("Provide --doc or --file")

    resp = _request("post", f"/v1/databases/{db}/collections/{collection}/insert", json={"document": document})
    data = check_response(resp)

    console.print(f"[green]✓[/green] Inserted document into '{collection}'")
    console.print(f"  _id: {data.get('inserted_id', data.get('_id', '-'))}")


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
    update_doc = {}
    if set_fields:
        set_dict = {}
        for field in set_fields:
            k, v = field.split("=", 1)
            set_dict[k] = v
        update_doc["$set"] = set_dict
    if unset_fields:
        update_doc["$unset"] = {f: "" for f in unset_fields}

    payload = {
        "filter": json.loads(filter),
        "update": update_doc,
        "upsert": upsert,
    }

    resp = _request("post", f"/v1/databases/{db}/collections/{collection}/update", json=payload)
    data = check_response(resp)

    console.print(f"[green]✓[/green] Updated documents in '{collection}'")
    console.print(f"  Matched: {data.get('matched_count', 0)}, Modified: {data.get('modified_count', 0)}")
    if upsert and data.get("upserted_id"):
        console.print(f"  Upserted: {data['upserted_id']}")


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

    payload = {"filter": json.loads(filter)}
    resp = _request("post", f"/v1/databases/{db}/collections/{collection}/delete", json=payload)
    data = check_response(resp)

    console.print(f"[green]✓[/green] Deleted documents from '{collection}'")
    console.print(f"  Deleted: {data.get('deleted_count', 0)}")


@doc_group.command(name="count")
@click.argument("collection")
@click.option("--db", "-d", default="default")
@click.option("--query", "-q", default="{}", help="Query filter")
def doc_count(collection: str, db: str, query: str):
    """Count documents."""
    payload = {"filter": json.loads(query)}
    resp = _request("post", f"/v1/databases/{db}/collections/{collection}/count", json=payload)
    data = check_response(resp)
    console.print(f"[cyan]Count in {db}.{collection}:[/cyan] {data.get('count', 0):,}")


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
    resp = _request("get", f"/v1/databases/{db}/collections/{collection}/indexes")
    data = check_response(resp)
    items = data.get("indexes", [])

    table = Table(title=f"Indexes on '{collection}'", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Keys", style="white")
    table.add_column("Type", style="yellow")
    table.add_column("Size", style="dim")

    for idx in items:
        keys = idx.get("keys", idx.get("key", {}))
        keys_str = ", ".join(f"{k}: {v}" for k, v in keys.items()) if isinstance(keys, dict) else str(keys)
        table.add_row(
            idx.get("name", "-"),
            keys_str,
            idx.get("type", "standard"),
            idx.get("size", "-"),
        )

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
    key_dict = {}
    for pair in keys.split(","):
        parts = pair.strip().split(":")
        key_dict[parts[0]] = int(parts[1]) if len(parts) > 1 else 1

    payload = {"keys": key_dict}
    if name:
        payload["name"] = name
    if unique:
        payload["unique"] = True
    if sparse:
        payload["sparse"] = True
    if ttl:
        payload["expire_after_seconds"] = int(ttl)

    resp = _request("post", f"/v1/databases/{db}/collections/{collection}/indexes", json=payload)
    data = check_response(resp)

    console.print(f"[green]✓[/green] Index created on '{collection}'")
    console.print(f"  Name: {data.get('name', name or '-')}")
    console.print(f"  Keys: {keys}")
    if unique:
        console.print("  Unique: Yes")


@indexes.command(name="drop")
@click.argument("collection")
@click.argument("index_name")
@click.option("--db", "-d", default="default")
def indexes_drop(collection: str, index_name: str, db: str):
    """Drop an index."""
    resp = _request("delete", f"/v1/databases/{db}/collections/{collection}/indexes/{index_name}")
    check_response(resp)
    console.print(f"[green]✓[/green] Index '{index_name}' dropped from '{collection}'")


# ============================================================================
# Admin
# ============================================================================


@doc_group.command(name="backup")
@click.argument("name")
@click.option("--output", "-o", help="Output path")
def doc_backup(name: str, output: str):
    """Create database backup."""
    payload = {"database": name}
    if output:
        payload["output"] = output

    resp = _request("post", "/v1/backups", json=payload)
    data = check_response(resp)
    console.print(f"[green]✓[/green] Backup created for '{name}'")
    console.print(f"  Backup ID: {data.get('id', '-')}")


@doc_group.command(name="restore")
@click.argument("backup_id")
@click.option("--to", "-t", help="Target database name")
def doc_restore(backup_id: str, to: str):
    """Restore from backup."""
    payload = {"backup_id": backup_id}
    if to:
        payload["target_database"] = to

    resp = _request("post", "/v1/backups/restore", json=payload)
    check_response(resp)
    console.print(f"[green]✓[/green] Restored from backup '{backup_id}'")


@doc_group.command(name="users")
@click.argument("action", type=click.Choice(["list", "create", "delete"]))
@click.option("--db", "-d", default="default")
@click.option("--username", "-u", help="Username")
@click.option("--role", "-r", help="Role (read, readWrite, dbAdmin)")
def doc_users(action: str, db: str, username: str, role: str):
    """Manage database users."""
    if action == "list":
        resp = _request("get", f"/v1/databases/{db}/users")
        data = check_response(resp)
        users = data.get("users", [])

        table = Table(title=f"Users for '{db}'", box=box.ROUNDED)
        table.add_column("Username", style="cyan")
        table.add_column("Role", style="green")
        table.add_column("Created", style="dim")

        for u in users:
            table.add_row(u.get("username", ""), u.get("role", "-"), str(u.get("created_at", ""))[:19])

        console.print(table)
        if not users:
            console.print("[dim]No users found[/dim]")

    elif action == "create":
        if not username or not role:
            raise click.ClickException("--username and --role required for create")
        resp = _request("post", f"/v1/databases/{db}/users", json={"username": username, "role": role})
        data = check_response(resp)
        console.print(f"[green]✓[/green] User '{username}' created with role '{role}'")
        if data.get("password"):
            console.print(f"  Password: {data['password']}")

    elif action == "delete":
        if not username:
            raise click.ClickException("--username required for delete")
        resp = _request("delete", f"/v1/databases/{db}/users/{username}")
        check_response(resp)
        console.print(f"[green]✓[/green] User '{username}' deleted")
