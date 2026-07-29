"""One response decision, applied by every surface that talks to IAM.

THE DEFECT. Three modules in this package each decided independently whether an
IAM response was a value or an error, and they disagreed on the question that
actually bites: *is the body JSON at all?*

    hanzo_iam.oauth      content-type gate  -> legible "wrong path"
    hanzo_iam.client     none               -> JSONDecodeError
    hanzo_iam.fastapi    none               -> JSONDecodeError

Only `oauth` had the gate, and its own comment says why: hanzo.id serves its
sign-in SPA (200 text/html) on every unmatched path, so a client that trusts the
status code dies inside `.json()` with an inscrutable parse error instead of
saying which path was wrong. `models.py` documents the same trap for the OIDC
paths. The other two surfaces call the SAME host over the SAME base URL, so they
had the same bug and none of the protection.

Collapsing three decoders into one is only safe if the survivor keeps the
STRICTEST behaviour of all three. These tests pin that: the content-type gate
(oauth's), the `{status:"error"}` envelope (client's), and refusal on a non-2xx
(neither had it — a 403 from the authz seam used to surface as an empty list).
"""

from __future__ import annotations

import httpx
import pytest

from hanzo_iam.client import IAMClient
from hanzo_iam.config import IAMConfig
from hanzo_iam.response import IAMError, decode, unwrap

# The body hanzo.id actually returns on an unmatched path: 200, text/html, the
# sign-in single-page app. Every assertion about "wrong path" is about this.
SPA = ("<!doctype html><html><body>sign in</body></html>", "text/html; charset=utf-8")


@pytest.fixture
def config() -> IAMConfig:
    return IAMConfig(
        server_url="https://hanzo.id",
        client_id="cid",
        client_secret="csec",
        organization="acme",
        application="myapp",
    )


def _respond(client: IAMClient, response: httpx.Response) -> None:
    """Point `client` at an in-memory transport that always answers `response`."""
    client._http = httpx.Client(
        base_url=client.config.base_url,
        transport=httpx.MockTransport(lambda _req: response),
    )


def _resp(status: int = 200, *, text: str | None = None, ctype: str = "", json=None):
    """Build a response carrying a real request, so error text can name the URL."""
    request = httpx.Request("GET", "https://hanzo.id/v1/iam/get-users")
    if json is not None:
        return httpx.Response(status, json=json, request=request)
    return httpx.Response(
        status, text=text or "", headers={"content-type": ctype}, request=request
    )


class TestTheContentTypeGate:
    """A non-JSON body is a WRONG PATH, not a rejected call.

    This is the guard only `oauth` had. It is the one that must survive.
    """

    def test_decode_refuses_a_200_html_page(self):
        body, ctype = SPA
        with pytest.raises(IAMError) as e:
            decode(_resp(200, text=body, ctype=ctype), "get-users")
        assert "wrong path" in str(e.value)

    def test_decode_names_the_url_it_asked_for(self):
        body, ctype = SPA
        with pytest.raises(IAMError) as e:
            decode(_resp(200, text=body, ctype=ctype), "get-users")
        assert "/v1/iam/get-users" in str(e.value)

    def test_the_admin_client_gets_the_same_gate(self, config):
        """The defect, at the surface that lacked it.

        Before: `.json()` on the SPA -> json.JSONDecodeError, which names a byte
        offset and not the path. `hanzo iam set-password` hits exactly this,
        because canonical IAM serves no /v1/iam/set-password at all.
        """
        client = IAMClient(config=config)
        body, ctype = SPA
        _respond(client, httpx.Response(200, text=body, headers={"content-type": ctype}))

        with pytest.raises(IAMError) as e:
            client.get_users(owner="acme")
        assert "wrong path" in str(e.value)

    def test_a_missing_content_type_is_also_refused(self):
        with pytest.raises(IAMError):
            decode(_resp(200, text="whatever", ctype=""), "get-users")

    def test_unparseable_json_is_refused_not_returned(self):
        with pytest.raises(IAMError):
            decode(_resp(200, text="{not json", ctype="application/json"), "get-users")


class TestTheErrorChannels:
    """Every way IAM says no, refused in one place."""

    def test_oauth_error_object(self):
        with pytest.raises(IAMError) as e:
            decode(
                _resp(400, json={"error": "invalid_grant", "error_description": "nope"}),
                "token endpoint",
            )
        assert "invalid_grant" in str(e.value)

    def test_compat_envelope_error(self):
        with pytest.raises(IAMError) as e:
            unwrap(_resp(200, json={"status": "error", "msg": "no such user"}), "get-user")
        assert "no such user" in str(e.value)

    def test_a_403_is_refused_and_not_read_as_empty(self):
        """The authz seam refuses cross-tenant reads with a 403 + JSON body.

        Neither old decoder checked the status: `client` called
        raise_for_status() (losing the server's words) and the envelope branch
        never ran, so a refusal that arrived as `{"data": null}` would read as
        "this org has no users" — a refusal indistinguishable from an empty
        tenant. It must raise.
        """
        with pytest.raises(IAMError) as e:
            unwrap(_resp(403, json={"status": 403, "error": "forbidden"}), "get-users")
        assert "403" in str(e.value)


class TestTheEnvelopeIsUnwrappedOnce:
    def test_unwrap_returns_the_data(self):
        assert unwrap(_resp(200, json={"status": "ok", "data": [1, 2]}), "x") == [1, 2]

    def test_decode_does_not_unwrap_an_oidc_payload(self):
        """A token response has no envelope; decode must hand it back whole."""
        payload = {"access_token": "t", "token_type": "Bearer", "expires_in": 3600}
        assert decode(_resp(200, json=payload), "token endpoint") == payload


class TestOneDecoderNotThree:
    """No module keeps a private copy of the decision."""

    def test_oauth_has_no_private_decoder(self):
        import hanzo_iam.oauth as oauth

        assert not hasattr(oauth, "_json_or_raise")

    def test_fastapi_reads_no_json_of_its_own(self):
        import inspect

        import hanzo_iam.fastapi as fa

        assert "response.json()" not in inspect.getsource(fa)

    def test_client_reads_no_json_of_its_own(self):
        import inspect

        import hanzo_iam.client as c

        assert "response.json()" not in inspect.getsource(c)


class TestNoSecondWayToTheTokenEndpoint:
    """The OIDC protocol surface has ONE owner: hanzo_iam.oauth.

    `IAMClient` used to redeem and refresh tokens too, under different credential
    rules — it posted `client_secret` where `oauth` proves possession with PKCE.
    Two modules owning the token endpoint is two answers to "what authenticates
    this exchange". `client` is now the ADMIN surface only.
    """

    @pytest.mark.parametrize(
        "gone",
        [
            "get_authorization_url",  # -> oauth.authorize_url
            "exchange_code",  # -> oauth.exchange_code
            "refresh_token",  # -> oauth.refresh
            "get_user_info",  # -> fastapi._fetch_user_info
            "login",  # collided with hanzo_iam.login (oauth's browser flow)
            "client_credentials",
            "introspect_token",
            "get_openid_configuration",
            "get_jwks",
        ],
    )
    def test_client_no_longer_owns_the_oidc_surface(self, gone):
        assert not hasattr(IAMClient, gone)

    def test_oauth_owns_refresh(self):
        from hanzo_iam import oauth

        assert callable(oauth.refresh)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
