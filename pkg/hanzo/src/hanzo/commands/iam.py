"""Hanzo IAM — identity, from the command line.

Every entity IAM serves has the same five routes, so this file has one
implementation of them and a table of the entities it applies to:

    GET    /v1/iam/<entity>                  list, scoped by owner
    POST   /v1/iam/<entity>                  create
    GET    /v1/iam/<entity>/<owner>/<name>   read one
    PUT    /v1/iam/<entity>/<owner>/<name>   replace one
    DELETE /v1/iam/<entity>/<owner>/<name>   delete one

A row is named by owner and name, so every one of them needs --org. A list
answers a wrapper keyed by the plural — {"users": [...], "total": N} — and the
key is not always the word in the path, which is what the table carries.

The credential goes in Authorization, which is the only place IAM reads one.
"""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path

import click
import httpx
from rich.table import Table

from ..utils.output import console

AUTH = Path.home() / ".hanzo" / "auth.json"

# Entity, and the key its list arrives under. Everything else about the five
# routes is the same for every row, which is why there is a table here and not
# fourteen command trees.
ENTITIES: dict[str, str] = {
    "applications": "applications",
    "audit-logs": "auditLogs",
    "certs": "certs",
    "invitations": "invitations",
    "keys": "keys",
    "organizations": "organizations",
    "permissions": "permissions",
    "projects": "projects",
    "providers": "providers",
    "roles": "roles",
    "tokens": "tokens",
    "users": "users",
    "webauthn-credentials": "webauthnCredentials",
    "workspaces": "workspaces",
}

# webauthn-credentials scopes by the user it belongs to; every other entity
# scopes by owner.
SCOPE = {"webauthn-credentials": "user"}

# The columns worth showing for a row of each entity, in order. A row that has
# none of them prints as JSON.
COLUMNS = ("owner", "name", "displayName", "email", "type", "createdTime")


def stored() -> dict:
    try:
        return json.loads(AUTH.read_text())
    except Exception:
        return {}


def endpoint() -> str:
    return (os.getenv("IAM_URL") or stored().get("iam_url") or "https://hanzo.id").rstrip("/")


def credential() -> str:
    """The credential this CLI presents, as an Authorization value.

    A bearer if one is exported, otherwise the confidential client's own pair as
    HTTP Basic (RFC 6749 2.3.1).
    """
    token = os.getenv("IAM_TOKEN") or os.getenv("HANZO_API_KEY")
    if token:
        return token if token.startswith("Bearer ") else f"Bearer {token}"

    saved = stored()
    ident = os.getenv("IAM_CLIENT_ID") or saved.get("iam_client_id", "")
    secret = os.getenv("IAM_CLIENT_SECRET") or saved.get("iam_client_secret", "")
    if not ident or not secret:
        console.print("[red]no IAM credential.[/red] Run: hanzo iam configure")
        raise SystemExit(1)
    return "Basic " + base64.b64encode(f"{ident}:{secret}".encode()).decode()


def call(method: str, path: str, *, params: dict | None = None, body: dict | None = None) -> dict:
    """One request to IAM. Refusals arrive as the server wrote them."""
    try:
        with httpx.Client(timeout=30.0) as http:
            response = http.request(
                method,
                endpoint() + path,
                params=params or None,
                json=body,
                headers={"Authorization": credential()},
            )
    except httpx.ConnectError:
        console.print(f"[red]cannot reach IAM at {endpoint()}[/red]")
        raise SystemExit(1)

    if response.status_code >= 400:
        detail = response.text.strip()
        try:
            payload = response.json()
            # A refusal is an RFC 9457 problem document; absence is a 404.
            detail = (
                payload.get("detail")
                or payload.get("title")
                or payload.get("error")
                or payload.get("message")
                or detail
            )
        except Exception:
            pass
        console.print(f"[red]HTTP {response.status_code}[/red] {detail}")
        raise SystemExit(1)

    return response.json() if response.content else {}


def rows(payload: dict, entity: str) -> list[dict]:
    """The records in a list reply, under the key the entity declares.

    A key that is absent is an error, not an empty page: reading it as [] would
    report "no users" for a healthy org.
    """
    key = ENTITIES[entity]
    if not isinstance(payload, dict) or key not in payload:
        console.print(f"[red]no {key} in the reply[/red]")
        raise SystemExit(1)
    return payload[key] or []


def show(records: list[dict], entity: str) -> None:
    if not records:
        console.print(f"no {entity}")
        return

    present = [c for c in COLUMNS if any(r.get(c) for r in records)]
    if not present:
        console.print_json(json.dumps(records))
        return

    table = Table(title=f"{entity} ({len(records)})")
    for column in present:
        table.add_column(column)
    for record in records:
        table.add_row(*(str(record.get(c, "") or "") for c in present))
    console.print(table)


def fields(pairs: tuple[str, ...]) -> dict:
    """--set key=value, repeated. A value that parses as JSON arrives typed."""
    out: dict = {}
    for pair in pairs:
        key, _, value = pair.partition("=")
        try:
            out[key] = json.loads(value)
        except json.JSONDecodeError:
            out[key] = value
    return out


@click.group(name="iam")
def iam_group():
    """Hanzo IAM — identity and access.

    \b
      hanzo iam configure                        store the credential
      hanzo iam status                           who the credential is
      hanzo iam users list --org hanzo           any entity, five verbs
      hanzo iam users get z --org hanzo
      hanzo iam users create --org hanzo --set name=z --set email=z@hanzo.ai \\
                             --set password=...              IAM hashes it
      hanzo iam users update z --org hanzo --set displayName=Z
      hanzo iam users delete z --org hanzo
      hanzo iam password z --org hanzo           set a password
      hanzo iam call GET /v1/iam/roles --param owner=hanzo

    \b
    Entities: applications, audit-logs, certs, invitations, keys,
    organizations, permissions, projects, providers, roles, tokens, users,
    webauthn-credentials, workspaces.
    """


@iam_group.command()
@click.option("--url", "-u", help="IAM endpoint; default https://hanzo.id")
@click.option("--client-id", "-i", help="OAuth2 client id")
@click.option("--client-secret", "-s", help="OAuth2 client secret")
def configure(url: str, client_id: str, client_secret: str):
    """Store the IAM credential in ~/.hanzo/auth.json, readable only by you."""
    from rich.prompt import Prompt

    saved = stored()
    url = url or Prompt.ask("IAM URL", default=saved.get("iam_url", "https://hanzo.id"))
    client_id = client_id or Prompt.ask("Client ID", default=saved.get("iam_client_id", ""))
    client_secret = client_secret or Prompt.ask("Client Secret", password=True)

    saved.update(iam_url=url, iam_client_id=client_id, iam_client_secret=client_secret)
    AUTH.parent.mkdir(parents=True, exist_ok=True)
    AUTH.write_text(json.dumps(saved, indent=2))
    AUTH.chmod(0o600)

    console.print(f"[green]saved[/green] {AUTH} (0600)")


@iam_group.command()
def status():
    """Ask IAM who this credential is."""
    who = call("GET", "/v1/iam/oauth/userinfo")
    console.print(f"[green]{endpoint()}[/green]")
    for key in ("sub", "name", "email", "preferred_username", "owner", "iss"):
        if who.get(key):
            console.print(f"  {key:20} {who[key]}")


@iam_group.command(name="password")
@click.argument("username")
@click.option("--org", "-o", required=True, help="Organization")
@click.option("--password", "-p", prompt=True, hide_input=True, help="New password")
@click.option("--old-password", default="", help="The credential being replaced")
def set_password(username: str, org: str, password: str, old_password: str):
    """Set a user's password. IAM hashes it; the CLI never stores it."""
    call(
        "PUT",
        "/v1/iam/password",
        body={
            "organization": org,
            "username": username,
            "oldPassword": old_password,
            "password": password,
        },
    )
    console.print(f"[green]password set[/green] for {org}/{username}")


@iam_group.command(name="call")
@click.argument("method")
@click.argument("path")
@click.option("--param", "-p", multiple=True, help="query key=value; repeatable")
@click.option("--set", "-d", "body", multiple=True, help="body key=value; repeatable")
def raw(method: str, path: str, param: tuple[str, ...], body: tuple[str, ...]):
    """Call any IAM route directly, with this CLI's credential."""
    payload = fields(body) if body else None
    console.print_json(json.dumps(call(method.upper(), path, params=fields(param), body=payload)))


def wrap(entity: str, record: dict) -> dict:
    """The write body an entity takes.

    users nests its record so the create and update inputs can carry a password
    beside it — IAM hashes that, and it is never a field on the row itself.
    Every other entity writes the record flat.
    """
    if entity != "users":
        return record
    record = dict(record)
    password = record.pop("password", None)
    body = {"user": record}
    if password is not None:
        body["password"] = password
    return body


def register(entity: str) -> None:
    """Give one entity its five commands. Called once per row of ENTITIES."""

    @iam_group.group(name=entity)
    def group():
        f"""{entity}"""

    @group.command(name="list")
    @click.option("--org", "-o", default="", help="Scope to one organization")
    @click.option("--limit", type=int, default=0)
    @click.option("--offset", type=int, default=0)
    def _list(org: str, limit: int, offset: int):
        scope = {SCOPE.get(entity, "owner"): org} if org else {}
        if limit:
            scope["limit"] = limit
        if offset:
            scope["offset"] = offset
        show(rows(call("GET", f"/v1/iam/{entity}", params=scope), entity), entity)

    @group.command(name="get")
    @click.argument("name")
    @click.option("--org", "-o", required=True, help="Organization")
    def _get(name: str, org: str):
        console.print_json(json.dumps(call("GET", f"/v1/iam/{entity}/{org}/{name}")))

    @group.command(name="create")
    @click.option("--org", "-o", default="", help="Organization the record belongs to")
    @click.option("--set", "-d", "values", multiple=True, help="key=value; repeatable")
    @click.option("--file", "-f", type=click.File("r"), help="the record, as JSON")
    def _create(org: str, values: tuple[str, ...], file):
        record = json.load(file) if file else fields(values)
        if org:
            record.setdefault("owner", org)
        console.print_json(json.dumps(call("POST", f"/v1/iam/{entity}", body=wrap(entity, record))))

    @group.command(name="update")
    @click.argument("name")
    @click.option("--org", "-o", required=True, help="Organization")
    @click.option("--set", "-d", "values", multiple=True, help="key=value; repeatable")
    def _update(name: str, org: str, values: tuple[str, ...]):
        # PUT replaces the row, so start from the stored one and change what was
        # asked for. Sending only the changed fields would blank the rest.
        address = f"/v1/iam/{entity}/{org}/{name}"
        record = {**call("GET", address), **fields(values)}
        console.print_json(json.dumps(call("PUT", address, body=wrap(entity, record))))

    @group.command(name="delete")
    @click.argument("name")
    @click.option("--org", "-o", required=True, help="Organization")
    def _delete(name: str, org: str):
        call("DELETE", f"/v1/iam/{entity}/{org}/{name}")
        console.print(f"[green]deleted[/green] {org}/{name}")


for _entity in ENTITIES:
    register(_entity)
