"""How IAMClient presents its credential on the wire.

The defect these pin: the client used to put `clientId` and `clientSecret` in
the QUERY STRING. Two independent failures in one line —

  1. A client secret in a URL is disclosed to every access log, proxy log and
     Referer header on the path. Credentials belong in a header.
  2. iam does not accept it. The Guard resolves a confidential client from
     `Authorization: Basic <clientId>:<clientSecret>` (RFC 6749 2.3.1
     client_secret_basic) or a bearer, and reads no credential from the query
     at all — so the leaking form did not even authenticate.

So the assertion is two-sided: the header must carry the credential AND the
query must not.
"""

from __future__ import annotations

import base64

import httpx
import pytest

from hanzo_iam.client import IAMClient
from hanzo_iam.config import IAMConfig


def _capture(client: IAMClient, payload: dict) -> list[httpx.Request]:
    """Point `client` at an in-memory transport and record what it sends."""
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=payload)

    client._http = httpx.Client(
        base_url=client.config.base_url,
        transport=httpx.MockTransport(handler),
    )
    return seen


@pytest.fixture
def config() -> IAMConfig:
    return IAMConfig(
        server_url="https://hanzo.id",
        client_id="cid",
        client_secret="csec",
        organization="acme",
        application="myapp",
    )


class TestConfidentialClientCredential:
    def test_secret_travels_in_basic_header(self, config):
        client = IAMClient(config=config)
        seen = _capture(client, {"status": "ok", "data": []})

        client.get_users(owner="acme")

        expected = base64.b64encode(b"cid:csec").decode()
        assert seen[0].headers["Authorization"] == f"Basic {expected}"

    def test_secret_never_appears_in_the_url(self, config):
        client = IAMClient(config=config)
        seen = _capture(client, {"status": "ok", "data": []})

        client.get_users(owner="acme")

        url = str(seen[0].url)
        assert "csec" not in url
        assert "clientSecret" not in url
        assert "clientId" not in url

    def test_bearer_wins_and_carries_no_secret(self, config):
        client = IAMClient(config=config, bearer_token="tok")
        seen = _capture(client, {"status": "ok", "data": []})

        client.get_users(owner="acme")

        assert seen[0].headers["Authorization"] == "Bearer tok"
        assert "csec" not in str(seen[0].url)


class TestOwnerIsNamedNotAssumed:
    """Every org-scoped read takes the tenant as an argument.

    `get_users()` used to bind the config's organization with no way for a
    caller to name a different one, while its neighbours (`get_providers`,
    `get_roles`, `get_applications`) each took an `owner`. Same surface, three
    different answers to "may I name a tenant?". Now there is one answer.
    """

    def test_get_users_sends_the_owner_it_was_given(self, config):
        client = IAMClient(config=config)
        seen = _capture(client, {"status": "ok", "data": []})

        client.get_users(owner="other-tenant")

        assert seen[0].url.params["owner"] == "other-tenant"

    def test_get_users_defaults_to_the_configured_org(self, config):
        client = IAMClient(config=config)
        seen = _capture(client, {"status": "ok", "data": []})

        client.get_users()

        assert seen[0].url.params["owner"] == "acme"

    def test_get_organizations_sends_the_owner_it_was_given(self, config):
        client = IAMClient(config=config)
        seen = _capture(client, {"status": "ok", "data": []})

        client.get_organizations(owner="built-in")

        assert seen[0].url.params["owner"] == "built-in"


class TestOneClient:
    """There is one IAM HTTP client and one env reader, not two of each."""

    def test_no_async_duplicate(self):
        import hanzo_iam

        assert not hasattr(hanzo_iam, "AsyncIAMClient")

    def test_no_second_env_reader(self):
        assert not hasattr(IAMClient, "_config_from_env")

    def test_no_second_token_verifier(self):
        # hanzo_iam.tokens.verify is the ONE judge of a credential; it checks
        # the issuer and requires `exp`, neither of which the client's copy did.
        assert not hasattr(IAMClient, "validate_token")
        assert not hasattr(IAMClient, "validate_token_with_cert")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
