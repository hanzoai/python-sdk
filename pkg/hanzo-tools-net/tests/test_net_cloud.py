"""Offline tests for the cloud-backed net + vision wiring (no network).

Cloud calls are faked; the local DuckDuckGo/fetch fallbacks are patched so the
routing logic (cloud-first, local-fallback) is exercised deterministically.
"""

import asyncio
import base64

from hanzo_tools.core import CloudError

from hanzo_tools.net import FetchTool, VisionTool
from hanzo_tools.net.fetch_tool import _crawl_metadata, _extract_markdown


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


class FakeResponse:
    def __init__(self, text="<html><body>hi there</body></html>", url="https://x/"):
        self.text = text
        self.url = url
        self.status_code = 200


class FakeClient:
    async def get(self, url, **kw):
        return FakeResponse(url=url)


def _run(coro):
    return asyncio.run(coro)


# ── search ───────────────────────────────────────────────────────────────


def test_search_cloud_normalizes_searxng():
    t = FetchTool()
    t._cloud = FakeCloud(
        get_result={
            "results": [
                {"url": "u1", "title": "t1", "content": "c1", "engine": "bing"},
                {"url": "u2", "title": "t2", "content": "c2"},
            ]
        }
    )
    env = _run(t.call(None, action="search", query="hanzo", limit=5))
    assert env["ok"] is True
    _, path, params = t._cloud.calls[0]
    assert path == "/v1/websearch/search" and params["q"] == "hanzo"
    data = env["data"]
    assert data["engine"] == "hanzo" and data["count"] == 2
    assert data["results"][0] == {"url": "u1", "title": "t1", "snippet": "c1"}


def test_search_falls_back_to_duckduckgo_on_cloud_error():
    t = FetchTool()
    t._cloud = FakeCloud(get_result=CloudError("down"))

    async def fake_ddg(query, limit):
        return [{"url": "d", "title": "ddg", "snippet": "s"}]

    t._duckduckgo_search = fake_ddg
    env = _run(t.call(None, action="search", query="q"))
    assert env["ok"] is True
    assert env["data"]["engine"] == "duckduckgo"
    assert env["data"]["results"][0]["title"] == "ddg"


def test_search_engine_duckduckgo_skips_cloud():
    t = FetchTool()
    t._cloud = FakeCloud()  # configured, but should not be used

    async def fake_ddg(query, limit):
        return [{"url": "d", "title": "ddg", "snippet": "s"}]

    t._duckduckgo_search = fake_ddg
    env = _run(t.call(None, action="search", query="q", engine="duckduckgo"))
    assert env["ok"] is True
    assert env["data"]["engine"] == "duckduckgo"
    assert t._cloud.calls == []  # cloud never touched


# ── web_read ─────────────────────────────────────────────────────────────


def test_web_read_cloud_markdown():
    t = FetchTool()
    t._cloud = FakeCloud(
        post_result={"status": "ok", "data": {"markdown": "# Title\n\nBody"}}
    )
    env = _run(t.call(None, action="web_read", url="https://x"))
    assert env["ok"] is True
    assert env["data"]["source"] == "cloud"
    assert env["data"]["markdown"] == "# Title\n\nBody"
    _, path, body = t._cloud.calls[0]
    assert path == "/v1/crawl" and body == {"url": "https://x"}


def test_web_read_falls_back_local_when_cloud_errors():
    t = FetchTool()
    t._cloud = FakeCloud(post_result=CloudError("dns fail"))

    async def fake_get_client():
        return FakeClient()

    t._get_client = fake_get_client
    env = _run(t.call(None, action="web_read", url="https://x"))
    assert env["ok"] is True
    assert env["data"]["source"] == "local"
    assert "hi there" in env["data"]["markdown"]


def test_web_read_falls_back_when_cloud_returns_no_markdown():
    # Hanzo Crawl error envelope (data=null) → treated as no markdown → local.
    t = FetchTool()
    t._cloud = FakeCloud(post_result={"status": "error", "msg": "boom", "data": None})

    async def fake_get_client():
        return FakeClient()

    t._get_client = fake_get_client
    env = _run(t.call(None, action="web_read", url="https://x"))
    assert env["ok"] is True and env["data"]["source"] == "local"


def test_extract_markdown_shapes():
    assert _extract_markdown({"data": {"markdown": "m"}}) == "m"
    assert _extract_markdown({"success": True, "data": {"fit_markdown": "fm"}}) == "fm"
    assert _extract_markdown({"data": [{"raw_markdown": "rm"}]}) == "rm"
    assert _extract_markdown("bare string") == "bare string"
    assert _extract_markdown({"status": "error", "data": None}) == ""
    assert _crawl_metadata({"data": {"metadata": {"title": "T"}}}) == {"title": "T"}


# ── vision ───────────────────────────────────────────────────────────────


def test_vision_encodes_local_file(tmp_path):
    png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    )
    p = tmp_path / "pix.png"
    p.write_bytes(png)
    t = VisionTool()
    uri = _run(t._image_url(str(p)))
    assert uri.startswith("data:image/png;base64,")


def test_vision_data_uri_passthrough():
    t = VisionTool()
    duri = "data:image/png;base64,AAAA"
    assert _run(t._image_url(duri)) == duri


def test_vision_complete_extracts_answer():
    t = VisionTool()
    t._cloud = FakeCloud(
        post_result={
            "model": "zen3-vl",
            "choices": [{"message": {"content": "a cat"}}],
            "usage": {"total_tokens": 5},
        }
    )
    env = _run(
        t.call(None, action="ask", image="data:image/png;base64,AAAA", prompt="what?")
    )
    assert env["ok"] is True
    assert env["data"]["answer"] == "a cat"
    _, path, body = t._cloud.calls[0]
    assert path == "/v1/chat/completions"
    assert body["messages"][0]["content"][1]["image_url"]["url"] == (
        "data:image/png;base64,AAAA"
    )


def test_vision_not_configured_fails_closed():
    t = VisionTool()
    t._cloud = FakeCloud(configured=False)
    env = _run(t.call(None, action="ask", image="data:image/png;base64,AAAA"))
    assert env["ok"] is False and env["error"]["code"] == "INVALID_PARAMS"
