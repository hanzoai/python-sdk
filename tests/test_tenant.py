"""One credential, one endpoint, N subjects.

Nothing here touches the network. The stub below has the same `request()`
signature as :class:`hanzoai.cloud.rest.RESTClientObject`, which is the only
thing the client and the two mints ever call, so these exercise the real code
path and only the socket is missing.
"""

import json

import pytest

from hanzoai import Held, Fault, Grant, Token, Client
from hanzoai.cloud import IamApi


class Reply:
    """Shaped like `hanzoai.cloud.rest.RESTResponse`, without a socket."""

    def __init__(self, status, payload=None, headers=None):
        self.status = status
        self.reason = "stub"
        if isinstance(payload, (bytes, bytearray)):
            self.data = bytes(payload)
        elif payload is None:
            self.data = b""
        else:
            self.data = json.dumps(payload).encode()
        self.headers = headers or {"content-type": "application/json", "x-request-id": "req_1"}

    def read(self):
        return self.data

    def getheaders(self):
        return self.headers

    def getheader(self, name, default=None):
        return self.headers.get(name, default)


class Transport:
    """Answers each request with the next reply, and records what it was asked."""

    def __init__(self, *replies):
        self.replies = list(replies)
        self.calls = []

    def request(self, method, url, headers=None, body=None, post_params=None, _request_timeout=None):
        self.calls.append((method, url, dict(headers or {}), body, post_params))
        assert self.replies, "the client made more requests than the test staged"
        return self.replies.pop(0)


def minted(token, expires_in=600):
    """IAM's oauth answer, in RFC 6749's casing."""
    return Reply(200, {"access_token": token, "expires_in": expires_in, "token_type": "Bearer"})


def issued(token, expires_in=600):
    """IAM's act answer, in IAM's own casing."""
    return Reply(200, {"accessToken": token, "expiresIn": expires_in})


def operator(mint, calls=None):
    """A client whose identity mint and whose API calls are both stubs.

    Both mints ride the client's own pool in production, so with no separate
    `calls` the client's transport is the mint's — which is what lets `as_`
    reach the staged replies instead of a socket.
    """
    client = Client(credential=Token("cli_1", "shh", transport=mint))
    client.rest_client = mint if calls is None else calls
    return client


# --------------------------------------------------------------------------
# The identity — client credentials, never a bearer somebody pasted
# --------------------------------------------------------------------------


def test_the_mint_is_the_client_credentials_exchange_on_iam_s_own_host():
    """`POST https://hanzo.id/v1/iam/oauth/token`, client_secret_basic, form-encoded.

    Four things this pins, each of which fails silently if it drifts: the host
    is IAM's, not the platform API's; the grant is client_credentials; the
    credential rides as HTTP Basic rather than in the form; and `resource`
    names the server the token is for, so a token minted for api.hanzo.ai is
    useless anywhere else.
    """
    mint = Transport(minted("tok-1"))
    assert Token("cli_1", "shh", transport=mint).token() == "tok-1"

    method, url, headers, body, form = mint.calls[0]
    assert (method, url) == ("POST", "https://hanzo.id/v1/iam/oauth/token")
    assert headers["Authorization"] == "Basic Y2xpXzE6c2ho"  # base64("cli_1:shh")
    assert headers["Content-Type"] == "application/x-www-form-urlencoded"
    assert form == [("grant_type", "client_credentials"), ("resource", "https://api.hanzo.ai")]
    assert body is None


def test_the_resource_follows_the_endpoint_the_client_was_pointed_at():
    mint = Transport(minted("tok-1"))
    Token("cli_1", "shh", resource="https://api.acme.internal", transport=mint).token()
    assert mint.calls[0][4] == [("grant_type", "client_credentials"), ("resource", "https://api.acme.internal")]


def test_the_oauth_answer_is_snake_case():
    """RFC 6749 spells it `access_token`. camelCase here reads as no token at all."""
    mint = Transport(Reply(200, {"accessToken": "wrong", "expiresIn": 600}))
    with pytest.raises(Fault) as caught:
        Token("cli_1", "shh", transport=mint).token()
    assert "cli_1" in str(caught.value)


def test_the_token_is_held_until_it_nears_expiry():
    mint = Transport(minted("tok-1"))
    identity = Token("cli_1", "shh", transport=mint)

    assert [identity.token() for _ in range(5)] == ["tok-1"] * 5
    assert len(mint.calls) == 1


def test_a_token_inside_the_skew_is_replaced_while_it_still_works():
    """A token that dies in flight is a 401 nobody can tell from a revoked identity.

    `expires_in: 30` is inside the 60s window, so it is spent on arrival.
    """
    mint = Transport(minted("tok-1", expires_in=30), minted("tok-2", expires_in=600))
    identity = Token("cli_1", "shh", transport=mint)

    assert identity.token() == "tok-1"
    assert identity.token() == "tok-2"


def test_a_refused_mint_says_which_identity_was_refused():
    """A 401 reads the same whether the id is wrong, the secret is stale, or the
    app may not use this grant — and the reader is holding none of those."""
    mint = Transport(Reply(401, {"error": "invalid_client", "error_description": "client authentication required"}))
    with pytest.raises(Fault) as caught:
        Token("cli_1", "shh", transport=mint).token()

    assert caught.value.status == 401
    assert "cli_1" in str(caught.value)
    assert "invalid_client" in str(caught.value)


def test_the_client_takes_no_bearer():
    """There is no way to hand this SDK a token. That is the point.

    A credential the SDK is handed is a credential nobody rotates, and it says
    nothing about who is calling.
    """
    import inspect

    taken = set(inspect.signature(Client.__init__).parameters)
    assert not taken & {"token", "api_key", "access_token", "key", "bearer"}


def test_a_client_with_no_credential_builds_and_fails_at_the_first_call(monkeypatch):
    """Construction never fails on a missing credential; the first call does.

    There is nothing to exchange, so nothing is sent to IAM and nothing is sent
    unsigned to the gateway — an unsigned call comes back a bare 403, which
    reads as a refusal of the caller rather than the absence of one.
    """
    for name in ("HANZO_CLIENT_ID", "HANZO_CLIENT_SECRET"):
        monkeypatch.delenv(name, raising=False)

    client = Client()
    with pytest.raises(Fault) as caught:
        client.credential.token()
    assert caught.value.status == 0
    assert "HANZO_CLIENT_ID" in str(caught.value)


def test_every_option_falls_back_to_its_environment_variable(monkeypatch):
    monkeypatch.setenv("HANZO_CLIENT_ID", "cli_env")
    monkeypatch.setenv("HANZO_CLIENT_SECRET", "shh_env")
    monkeypatch.setenv("HANZO_BASE_URL", "https://api.acme.internal/")
    monkeypatch.setenv("HANZO_ISSUER_URL", "https://id.acme.internal/")

    client = Client()
    assert client.base == "https://api.acme.internal"
    assert client.issuer == "https://id.acme.internal"
    assert client.resource == "https://api.acme.internal", "the audience follows the endpoint by default"
    assert (client.credential.id, client.credential.secret) == ("cli_env", "shh_env")


# --------------------------------------------------------------------------
# The scope — the credential carries it, so no method takes a user id
# --------------------------------------------------------------------------


def test_as_mints_a_subject_token_from_the_client_s_own_token():
    """`POST https://hanzo.id/v1/iam/tokens/issue?id=<subject>`, no body.

    The subject rides as the `id` query because IAM reads the act grant off the
    token presented, and there is nothing to put in a body.
    """
    mint = Transport(minted("tok-operator"), issued("tok-usr-7"))
    scoped = operator(mint).as_("usr_7")

    assert scoped.credential.token() == "tok-usr-7"
    method, url, headers, body, _ = mint.calls[1]
    assert (method, url) == ("POST", "https://hanzo.id/v1/iam/tokens/issue?id=usr_7")
    assert headers["Authorization"] == "Bearer tok-operator"
    assert body is None


def test_the_subject_is_url_encoded():
    mint = Transport(minted("tok-operator"), issued("tok"))
    operator(mint).as_("acct/42 x&y").credential.token()
    assert mint.calls[1][1] == "https://hanzo.id/v1/iam/tokens/issue?id=acct%2F42+x%26y"


def test_the_act_answer_is_camel_case():
    """The two mints are different endpoints and each keeps its own wire."""
    mint = Transport(minted("tok-operator"), Reply(200, {"access_token": "wrong", "expires_in": 600}))
    with pytest.raises(Fault) as caught:
        operator(mint).as_("usr_7").credential.token()
    assert "usr_7" in str(caught.value)


def test_the_client_s_own_token_never_rides_a_scoped_call():
    """Two credentials on one request are two answers to who is calling."""
    mint = Transport(minted("tok-operator"), issued("tok-usr-7"))
    scoped = operator(mint).as_("usr_7")

    _, _, headers, _, _ = IamApi(scoped)._get_iam_keys_serialize(
        "org_1", _request_auth=None, _content_type=None, _headers=None, _host_index=0
    )
    assert headers["Authorization"] == "Bearer tok-usr-7"
    assert "tok-operator" not in headers["Authorization"]


def test_scoping_does_not_disturb_the_client_it_came_from():
    """Two subjects and the operator hold three credentials, not one shared slot."""
    mint = Transport(minted("tok-operator"), issued("tok-a"), issued("tok-b"))
    boss = operator(mint)
    a, b = boss.as_("usr_a"), boss.as_("usr_b")

    assert a.credential.token() == "tok-a"
    assert b.credential.token() == "tok-b"
    assert boss.credential.token() == "tok-operator"
    assert a.configuration is not b.configuration


def test_a_scoped_client_keeps_the_endpoint_and_the_issuer():
    mint = Transport(minted("tok-operator"))
    boss = Client(credential=Token("cli_1", "shh", transport=mint), base="https://api.acme.internal")
    scoped = boss.as_("usr_7")
    assert (scoped.base, scoped.issuer, scoped.resource) == (boss.base, boss.issuer, boss.resource)


def test_a_scoped_client_answers_the_same_six():
    mint = Transport(minted("tok-operator"))
    scoped = operator(mint).as_("usr_7")
    for capability in ("budget", "policy", "audit", "search", "kb", "graph"):
        assert getattr(scoped, capability).client is scoped


# --------------------------------------------------------------------------
# The call
# --------------------------------------------------------------------------


def test_send_puts_the_endpoint_the_credential_and_the_query_on_one_request():
    mint = Transport(minted("tok-1"))
    calls = Transport(Reply(200, {"plan": "pro"}))
    client = operator(mint, calls)

    reply = client.send("GET", "/v1/allowance", query={"window": "day", "empty": "", "absent": None})

    method, url, headers, body, _ = calls.calls[0]
    assert (method, url) == ("GET", "https://api.hanzo.ai/v1/allowance?window=day")
    assert headers["Authorization"] == "Bearer tok-1"
    assert body is None
    assert reply.status == 200
    assert reply.body == {"plan": "pro"}
    assert reply.request == "req_1", "x-request-id is what joins a call to its audit row"


def test_a_body_carries_its_media_type():
    mint = Transport(minted("tok-1"))
    calls = Transport(Reply(200, {"imported": 1}))
    client = operator(mint, calls)

    client.send("POST", "/v1/knowledge/import", body=b"PK\x03\x04", media="application/octet-stream")
    _, _, headers, body, _ = calls.calls[0]
    assert headers["Content-Type"] == "application/octet-stream"
    assert body == b"PK\x03\x04"


def test_a_401_re_mints_once_and_replays():
    """A rotated token costs a round trip, not an error the caller has to handle."""
    mint = Transport(minted("tok-stale"), minted("tok-fresh"))
    calls = Transport(Reply(401, {"code": "unauthorized"}), Reply(200, {"plan": "pro"}))
    client = operator(mint, calls)

    assert client.send("GET", "/v1/allowance").status == 200
    assert len(mint.calls) == 2, "the stale token was not dropped"
    assert calls.calls[0][2]["Authorization"] == "Bearer tok-stale"
    assert calls.calls[1][2]["Authorization"] == "Bearer tok-fresh"


def test_a_second_401_is_the_server_saying_no():
    mint = Transport(minted("tok-1"), minted("tok-2"))
    calls = Transport(Reply(401, {"code": "unauthorized"}), Reply(401, {"code": "unauthorized"}))
    client = operator(mint, calls)

    assert client.send("GET", "/v1/allowance").status == 401
    assert len(calls.calls) == 2


def test_a_read_that_was_refused_raises_rather_than_answering_nothing():
    mint = Transport(minted("tok-1"), minted("tok-1"))
    calls = Transport(
        Reply(401, {"code": "unauthorized", "detail": "sign in to view the audit trail"}),
        Reply(401, {"code": "unauthorized", "detail": "sign in to view the audit trail"}),
    )
    client = operator(mint, calls)

    with pytest.raises(Fault) as caught:
        client.audit.list()
    assert caught.value.status == 401
    assert "sign in to view the audit trail" in str(caught.value)


def test_a_generated_operation_that_was_held_raises_rather_than_returning_nothing():
    """No operation declares a schema for the hold, so the generated deserializer
    answers it with `None` — a queued call reading as one that succeeded and
    returned nothing. The six answer the same hold as an arm."""
    mint = Transport(minted("tok-1"))
    client = operator(mint)
    held = {"status": "held", "id": "apr_7f3", "clause": "iam.keys", "reason": "key reads are reviewed"}

    with pytest.raises(Held) as caught:
        client.response_deserialize(Reply(202, held), {"200": "object"})

    assert (caught.value.id, caught.value.clause) == ("apr_7f3", "iam.keys")
    assert caught.value.request == "req_1"


def test_a_202_that_is_not_a_hold_passes_through_to_the_generated_deserializer():
    """A dozen long-running operations answer 202 with their own schema."""
    mint = Transport(minted("tok-1"))
    response = operator(mint).response_deserialize(Reply(202, {"id": "dep_1", "status": "queued"}), {"202": "object"})
    assert response.status_code == 202
    assert response.data == {"id": "dep_1", "status": "queued"}
