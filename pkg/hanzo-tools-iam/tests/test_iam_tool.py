"""Tests for the IAM tool's canonical /v1/iam/ surface (HIP-0111/HIP-0026).

The Hanzo IAM server serves admin CRUD only under /v1/iam/; the upstream-shape
/api/ path falls through to a 200 text/html SPA catch-all. These tests pin the
URL builder to /v1/iam/ and prove the health check rejects that HTML catch-all.
"""

from __future__ import annotations

import json

import httpx

from hanzo_tools.iam.iam_tool import IAMTool, _iam_url, IAM_BASE_URL


def test_iam_url_uses_v1_iam_not_api():
    url = _iam_url("get-users")
    assert url == f"{IAM_BASE_URL}/v1/iam/get-users"
    assert "/api/" not in url


def test_iam_url_strips_leading_slash():
    assert _iam_url("/enforce") == f"{IAM_BASE_URL}/v1/iam/enforce"


def _patched_client(monkeypatch, handler):
    real_init = httpx.AsyncClient.__init__

    def init(self, *args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        real_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "__init__", init)


async def test_health_hits_canonical_healthz(monkeypatch):
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        return httpx.Response(
            200,
            json={"status": "ok", "data": {"service": "iam", "version": "v1.18.3"}},
        )

    _patched_client(monkeypatch, handler)
    out = json.loads(await IAMTool()._health())
    assert seen["url"] == f"{IAM_BASE_URL}/v1/iam/healthz"
    assert out["status"] == "ok"
    assert out["data"]["service"] == "iam"


async def test_health_rejects_html_spa_catch_all(monkeypatch):
    # A 200 text/html SPA response must NOT be reported as healthy.
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<!DOCTYPE html><html></html>",
                              headers={"content-type": "text/html; charset=utf-8"})

    _patched_client(monkeypatch, handler)
    out = json.loads(await IAMTool()._health())
    assert out["status"] == "error"
