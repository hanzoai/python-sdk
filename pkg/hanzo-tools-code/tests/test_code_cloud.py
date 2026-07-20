"""Offline tests for the cloud-backed code actions (no network).

A FakeCloud is injected so the /v1/code/* wiring is exercised deterministically:
correct paths, params, and body shapes, plus the fail-closed not-configured path.
"""

import asyncio

from hanzo_tools.core import CloudError

from hanzo_tools.code import CodeTool


class FakeCloud:
    def __init__(self, get_result=None, post_result=None, configured=True):
        self.get_result = get_result if get_result is not None else {}
        self.post_result = post_result if post_result is not None else {}
        self.calls = []
        self._configured = configured

    def configured(self):
        return self._configured

    async def get(self, path, params=None):
        self.calls.append(("GET", path, params))
        if isinstance(self.get_result, Exception):
            raise self.get_result
        return self.get_result

    async def post(self, path, json_body=None):
        self.calls.append(("POST", path, json_body))
        if isinstance(self.post_result, Exception):
            raise self.post_result
        return self.post_result


def _run(coro):
    return asyncio.run(coro)


def test_has_cloud_actions():
    t = CodeTool()
    for a in ("search", "context", "ask", "index"):
        assert a in t._handlers


def test_search_maps_to_code_search():
    t = CodeTool()
    t._cloud = FakeCloud(get_result={"query": "q", "results": [{"file": "a.go"}]})
    env = _run(t.call(None, action="search", query="parse", type="hybrid", limit=5))
    assert env["ok"] is True
    method, path, params = t._cloud.calls[0]
    assert method == "GET" and path == "/v1/code/search"
    assert params["q"] == "parse" and params["type"] == "hybrid" and params["limit"] == 5
    assert env["data"]["results"] == [{"file": "a.go"}]


def test_context_posts_body():
    t = CodeTool()
    t._cloud = FakeCloud(post_result={"usedTokens": 10, "spans": []})
    env = _run(t.call(None, action="context", query="how", budgetTokens=123, repo="r"))
    assert env["ok"] is True
    method, path, body = t._cloud.calls[0]
    assert method == "POST" and path == "/v1/code/context"
    assert body == {"query": "how", "budgetTokens": 123, "repo": "r"}


def test_ask_posts_body():
    t = CodeTool()
    t._cloud = FakeCloud(post_result={"question": "q", "answer": "a", "citations": []})
    env = _run(t.call(None, action="ask", query="what does X do"))
    assert env["ok"] is True
    method, path, body = t._cloud.calls[0]
    assert method == "POST" and path == "/v1/code/ask"
    assert body == {"query": "what does X do"}


def test_index_collects_dir(tmp_path):
    (tmp_path / "a.py").write_text("def a():\n    return 1\n")
    (tmp_path / "b.txt").write_text("ignored ext")  # .txt not in LANG_MAP
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "c.py").write_text("skip me")

    t = CodeTool()
    t._cloud = FakeCloud(post_result={"repo": "demo", "indexed": 1})
    env = _run(t.call(None, action="index", repo="demo", path=str(tmp_path)))
    assert env["ok"] is True
    method, path, body = t._cloud.calls[0]
    assert method == "POST" and path == "/v1/code/index"
    assert body["repo"] == "demo"
    paths = {f["path"] for f in body["files"]}
    assert paths == {"a.py"}  # only .py, node_modules skipped


def test_index_explicit_files():
    t = CodeTool()
    t._cloud = FakeCloud(post_result={"indexed": 1})
    files = [{"path": "x.go", "content": "package x"}]
    env = _run(t.call(None, action="index", repo="r", files=files))
    assert env["ok"] is True
    _, _, body = t._cloud.calls[0]
    assert body["files"] == files


def test_not_configured_fails_closed():
    t = CodeTool()
    t._cloud = FakeCloud(configured=False)
    env = _run(t.call(None, action="search", query="x"))
    assert env["ok"] is False
    assert env["error"]["code"] == "INVALID_PARAMS"


def test_cloud_error_surfaces():
    t = CodeTool()
    t._cloud = FakeCloud(get_result=CloudError("boom", status=500))
    env = _run(t.call(None, action="search", query="x"))
    assert env["ok"] is False
    assert env["error"]["code"] == "INTERNAL_ERROR"
