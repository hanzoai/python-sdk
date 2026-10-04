"""Tests for repo: repositories on Hanzo git and their GitHub links, over /v1/sync.

The tool runs against a real HanzoCloud whose httpx transport answers as
api.hanzo.ai does, so each test reads the request that went out and what the
tool made of the answer. The live test is skipped when no Hanzo credential
resolves.
"""

import asyncio

import httpx
import pytest
from hanzo_tools.core import HanzoCloud

from hanzo_tools.vcs import TOOLS, RepoTool

UI = {
    "id": "sync_713c4bb98167c774be9d6d01a35ac69f",
    "kind": "git",
    "source": {"provider": "github", "locator": "https://github.com/hanzoai/ui.git"},
    "target": {"provider": "hanzo-git", "locator": "ui"},
    "direction": "pull",
    "trigger": "poll",
    "createdAt": "2026-07-22T10:42:41Z",
    "updatedAt": "2026-10-04T23:06:13Z",
    "scope": "repo",
    "native": {
        "url": "https://git.hanzo.ai/hanzoai/hanzoai_ui",
        "clone": "https://git.hanzo.ai/hanzoai/hanzoai_ui.git",
        "branch": "main",
        "status": "synced",
        "sizeBytes": 131655680,
    },
}
ARC = {
    "id": "sync_0b1d",
    "source": {"provider": "github", "locator": "https://github.com/hanzoai/arc.git"},
    "target": {"provider": "hanzo-git", "locator": "arc"},
    "direction": "both",
    "trigger": "webhook",
    "scope": "repo",
    "native": {
        "status": "conflict",
        "branch": "main",
        "url": "https://git.hanzo.ai/hanzoai/hanzoai_arc",
    },
}
ACCOUNT = {
    "id": "sync_acct",
    "source": {"provider": "github", "locator": "https://github.com/hanzoai"},
    "direction": "pull",
    "trigger": "webhook",
    "scope": "account",
}


class Gateway:
    def __init__(self):
        self.seen: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.seen.append(request)
        path = request.url.path
        if request.method == "GET" and path == "/v1/sync":
            return httpx.Response(200, json={"data": [UI, ARC, ACCOUNT]})
        if request.method == "POST" and path == f"/v1/sync/{UI['id']}/run":
            return httpx.Response(202, json={"queued": True, "id": UI["id"]})
        return httpx.Response(404, json={"error": "no such sync"})


def wired():
    gw = Gateway()
    cloud = HanzoCloud(base_url="https://api.hanzo.ai", key="sk-test")
    cloud._client = httpx.AsyncClient(
        base_url="https://api.hanzo.ai", transport=httpx.MockTransport(gw)
    )
    tool = RepoTool()
    tool._cloud = cloud
    return tool, gw


def run(tool, **kw):
    async def call():
        try:
            return await tool.call(None, **kw)
        finally:
            if tool._cloud is not None:
                await tool._cloud.aclose()

    return asyncio.run(call())


def test_the_package_carries_git_and_repo():
    assert [t.name for t in TOOLS] == ["git", "repo"]
    assert RepoTool.DEFAULT_ACTION == "list"


def test_list_reads_every_link_and_where_it_stands():
    tool, gw = wired()
    env = run(tool)
    assert env["ok"], env
    assert (gw.seen[-1].method, gw.seen[-1].url.path) == ("GET", "/v1/sync")
    assert gw.seen[-1].headers["authorization"] == "Bearer sk-test"
    assert env["data"]["count"] == 3
    assert env["data"]["repos"][0] == {
        "id": "sync_713c4bb98167c774be9d6d01a35ac69f",
        "scope": "repo",
        "source": "https://github.com/hanzoai/ui.git",
        "target": "ui",
        "direction": "pull",
        "trigger": "poll",
        "status": "synced",
        "branch": "main",
        "url": "https://git.hanzo.ai/hanzoai/hanzoai_ui",
        "synced_at": "2026-10-04T23:06:13Z",
    }
    # An account link has no native copy of its own: its standing reads None.
    assert (env["data"]["repos"][2]["scope"], env["data"]["repos"][2]["status"]) == (
        "account",
        None,
    )


def test_list_narrows_by_words_and_by_status():
    tool, _ = wired()
    assert [r["id"] for r in run(tool, action="list", search="hanzoai arc")["data"]["repos"]] == [
        "sync_0b1d"
    ]
    tool, _ = wired()
    assert [r["id"] for r in run(tool, action="list", status="conflict")["data"]["repos"]] == [
        "sync_0b1d"
    ]


def test_sync_runs_one_link_now():
    tool, gw = wired()
    env = run(tool, action="sync", id=UI["id"])
    assert env["ok"], env
    assert (gw.seen[-1].method, gw.seen[-1].url.path) == ("POST", f"/v1/sync/{UI['id']}/run")
    assert env["data"] == {"queued": True, "id": UI["id"]}


def test_sync_needs_an_id_and_names_one_it_does_not_know():
    tool, gw = wired()
    env = run(tool, action="sync")
    assert not env["ok"] and "id required" in env["error"]["message"]
    assert gw.seen == []
    tool, gw = wired()
    env = run(tool, action="sync", id="sync_nope/../x")
    assert not env["ok"] and env["error"]["code"] == "NOT_FOUND"
    assert gw.seen[-1].url.raw_path.decode() == "/v1/sync/sync_nope%2F..%2Fx/run"


@pytest.mark.skipif(not HanzoCloud().configured(), reason="no Hanzo credential")
def test_live_list_reads_the_org_s_links():
    env = run(RepoTool())
    assert env["ok"], env
    repos = env["data"]["repos"]
    assert env["data"]["count"] == len(repos)
    assert all(r["id"].startswith("sync_") for r in repos)
    assert all(r["status"] in (None, "synced", "conflict", "pending", "paused") for r in repos)
