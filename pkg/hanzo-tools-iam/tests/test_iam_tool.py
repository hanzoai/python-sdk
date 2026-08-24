"""The IAM tool's addresses and readers, pinned.

IAM serves its CRUD under /v1/iam/. A collection is a plural noun and one row of
it is {collection}/{owner}/{name}. A collection GET answers a wrapper keyed by
the plural, so a reader that falls back to [] would report "no users" for a
healthy org — every case here asserts on the value.
"""

from __future__ import annotations

import json

import httpx
import pytest

from hanzo_tools.iam.iam_tool import ACTIONS, IAMTool, _iam_url, IAM_BASE_URL


def test_iam_url_uses_v1_iam_not_api():
    url = _iam_url("users")
    assert url == f"{IAM_BASE_URL}/v1/iam/users"
    assert "/api/" not in url


def test_iam_url_strips_leading_slash():
    assert _iam_url("/users") == f"{IAM_BASE_URL}/v1/iam/users"


def test_no_action_names_an_address_iam_does_not_serve():
    # enforce, get-system-info and healthz are 404 with no successor.
    for gone in ("enforce", "system_info", "health"):
        assert gone not in ACTIONS


def _serve(monkeypatch, handler):
    """Answer every IAM call with `handler`, holding a session token."""
    real_init = httpx.AsyncClient.__init__

    def init(self, *args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        real_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "__init__", init)

    class Session:
        @staticmethod
        def get_iam_token():
            return "jwt-value"

    monkeypatch.setattr("hanzo_tools.iam.iam_tool._get_session", lambda: Session())


def _recorder(body):
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["url"] = str(request.url)
        seen["auth"] = request.headers.get("authorization")
        seen["body"] = request.read().decode() or None
        return httpx.Response(200, json=body)

    return seen, handler


LIST_BODY = {
    "users": [{"name": "alice", "email": "a@hanzo.ai"}],
    "total": 1,
    "organizations": [{"name": "hanzo"}],
    "roles": [{"name": "admin", "users": ["hanzo/alice"]}],
    "permissions": [{"name": "p"}],
    "providers": [{"name": "google"}],
    "applications": [{"name": "app"}],
    "tokens": [{"name": "t"}],
    "sessions": [{"name": "s"}],
    "invitations": [{"name": "i"}],
    "auditLogs": [{"name": "r"}],
    "owner": "hanzo",
    "name": "alice",
    "deleted": True,
}


@pytest.mark.parametrize(
    "action,params,method,path",
    [
        ("users", {}, "GET", "/v1/iam/users"),
        ("users", {"owner": "hanzo"}, "GET", "/v1/iam/users?owner=hanzo"),
        ("user", {"id": "hanzo/alice"}, "GET", "/v1/iam/users/hanzo/alice"),
        ("delete_user", {"id": "hanzo/alice"}, "DELETE", "/v1/iam/users/hanzo/alice"),
        ("orgs", {}, "GET", "/v1/iam/organizations"),
        ("org", {"id": "admin/hanzo"}, "GET", "/v1/iam/organizations/admin/hanzo"),
        ("roles", {}, "GET", "/v1/iam/roles"),
        ("role", {"id": "hanzo/admin"}, "GET", "/v1/iam/roles/hanzo/admin"),
        ("permissions", {}, "GET", "/v1/iam/permissions"),
        ("providers", {}, "GET", "/v1/iam/providers"),
        ("apps", {"owner": "hanzo"}, "GET", "/v1/iam/applications?owner=hanzo"),
        ("tokens", {}, "GET", "/v1/iam/tokens"),
        ("sessions", {"owner": "hanzo"}, "GET", "/v1/iam/sessions?owner=hanzo"),
        ("invitations", {}, "GET", "/v1/iam/invitations"),
        ("records", {}, "GET", "/v1/iam/audit-logs"),
        (
            "create_user",
            {"owner": "hanzo", "name": "alice", "email": "a@hanzo.ai"},
            "POST",
            "/v1/iam/users",
        ),
        (
            "invite",
            {"email": "a@hanzo.ai", "org": "hanzo"},
            "POST",
            "/v1/iam/invitations",
        ),
    ],
)
async def test_each_action_addresses_the_canonical_route(
    monkeypatch, action, params, method, path
):
    seen, handler = _recorder(LIST_BODY)
    _serve(monkeypatch, handler)

    out = json.loads(await IAMTool().call(None, action=action, **params))
    assert "error" not in out, out
    assert seen["method"] == method
    assert seen["url"] == f"{IAM_BASE_URL}{path}"
    assert seen["auth"] == "Bearer jwt-value"


async def test_a_list_reads_the_key_the_server_names(monkeypatch):
    _, handler = _recorder(LIST_BODY)
    _serve(monkeypatch, handler)

    out = json.loads(await IAMTool().call(None, action="users", owner="hanzo"))
    assert out["count"] == 1
    assert out["total"] == 1
    assert out["users"][0]["name"] == "alice"


async def test_a_bare_array_is_an_error_not_an_empty_page(monkeypatch):
    _, handler = _recorder([{"name": "alice"}])
    _serve(monkeypatch, handler)

    out = json.loads(await IAMTool().call(None, action="users"))
    assert "no users list" in out["error"]


async def test_update_reads_the_row_then_replaces_it(monkeypatch):
    calls: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append((request.method, request.url.path))
        return httpx.Response(200, json={"owner": "hanzo", "name": "alice"})

    _serve(monkeypatch, handler)
    await IAMTool().call(None, action="update_user", id="hanzo/alice", email="b@hanzo.ai")
    assert calls == [
        ("GET", "/v1/iam/users/hanzo/alice"),
        ("PUT", "/v1/iam/users/hanzo/alice"),
    ]


async def test_the_password_rides_the_create_call_beside_the_row(monkeypatch):
    seen, handler = _recorder({"owner": "hanzo", "name": "alice"})
    _serve(monkeypatch, handler)

    await IAMTool().call(
        None,
        action="create_user",
        owner="hanzo",
        name="alice",
        email="a@hanzo.ai",
        password="secret-pw",
    )
    body = json.loads(seen["body"])
    assert body["password"] == "secret-pw"
    assert "password" not in body["user"]


async def test_absence_is_reported_as_a_404(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"title": "not found"})

    _serve(monkeypatch, handler)
    out = json.loads(await IAMTool().call(None, action="user", id="hanzo/nobody"))
    assert "404" in out["error"]


async def test_a_route_that_needs_an_owner_asks_for_one(monkeypatch):
    _, handler = _recorder(LIST_BODY)
    _serve(monkeypatch, handler)

    for action in ("apps", "sessions"):
        out = json.loads(await IAMTool().call(None, action=action))
        assert "owner" in out["error"]
