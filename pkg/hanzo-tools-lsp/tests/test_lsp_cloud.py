"""`lsp` against a stand-in /v1/code/lsp (no network).

One tool, two planes. These fake the wire, not the client: a real HanzoCloud
runs over a canned transport, so what is under test is what actually goes out
when a caller names a `repo` — the op the action maps to, the body it carries
(0-based line, UTF-16 character), and the answer coming back verbatim. With no
`repo`, nothing leaves the process.
"""

import json
import asyncio

from hanzo_tools.lsp import TOOLS, LSPTool
from hanzo_tools.core import HanzoCloud
from hanzo_tools.lsp.lsp_tool import CLOUD_OPS, LOCAL_ACTIONS


def _run(coro):
    return asyncio.run(coro)


class FakeResponse:
    def __init__(self, payload, status=200):
        self.status_code = status
        self.payload = payload
        self.text = json.dumps(payload)

    def json(self):
        return self.payload


class FakeClient:
    """An httpx-shaped client that records requests and replays one reply."""

    def __init__(self, reply, status=200):
        self.reply = reply
        self.status = status
        self.calls = []

    async def request(self, method, path, **kw):
        self.calls.append((method, path, kw))
        return FakeResponse(self.reply, self.status)


def tool_over(reply=None, key="hk-test", status=200):
    """An LSPTool whose cloud client answers from a canned transport."""
    tool = LSPTool()
    cloud = HanzoCloud(key=key)
    client = FakeClient(reply if reply is not None else {"locations": []}, status)

    async def fake_get_client():
        return client

    cloud._get_client = fake_get_client
    tool._cloud = cloud
    return tool, client


def sent(client):
    """The one request the tool made: (path, body)."""
    assert len(client.calls) == 1, f"expected one request, saw {client.calls}"
    method, path, kw = client.calls[0]
    assert method == "POST"
    return path, kw["json"]


# ── repo → the cloud index ───────────────────────────────────────────────


def test_definition_locates_with_a_relation_in_lsp_frame():
    hit = {"locations": [{"repo": "hanzoai/mcp", "path": "rust/src/hanzo_api.rs", "line": 18}]}
    tool, client = tool_over(hit)
    out = _run(
        tool.run(
            action="definition",
            repo="hanzoai/mcp",
            rev="main",
            file="rust/src/tools/lsp_tool.rs",
            line=42,
            character=7,
        )
    )

    assert out.data == hit, "the cloud's answer comes back verbatim"
    path, body = sent(client)
    assert path == "/v1/code/lsp/locate"
    assert body == {
        "repo": "hanzoai/mcp",
        "rev": "main",
        "path": "rust/src/tools/lsp_tool.rs",
        # the tool's 1-based line 42 leaves as LSP's 0-based 41
        "line": 41,
        "character": 7,
        "relation": "definition",
    }


def test_locate_relations_share_one_op():
    for action, relation in [
        ("definition", "definition"),
        ("references", "reference"),
        ("type", "type"),
        ("implementation", "implementation"),
    ]:
        tool, client = tool_over()
        _run(tool.run(action=action, repo="hanzoai/mcp", file="a.py", line=1, character=0))
        path, body = sent(client)
        assert path == "/v1/code/lsp/locate"
        assert body["relation"] == relation
        assert body["line"] == 0
        assert "rev" not in body, "an unnamed rev is absent, not empty"


def test_standalone_ops_carry_no_relation():
    for action, op in [
        ("hover", "hover"),
        ("symbols", "symbols"),
        ("diagnostics", "diagnostics"),
        ("completion", "complete"),
    ]:
        tool, client = tool_over({"ok": True})
        _run(tool.run(action=action, repo="hanzoai/mcp", file="a.py", line=9, character=4))
        path, body = sent(client)
        assert path == f"/v1/code/lsp/{op}"
        assert "relation" not in body
        assert body["path"] == "a.py"
        assert body["line"] == 8


def test_every_cloud_action_is_mapped():
    assert set(CLOUD_OPS) == {
        "definition",
        "references",
        "type",
        "implementation",
        "hover",
        "symbols",
        "diagnostics",
        "completion",
    }
    for op, relation in CLOUD_OPS.values():
        assert op in {"locate", "hover", "symbols", "diagnostics", "complete"}
        assert (relation is None) == (op != "locate")


def test_upstream_failure_is_reported_not_raised():
    tool, client = tool_over({"error": "nope"}, status=502)
    out = _run(tool.run(action="hover", repo="hanzoai/mcp", file="a.py", line=1))
    assert out.data["repo"] == "hanzoai/mcp"
    assert "502" in out.data["error"]


def test_without_a_key_nothing_is_sent():
    tool, client = tool_over(key="")
    out = _run(tool.run(action="hover", repo="hanzoai/mcp", file="a.py", line=1))
    assert "hk-" in out.data["error"]
    assert client.calls == []


# ── file → the local plane ───────────────────────────────────────────────


def test_file_alone_stays_local_and_sends_nothing():
    tool, client = tool_over()
    out = _run(tool.run(action="definition", file="notes.txt"))
    assert "Unsupported file type" in out.data["error"]
    assert "go" in out.data["supported_languages"]
    assert client.calls == []


def test_neither_file_nor_repo_fails_cleanly():
    tool, client = tool_over()
    out = _run(tool.run(action="definition"))
    assert out.data["error"].startswith("file is required")
    assert client.calls == []


def test_an_invalid_action_lists_both_planes():
    tool, _ = tool_over()
    out = _run(tool.run(action="frobnicate", file="a.py"))
    assert "Invalid action" in out.data["error"]
    assert "implementation" in out.data["error"]


def test_a_local_only_action_with_repo_says_so():
    tool, client = tool_over()
    out = _run(tool.run(action="rename", repo="hanzoai/mcp", file="a.py", new_name="x"))
    assert "needs a working tree" in out.data["error"]
    assert client.calls == []


def test_a_cloud_only_action_without_repo_says_so():
    tool, client = tool_over()
    out = _run(tool.run(action="symbols", file="a.py"))
    assert "pass `repo`" in out.data["error"]
    assert out.data["local_actions"] == LOCAL_ACTIONS
    assert client.calls == []


# ── one tool ─────────────────────────────────────────────────────────────


def test_lsp_is_one_tool_with_both_planes_on_its_handler():
    assert [t.name for t in TOOLS] == ["lsp"]

    handlers = {}

    class Server:
        def tool(self, name, description):
            def register(fn):
                handlers[name] = fn
                return fn

            return register

    LSPTool().register(Server())
    assert set(handlers) == {"lsp"}
    params = handlers["lsp"].__annotations__
    assert "repo" in params and "rev" in params and "file" in params
