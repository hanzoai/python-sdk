"""The one rule that turns an HTTP answer into an arm.

Nothing here touches the network or the generated client. `answer.read` takes a
:class:`hanzoai.wire.Reply` — a status, a decoded body and a request id — which
is exactly what the client hands it.
"""

import pytest

from hanzoai import Ok, Cure, Held, Fault, Denied, answer
from hanzoai.wire import Reply

REFUSAL = {
    "type": "about:blank",
    "title": "Payment Required",
    "status": 402,
    "detail": "the wallet is empty",
    "code": "insufficient_balance",
    "cure": [{"kind": "credit", "url": "/v1/billing"}],
}

HOLD = {"status": "held", "id": "apr_7f3", "clause": "graph.assert", "reason": "a person reviews graph writes"}


def reply(status, body=None, request="req_1"):
    return Reply(status=status, body=body, request=request)


# --------------------------------------------------------------------------
# The three arms
# --------------------------------------------------------------------------


def test_a_2xx_is_ok_and_carries_what_it_decoded():
    a = answer.read(reply(200, {"n": 7}), lambda b: b["n"])
    assert isinstance(a, Ok)
    assert (a.status, a.value, a.request) == ("ok", 7, "req_1")
    assert a.denied is None and a.held is None


def test_a_402_is_denied_whatever_the_code_says():
    """Money refused is money refused. The code names which refusal, not whether."""
    a = answer.read(reply(402, REFUSAL), _never)

    assert a.denied is a
    assert isinstance(a, Denied)
    assert (a.code, a.reason, a.request) == ("insufficient_balance", "the wallet is empty", "req_1")
    assert a.cures == (Cure(kind="credit", url="/v1/billing"),)


def test_the_second_402_body_reads_the_same():
    """Cloud answers a refusal two ways. A caller learns neither.

    `errmap` answers the RFC 9457 envelope with `code` and `detail`; the money
    gate answers `{error, product, reason, message, cure}`, where `error` is
    always `payment_required` and `message` is the sentence. Its own `reason` —
    "unpaid", "unresolved" — names the admit leg that failed rather than
    explaining anything to a person, so it is dropped. Both bodies land on the
    same arm with the same fields filled, so no capability sniffs for a shape.
    """
    a = answer.read(
        reply(
            402,
            {
                "error": "payment_required",
                "product": "inference",
                "reason": "unpaid",
                "message": "no active subscription for inference and no prepaid credit",
                "cure": [{"kind": "raise-cap", "url": "/v1/billing/limits"}],
            },
        ),
        _never,
    )
    assert (a.code, a.product) == ("payment_required", "inference")
    assert a.reason == "no active subscription for inference and no prepaid credit"
    assert a.cures == (Cure(kind="raise-cap", url="/v1/billing/limits"),)


@pytest.mark.parametrize("code", ["spend_cap_exceeded", "insufficient_balance"])
def test_a_403_carrying_a_refusal_code_is_denied(code):
    """The workaround for one cloud defect, and the only reason a code list exists.

    Cloud spells "no validated principal" as 403 forbidden, so the status alone
    cannot say whether the caller was refused or was never let in. These two
    codes say it was refused, and they are the two cloud emits. Once cloud
    answers 401 for the other case, the rule collapses to "402 or 403" and this
    list goes.
    """
    a = answer.read(reply(403, {"code": code, "detail": "no"}), _never)
    assert isinstance(a, Denied)
    assert a.code == code


@pytest.mark.parametrize("code", ["policy_denied", "entitlement_required"])
def test_a_403_carrying_a_code_cloud_does_not_emit_decided_nothing(code):
    """No route in cloud writes either word.

    A 403 an SDK read as denied on a code no server sends would hand a caller a
    cure for a refusal nobody made — and the same 403 is what an unauthenticated
    call collects.
    """
    with pytest.raises(Fault):
        answer.read(reply(403, {"code": code, "detail": "no"}), _never)


def test_a_bare_403_decided_nothing_and_raises():
    """`{"code": "forbidden"}` is what an unauthenticated call collects.

    Nothing was decided about the request, so there is no arm to read. This is
    the live body of `GET /v1/allowance` with no credential.
    """
    with pytest.raises(Fault) as caught:
        answer.read(reply(403, {"code": "forbidden", "detail": "allowance: a validated principal is required"}), _never)
    assert caught.value.status == 403
    assert "a validated principal is required" in str(caught.value)
    assert "req_1" in str(caught.value), "the request id has to survive into the error"


def test_a_202_carrying_a_hold_is_held():
    a = answer.read(reply(202, HOLD), _never)

    assert a.held is a
    assert isinstance(a, Held)
    assert (a.id, a.clause, a.reason) == ("apr_7f3", "graph.assert", "a person reviews graph writes")
    assert a.denied is None


def test_a_202_that_is_not_a_hold_is_ok():
    """The body decides, never the status code.

    A dozen long-running operations answer 202 for "accepted, working on it".
    Reading 202 as a hold would break every one of them.
    """
    a = answer.read(reply(202, {"id": "dep_1", "status": "queued"}), lambda b: b["id"])
    assert isinstance(a, Ok)
    assert a.value == "dep_1"


@pytest.mark.parametrize("status", [401, 400, 404, 409, 429, 500, 503])
def test_a_status_with_no_decision_in_it_raises(status):
    with pytest.raises(Fault) as caught:
        answer.read(reply(status, {"detail": "no"}), _never)
    assert caught.value.status == status


# --------------------------------------------------------------------------
# What the arms let you do
# --------------------------------------------------------------------------


def test_reading_the_value_of_a_refusal_raises_the_refusal():
    """The whole safety property: you cannot reach past an arm you did not check."""
    a = answer.read(reply(402, REFUSAL), _never)
    with pytest.raises(Denied) as caught:
        _ = a.value
    assert caught.value.code == "insufficient_balance"


def test_reading_the_value_of_a_hold_raises_the_hold():
    a = answer.read(reply(202, HOLD), _never)
    with pytest.raises(Held) as caught:
        _ = a.value
    assert caught.value.id == "apr_7f3"


def test_the_arms_are_matched_structurally():
    """Three frozen types with a discriminant, so `match` sees them apart."""
    seen = []
    for a in (
        answer.read(reply(200, {}), lambda _: "ran"),
        answer.read(reply(402, REFUSAL), _never),
        answer.read(reply(202, HOLD), _never),
    ):
        match a:
            case Ok(value=v):
                seen.append(v)
            case Denied(code=code):
                seen.append(code)
            case Held(id=id):
                seen.append(id)
    assert seen == ["ran", "insufficient_balance", "apr_7f3"]


def test_every_arm_carries_the_request_id():
    """The join to the audit trail. It is on all three or the composition fails."""
    arms = [
        answer.read(reply(200, {}), lambda _: None),
        answer.read(reply(402, REFUSAL), _never),
        answer.read(reply(202, HOLD), _never),
    ]
    assert [a.request for a in arms] == ["req_1"] * 3


def test_a_refusal_says_what_it_is_when_printed():
    a = answer.read(reply(402, REFUSAL), _never)
    assert str(a) == "insufficient_balance: the wallet is empty"
    assert str(answer.read(reply(202, HOLD), _never)) == "held on graph.assert: a person reviews graph writes"


# --------------------------------------------------------------------------
# The plain read
# --------------------------------------------------------------------------


def test_a_plain_read_answers_its_body():
    assert answer.value(reply(200, {"plan": "pro"})) == {"plan": "pro"}


def test_a_plain_read_that_failed_raises_rather_than_answering_nothing():
    with pytest.raises(Fault) as caught:
        answer.value(reply(401, {"code": "unauthorized", "detail": "sign in to view the audit trail"}))
    assert caught.value.status == 401


def _never(body):
    raise AssertionError("a refused or held answer must not decode a value")
