"""The `hanzo` router acts as whoever the login says, and says so without saying the secret.

The CLI is a stub shell script standing in for ~/.local/bin/hanzo, HOME is an empty
directory, and HTTP is an httpx MockTransport: no test reads this machine's login or
opens a socket.
"""

import base64
import json
import shlex
import stat
import time
from pathlib import Path
from unittest.mock import AsyncMock

import hanzo_login as login
import httpx
import pytest
from mcp.server import FastMCP

from hanzo_tools.api import spec as openapi
from hanzo_tools.api.hanzo_tool import HanzoTool

SPEC = {"paths": {"/v1/kb/search": {"post": {"tags": ["kb"]}}, "/v1/billing/plans": {"get": {"tags": ["billing"]}}}}


class Everything:
    def __contains__(self, _):
        return True


def jwt(claims: dict) -> str:
    def part(obj: dict) -> str:
        return base64.urlsafe_b64encode(json.dumps(obj).encode()).decode().rstrip("=")

    return f"{part({'alg': 'none'})}.{part(claims)}.sig"


LOGIN = jwt(
    {
        "owner": "hanzo",
        "name": "z",
        "displayName": "Zach",
        "email": "z@hanzo.ai",
        "orgs": [{"org": "hanzo", "role": "admin"}],
        "exp": int(time.time()) + 3600,
    }
)
OPS = jwt({"owner": "lux", "name": "ops", "email": "ops@lux.network", "exp": int(time.time()) + 3600})
ROWS = json.dumps(
    [
        {"key": "hanzo/z", "owner": "hanzo", "subject": "z@hanzo.ai", "expiry": 1893456000, "active": True},
        {"key": "lux/ops", "owner": "lux", "subject": "ops@lux.network", "active": False},
    ]
)


class Machine:
    def __init__(self, root: Path, monkeypatch: pytest.MonkeyPatch):
        self.home = root / "home"
        self.home.mkdir()
        self.log = root / "argv.log"
        self.exe = root / "hanzo"
        self.monkeypatch = monkeypatch

    def hanzo(self, answers: dict[str, tuple[int, str, str]]) -> None:
        cases = "".join(
            f"  {shlex.quote(a)}) printf '%s' {shlex.quote(o)}; printf '%s' {shlex.quote(e)} >&2; exit {c};;\n"
            for a, (c, o, e) in answers.items()
        )
        self.exe.write_text(
            f'#!/bin/sh\necho "$*" >> {shlex.quote(str(self.log))}\n'
            f'case "$*" in\n{cases}  *) echo "unknown: $*" >&2; exit 2;;\nesac\n'
        )
        self.exe.chmod(self.exe.stat().st_mode | stat.S_IXUSR)
        self.monkeypatch.setattr(login, "cli", lambda: self.exe)

    def config(self, key: str) -> None:
        (self.home / ".hanzo").mkdir(exist_ok=True)
        (self.home / ".hanzo" / "config.json").write_text(json.dumps({"apiKey": key}))

    def runs(self) -> list[str]:
        return self.log.read_text().splitlines() if self.log.exists() else []


@pytest.fixture
def machine(tmp_path, monkeypatch):
    m = Machine(tmp_path, monkeypatch)
    monkeypatch.setenv("HOME", str(m.home))
    monkeypatch.delenv("HANZO_API_KEY", raising=False)
    monkeypatch.delenv("HANZO_KEY", raising=False)
    monkeypatch.setattr(login, "cli", lambda: tmp_path / "absent")
    login.forget()
    login.use(None)
    yield m
    login.forget()
    login.use(None)


def router(seen=None):
    """The tool with a stub catalog and a cloud that answers from memory."""
    tool = HanzoTool()
    tool._catalog = openapi.Catalog(SPEC, allow=Everything())
    tool._source = "test"

    def handler(request):
        if seen is not None:
            seen.append(request)
        return httpx.Response(200, json={"ok": 1})

    tool._get_cloud()._client = httpx.AsyncClient(
        base_url="https://api.hanzo.ai", transport=httpx.MockTransport(handler)
    )
    return tool


async def ask(tool, **kw):
    return json.loads(await tool.call(AsyncMock(), **kw))


# -- the order, seen through whoami -------------------------------------------


@pytest.mark.asyncio
async def test_whoami_env_beats_login_beats_stored(machine, monkeypatch):
    machine.hanzo({"auth token": (0, LOGIN + "\n", ""), "auth list -o json": (0, ROWS, "")})
    machine.config("sk-stale-key-for-another-account")
    tool = router()

    out = await ask(tool, service="auth", action="whoami")
    assert out["source"] == "login" and out["identity"] == "hanzo/z"

    monkeypatch.setenv("HANZO_API_KEY", "sk-explicit-key")
    out = await ask(tool, service="auth", action="whoami")
    assert out == {"source": "env", "using": None, "key": "sk-…"}


@pytest.mark.asyncio
async def test_whoami_a_failed_login_falls_through_to_stored_and_says_why(machine):
    machine.hanzo({"auth token": (1, "", "not signed in: run `hanzo auth login`\n")})
    machine.config("pk-legacy")
    out = await ask(router(), service="auth", action="whoami")
    assert out == {"source": "stored", "using": None, "key": "pk-…", "login": "not signed in: run `hanzo auth login`"}


@pytest.mark.asyncio
async def test_whoami_names_the_person_the_org_and_the_orgs_from_the_claims(machine):
    machine.hanzo({"auth token": (0, LOGIN + "\n", ""), "auth list -o json": (0, ROWS, "")})
    out = await ask(router(), service="auth", action="whoami")
    assert out == {
        "source": "login",
        "using": None,
        "identity": "hanzo/z",
        "email": "z@hanzo.ai",
        "name": "Zach",
        "org": "hanzo",
        "orgs": [{"org": "hanzo", "role": "admin"}],
    }


@pytest.mark.asyncio
async def test_whoami_takes_the_identity_from_the_claims_when_the_cli_lists_none(machine):
    machine.hanzo({"auth token": (0, LOGIN + "\n", "")})
    assert (await ask(router(), service="auth", action="whoami"))["identity"] == "hanzo/z"


@pytest.mark.asyncio
async def test_whoami_never_carries_a_token_or_a_key(machine, monkeypatch):
    machine.hanzo(
        {
            "auth token": (0, LOGIN + "\n", ""),
            "auth token --as lux/ops": (0, OPS + "\n", ""),
            "auth list -o json": (0, ROWS, ""),
        }
    )
    tool = router()
    seen = [await tool.call(AsyncMock(), service="auth", action="whoami")]
    seen.append(await tool.call(AsyncMock(), service="auth", action="whoami", **{"as": "lux/ops"}))
    monkeypatch.setenv("HANZO_API_KEY", "sk-0123456789abcdef")
    seen.append(await tool.call(AsyncMock(), service="auth", action="whoami"))
    seen.append(await tool.call(AsyncMock(), service="auth", action="list"))
    blob = "".join(seen)
    for secret in (LOGIN, OPS, LOGIN.split(".")[1], OPS.split(".")[1], "0123456789abcdef", "sk-0123"):
        assert secret not in blob


# -- naming an identity -------------------------------------------------------


@pytest.mark.asyncio
async def test_as_asks_the_login_for_that_identity_even_when_a_key_is_set(machine, monkeypatch):
    machine.hanzo({"auth token --as lux/ops": (0, OPS + "\n", "")})
    monkeypatch.setenv("HANZO_API_KEY", "sk-explicit-key")
    seen = []
    out = await ask(router(seen), service="billing", action="plans", **{"as": "lux/ops"})
    assert out["data"] == {"ok": 1}
    assert machine.runs() == ["auth token --as lux/ops"]
    assert seen[0].headers["authorization"] == f"Bearer {OPS}"


@pytest.mark.asyncio
async def test_with_a_key_and_no_identity_the_key_wins_and_the_login_is_not_asked(machine, monkeypatch):
    machine.hanzo({"auth token": (0, LOGIN + "\n", "")})
    monkeypatch.setenv("HANZO_API_KEY", "sk-explicit-key")
    seen = []
    await ask(router(seen), service="billing", action="plans")
    assert seen[0].headers["authorization"] == "Bearer sk-explicit-key"
    assert machine.runs() == []


@pytest.mark.asyncio
async def test_as_beats_use_for_one_call(machine):
    machine.hanzo({"auth token --as lux/ops": (0, OPS + "\n", ""), "auth token --as hanzo/z": (0, LOGIN + "\n", "")})
    tool = router(seen := [])
    await ask(tool, service="auth", action="use", params={"identity": "hanzo/z"})
    await ask(tool, service="billing", action="plans")
    await ask(tool, service="billing", action="plans", **{"as": "lux/ops"})
    assert [r.headers["authorization"] for r in seen] == [f"Bearer {LOGIN}", f"Bearer {OPS}"]


@pytest.mark.asyncio
@pytest.mark.parametrize("bad", ["--help", "a b", "../x"])
async def test_an_identity_that_could_be_argv_is_refused_everywhere_before_argv(machine, bad):
    machine.hanzo({})
    tool = router(sent := [])
    for kw in (
        dict(service="billing", action="plans", **{"as": bad}),
        dict(service="auth", action="whoami", **{"as": bad}),
        dict(service="auth", action="use", params={"identity": bad}),
        dict(service="auth", action="switch", params={"identity": bad}),
    ):
        out = await ask(tool, **kw)
        assert "error" in out and "identity is owner or owner/name" in out["error"]
    assert machine.runs() == [] and sent == []


@pytest.mark.asyncio
async def test_an_identity_the_login_does_not_hold_sends_nothing(machine):
    machine.hanzo({"auth token --as x/y": (1, "", "no identity x/y\n")})
    out = await ask(router(sent := []), service="billing", action="plans", **{"as": "x/y"})
    assert "no identity x/y" in out["error"] and sent == []


# -- org ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_org_is_the_header_and_not_part_of_the_operations_input(machine, monkeypatch):
    monkeypatch.setenv("HANZO_API_KEY", "sk-explicit-key")
    seen = []
    tool = router(seen)
    await ask(tool, service="kb", action="search", params={"query": "oauth"}, org="lux")
    assert seen[0].headers["x-org-id"] == "lux"
    assert json.loads(seen[0].content) == {"query": "oauth"}


@pytest.mark.asyncio
async def test_an_operations_own_org_stays_inside_params(machine, monkeypatch):
    monkeypatch.setenv("HANZO_API_KEY", "sk-explicit-key")
    seen = []
    await ask(router(seen), service="kb", action="search", params={"query": "q", "org": "zoo"})
    assert "x-org-id" not in seen[0].headers
    assert json.loads(seen[0].content) == {"query": "q", "org": "zoo"}


@pytest.mark.asyncio
async def test_an_org_that_could_split_a_header_is_refused(machine, monkeypatch):
    monkeypatch.setenv("HANZO_API_KEY", "sk-explicit-key")
    out = await ask(router(sent := []), service="billing", action="plans", org="x\r\nHost: evil")
    assert "error" in out and sent == []


# -- list, use, switch --------------------------------------------------------


@pytest.mark.asyncio
async def test_list_is_the_clis_identities_with_the_active_one_marked(machine):
    machine.hanzo({"auth list -o json": (0, ROWS, "")})
    out = await ask(router(), service="auth", action="list")
    assert out["active"] == "hanzo/z" and out["using"] is None
    assert [(r["key"], r["active"]) for r in out["identities"]] == [("hanzo/z", True), ("lux/ops", False)]


@pytest.mark.asyncio
async def test_use_is_this_process_only_and_switch_is_global(machine):
    machine.hanzo({"auth token --as lux/ops": (0, OPS + "\n", ""), "auth switch lux/ops": (0, "", "")})
    tool = router()

    used = await ask(tool, service="auth", action="use", params={"identity": "lux/ops"})
    assert used["using"] == "lux/ops" and used["scope"] == "process"
    assert "this process only" in used["message"].lower() and "GLOBAL" not in used["message"]
    assert machine.runs() == ["auth token --as lux/ops"]  # verified with the login first, switch not run

    switched = await ask(tool, service="auth", action="switch", params={"identity": "lux/ops"})
    assert switched["active"] == "lux/ops" and switched["scope"] == "machine"
    assert switched["message"].startswith("GLOBAL: every Hanzo tool and session on this machine now acts as lux/ops")
    assert machine.runs()[-1] == "auth switch lux/ops"


@pytest.mark.asyncio
async def test_use_without_an_identity_clears_the_choice(machine):
    machine.hanzo({"auth token --as lux/ops": (0, OPS + "\n", ""), "auth token": (0, LOGIN + "\n", "")})
    tool = router()
    await ask(tool, service="auth", action="use", params={"identity": "lux/ops"})
    assert login.using() == "lux/ops"
    out = await ask(tool, service="auth", action="use")
    assert out["using"] is None and login.using() is None
    assert (await ask(tool, service="auth", action="whoami"))["using"] is None


@pytest.mark.asyncio
async def test_use_of_an_identity_the_login_does_not_hold_changes_nothing(machine):
    machine.hanzo({"auth token --as x/y": (1, "", "no identity x/y\n")})
    out = await ask(router(), service="auth", action="use", params={"identity": "x/y"})
    assert "no identity x/y" in out["error"] and login.using() is None


@pytest.mark.asyncio
async def test_an_unknown_auth_action_names_the_four(machine):
    out = await ask(router(), service="auth", action="login")
    assert "whoami, list, use or switch" in out["error"] and "hint" not in out


@pytest.mark.asyncio
async def test_auth_needs_neither_the_catalog_nor_a_network(machine):
    machine.hanzo({"auth list -o json": (0, ROWS, "")})
    tool = HanzoTool()
    await ask(tool, service="auth", action="list")
    assert tool._catalog is None


# -- the door -----------------------------------------------------------------


@pytest.mark.asyncio
async def test_the_mcp_door_takes_as_and_org_and_hides_the_context(machine):
    machine.hanzo({"auth token --as lux/ops": (0, OPS + "\n", "")})
    tool = router(seen := [])
    server = FastMCP("t")
    tool.register(server)
    schema = (await server.list_tools())[0].inputSchema
    assert set(schema["properties"]) == {"service", "action", "params", "method", "as", "org"}
    await server.call_tool(
        "hanzo", {"service": "kb", "action": "search", "params": '{"query": "q"}', "as": "lux/ops", "org": "lux"}
    )
    assert seen[0].headers["authorization"] == f"Bearer {OPS}" and seen[0].headers["x-org-id"] == "lux"
    assert json.loads(seen[0].content) == {"query": "q"}


# -- a fresh machine ----------------------------------------------------------


@pytest.mark.asyncio
async def test_a_fresh_machine_with_only_the_cli_acts_as_its_login_and_identifies_itself(machine):
    assert list(machine.home.iterdir()) == []
    machine.hanzo({"auth token": (0, LOGIN + "\n", ""), "auth list -o json": (0, ROWS, "")})
    seen = []
    tool = router(seen)
    out = await ask(tool, service="billing", action="plans")
    assert out["data"] == {"ok": 1}
    assert seen[0].headers["authorization"] == f"Bearer {LOGIN}"
    assert seen[0].headers["user-agent"].startswith("hanzo-tools-api/")
    assert (await ask(tool, service="auth", action="whoami"))["identity"] == "hanzo/z"
    assert list(machine.home.iterdir()) == []
