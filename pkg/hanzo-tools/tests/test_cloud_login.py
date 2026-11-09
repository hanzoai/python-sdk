"""HanzoCloud follows the login: the credential is resolved on each request, an identity or
an org can be named for one call, and a fresh machine needs nothing but the hanzo CLI."""

import asyncio

import httpx
import pytest
import hanzo_login as login
from hanzo_tools.core import NO_KEY, CloudError, HanzoCloud


def serve(c, seen):
    def handler(request):
        seen.append(request)
        return httpx.Response(200, json={"ok": 1})

    c._client = httpx.AsyncClient(base_url="https://api.hanzo.ai", transport=httpx.MockTransport(handler))
    return c


@pytest.fixture(autouse=True)
def nobody(monkeypatch, tmp_path):
    """No test reads this machine's key, config or CLI."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("HANZO_API_KEY", raising=False)
    monkeypatch.delenv("HANZO_KEY", raising=False)
    monkeypatch.setattr(login, "cli", lambda: tmp_path / "absent")
    login.forget()
    login.use(None)
    yield
    login.forget()
    login.use(None)


def test_a_pinned_key_is_sent_and_the_login_is_not_asked(monkeypatch):
    def asked(identity=None):
        raise AssertionError("the login was asked")

    monkeypatch.setattr(login, "credential", asked)
    seen = []
    c = serve(HanzoCloud(key="sk-pinned"), seen)
    assert asyncio.run(c.get("/v1/models")) == {"ok": 1}
    assert seen[0].headers["authorization"] == "Bearer sk-pinned"
    assert c.configured()


def test_an_empty_pinned_key_is_no_credential(monkeypatch):
    monkeypatch.setattr(login, "credential", lambda identity=None: login.Credential("login", "tok"))
    c = HanzoCloud(key="")
    assert not c.configured()


def test_the_credential_is_resolved_on_each_request_so_a_refreshed_login_is_followed(monkeypatch):
    tokens = iter(["jwt-one", "jwt-two"])
    monkeypatch.setattr(login, "credential", lambda identity=None: login.Credential("login", next(tokens)))
    seen = []
    c = serve(HanzoCloud(), seen)
    asyncio.run(c.get("/v1/a"))
    asyncio.run(c.get("/v1/b"))
    assert [r.headers["authorization"] for r in seen] == ["Bearer jwt-one", "Bearer jwt-two"]


def test_an_identity_for_one_call_asks_the_login_for_it(monkeypatch):
    asked = []

    def credential(identity=None):
        asked.append(identity)
        return login.Credential("login", f"jwt-{identity or 'active'}", identity)

    monkeypatch.setattr(login, "credential", credential)
    seen = []
    c = serve(HanzoCloud(key="sk-pinned"), seen)
    asyncio.run(c.call("GET", "/v1/a", identity="lux/ops"))
    asyncio.run(c.call("GET", "/v1/b"))
    assert asked == ["lux/ops"]
    assert [r.headers["authorization"] for r in seen] == ["Bearer jwt-lux/ops", "Bearer sk-pinned"]


def test_an_org_is_the_x_org_id_header(monkeypatch):
    monkeypatch.setattr(login, "credential", lambda identity=None: login.Credential("login", "jwt"))
    seen = []
    c = serve(HanzoCloud(), seen)
    asyncio.run(c.call("GET", "/v1/a", org="lux"))
    asyncio.run(c.call("GET", "/v1/b"))
    assert seen[0].headers["x-org-id"] == "lux" and "x-org-id" not in seen[1].headers


def test_an_org_that_could_split_a_header_is_refused_before_any_request(monkeypatch):
    monkeypatch.setattr(login, "credential", lambda identity=None: login.Credential("login", "jwt"))
    seen = []
    c = serve(HanzoCloud(), seen)
    with pytest.raises(CloudError):
        asyncio.run(c.call("GET", "/v1/a", org="x\r\nHost: evil"))
    assert seen == []


def test_an_identity_the_login_refuses_is_a_cloud_error_and_nothing_is_sent(monkeypatch):
    def refuse(identity=None):
        raise login.LoginError("no identity x/y")

    monkeypatch.setattr(login, "credential", refuse)
    seen = []
    c = serve(HanzoCloud(), seen)
    with pytest.raises(CloudError, match="no identity x/y"):
        asyncio.run(c.call("GET", "/v1/a", identity="x/y"))
    assert seen == [] and not c.configured()


def test_the_client_identifies_itself(monkeypatch):
    monkeypatch.setattr(login, "credential", lambda identity=None: login.Credential("login", "jwt"))
    seen = []
    asyncio.run(serve(HanzoCloud(), seen).get("/v1/a"))
    asyncio.run(serve(HanzoCloud(agent="hanzo-tools-api/9.9.9"), seen).get("/v1/a"))
    assert seen[0].headers["user-agent"].startswith("hanzo-tools/")
    assert seen[1].headers["user-agent"] == "hanzo-tools-api/9.9.9"


def test_a_fresh_machine_with_only_the_cli_calls_the_cloud_as_its_login(monkeypatch, tmp_path):
    assert list(tmp_path.iterdir()) == []
    stub = tmp_path / "hanzo"
    stub.write_text('#!/bin/sh\n[ "$*" = "auth token" ] && echo jwt-from-the-cli && exit 0\nexit 2\n')
    stub.chmod(0o755)
    monkeypatch.setattr(login, "cli", lambda: stub)
    seen = []
    c = serve(HanzoCloud(), seen)
    assert c.configured()
    assert asyncio.run(c.get("/v1/models")) == {"ok": 1}
    assert seen[0].headers["authorization"] == "Bearer jwt-from-the-cli"


def test_with_nothing_on_the_machine_the_client_is_not_configured():
    assert not HanzoCloud().configured()
    assert "hanzo auth login" in NO_KEY
