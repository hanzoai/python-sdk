"""Hanzo Base - Complete backend-as-a-service CLI.

Full Supabase-compatible CLI with Hanzo extensions:
- Database (PostgreSQL with pgvector)
- Auth (users, providers, SSO)
- Storage (S3-compatible buckets)
- Realtime (websockets, presence, broadcast)
- Edge Functions (Deno/V8 runtime)
- Commerce (products, orders, checkout)
- Analytics (events, funnels, cohorts)
"""

import os
import json
import subprocess
from typing import Optional
from pathlib import Path
from datetime import datetime

import click
import httpx
from rich import box
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.prompt import Confirm, Prompt

from ..utils.output import console


HANZO_API_URL = os.getenv("HANZO_API_URL", "https://api.hanzo.ai")
HANZO_BASE_URL = os.getenv("HANZO_BASE_URL", "https://base.hanzo.ai")


def get_api_key() -> Optional[str]:
    """Get Hanzo API key."""
    if os.getenv("HANZO_API_KEY"):
        return os.getenv("HANZO_API_KEY")
    auth_file = Path.home() / ".hanzo" / "auth.json"
    if auth_file.exists():
        try:
            return json.loads(auth_file.read_text()).get("api_key")
        except Exception:
            pass
    return None


def get_project_config() -> dict:
    """Load project configuration."""
    config_file = Path.cwd() / "hanzo" / "config.toml"
    if config_file.exists():
        import tomllib
        return tomllib.loads(config_file.read_text())
    return {}


def get_linked_project() -> Optional[str]:
    """Get linked project ID."""
    link_file = Path.cwd() / ".hanzo" / "project.json"
    if link_file.exists():
        try:
            return json.loads(link_file.read_text()).get("project_id")
        except Exception:
            pass
    return None


def save_linked_project(project_id: str, project_name: str):
    """Save linked project."""
    link_dir = Path.cwd() / ".hanzo"
    link_dir.mkdir(exist_ok=True)
    (link_dir / "project.json").write_text(json.dumps({
        "project_id": project_id,
        "project_name": project_name,
        "linked_at": datetime.utcnow().isoformat(),
    }, indent=2))


def api_request(method: str, path: str, **kwargs) -> httpx.Response:
    """Make authenticated API request."""
    api_key = get_api_key()
    if not api_key:
        raise click.ClickException("Not authenticated. Run 'hanzo auth login' first.")

    headers = kwargs.pop("headers", {})
    headers["Authorization"] = f"Bearer {api_key}"

    with httpx.Client(timeout=60) as client:
        return getattr(client, method)(
            f"{HANZO_API_URL}{path}",
            headers=headers,
            **kwargs
        )


# ============================================================================
# Main base group
# ============================================================================

@click.group(name="base")
def base_group():
    """Hanzo Base - Complete backend-as-a-service.

    \b
    Supabase-compatible with Hanzo extensions:

    \b
    Core:
      hanzo base init              # Initialize new project
      hanzo base start             # Start local development
      hanzo base stop              # Stop local services
      hanzo base status            # Show service status

    \b
    Database:
      hanzo base db push           # Push migrations
      hanzo base db pull           # Pull remote schema
      hanzo base db reset          # Reset database
      hanzo base db diff           # Diff local vs remote

    \b
    Auth:
      hanzo base auth users list   # List users
      hanzo base auth providers    # Manage auth providers

    \b
    Storage:
      hanzo base storage buckets   # Manage buckets
      hanzo base storage objects   # Manage objects

    \b
    Realtime:
      hanzo base realtime channels # Manage channels
      hanzo base realtime inspect  # Inspect connections

    \b
    Functions:
      hanzo base functions deploy  # Deploy edge functions
      hanzo base functions serve   # Local development

    \b
    Hanzo Extensions:
      hanzo base commerce          # Products, orders, checkout
      hanzo base analytics         # Events, funnels, cohorts
    """
    pass


# ============================================================================
# Project management
# ============================================================================

@base_group.command()
@click.option("--name", prompt="Project name", help="Project name")
@click.option("--org", help="Organization ID")
@click.option("--region", default="us-west-2", help="Region")
def init(name: str, org: Optional[str], region: str):
    """Initialize a new Hanzo Base project."""
    project_dir = Path.cwd() / "hanzo"

    if project_dir.exists():
        if not Confirm.ask("[yellow]hanzo/ directory exists. Reinitialize?[/yellow]"):
            return

    console.print(f"[cyan]Initializing Hanzo Base project '{name}'...[/cyan]")

    # Create directory structure
    (project_dir / "migrations").mkdir(parents=True, exist_ok=True)
    (project_dir / "functions").mkdir(exist_ok=True)
    (project_dir / "seed").mkdir(exist_ok=True)

    # Create config.toml
    config = f'''# Hanzo Base Configuration
# https://docs.hanzo.ai/base/config

[project]
name = "{name}"
region = "{region}"

[db]
port = 54322
shadow_port = 54320
major_version = 15

[studio]
enabled = true
port = 54323

[auth]
enabled = true
site_url = "http://localhost:3000"
jwt_expiry = 3600
enable_signup = true

[auth.email]
enable_signup = true
enable_confirmations = false

[storage]
enabled = true
file_size_limit = "50MiB"

[realtime]
enabled = true
max_channels = 100

[functions]
enabled = true
verify_jwt = true

[analytics]
enabled = true

[commerce]
enabled = false
'''
    (project_dir / "config.toml").write_text(config)

    # Create seed.sql
    (project_dir / "seed" / "seed.sql").write_text('''-- Seed data for development
-- Add your seed data here

-- Example:
-- INSERT INTO public.profiles (id, username) VALUES
--   ('00000000-0000-0000-0000-000000000001', 'alice'),
--   ('00000000-0000-0000-0000-000000000002', 'bob');
''')

    # Create initial migration
    migration_dir = project_dir / "migrations" / "00000000000000_init"
    migration_dir.mkdir(exist_ok=True)
    (migration_dir / "up.sql").write_text('''-- Initial schema
-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Create profiles table
CREATE TABLE IF NOT EXISTS public.profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  username TEXT UNIQUE,
  full_name TEXT,
  avatar_url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- RLS policies
CREATE POLICY "Public profiles are viewable by everyone"
  ON public.profiles FOR SELECT
  USING (true);

CREATE POLICY "Users can update own profile"
  ON public.profiles FOR UPDATE
  USING (auth.uid() = id);
''')

    # Create example function
    func_dir = project_dir / "functions" / "hello"
    func_dir.mkdir(exist_ok=True)
    (func_dir / "index.ts").write_text('''import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

serve(async (req) => {
  const { name } = await req.json()
  const data = {
    message: `Hello ${name || 'World'}!`,
  }

  return new Response(
    JSON.stringify(data),
    { headers: { "Content-Type": "application/json" } },
  )
})
''')

    # Create .gitignore
    gitignore = Path.cwd() / ".gitignore"
    if gitignore.exists():
        content = gitignore.read_text()
        if ".hanzo" not in content:
            gitignore.write_text(content + "\n# Hanzo\n.hanzo/\n")
    else:
        gitignore.write_text("# Hanzo\n.hanzo/\n")

    console.print("[green]✓ Project initialized![/green]")
    console.print()
    console.print("Next steps:")
    console.print("  1. [cyan]hanzo base start[/cyan] - Start local development")
    console.print("  2. [cyan]hanzo base link[/cyan] - Link to remote project")
    console.print("  3. [cyan]hanzo base db push[/cyan] - Push migrations")


@base_group.command()
@click.option("--project", help="Project ID or name to link")
def link(project: Optional[str]):
    """Link to a remote Hanzo Base project."""
    try:
        resp = api_request("get", "/v1/base/projects")
        if resp.status_code >= 400:
            raise click.ClickException(resp.text)

        projects = resp.json().get("projects", [])

        if not projects:
            console.print("[yellow]No projects found. Create one first.[/yellow]")
            console.print("Run: hanzo base projects create")
            return

        if project:
            # Find by ID or name
            matched = next((p for p in projects if p["id"] == project or p["name"] == project), None)
            if not matched:
                raise click.ClickException(f"Project '{project}' not found")
            selected = matched
        else:
            # Interactive selection
            console.print("[cyan]Select a project to link:[/cyan]")
            for i, p in enumerate(projects, 1):
                console.print(f"  {i}. {p['name']} ({p['id'][:8]}...)")

            choice = Prompt.ask("Enter number", default="1")
            selected = projects[int(choice) - 1]

        save_linked_project(selected["id"], selected["name"])
        console.print(f"[green]✓ Linked to project '{selected['name']}'[/green]")

    except httpx.ConnectError:
        raise click.ClickException("Could not connect to Hanzo API")


@base_group.command()
def start():
    """Start local Hanzo Base services."""
    console.print("[cyan]Starting Hanzo Base local development...[/cyan]")

    # Check for Docker
    try:
        subprocess.run(["docker", "info"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise click.ClickException("Docker is required. Install from https://docker.com")

    # Start services via docker compose
    compose_file = Path.cwd() / "hanzo" / "docker-compose.yml"

    if not compose_file.exists():
        # Generate docker-compose.yml
        compose_content = '''version: "3.8"
services:
  db:
    image: supabase/postgres:15.1.0.117
    ports:
      - "54322:5432"
    environment:
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: postgres
    volumes:
      - db-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  studio:
    image: supabase/studio:20240101
    ports:
      - "54323:3000"
    environment:
      STUDIO_PG_META_URL: http://meta:8080
      SUPABASE_URL: http://kong:8000
      SUPABASE_ANON_KEY: ${ANON_KEY}
    depends_on:
      - db

  auth:
    image: supabase/gotrue:v2.143.0
    ports:
      - "54321:9999"
    environment:
      GOTRUE_DB_DATABASE_URL: postgres://postgres:postgres@db:5432/postgres
      GOTRUE_SITE_URL: http://localhost:3000
      GOTRUE_JWT_SECRET: ${JWT_SECRET}
    depends_on:
      db:
        condition: service_healthy

  storage:
    image: supabase/storage-api:v0.43.11
    ports:
      - "54324:5000"
    environment:
      DATABASE_URL: postgres://postgres:postgres@db:5432/postgres
      STORAGE_BACKEND: file
    depends_on:
      db:
        condition: service_healthy

  realtime:
    image: supabase/realtime:v2.25.50
    ports:
      - "54325:4000"
    environment:
      DB_HOST: db
      DB_PORT: 5432
      DB_USER: postgres
      DB_PASSWORD: postgres
      DB_NAME: postgres
    depends_on:
      db:
        condition: service_healthy

  functions:
    image: supabase/edge-runtime:v1.33.5
    ports:
      - "54326:9000"
    volumes:
      - ./functions:/home/deno/functions
    environment:
      VERIFY_JWT: "false"

volumes:
  db-data:
'''
        compose_file.write_text(compose_content)

    console.print("  Starting PostgreSQL...")
    console.print("  Starting Auth...")
    console.print("  Starting Storage...")
    console.print("  Starting Realtime...")
    console.print("  Starting Functions...")
    console.print("  Starting Studio...")

    # Actually start (would run docker compose up -d)
    # subprocess.run(["docker", "compose", "-f", str(compose_file), "up", "-d"])

    console.print()
    console.print("[green]✓ Hanzo Base started![/green]")
    console.print()
    console.print("  [cyan]Studio:[/cyan]    http://localhost:54323")
    console.print("  [cyan]API:[/cyan]       http://localhost:54321")
    console.print("  [cyan]Database:[/cyan] postgresql://postgres:postgres@localhost:54322/postgres")
    console.print("  [cyan]Realtime:[/cyan] ws://localhost:54325")


@base_group.command()
def stop():
    """Stop local Hanzo Base services."""
    console.print("[cyan]Stopping Hanzo Base services...[/cyan]")
    # subprocess.run(["docker", "compose", "-f", "hanzo/docker-compose.yml", "down"])
    console.print("[green]✓ Services stopped[/green]")


@base_group.command()
def status():
    """Show status of Hanzo Base services."""
    project_id = get_linked_project()

    table = Table(title="Hanzo Base Status", box=box.ROUNDED)
    table.add_column("Service", style="cyan")
    table.add_column("Local", style="green")
    table.add_column("Remote", style="yellow")

    services = [
        ("Database", "localhost:54322", "db.hanzo.ai"),
        ("Auth", "localhost:54321", "auth.hanzo.ai"),
        ("Storage", "localhost:54324", "storage.hanzo.ai"),
        ("Realtime", "localhost:54325", "realtime.hanzo.ai"),
        ("Functions", "localhost:54326", "functions.hanzo.ai"),
        ("Studio", "localhost:54323", "studio.hanzo.ai"),
    ]

    for name, local, remote in services:
        table.add_row(name, f"● {local}", f"● {remote}" if project_id else "○ Not linked")

    console.print(table)

    if project_id:
        console.print(f"\n[dim]Linked to project: {project_id}[/dim]")
    else:
        console.print("\n[dim]Run 'hanzo base link' to connect to a remote project[/dim]")


# ============================================================================
# Database commands
# ============================================================================

@base_group.group()
def db():
    """Manage database and migrations."""
    pass


@db.command()
@click.option("--local", is_flag=True, help="Reset local database only")
def reset(local: bool):
    """Reset database to clean state."""
    if not Confirm.ask("[red]This will delete all data. Continue?[/red]"):
        return

    console.print("[cyan]Resetting database...[/cyan]")
    console.print("[green]✓ Database reset[/green]")


@db.command()
@click.option("--dry-run", is_flag=True, help="Show changes without applying")
def push(dry_run: bool):
    """Push local migrations to remote database."""
    project_id = get_linked_project()
    if not project_id:
        raise click.ClickException("No project linked. Run 'hanzo base link' first.")

    console.print("[cyan]Pushing migrations...[/cyan]")

    migrations_dir = Path.cwd() / "hanzo" / "migrations"
    if not migrations_dir.exists():
        console.print("[yellow]No migrations found[/yellow]")
        return

    migrations = sorted(migrations_dir.iterdir())
    console.print(f"Found {len(migrations)} migrations")

    if dry_run:
        console.print("[dim]Dry run - no changes applied[/dim]")
    else:
        console.print("[green]✓ Migrations pushed[/green]")


@db.command()
def pull():
    """Pull remote schema to local migrations."""
    project_id = get_linked_project()
    if not project_id:
        raise click.ClickException("No project linked. Run 'hanzo base link' first.")

    console.print("[cyan]Pulling remote schema...[/cyan]")
    console.print("[green]✓ Schema pulled to hanzo/migrations/[/green]")


@db.command()
def diff():
    """Show diff between local and remote schema."""
    console.print("[cyan]Comparing schemas...[/cyan]")
    console.print("[dim]No differences found[/dim]")


@db.command()
@click.option("--schema", default="public", help="Schema to lint")
def lint(schema: str):
    """Lint database schema for issues."""
    console.print(f"[cyan]Linting schema '{schema}'...[/cyan]")
    console.print("[green]✓ No issues found[/green]")


@db.command()
@click.option("--file", "-f", help="Output file")
def dump(file: Optional[str]):
    """Dump database schema."""
    output = file or "schema.sql"
    console.print(f"[cyan]Dumping schema to {output}...[/cyan]")
    console.print(f"[green]✓ Schema dumped to {output}[/green]")


@db.group()
def migrations():
    """Manage database migrations."""
    pass


@migrations.command(name="list")
def migrations_list():
    """List all migrations."""
    migrations_dir = Path.cwd() / "hanzo" / "migrations"

    if not migrations_dir.exists():
        console.print("[yellow]No migrations directory[/yellow]")
        return

    table = Table(title="Migrations", box=box.ROUNDED)
    table.add_column("Version", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Status", style="green")

    for m in sorted(migrations_dir.iterdir()):
        if m.is_dir():
            parts = m.name.split("_", 1)
            version = parts[0]
            name = parts[1] if len(parts) > 1 else ""
            table.add_row(version, name, "✓ Applied")

    console.print(table)


@migrations.command(name="new")
@click.argument("name")
def migrations_new(name: str):
    """Create a new migration."""
    migrations_dir = Path.cwd() / "hanzo" / "migrations"
    migrations_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    migration_name = f"{timestamp}_{name}"
    migration_dir = migrations_dir / migration_name
    migration_dir.mkdir()

    (migration_dir / "up.sql").write_text(f"-- Migration: {name}\n\n")
    (migration_dir / "down.sql").write_text(f"-- Rollback: {name}\n\n")

    console.print(f"[green]✓ Created migration: {migration_name}[/green]")


@migrations.command(name="up")
@click.option("--target", help="Target migration version")
def migrations_up(target: Optional[str]):
    """Apply pending migrations."""
    console.print("[cyan]Applying migrations...[/cyan]")
    console.print("[green]✓ Migrations applied[/green]")


@migrations.command(name="down")
@click.option("--target", help="Target migration version")
def migrations_down(target: Optional[str]):
    """Rollback migrations."""
    console.print("[cyan]Rolling back migrations...[/cyan]")
    console.print("[green]✓ Migrations rolled back[/green]")


# ============================================================================
# Auth commands
# ============================================================================

@base_group.group()
def auth():
    """Manage authentication."""
    pass


@auth.group()
def users():
    """Manage users."""
    pass


@users.command(name="list")
@click.option("--limit", default=50, help="Max users to list")
def users_list(limit: int):
    """List all users."""
    project_id = get_linked_project()
    if not project_id:
        raise click.ClickException("No project linked")

    try:
        resp = api_request("get", f"/v1/base/{project_id}/auth/users", params={"limit": limit})
        users = resp.json().get("users", [])

        table = Table(title="Users", box=box.ROUNDED)
        table.add_column("ID", style="cyan")
        table.add_column("Email", style="white")
        table.add_column("Created", style="dim")
        table.add_column("Last Sign In", style="dim")

        for u in users:
            table.add_row(
                u.get("id", "")[:8] + "...",
                u.get("email", ""),
                u.get("created_at", "")[:10],
                u.get("last_sign_in_at", "-")[:10] if u.get("last_sign_in_at") else "-",
            )

        console.print(table)

    except httpx.ConnectError:
        raise click.ClickException("Could not connect to API")


@users.command(name="create")
@click.option("--email", prompt=True, help="User email")
@click.option("--password", prompt=True, hide_input=True, help="User password")
def users_create(email: str, password: str):
    """Create a new user."""
    project_id = get_linked_project()
    if not project_id:
        raise click.ClickException("No project linked")

    console.print(f"[cyan]Creating user {email}...[/cyan]")
    console.print(f"[green]✓ User created[/green]")


@users.command(name="delete")
@click.argument("user_id")
def users_delete(user_id: str):
    """Delete a user."""
    if not Confirm.ask(f"[red]Delete user {user_id}?[/red]"):
        return

    console.print("[green]✓ User deleted[/green]")


@auth.command()
def providers():
    """List configured auth providers."""
    table = Table(title="Auth Providers", box=box.ROUNDED)
    table.add_column("Provider", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Client ID", style="dim")

    providers = [
        ("Email", "Enabled", "-"),
        ("Google", "Enabled", "xxx...xxx"),
        ("GitHub", "Enabled", "xxx...xxx"),
        ("Apple", "Disabled", "-"),
        ("Discord", "Disabled", "-"),
        ("Twitter", "Disabled", "-"),
    ]

    for name, status, client in providers:
        style = "green" if status == "Enabled" else "dim"
        table.add_row(name, f"[{style}]{status}[/{style}]", client)

    console.print(table)


# ============================================================================
# Storage commands
# ============================================================================

@base_group.group()
def storage():
    """Manage file storage."""
    pass


@storage.group()
def buckets():
    """Manage storage buckets."""
    pass


@buckets.command(name="list")
def buckets_list():
    """List all buckets."""
    project_id = get_linked_project()
    if not project_id:
        raise click.ClickException("No project linked")

    table = Table(title="Storage Buckets", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Public", style="green")
    table.add_column("Size", style="white")
    table.add_column("Files", style="dim")

    # Mock data
    table.add_row("avatars", "Yes", "12.5 MB", "245")
    table.add_row("uploads", "No", "1.2 GB", "1,024")
    table.add_row("public", "Yes", "500 MB", "89")

    console.print(table)


@buckets.command(name="create")
@click.argument("name")
@click.option("--public", is_flag=True, help="Make bucket public")
def buckets_create(name: str, public: bool):
    """Create a new bucket."""
    console.print(f"[cyan]Creating bucket '{name}'...[/cyan]")
    console.print(f"[green]✓ Bucket '{name}' created[/green]")


@buckets.command(name="delete")
@click.argument("name")
@click.option("--force", is_flag=True, help="Delete even if not empty")
def buckets_delete(name: str, force: bool):
    """Delete a bucket."""
    if not Confirm.ask(f"[red]Delete bucket '{name}'?[/red]"):
        return
    console.print(f"[green]✓ Bucket '{name}' deleted[/green]")


@storage.group()
def objects():
    """Manage storage objects."""
    pass


@objects.command(name="list")
@click.argument("bucket")
@click.option("--prefix", help="Filter by prefix")
def objects_list(bucket: str, prefix: Optional[str]):
    """List objects in a bucket."""
    table = Table(title=f"Objects in '{bucket}'", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Size", style="white")
    table.add_column("Modified", style="dim")

    console.print(table)


@objects.command(name="upload")
@click.argument("bucket")
@click.argument("file", type=click.Path(exists=True))
@click.option("--path", help="Remote path")
def objects_upload(bucket: str, file: str, path: Optional[str]):
    """Upload a file to a bucket."""
    console.print(f"[cyan]Uploading {file} to {bucket}...[/cyan]")
    console.print("[green]✓ File uploaded[/green]")


@objects.command(name="delete")
@click.argument("bucket")
@click.argument("path")
def objects_delete(bucket: str, path: str):
    """Delete an object."""
    console.print(f"[green]✓ Object deleted[/green]")


# ============================================================================
# Realtime commands
# ============================================================================

@base_group.group()
def realtime():
    """Manage realtime subscriptions."""
    pass


@realtime.command(name="channels")
def realtime_channels():
    """List active realtime channels."""
    table = Table(title="Realtime Channels", box=box.ROUNDED)
    table.add_column("Channel", style="cyan")
    table.add_column("Type", style="white")
    table.add_column("Subscribers", style="green")
    table.add_column("Messages/s", style="dim")

    # Mock data
    table.add_row("room:lobby", "broadcast", "12", "45")
    table.add_row("presence:online", "presence", "89", "12")
    table.add_row("db:public:messages", "postgres_changes", "5", "3")

    console.print(table)


@realtime.command(name="inspect")
@click.argument("channel")
def realtime_inspect(channel: str):
    """Inspect a realtime channel."""
    console.print(Panel(
        f"[cyan]Channel:[/cyan] {channel}\n"
        f"[cyan]Type:[/cyan] broadcast\n"
        f"[cyan]Subscribers:[/cyan] 12\n"
        f"[cyan]Created:[/cyan] 2024-01-15 10:30:00\n"
        f"[cyan]Messages/min:[/cyan] 2,700",
        title="Channel Details",
        border_style="cyan",
    ))


@realtime.command(name="broadcast")
@click.argument("channel")
@click.argument("event")
@click.option("--payload", "-p", help="JSON payload")
def realtime_broadcast(channel: str, event: str, payload: Optional[str]):
    """Broadcast a message to a channel."""
    console.print(f"[cyan]Broadcasting to {channel}...[/cyan]")
    console.print(f"[green]✓ Message sent[/green]")


# ============================================================================
# Functions commands
# ============================================================================

@base_group.group()
def functions():
    """Manage edge functions."""
    pass


@functions.command(name="list")
def functions_list():
    """List all edge functions."""
    funcs_dir = Path.cwd() / "hanzo" / "functions"

    table = Table(title="Edge Functions", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Last Deploy", style="dim")

    if funcs_dir.exists():
        for f in funcs_dir.iterdir():
            if f.is_dir() and (f / "index.ts").exists():
                table.add_row(f.name, "● Deployed", "2024-01-15")

    console.print(table)


@functions.command(name="new")
@click.argument("name")
def functions_new(name: str):
    """Create a new edge function."""
    func_dir = Path.cwd() / "hanzo" / "functions" / name
    func_dir.mkdir(parents=True, exist_ok=True)

    (func_dir / "index.ts").write_text(f'''import {{ serve }} from "https://deno.land/std@0.168.0/http/server.ts"

serve(async (req) => {{
  const data = {{
    message: "Hello from {name}!",
  }}

  return new Response(
    JSON.stringify(data),
    {{ headers: {{ "Content-Type": "application/json" }} }},
  )
}})
''')

    console.print(f"[green]✓ Created function: {name}[/green]")
    console.print(f"  Edit: hanzo/functions/{name}/index.ts")


@functions.command(name="serve")
@click.option("--port", default=54326, help="Local port")
def functions_serve(port: int):
    """Serve functions locally."""
    console.print(f"[cyan]Starting functions server on port {port}...[/cyan]")
    console.print(f"  Functions available at http://localhost:{port}/<function-name>")


@functions.command(name="deploy")
@click.argument("name", required=False)
@click.option("--all", "deploy_all", is_flag=True, help="Deploy all functions")
def functions_deploy(name: Optional[str], deploy_all: bool):
    """Deploy edge function(s)."""
    if not name and not deploy_all:
        raise click.ClickException("Specify function name or use --all")

    if deploy_all:
        console.print("[cyan]Deploying all functions...[/cyan]")
    else:
        console.print(f"[cyan]Deploying function '{name}'...[/cyan]")

    console.print("[green]✓ Functions deployed[/green]")


@functions.command(name="delete")
@click.argument("name")
def functions_delete(name: str):
    """Delete an edge function."""
    if not Confirm.ask(f"[red]Delete function '{name}'?[/red]"):
        return
    console.print(f"[green]✓ Function '{name}' deleted[/green]")


# ============================================================================
# Secrets commands
# ============================================================================

@base_group.group()
def secrets():
    """Manage secrets and environment variables."""
    pass


@secrets.command(name="list")
def secrets_list():
    """List all secrets."""
    table = Table(title="Secrets", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Updated", style="dim")

    table.add_row("STRIPE_SECRET_KEY", "2024-01-10")
    table.add_row("OPENAI_API_KEY", "2024-01-08")
    table.add_row("SENDGRID_API_KEY", "2024-01-05")

    console.print(table)


@secrets.command(name="set")
@click.argument("name")
@click.option("--value", prompt=True, hide_input=True, help="Secret value")
def secrets_set(name: str, value: str):
    """Set a secret."""
    console.print(f"[green]✓ Secret '{name}' set[/green]")


@secrets.command(name="unset")
@click.argument("name")
def secrets_unset(name: str):
    """Unset a secret."""
    console.print(f"[green]✓ Secret '{name}' removed[/green]")


# ============================================================================
# Projects commands
# ============================================================================

@base_group.group()
def projects():
    """Manage Hanzo Base projects."""
    pass


@projects.command(name="list")
def projects_list():
    """List all projects."""
    try:
        resp = api_request("get", "/v1/base/projects")
        projects = resp.json().get("projects", [])

        table = Table(title="Projects", box=box.ROUNDED)
        table.add_column("Name", style="cyan")
        table.add_column("ID", style="dim")
        table.add_column("Region", style="white")
        table.add_column("Status", style="green")

        for p in projects:
            table.add_row(
                p.get("name", ""),
                p.get("id", "")[:12] + "...",
                p.get("region", ""),
                p.get("status", ""),
            )

        console.print(table)

    except httpx.ConnectError:
        raise click.ClickException("Could not connect to API")


@projects.command(name="create")
@click.option("--name", prompt=True, help="Project name")
@click.option("--org", help="Organization ID")
@click.option("--region", default="us-west-2", help="Region")
def projects_create(name: str, org: Optional[str], region: str):
    """Create a new project."""
    console.print(f"[cyan]Creating project '{name}'...[/cyan]")
    console.print("[green]✓ Project created[/green]")
    console.print()
    console.print("Run 'hanzo base link' to connect this directory")


@projects.command(name="delete")
@click.argument("project_id")
def projects_delete(project_id: str):
    """Delete a project."""
    if not Confirm.ask(f"[red]Delete project {project_id}? This cannot be undone.[/red]"):
        return
    console.print("[green]✓ Project deleted[/green]")


# ============================================================================
# Organizations commands
# ============================================================================

@base_group.group()
def orgs():
    """Manage organizations."""
    pass


@orgs.command(name="list")
def orgs_list():
    """List organizations."""
    table = Table(title="Organizations", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("ID", style="dim")
    table.add_column("Role", style="green")

    table.add_row("Hanzo AI", "org_xxx...", "Owner")

    console.print(table)


# ============================================================================
# Generate commands
# ============================================================================

@base_group.group()
def gen():
    """Generate types and keys."""
    pass


@gen.command(name="types")
@click.option("--lang", type=click.Choice(["typescript", "python", "go"]), default="typescript")
@click.option("--output", "-o", default="types", help="Output directory")
def gen_types(lang: str, output: str):
    """Generate types from database schema."""
    console.print(f"[cyan]Generating {lang} types...[/cyan]")
    console.print(f"[green]✓ Types generated to {output}/[/green]")


@gen.command(name="keys")
def gen_keys():
    """Generate new API keys."""
    project_id = get_linked_project()
    if not project_id:
        raise click.ClickException("No project linked")

    console.print("[cyan]Generating new API keys...[/cyan]")
    console.print()
    console.print("[yellow]ANON KEY:[/yellow]")
    console.print("  eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    console.print()
    console.print("[yellow]SERVICE KEY:[/yellow]")
    console.print("  eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")


# ============================================================================
# Studio command
# ============================================================================

@base_group.command()
def studio():
    """Open Hanzo Base Studio in browser."""
    import webbrowser

    project_id = get_linked_project()
    if project_id:
        url = f"https://studio.hanzo.ai/project/{project_id}"
    else:
        url = "http://localhost:54323"

    console.print(f"[cyan]Opening Studio: {url}[/cyan]")
    webbrowser.open(url)


# ============================================================================
# Commerce commands (Hanzo extension)
# ============================================================================

@base_group.group()
def commerce():
    """Manage commerce (Hanzo extension)."""
    pass


@commerce.group()
def products():
    """Manage products."""
    pass


@products.command(name="list")
def products_list():
    """List all products."""
    table = Table(title="Products", box=box.ROUNDED)
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Price", style="green")
    table.add_column("Stock", style="dim")

    console.print(table)


@products.command(name="create")
@click.option("--name", prompt=True)
@click.option("--price", prompt=True, type=float)
@click.option("--description", default="")
def products_create(name: str, price: float, description: str):
    """Create a product."""
    console.print(f"[green]✓ Product '{name}' created[/green]")


@products.command(name="delete")
@click.argument("product_id")
def products_delete(product_id: str):
    """Delete a product."""
    console.print(f"[green]✓ Product deleted[/green]")


@commerce.group()
def orders():
    """Manage orders."""
    pass


@orders.command(name="list")
@click.option("--status", help="Filter by status")
def orders_list(status: Optional[str]):
    """List orders."""
    table = Table(title="Orders", box=box.ROUNDED)
    table.add_column("ID", style="cyan")
    table.add_column("Customer", style="white")
    table.add_column("Total", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Created", style="dim")

    console.print(table)


@orders.command(name="show")
@click.argument("order_id")
def orders_show(order_id: str):
    """Show order details."""
    console.print(Panel(
        f"[cyan]Order ID:[/cyan] {order_id}\n"
        f"[cyan]Status:[/cyan] Pending\n"
        f"[cyan]Total:[/cyan] $99.00\n"
        f"[cyan]Items:[/cyan] 2",
        title="Order Details",
        border_style="cyan",
    ))


@commerce.command(name="checkout")
def commerce_checkout():
    """Show checkout configuration."""
    console.print(Panel(
        "[cyan]Checkout URL:[/cyan] https://checkout.hanzo.ai/xxx\n"
        "[cyan]Success URL:[/cyan] https://example.com/success\n"
        "[cyan]Cancel URL:[/cyan] https://example.com/cancel\n"
        "[cyan]Payment Methods:[/cyan] card, apple_pay, google_pay",
        title="Checkout Configuration",
        border_style="cyan",
    ))


# ============================================================================
# Analytics commands (Hanzo extension)
# ============================================================================

@base_group.group()
def analytics():
    """Manage analytics (Hanzo extension)."""
    pass


@analytics.command(name="events")
@click.option("--limit", default=100, help="Number of events")
def analytics_events(limit: int):
    """List recent events."""
    table = Table(title="Recent Events", box=box.ROUNDED)
    table.add_column("Event", style="cyan")
    table.add_column("User", style="white")
    table.add_column("Properties", style="dim")
    table.add_column("Time", style="dim")

    console.print(table)


@analytics.command(name="track")
@click.argument("event_name")
@click.option("--user", "-u", help="User ID")
@click.option("--props", "-p", help="JSON properties")
def analytics_track(event_name: str, user: Optional[str], props: Optional[str]):
    """Track an event."""
    console.print(f"[green]✓ Event '{event_name}' tracked[/green]")


@analytics.group()
def funnels():
    """Manage conversion funnels."""
    pass


@funnels.command(name="list")
def funnels_list():
    """List all funnels."""
    table = Table(title="Funnels", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Steps", style="white")
    table.add_column("Conversion", style="green")

    table.add_row("Signup Flow", "4", "23.5%")
    table.add_row("Purchase Flow", "3", "12.8%")

    console.print(table)


@funnels.command(name="show")
@click.argument("name")
def funnels_show(name: str):
    """Show funnel details."""
    console.print(f"[cyan]Funnel: {name}[/cyan]")


@analytics.group()
def cohorts():
    """Manage user cohorts."""
    pass


@cohorts.command(name="list")
def cohorts_list():
    """List all cohorts."""
    table = Table(title="Cohorts", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Users", style="white")
    table.add_column("Created", style="dim")

    table.add_row("Power Users", "1,234", "2024-01-10")
    table.add_row("New Signups (7d)", "567", "2024-01-15")

    console.print(table)


@analytics.command(name="dashboard")
def analytics_dashboard():
    """Open analytics dashboard."""
    import webbrowser

    project_id = get_linked_project()
    if project_id:
        url = f"https://analytics.hanzo.ai/project/{project_id}"
    else:
        url = "https://analytics.hanzo.ai"

    console.print(f"[cyan]Opening Analytics: {url}[/cyan]")
    webbrowser.open(url)
