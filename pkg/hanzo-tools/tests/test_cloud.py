"""Tests for hanzo_tools.core.cloud — what a refused call and an answered one hand back.

HanzoCloud runs against an httpx MockTransport answering as api.hanzo.ai does,
so no socket is opened.
"""

import asyncio

import httpx
import pytest
from hanzo_tools.core import CloudError, HanzoCloud

FREE_PLAN_CAP = {
    "error": {
        "message": "Free plan: today's Kai requests are used. Upgrade for more: https://hanzo.ai/pay",
        "type": "rate_limit_error",
        "code": "free_plan_cap",
        "class": "ours",
        "resets_at": "2026-10-05T00:00:00Z",
    }
}


def cloud(handler):
    c = HanzoCloud(base_url="https://api.hanzo.ai", key="sk-test")
    c._client = httpx.AsyncClient(base_url="https://api.hanzo.ai", transport=httpx.MockTransport(handler))
    return c


def test_send_hands_back_the_body_and_the_headers():
    c = cloud(lambda r: httpx.Response(200, json={"ok": 1}, headers={"X-Hanzo-Paid-By": "credits"}))
    body, headers = asyncio.run(c.send("POST", "/v1/chat/completions", json={"model": "m"}))
    assert body == {"ok": 1}
    assert headers["x-hanzo-paid-by"] == "credits"


def test_a_refusal_carries_its_whole_body_and_headers():
    c = cloud(lambda r: httpx.Response(429, json=FREE_PLAN_CAP, headers={"X-Hanzo-Usage": "limited"}))
    with pytest.raises(CloudError) as raised:
        asyncio.run(c.post("/v1/decisions", {"model": "kai"}))
    e = raised.value
    assert e.status == 429
    assert e.body == FREE_PLAN_CAP
    assert e.headers["x-hanzo-usage"] == "limited"
    assert "429" in str(e) and "free_plan_cap" in str(e)


def test_a_body_that_is_not_json_is_none_and_a_transport_failure_has_no_answer():
    c = cloud(lambda r: httpx.Response(502, text="<html>bad gateway</html>"))
    with pytest.raises(CloudError) as raised:
        asyncio.run(c.get("/v1/models"))
    assert (raised.value.status, raised.value.body) == (502, None)

    def down(request):
        raise httpx.ConnectError("no route", request=request)

    with pytest.raises(CloudError) as raised:
        asyncio.run(cloud(down).get("/v1/models"))
    assert (raised.value.status, raised.value.body, dict(raised.value.headers)) == (None, None, {})


def test_get_and_post_still_answer_the_body_alone():
    c = cloud(lambda r: httpx.Response(200, json={"data": [1, 2]}))
    assert asyncio.run(c.get("/v1/models")) == {"data": [1, 2]}
    assert asyncio.run(c.post("/v1/x", {})) == {"data": [1, 2]}
