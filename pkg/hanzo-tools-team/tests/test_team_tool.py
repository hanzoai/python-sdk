"""The team tool's addresses and readers, pinned.

Tenancy lives in IAM under /v1/iam/. A workspace is named by owner and name, so
one row is workspaces/{owner}/{name}. Workspaces answer the wrapper shape;
memberships and account answer the {status, msg, data} envelope. Reading one
shape with the other reader is the failure worth catching, so every case asserts
on the value.
"""

from __future__ import annotations

import json

import httpx
import pytest

from hanzo_tools.team.team_tool import ACTIONS, TeamTool, _iam_url, IAM_BASE_URL


def test_addresses_live_under_v1_iam():
    assert _iam_url("workspaces") == f"{IAM_BASE_URL}/v1/iam/workspaces"
    assert _iam_url("/account") == f"{IAM_BASE_URL}/v1/iam/account"


def test_the_tool_names_no_surface_iam_lacks():
    # IAM has no groups surface, so no action may reach for one.
    assert "groups" not in ACTIONS


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

    monkeypatch.setattr("hanzo_tools.team.team_tool._get_session", lambda: Session())


BODY = {
    "workspaces": [{"owner": "hanzo", "name": "research"}],
    "total": 1,
    "status": "ok",
    "msg": "",
    "data": [{"user": "hanzo/alice", "org": "hanzo", "role": "admin"}],
    "owner": "hanzo",
    "name": "research",
    "deleted": True,
}


def _recorder(body=BODY):
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["url"] = str(request.url)
        seen["auth"] = request.headers.get("authorization")
        seen["body"] = request.read().decode() or None
        return httpx.Response(200, json=body)

    return seen, handler


@pytest.mark.parametrize(
    "action,params,method,path",
    [
        ("workspaces", {}, "GET", "/v1/iam/workspaces"),
        ("workspaces", {"owner": "hanzo"}, "GET", "/v1/iam/workspaces?owner=hanzo"),
        ("workspace", {"id": "hanzo/research"}, "GET", "/v1/iam/workspaces/hanzo/research"),
        (
            "create_workspace",
            {"owner": "hanzo", "name": "research"},
            "POST",
            "/v1/iam/workspaces",
        ),
        (
            "delete_workspace",
            {"id": "hanzo/research"},
            "DELETE",
            "/v1/iam/workspaces/hanzo/research",
        ),
        ("members", {"org": "hanzo"}, "GET", "/v1/iam/memberships?org=hanzo"),
        ("invite", {"org": "hanzo", "email": "a@hanzo.ai"}, "POST", "/v1/iam/invitations"),
        ("account", {}, "GET", "/v1/iam/account"),
    ],
)
async def test_each_action_addresses_the_canonical_route(
    monkeypatch, action, params, method, path
):
    seen, handler = _recorder()
    _serve(monkeypatch, handler)

    out = json.loads(await TeamTool().call(None, action=action, **params))
    assert not (isinstance(out, dict) and "error" in out), out
    assert seen["method"] == method
    assert seen["url"] == f"{IAM_BASE_URL}{path}"
    assert seen["auth"] == "Bearer jwt-value"


async def test_a_workspace_list_reads_the_key_the_server_names(monkeypatch):
    _, handler = _recorder()
    _serve(monkeypatch, handler)

    out = json.loads(await TeamTool().call(None, action="workspaces"))
    assert out["count"] == 1
    assert out["total"] == 1
    assert out["workspaces"][0] == {
        "owner": "hanzo",
        "name": "research",
        "displayName": None,
        "organization": None,
        "createdTime": None,
    }


async def test_a_bare_array_is_an_error_not_an_empty_page(monkeypatch):
    _, handler = _recorder([{"name": "research"}])
    _serve(monkeypatch, handler)

    out = json.loads(await TeamTool().call(None, action="workspaces"))
    assert "no workspaces list" in out["error"]


async def test_membership_reads_the_envelope_not_the_wrapper(monkeypatch):
    _, handler = _recorder()
    _serve(monkeypatch, handler)

    out = json.loads(await TeamTool().call(None, action="members", org="hanzo"))
    assert out["count"] == 1
    assert out["members"][0]["user"] == "hanzo/alice"


async def test_a_stated_error_in_the_envelope_is_raised(monkeypatch):
    _, handler = _recorder({"status": "error", "msg": "org required"})
    _serve(monkeypatch, handler)

    out = json.loads(await TeamTool().call(None, action="members", org="hanzo"))
    assert out["error"] == "org required"


async def test_a_missing_workspace_is_reported_as_a_404(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"title": "not found"})

    _serve(monkeypatch, handler)
    out = json.loads(await TeamTool().call(None, action="workspace", id="hanzo/nope"))
    assert "404" in out["error"]


async def test_a_workspace_is_named_by_owner_and_name(monkeypatch):
    seen, handler = _recorder()
    _serve(monkeypatch, handler)

    out = json.loads(await TeamTool().call(None, action="workspace"))
    assert "owner/name" in out["error"]

    await TeamTool().call(None, action="create_workspace", owner="hanzo", name="research")
    assert json.loads(seen["body"]) == {
        "owner": "hanzo",
        "name": "research",
        "displayName": "research",
        "organization": "hanzo",
    }
