"""Where the confidential client's credential rides.

IAM reads a credential from Authorization and nowhere else — its `app()` calls
httpx.Basic(c) and never looks at the query. A pair in the query string
therefore authenticates nothing and lands in every log on the path.
"""

import base64

import httpx
import pytest

from hanzo_iam.client import IAMClient, basic
from hanzo_iam.config import IAMConfig


CONFIG = IAMConfig(
    server_url="https://hanzo.id",
    client_id="app-id",
    client_secret="app-secret",
    organization="hanzo",
    application="hanzo-cloud",
)


def client(handler):
    c = IAMClient(config=CONFIG)
    c._http = httpx.Client(
        base_url=CONFIG.base_url, transport=httpx.MockTransport(handler)
    )
    return c


def seen(call):
    """Run one admin call against a mock and return the request it sent.

    Only the request matters here, so a reply the caller cannot deserialize is
    still an answer.
    """
    captured = {}

    def handler(request):
        captured["request"] = request
        return httpx.Response(200, json={"status": "ok", "data": {}, "data2": []})

    try:
        call(client(handler))
    except Exception:
        pass
    return captured["request"]


def test_basic_renders_the_pair():
    assert basic("id", "secret") == "Basic " + base64.b64encode(b"id:secret").decode()


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.get_user("z"),
        lambda c: c.get_users(),
        lambda c: c.get_application(),
        lambda c: c.get_organizations(),
    ],
)
def test_credential_is_in_authorization_never_the_query(call):
    request = seen(call)

    assert request.headers["Authorization"] == basic("app-id", "app-secret")

    query = str(request.url.query)
    assert "app-secret" not in query
    assert "clientSecret" not in query
    assert "clientId" not in query


def test_a_bearer_replaces_the_pair():
    seen_auth = {}

    def handler(request):
        seen_auth["value"] = request.headers["Authorization"]
        return httpx.Response(200, json={"status": "ok", "data": {}})

    c = client(handler)
    c._bearer_token = "tok"
    try:
        c.get_user("z")
    except Exception:
        pass

    assert seen_auth["value"] == "Bearer tok"


@pytest.mark.asyncio
async def test_the_async_client_puts_it_in_the_same_place():
    """AsyncIAMClient is the exported one, and it had the same leak."""
    from hanzo_iam import AsyncIAMClient

    captured = {}

    def handler(request):
        captured["request"] = request
        return httpx.Response(200, json={"status": "ok", "data": {}, "data2": []})

    c = AsyncIAMClient(config=CONFIG)
    c._http = httpx.AsyncClient(
        base_url=CONFIG.base_url, transport=httpx.MockTransport(handler)
    )
    try:
        await c.get_users()
    except Exception:
        pass

    request = captured["request"]
    assert request.headers["Authorization"] == basic("app-id", "app-secret")
    assert "app-secret" not in str(request.url.query)
    assert "clientSecret" not in str(request.url.query)
