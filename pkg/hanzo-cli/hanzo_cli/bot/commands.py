"""Hanzo CLI — Bot gateway management.

Manage the Hanzo bot-gateway deployment via PaaS API,
and run local bot agent nodes that connect to gw.hanzo.bot.

Usage:
    hanzo bot status                    Show container + pod status
    hanzo bot logs [--tail N]           View recent logs
    hanzo bot deploy                    Trigger redeploy
    hanzo bot env [KEY=VAL ...]         Show/set env vars
    hanzo bot events                    Show container events
    hanzo bot install                   Install @hanzo/bot locally
    hanzo bot run [--daemon]            Run local bot node agent
    hanzo bot stop                      Stop local bot node daemon
"""

from __future__ import annotations

import http.server
import json
import os
import shutil
import signal
import subprocess
import sys
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.table import Table

from hanzo_cli.paas.client import PaaSClient
from hanzo_cli.paas.context import resolve

console = Console()

# ── local node constants ─────────────────────────────────────────────

HANZO_BIN = Path.home() / ".hanzo" / "bin"
BOT_PID_FILE = Path.home() / ".hanzo" / "bot" / "node.pid"
BOT_LOG_FILE = Path.home() / ".hanzo" / "bot" / "node.log"
DEFAULT_GATEWAY_HOST = "gw.hanzo.bot"
DEFAULT_GATEWAY_PORT = 443
NPM_PACKAGE = "@hanzo/bot"
BOT_IAM_CLIENT_ID = "hanzobot-client-id"
BOT_IAM_SERVER_URL = "https://hanzo.id"
BOT_IAM_ORG = "hanzo"
BOT_IAM_APP = "app-hanzobot"
BOT_CALLBACK_PORT = 8398
BOT_CALLBACK_PATH = "/callback"
BOT_TOKEN_FILE = Path.home() / ".hanzo" / "bot" / "token.json"

# ── defaults ──────────────────────────────────────────────────────────

# Known Hanzo production bot container context.
# These can be overridden via --org / --project / --env flags.
DEFAULT_BOT_ORG = "698cda6739f65183b3009313"
DEFAULT_BOT_PROJECT = "698cda6739f65183b3009318"
DEFAULT_BOT_ENV = "698cda6739f65183b300931c"
DEFAULT_BOT_NAME = "bot"


# ── shared options ────────────────────────────────────────────────────


def _org_option(fn):
    return click.option(
        "--org", default=None, help="Organization ID (default: Hanzo)."
    )(fn)


def _project_option(fn):
    return click.option(
        "--project", default=None, help="Project ID (default: Platform)."
    )(fn)


def _env_option(fn):
    return click.option(
        "--env", "env_id", default=None, help="Environment ID (default: production)."
    )(fn)


def _name_option(fn):
    return click.option(
        "--name",
        "-n",
        default=DEFAULT_BOT_NAME,
        help="Container name (default: bot).",
    )(fn)


def _resolve_bot(
    org: str | None,
    project: str | None,
    env_id: str | None,
) -> tuple[str, str, str]:
    """Resolve org/project/env, falling back to bot defaults."""
    ctx_org, ctx_proj, ctx_env = resolve(org, project, env_id)
    return (
        ctx_org or DEFAULT_BOT_ORG,
        ctx_proj or DEFAULT_BOT_PROJECT,
        ctx_env or DEFAULT_BOT_ENV,
    )


def _find_container(
    client: PaaSClient,
    org_id: str,
    project_id: str,
    env_id: str,
    name: str,
) -> dict[str, Any]:
    """Look up a container by name."""
    containers = client.list_containers(org_id, project_id, env_id)
    items = (
        containers
        if isinstance(containers, list)
        else containers.get("data", containers)
    )
    for c in items:
        if c.get("iid") == name or c.get("name") == name or c.get("slug") == name:
            return c
    console.print(f"[red]Bot container '{name}' not found.[/red]")
    raise SystemExit(1)


# ── group ─────────────────────────────────────────────────────────────


@click.group()
def bot() -> None:
    """Manage the Hanzo bot-gateway deployment."""


# ── status ────────────────────────────────────────────────────────────


@bot.command("status")
@_name_option
@_org_option
@_project_option
@_env_option
def bot_status(
    name: str,
    org: str | None,
    project: str | None,
    env_id: str | None,
) -> None:
    """Show bot container status and pods."""
    org_id, project_id, env_id = _resolve_bot(org, project, env_id)

    client = PaaSClient.from_auth()
    try:
        container = _find_container(client, org_id, project_id, env_id, name)
        cid = str(container.get("_id", container.get("id")))

        # Container info
        table = Table(title=f"Bot: {name}")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")
        table.add_row("ID", cid)
        table.add_row("Type", container.get("type", "—"))

        pipeline = container.get("pipelineStatus", "—")
        if isinstance(pipeline, dict):
            pipeline = pipeline.get("status", str(pipeline))
        table.add_row("Pipeline", str(pipeline))

        reg = container.get("registry", {})
        if isinstance(reg, dict) and reg.get("imageUrl"):
            table.add_row("Image", reg["imageUrl"])

        status = container.get("status", {})
        if isinstance(status, dict):
            table.add_row("Desired", str(status.get("desiredReplicas", "—")))
            table.add_row("Ready", str(status.get("readyReplicas", "—")))
            table.add_row("Available", str(status.get("availableReplicas", "—")))
        console.print(table)

        # Pods
        try:
            pods_data = client.get_container_pods(org_id, project_id, env_id, cid)
            pods = (
                pods_data if isinstance(pods_data, list) else pods_data.get("data", [])
            )
            if pods:
                pod_table = Table(title="Pods")
                pod_table.add_column("Name", style="cyan")
                pod_table.add_column("Status", style="green")
                pod_table.add_column("Restarts", style="yellow", justify="right")
                pod_table.add_column("Age", style="dim")
                for p in pods:
                    pod_table.add_row(
                        p.get("name", "—"),
                        p.get("status", "—"),
                        str(p.get("restartCount", 0)),
                        p.get("age", "—"),
                    )
                console.print(pod_table)
            else:
                console.print("[yellow]No pods found.[/yellow]")
        except Exception:
            pass
    finally:
        client.close()


# ── logs ──────────────────────────────────────────────────────────────


@bot.command("logs")
@click.option("--tail", "-t", type=int, default=100, help="Number of lines to show.")
@_name_option
@_org_option
@_project_option
@_env_option
def bot_logs(
    tail: int,
    name: str,
    org: str | None,
    project: str | None,
    env_id: str | None,
) -> None:
    """Show bot container logs."""
    org_id, project_id, env_id = _resolve_bot(org, project, env_id)

    client = PaaSClient.from_auth()
    try:
        container = _find_container(client, org_id, project_id, env_id, name)
        cid = str(container.get("_id", container.get("id")))
        logs_data = client.get_container_logs(org_id, project_id, env_id, cid)

        if isinstance(logs_data, dict) and "logs" in logs_data:
            pod_logs = logs_data["logs"]
            if isinstance(pod_logs, list):
                for pod in pod_logs:
                    if isinstance(pod, dict):
                        pod_name = pod.get("podName", "?")
                        lines = pod.get("logs", [])
                        if len(pod_logs) > 1:
                            click.echo(click.style(f"--- {pod_name} ---", fg="cyan"))
                        shown = lines[-tail:] if tail else lines
                        for line in shown:
                            if line:
                                click.echo(line)
                    else:
                        click.echo(str(pod))
            else:
                click.echo(str(pod_logs))
        elif isinstance(logs_data, str):
            lines = logs_data.splitlines()
            for line in lines[-tail:]:
                click.echo(line)
        elif isinstance(logs_data, list):
            for line in logs_data[-tail:]:
                click.echo(line)
        else:
            click.echo(json.dumps(logs_data, indent=2))
    finally:
        client.close()


# ── deploy ────────────────────────────────────────────────────────────


@bot.command("deploy")
@_name_option
@_org_option
@_project_option
@_env_option
def bot_deploy(
    name: str,
    org: str | None,
    project: str | None,
    env_id: str | None,
) -> None:
    """Trigger a redeploy of the bot container."""
    org_id, project_id, env_id = _resolve_bot(org, project, env_id)

    client = PaaSClient.from_auth()
    try:
        container = _find_container(client, org_id, project_id, env_id, name)
        cid = str(container.get("_id", container.get("id")))
        client.redeploy_container(org_id, project_id, env_id, cid)
    finally:
        client.close()

    console.print(f"[green]Redeployment triggered for '{name}'.[/green]")


# ── env ───────────────────────────────────────────────────────────────


@bot.command("env")
@click.argument("vars", nargs=-1)
@_name_option
@_org_option
@_project_option
@_env_option
def bot_env(
    vars: tuple[str, ...],
    name: str,
    org: str | None,
    project: str | None,
    env_id: str | None,
) -> None:
    """Show or set bot environment variables.

    Without arguments, shows current vars. With KEY=VAL pairs, sets them.

    \b
    Examples:
        hanzo bot env                              Show current vars
        hanzo bot env NODE_ENV=production           Set a var
        hanzo bot env BOT_TOKEN=xxx LOG_LEVEL=debug Set multiple
    """
    org_id, project_id, env_id = _resolve_bot(org, project, env_id)

    client = PaaSClient.from_auth()
    try:
        container = _find_container(client, org_id, project_id, env_id, name)
        cid = str(container.get("_id", container.get("id")))

        if not vars:
            # Show current vars
            variables = container.get("variables", [])
            if not variables:
                console.print("[yellow]No environment variables set.[/yellow]")
                return
            table = Table(title=f"Env vars: {name}")
            table.add_column("Key", style="cyan")
            table.add_column("Value", style="dim")
            for v in variables:
                val = v.get("value", "")
                masked = f"{val[:4]}***" if len(val) > 4 else val
                table.add_row(v.get("name", "—"), masked)
            console.print(table)
        else:
            # Set vars
            new_vars = []
            for kv in vars:
                if "=" not in kv:
                    console.print(f"[red]Invalid format: '{kv}'. Use KEY=VALUE.[/red]")
                    raise SystemExit(1)
                k, v = kv.split("=", 1)
                new_vars.append({"name": k, "value": v})

            # Merge with existing
            existing = {v["name"]: v["value"] for v in container.get("variables", [])}
            for nv in new_vars:
                existing[nv["name"]] = nv["value"]

            merged = [{"name": k, "value": v} for k, v in existing.items()]
            container["variables"] = merged
            client.update_container(org_id, project_id, env_id, cid, container)
            console.print(
                f"[green]Set {len(new_vars)} variable(s) on '{name}'.[/green]"
            )
    finally:
        client.close()


# ── events ────────────────────────────────────────────────────────────


@bot.command("events")
@_name_option
@_org_option
@_project_option
@_env_option
def bot_events(
    name: str,
    org: str | None,
    project: str | None,
    env_id: str | None,
) -> None:
    """Show bot container events."""
    org_id, project_id, env_id = _resolve_bot(org, project, env_id)

    client = PaaSClient.from_auth()
    try:
        container = _find_container(client, org_id, project_id, env_id, name)
        cid = str(container.get("_id", container.get("id")))
        events_data = client.get_container_events(org_id, project_id, env_id, cid)

        events = (
            events_data
            if isinstance(events_data, list)
            else events_data.get("data", [])
        )
        if not events:
            console.print("[yellow]No events found.[/yellow]")
            return

        table = Table(title=f"Events: {name}")
        table.add_column("Type", style="cyan")
        table.add_column("Reason", style="yellow")
        table.add_column("Message", style="white")
        table.add_column("Age", style="dim")

        for e in events:
            table.add_row(
                e.get("type", "—"),
                e.get("reason", "—"),
                e.get("message", "—"),
                e.get("age", e.get("lastTimestamp", "—")),
            )
        console.print(table)
    finally:
        client.close()


# ── local node helpers ───────────────────────────────────────────────


def _find_bot_binary() -> str | None:
    """Search PATH and ~/.hanzo/bin for the hanzo-bot binary."""
    for name in ("hanzo-bot",):
        path = shutil.which(name)
        if path:
            return path
        candidate = HANZO_BIN / name
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


def _install_bot() -> bool:
    """Install @hanzo/bot via npm. Returns True on success."""
    npm = shutil.which("npm") or shutil.which("pnpm")
    if not npm:
        console.print("[red]npm/pnpm not found. Install Node.js first:[/red]")
        console.print("  curl -fsSL https://hanzo.bot/install.sh | bash")
        return False
    try:
        console.print(f"[cyan]Installing {NPM_PACKAGE}...[/cyan]")
        result = subprocess.run(
            [npm, "install", "-g", NPM_PACKAGE],
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
        console.print(f"[green]Installed {NPM_PACKAGE}[/green]")
        return True
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Install failed:[/red] {e.stderr.strip()}")
        return False
    except subprocess.TimeoutExpired:
        console.print("[red]Install timed out.[/red]")
        return False


def _ensure_bot_binary() -> str:
    """Find or install the hanzo-bot binary. Returns the path or exits."""
    binary = _find_bot_binary()
    if binary:
        return binary

    console.print("[yellow]hanzo-bot not found. Installing...[/yellow]")
    if _install_bot():
        binary = _find_bot_binary()
    if not binary:
        console.print("[red]Failed to install hanzo-bot.[/red]")
        console.print("Install manually: npm install -g @hanzo/bot")
        console.print("  or: curl -fsSL https://hanzo.bot/install.sh | bash")
        raise SystemExit(1)
    return binary


def _env(name: str) -> str:
    """Read env var, accepting both IAM_ and legacy HANZO_IAM_ prefixes."""
    return os.environ.get(name, "") or os.environ.get(f"HANZO_{name}", "")


def _save_bot_token(data: dict[str, Any]) -> None:
    """Save bot gateway token to disk."""
    BOT_TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    BOT_TOKEN_FILE.write_text(json.dumps(data, indent=2))
    BOT_TOKEN_FILE.chmod(0o600)


def _load_bot_token() -> dict[str, Any] | None:
    """Load stored bot gateway token."""
    if not BOT_TOKEN_FILE.exists():
        return None
    try:
        import time

        data = json.loads(BOT_TOKEN_FILE.read_text())
        # Check expiry
        exp = data.get("expires_at", 0)
        if exp and exp < time.time():
            return None
        return data
    except (json.JSONDecodeError, OSError):
        return None


class _BotOAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    """HTTP handler that captures the bot OAuth callback code."""

    code: str | None = None
    state: str | None = None
    error: str | None = None

    def do_GET(self) -> None:  # noqa: N802
        from urllib.parse import parse_qs, urlparse

        parsed = urlparse(self.path)
        if parsed.path != BOT_CALLBACK_PATH:
            self.send_response(404)
            self.end_headers()
            return

        qs = parse_qs(parsed.query)
        if "error" in qs:
            _BotOAuthCallbackHandler.error = qs["error"][0]
            self._respond("Login failed. You can close this window.", success=False)
            return

        _BotOAuthCallbackHandler.code = qs.get("code", [None])[0]
        _BotOAuthCallbackHandler.state = qs.get("state", [None])[0]
        self._respond("Bot login successful! You can close this window.")

    def _respond(self, message: str, success: bool = True) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        accent = "#6C5CE7" if success else "#e74c3c"
        body = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hanzo Bot</title>
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{
    font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
    background:#0a0a0a;color:#fafafa;
    display:flex;align-items:center;justify-content:center;
    min-height:100vh;
  }}
  .card{{
    text-align:center;max-width:420px;padding:48px 32px;
    background:#111;border:1px solid #222;border-radius:16px;
  }}
  .logo{{font-size:28px;font-weight:700;letter-spacing:-.5px;margin-bottom:32px;color:#fff}}
  .logo span{{color:{accent}}}
  .icon{{font-size:48px;margin-bottom:20px}}
  h2{{font-size:20px;font-weight:600;margin-bottom:8px;color:#fff}}
  .sub{{color:#888;font-size:14px;line-height:1.5;margin-bottom:28px}}
  .tagline{{
    font-size:13px;color:#555;border-top:1px solid #222;
    padding-top:20px;margin-top:8px;
  }}
</style>
</head>
<body>
<div class="card">
  <div class="logo"><span>&#x25B2;</span> hanzo bot</div>
  <div class="icon">{"&#x2705;" if success else "&#x274C;"}</div>
  <h2>{message}</h2>
  <p class="sub">You can close this window and return to your terminal.</p>
  <p class="tagline">Build something you love.</p>
</div>
</body>
</html>"""
        self.wfile.write(body.encode())

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress default request logging."""


def _bot_browser_login() -> str:
    """Run browser OAuth login flow for the bot gateway.

    Opens the user's browser to the IAM login page (hanzobot application),
    starts a local HTTP server to receive the callback, exchanges the code
    for tokens scoped to hanzobot-client-id.

    Returns:
        Access token string.
    """
    import secrets
    import time
    import webbrowser

    from hanzo_iam import IAMClient, IAMConfig

    config = IAMConfig(
        server_url=BOT_IAM_SERVER_URL,
        client_id=BOT_IAM_CLIENT_ID,
        client_secret="",
        organization=BOT_IAM_ORG,
        application=BOT_IAM_APP,
    )
    client = IAMClient(config=config)

    redirect_uri = f"http://localhost:{BOT_CALLBACK_PORT}{BOT_CALLBACK_PATH}"
    state = secrets.token_urlsafe(32)

    auth_url = client.get_authorization_url(
        redirect_uri=redirect_uri,
        state=state,
        scope="openid profile email",
    )

    # Reset handler state
    _BotOAuthCallbackHandler.code = None
    _BotOAuthCallbackHandler.state = None
    _BotOAuthCallbackHandler.error = None

    server = http.server.HTTPServer(
        ("127.0.0.1", BOT_CALLBACK_PORT), _BotOAuthCallbackHandler
    )
    server.timeout = 120

    console.print(f"[cyan]Opening browser to login at {BOT_IAM_SERVER_URL}...[/cyan]")
    webbrowser.open(auth_url)
    console.print(
        f"Waiting for callback on http://localhost:{BOT_CALLBACK_PORT}{BOT_CALLBACK_PATH}"
    )

    while (
        _BotOAuthCallbackHandler.code is None
        and _BotOAuthCallbackHandler.error is None
    ):
        server.handle_request()

    server.server_close()

    if _BotOAuthCallbackHandler.error:
        console.print(f"[red]Login failed:[/red] {_BotOAuthCallbackHandler.error}")
        raise SystemExit(1)

    if _BotOAuthCallbackHandler.state != state:
        console.print("[red]State mismatch — possible CSRF attack.[/red]")
        raise SystemExit(1)

    code = _BotOAuthCallbackHandler.code
    if not code:
        console.print("[red]No authorization code received.[/red]")
        raise SystemExit(1)

    tokens = client.exchange_code(code=code, redirect_uri=redirect_uri)
    client.close()

    access_token = tokens.access_token
    if not access_token:
        console.print("[red]No access token in response.[/red]")
        raise SystemExit(1)

    _save_bot_token({
        "access_token": access_token,
        "refresh_token": tokens.refresh_token or "",
        "id_token": tokens.id_token or "",
        "expires_at": time.time() + (tokens.expires_in or 604800),
        "client_id": BOT_IAM_CLIENT_ID,
        "server_url": BOT_IAM_SERVER_URL,
        "organization": BOT_IAM_ORG,
        "application": BOT_IAM_APP,
        "login_time": int(time.time()),
    })

    console.print("[green]Bot login successful.[/green]")
    return access_token


def _bot_password_login(
    username: str | None = None, password: str | None = None
) -> str:
    """Login via password grant using the hanzobot client. Returns access_token."""
    import httpx
    import time

    if not username:
        username = click.prompt("Email")
    if not password:
        password = click.prompt("Password", hide_input=True)

    resp = httpx.post(
        f"{BOT_IAM_SERVER_URL}/api/login/oauth/access_token",
        data={
            "grant_type": "password",
            "client_id": BOT_IAM_CLIENT_ID,
            "username": username,
            "password": password,
            "scope": "openid profile email",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30.0,
    )
    data = resp.json()
    access_token = data.get("access_token", "")
    if not access_token:
        err = (
            data.get("error_description")
            or data.get("msg")
            or data.get("error", "unknown error")
        )
        console.print(f"[red]Login failed:[/red] {err}")
        raise SystemExit(1)

    _save_bot_token({
        "access_token": access_token,
        "refresh_token": data.get("refresh_token", ""),
        "expires_at": time.time() + data.get("expires_in", 604800),
        "client_id": BOT_IAM_CLIENT_ID,
        "username": username,
        "login_time": int(time.time()),
    })
    return access_token


def _get_iam_token() -> str:
    """Get an IAM access token for the bot gateway.

    Credential chain:
    1. BOT_GATEWAY_TOKEN env var
    2. Stored bot token (~/.hanzo/bot/token.json)
    3. IAM_CLIENT_ID + IAM_CLIENT_SECRET client credentials
    4. Interactive login prompt
    """
    # Check env var first
    token = _env("BOT_GATEWAY_TOKEN").strip()
    if token:
        return token

    # Try stored bot-specific token (issued by hanzobot-client-id)
    bot_data = _load_bot_token()
    if bot_data and bot_data.get("access_token"):
        return bot_data["access_token"]

    # Try client credentials grant
    client_id = _env("IAM_CLIENT_ID")
    client_secret = _env("IAM_CLIENT_SECRET")
    if client_id and client_secret:
        try:
            import httpx

            resp = httpx.post(
                f"{BOT_IAM_SERVER_URL}/api/login/oauth/access_token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "scope": "openid profile email",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30.0,
            )
            data = resp.json()
            if data.get("access_token"):
                return data["access_token"]
        except Exception:
            pass

    # Interactive login — browser OAuth flow
    console.print("[cyan]Login required for bot gateway.[/cyan]")
    return _bot_browser_login()


def _read_pid() -> int | None:
    """Read the daemon PID from the pid file."""
    if not BOT_PID_FILE.exists():
        return None
    try:
        pid = int(BOT_PID_FILE.read_text().strip())
        # Check if process is alive
        os.kill(pid, 0)
        return pid
    except (ValueError, OSError):
        BOT_PID_FILE.unlink(missing_ok=True)
        return None


def _write_pid(pid: int) -> None:
    """Write daemon PID to file."""
    BOT_PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    BOT_PID_FILE.write_text(str(pid))


# ── install ──────────────────────────────────────────────────────────


@bot.command("install")
def bot_install() -> None:
    """Install the @hanzo/bot agent locally.

    Downloads and installs the hanzo-bot CLI from npm.
    Requires Node.js (v22+) to be installed.
    """
    binary = _find_bot_binary()
    if binary:
        # Show current version
        try:
            result = subprocess.run(
                [binary, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            version = result.stdout.strip() if result.returncode == 0 else "unknown"
        except Exception:
            version = "unknown"
        console.print(f"[green]hanzo-bot already installed:[/green] {binary} ({version})")
        return

    if _install_bot():
        binary = _find_bot_binary()
        if binary:
            console.print(f"[green]Installed at:[/green] {binary}")
    else:
        raise SystemExit(1)


# ── login ─────────────────────────────────────────────────────────────


@bot.command("login")
@click.option(
    "--no-browser",
    is_flag=True,
    help="Use password login instead of browser OAuth.",
)
def bot_login_cmd(no_browser: bool) -> None:
    """Authenticate with the bot gateway.

    Opens your browser to log in via Hanzo IAM. The token is stored
    at ~/.hanzo/bot/token.json and used for subsequent bot commands.

    \b
    Examples:
        hanzo bot login                    Browser OAuth login
        hanzo bot login --no-browser       Password login
    """
    if no_browser:
        token = _bot_password_login()
    else:
        token = _bot_browser_login()

    # Decode and show who we logged in as
    try:
        import base64

        parts = token.split(".")
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=="))
        name = payload.get("name", "unknown")
        email = payload.get("email", "")
        console.print(f"[green]Logged in as:[/green] {name} ({email})")
    except Exception:
        console.print("[green]Login stored.[/green]")


@bot.command("logout")
def bot_logout_cmd() -> None:
    """Clear stored bot gateway credentials."""
    if BOT_TOKEN_FILE.exists():
        BOT_TOKEN_FILE.unlink()
        console.print("[green]Bot credentials cleared.[/green]")
    else:
        console.print("[yellow]No bot credentials stored.[/yellow]")


# ── run ──────────────────────────────────────────────────────────────


@bot.command("run")
@click.option(
    "--host",
    default=DEFAULT_GATEWAY_HOST,
    help=f"Gateway host (default: {DEFAULT_GATEWAY_HOST}).",
)
@click.option(
    "--port",
    default=DEFAULT_GATEWAY_PORT,
    type=int,
    help=f"Gateway port (default: {DEFAULT_GATEWAY_PORT}).",
)
@click.option("--no-tls", is_flag=True, help="Disable TLS.")
@click.option(
    "--display-name",
    default=None,
    help="Node display name (default: hostname).",
)
@click.option(
    "--daemon",
    "-d",
    is_flag=True,
    help="Run as background daemon.",
)
@click.option(
    "--token",
    default=None,
    help="IAM token (default: from hanzo login).",
)
def bot_run(
    host: str,
    port: int,
    no_tls: bool,
    display_name: str | None,
    daemon: bool,
    token: str | None,
) -> None:
    """Run a local bot agent node connected to the gateway.

    Starts a headless bot node on this machine that connects to
    the Hanzo gateway (gw.hanzo.bot by default). The node appears
    in the Playground dashboard at app.hanzo.bot.

    \b
    Examples:
        hanzo bot run                           Run in foreground
        hanzo bot run -d                        Run as daemon
        hanzo bot run --display-name "My Mac"   Custom display name
        hanzo bot run --host my-gateway.example.com  Custom gateway
    """
    # Check for existing daemon
    existing_pid = _read_pid()
    if existing_pid:
        console.print(
            f"[yellow]Bot node already running (PID {existing_pid}).[/yellow]"
        )
        console.print("Use 'hanzo bot stop' to stop it first.")
        raise SystemExit(1)

    # Find or install hanzo-bot
    binary = _ensure_bot_binary()

    # Resolve IAM token
    iam_token = token or _get_iam_token()

    # Build command
    cmd = [binary, "node", "run", "--host", host, "--port", str(port)]
    if not no_tls:
        cmd.append("--tls")
    if display_name:
        cmd.extend(["--display-name", display_name])
    else:
        import platform as platform_mod

        cmd.extend(["--display-name", platform_mod.node()])

    # Set up environment
    env = os.environ.copy()
    env["BOT_GATEWAY_TOKEN"] = iam_token

    if daemon:
        # Run as background daemon
        BOT_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        log_fd = open(BOT_LOG_FILE, "a")
        proc = subprocess.Popen(
            cmd,
            env=env,
            stdout=log_fd,
            stderr=log_fd,
            start_new_session=True,
        )
        _write_pid(proc.pid)
        console.print(f"[green]Bot node started (PID {proc.pid}).[/green]")
        console.print(f"  Gateway: {'wss' if not no_tls else 'ws'}://{host}:{port}")
        console.print(f"  Logs:    {BOT_LOG_FILE}")
        console.print(f"  PID:     {BOT_PID_FILE}")
        console.print()
        console.print("Stop with: [cyan]hanzo bot stop[/cyan]")
    else:
        # Run in foreground
        console.print(
            f"[cyan]Connecting to {'wss' if not no_tls else 'ws'}://{host}:{port}...[/cyan]"
        )
        try:
            proc = subprocess.Popen(cmd, env=env)
            proc.wait()
        except KeyboardInterrupt:
            console.print("\n[yellow]Shutting down...[/yellow]")
            proc.terminate()
            proc.wait(timeout=5)


# ── stop ─────────────────────────────────────────────────────────────


@bot.command("stop")
def bot_stop() -> None:
    """Stop the local bot node daemon."""
    pid = _read_pid()
    if not pid:
        console.print("[yellow]No bot node daemon running.[/yellow]")
        return

    try:
        os.kill(pid, signal.SIGTERM)
        console.print(f"[green]Stopped bot node (PID {pid}).[/green]")
    except ProcessLookupError:
        console.print("[yellow]Process already exited.[/yellow]")
    finally:
        BOT_PID_FILE.unlink(missing_ok=True)
