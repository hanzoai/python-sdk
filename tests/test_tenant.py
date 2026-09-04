"""The tenant fabric: one operator credential, N isolated customers.

Nothing here touches the network. The stub below has the same `request()`
signature as :class:`hanzoai.cloud.rest.RESTClientObject`, which is the only
thing the client and the mint ever call, so these exercise the real code path
and only the socket is missing.
"""

import json

import pytest

from hanzoai import (
    Done,
    Held,
    Grant,
    Client,
    Approval,
    result,
    unwrap,
    is_done,
    is_held,
)
from hanzoai.cloud import IamApi, Configuration
from hanzoai.cloud.exceptions import ApiException


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
        self.headers = headers or {"content-type": "application/json"}

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
        self.calls.append((method, url, dict(headers or {}), body))
        assert self.replies, "the client made more requests than the test staged"
        return self.replies.pop(0)


def issued(token, expires_in=600):
    """IAM's answer, in IAM's casing."""
    return Reply(200, {"accessToken": token, "expiresIn": expires_in})


# --------------------------------------------------------------------------
# The mint
# --------------------------------------------------------------------------


def test_the_mint_is_iam_s_own_host_and_the_subject_is_a_query():
    """`POST https://hanzo.id/v1/iam/tokens/issue?id=<subject>`, no body.

    Three things this pins, each of which fails silently if it drifts: the host
    is IAM's, not the platform API's, which 404s this path; the path carries the
    `iam` segment; and the subject rides as the `id` query, because IAM reads
    the grant off the key and there is nothing to put in a body.
    """
    transport = Transport(issued("tok-user-42"))
    grant = Grant("hk-operator", "user_42", transport=transport)

    assert grant.token() == "tok-user-42"

    method, url, headers, body = transport.calls[0]
    assert method == "POST"
    assert url == "https://hanzo.id/v1/iam/tokens/issue?id=user_42"
    assert headers["Authorization"] == "Bearer hk-operator"
    assert body is None


def test_the_subject_is_url_encoded():
    """An externalId is whatever the operator filed the member under."""
    transport = Transport(issued("tok"))
    Grant("hk-operator", "acct/42 x&y", transport=transport).token()
    _, url, _, _ = transport.calls[0]
    assert url == "https://hanzo.id/v1/iam/tokens/issue?id=acct%2F42+x%26y"


def test_the_issuer_is_overridable_for_a_private_estate():
    transport = Transport(issued("tok"))
    Grant("hk-operator", "user_42", issuer="https://id.acme.internal/", transport=transport).token()
    _, url, _, _ = transport.calls[0]
    assert url == "https://id.acme.internal/v1/iam/tokens/issue?id=user_42"


def test_the_response_is_camel_case():
    """`accessToken` / `expiresIn`. snake_case here reads as no token at all."""
    transport = Transport(Reply(200, {"access_token": "wrong", "expires_in": 600}))
    grant = Grant("hk-operator", "user_42", transport=transport)

    with pytest.raises(ApiException) as caught:
        grant.token()
    assert "user_42" in str(caught.value)


def test_the_token_is_cached_to_expiry():
    """One mint serves every call until the token nears expiry."""
    transport = Transport(issued("tok-1"))
    grant = Grant("hk-operator", "user_42", transport=transport)

    assert [grant.token() for _ in range(5)] == ["tok-1"] * 5
    assert len(transport.calls) == 1


def test_a_token_inside_the_skew_is_not_reused():
    """A token about to die is replaced before it rides a request, not after.

    `expiresIn: 10` is inside the 30s skew, so it is spent on arrival.
    """
    transport = Transport(issued("tok-1", expires_in=10), issued("tok-2", expires_in=600))
    grant = Grant("hk-operator", "user_42", transport=transport)

    assert grant.token() == "tok-1"
    assert grant.token() == "tok-2"
    assert len(transport.calls) == 2


def test_invalidate_forces_the_next_read_to_mint():
    transport = Transport(issued("tok-1"), issued("tok-2"))
    grant = Grant("hk-operator", "user_42", transport=transport)

    assert grant.token() == "tok-1"
    grant.invalidate()
    assert grant.token() == "tok-2"


def test_a_refused_mint_is_a_typed_error():
    """Non-2xx carries the status and the body, never a bare string."""
    transport = Transport(Reply(403, {"error": "no act grant on this key"}))
    grant = Grant("hk-operator", "user_42", transport=transport)

    with pytest.raises(ApiException) as caught:
        grant.token()
    assert caught.value.status == 403
    assert "no act grant" in caught.value.body


# --------------------------------------------------------------------------
# The scope
# --------------------------------------------------------------------------


def operator(transport):
    """An operator client whose pool — and so whose mint — is the stub."""
    client = Client(Configuration(host="https://api.hanzo.ai", access_token="hk-operator"))
    client.rest_client = transport
    return client


def test_as_puts_the_minted_token_on_the_request():
    """End to end: serialize a real operation off a scoped client.

    The generated serializer reads the credential through
    `Configuration.auth_settings()`, so this asserts the whole path — mint,
    cache, `auth_settings`, `_apply_auth_params` — and not a field we set.
    """
    transport = Transport(issued("tok-user-42"))
    client = operator(transport).as_("user_42")

    _, _, headers, _, _ = IamApi(client)._get_iam_keys_serialize(
        "org_1", _request_auth=None, _content_type=None, _headers=None, _host_index=0
    )
    assert headers["Authorization"] == "Bearer tok-user-42"


def test_the_operator_key_never_rides_a_scoped_client():
    transport = Transport(issued("tok-user-42"))
    client = operator(transport).as_("user_42")

    assert client.grant.subject == "user_42"
    _, _, headers, _, _ = IamApi(client)._get_iam_keys_serialize(
        "org_1", _request_auth=None, _content_type=None, _headers=None, _host_index=0
    )
    assert "hk-operator" not in headers["Authorization"]


def test_scoping_does_not_disturb_the_operator():
    """Two subjects and the operator hold three credentials, not one shared slot."""
    transport = Transport(issued("tok-a"), issued("tok-b"))
    boss = operator(transport)
    a, b = boss.as_("user_a"), boss.as_("user_b")

    assert a.grant.token() == "tok-a"
    assert b.grant.token() == "tok-b"
    assert boss.configuration.access_token == "hk-operator"
    assert a.configuration is not b.configuration


def test_scoping_without_a_credential_refuses():
    with pytest.raises(ApiException):
        Client(Configuration(host="https://api.hanzo.ai")).as_("user_42")


def test_a_401_re_mints_once_and_retries():
    """A rotated token costs a round trip, not an error the caller handles."""
    mint = Transport(issued("tok-stale"), issued("tok-fresh"))
    calls = Transport(Reply(401, {"error": "expired"}), Reply(200, {"ok": True}))

    client = Client(
        Configuration(host="https://api.hanzo.ai"),
        grant=Grant("hk-operator", "user_42", transport=mint),
    )
    client.rest_client = calls

    # What `param_serialize` did on the way in: the request rides the token the
    # grant was holding.
    staged = client.grant.token()
    assert staged == "tok-stale"

    response = client.call_api(
        "GET",
        "https://api.hanzo.ai/v1/keys",
        {"Authorization": "Bearer " + staged},
    )

    assert response.status == 200
    assert len(mint.calls) == 2, "the stale token was not dropped"
    assert calls.calls[0][2]["Authorization"] == "Bearer tok-stale"
    assert calls.calls[1][2]["Authorization"] == "Bearer tok-fresh"


def test_a_401_is_retried_once_and_then_stands():
    """Two 401s are an answer, not a loop."""
    mint = Transport(issued("tok-1"), issued("tok-2"))
    calls = Transport(Reply(401, {"error": "expired"}), Reply(401, {"error": "expired"}))

    client = Client(
        Configuration(host="https://api.hanzo.ai"),
        grant=Grant("hk-operator", "user_42", transport=mint),
    )
    client.rest_client = calls

    assert client.call_api("GET", "https://api.hanzo.ai/v1/keys", {}).status == 401
    assert len(calls.calls) == 2


def test_an_unscoped_client_does_not_re_mint():
    """No grant, nothing to re-mint: the 401 is the caller's to deal with."""
    calls = Transport(Reply(401, {"error": "bad key"}))
    client = Client(Configuration(host="https://api.hanzo.ai", access_token="hk-operator"))
    client.rest_client = calls

    assert client.call_api("GET", "https://api.hanzo.ai/v1/keys", {}).status == 401
    assert len(calls.calls) == 1


# --------------------------------------------------------------------------
# The held result
# --------------------------------------------------------------------------

HELD = {
    "status": "held",
    "id": "apr_7f3",
    "clause": "memory.remember",
    "reason": "writes to a customer profile need review",
}


def deserialize(reply, types=None):
    client = Client(Configuration(host="https://api.hanzo.ai", access_token="hk-operator"))
    return client.response_deserialize(reply, types or {"200": "object"})


def test_a_held_call_raises_rather_than_returning_nothing():
    """No operation declares a schema for the hold, so the generated
    deserializer answers it with `None` — a queued call reading as a call that
    succeeded and returned nothing. This is the whole point of the fabric."""
    with pytest.raises(Held) as caught:
        deserialize(Reply(202, HELD))

    held = caught.value
    assert held.approval == Approval(
        id="apr_7f3", clause="memory.remember", reason="writes to a customer profile need review"
    )
    assert held.status == 202
    assert "memory.remember" in str(held)


def test_a_202_that_is_not_a_hold_passes_through():
    """A dozen long-running operations answer 202 with their own schema.

    The body is the discriminator, not the status code. Blanket-raising on 202
    would break every deploy and build call in the document.
    """
    response = deserialize(Reply(202, {"id": "dep_1", "status": "queued"}), {"202": "object"})
    assert response.status_code == 202
    assert response.data == {"id": "dep_1", "status": "queued"}


def test_result_turns_the_raise_into_a_value():
    def call():
        raise Held(Approval.held(HELD), body=json.dumps(HELD))

    r = result(call)
    assert is_held(r)
    assert not is_done(r)
    assert (r.id, r.clause, r.reason) == ("apr_7f3", "memory.remember", "writes to a customer profile need review")


def test_result_carries_a_completed_call():
    r = result(lambda: {"id": "card_1"})
    assert is_done(r)
    assert unwrap(r) == {"id": "card_1"}


def test_unwrapping_a_hold_raises_and_names_the_approval():
    """The one thing a caller must not be able to do is read a hold as a value."""
    with pytest.raises(Held) as caught:
        unwrap(Approval.held(HELD))
    assert caught.value.approval.id == "apr_7f3"


def test_the_two_arms_share_no_member():
    """`Approval` has no `value` and `Done` has no `id`.

    Reading either without checking `status` first fails at the attribute
    instead of quietly handing back a half-answer — which is as close as Python
    gets to the sum type a compiler would refuse to let you ignore.
    """
    assert not hasattr(Approval.held(HELD), "value")
    assert not hasattr(Done({"id": "card_1"}), "id")


def test_an_approval_read_back_is_the_same_shape():
    """`GET /v1/approvals/{id}` answers in the field names of the 202."""
    fetched = Approval.held(json.dumps(HELD).encode())
    assert fetched == Approval.held(HELD)


def test_a_resolved_approval_is_not_a_hold():
    assert Approval.held({"status": "approved", "id": "apr_7f3"}) is None
    assert Approval.held(b"") is None
    assert Approval.held("not json") is None


def test_a_hold_with_fields_omitted_still_has_all_four():
    assert Approval.held({"status": "held", "id": "apr_7f3"}) == Approval(id="apr_7f3", clause="", reason="")


# --------------------------------------------------------------------------
# The typed error
# --------------------------------------------------------------------------


def test_a_non_2xx_is_a_typed_error_carrying_status_and_body():
    with pytest.raises(ApiException) as caught:
        deserialize(Reply(500, {"error": "boom"}))
    assert caught.value.status == 500
    assert json.loads(caught.value.body) == {"error": "boom"}
