from typing import Any
from collections.abc import Callable

import pytest
from wire import Wire, Client, reply
from hanzo_kai import (
    Noul,
    APIError,
    KaiError,
    RetryPolicy,
    NotFoundError,
    RateLimitError,
    APITimeoutError,
    BadRequestError,
    APIConnectionError,
    AuthenticationError,
    InternalServerError,
    PaymentRequiredError,
    PermissionDeniedError,
    UnprocessableEntityError,
    APIResponseValidationError,
)

Build = Callable[..., Client]
ONCE = RetryPolicy(max_retries=0)
QUESTIONS = {"q": Noul(instructions="Is this about billing?")}


@pytest.mark.parametrize(
    ("status", "kind"),
    [
        (400, BadRequestError),
        (401, AuthenticationError),
        (402, PaymentRequiredError),
        (403, PermissionDeniedError),
        (404, NotFoundError),
        (405, APIError),
        (409, APIError),
        (422, UnprocessableEntityError),
        (429, RateLimitError),
        (500, InternalServerError),
        (502, InternalServerError),
        (503, InternalServerError),
    ],
)
def test_status_maps_to_its_class(client: Build, status: int, kind: type[APIError]) -> None:
    sent = {"error": {"code": status, "message": f"status {status} said this"}}
    with pytest.raises(APIError) as caught:
        client(Wire(reply(status, sent, headers={"x-request-id": "req-9"})), retry=ONCE).decide("x", QUESTIONS)
    error = caught.value
    assert type(error) is kind
    assert (error.status, error.code, error.message) == (status, status, f"status {status} said this")
    assert error.body == sent
    assert error.request_id == "req-9"
    assert error.endpoint == "POST https://api.hanzo.ai/v1/decisions"
    assert str(error) == f"{status} status {status} said this (request req-9)"


BODIES: list[tuple[int, dict[str, Any] | None, str | None, str, Any]] = [
    # the decision runtime
    (
        400,
        {"error": {"code": 400, "message": "question 'q': no 'instructions'; add the text the model should answer"}},
        None,
        "question 'q': no 'instructions'; add the text the model should answer",
        400,
    ),
    (422, {"error": {"code": 422, "message": "options over the window"}}, None, "options over the window", 422),
    # the gateway, error object
    (
        402,
        {"error": {"message": "no plan or balance", "type": "billing", "code": "payment_required"}},
        None,
        "no plan or balance",
        "payment_required",
    ),
    # the gateway, status and msg
    (
        401,
        {
            "status": "error",
            "msg": "API key validation failed: API key sk-invali… does not resolve — mint a new one at https://console.hanzo.ai/api-keys",
            "data": None,
            "data2": None,
        },
        None,
        "API key validation failed: API key sk-invali… does not resolve — mint a new one at https://console.hanzo.ai/api-keys",
        None,
    ),
    # plain text
    (404, None, "not found", "not found", None),
    # empty
    (503, None, "", "Service Unavailable", None),
    # JSON that names no sentence
    (500, {"trace": "abc"}, None, '{"trace": "abc"}', None),
    # the decision runtime, over reach
    (
        422,
        {
            "error": {
                "code": "state_too_long",
                "message": "state and question need more tokens than the checkpoint reads",
            }
        },
        None,
        "state and question need more tokens than the checkpoint reads",
        "state_too_long",
    ),
    # FastAPI, as /v1/systemone sends it
    (400, {"detail": "Unknown model: jev-latest"}, None, "Unknown model: jev-latest", None),
    (401, {"detail": "invalid API key"}, None, "invalid API key", None),
    (
        422,
        {
            "detail": [
                {"loc": ["body", "questions", "q", "criteria"], "msg": "at most 255 labels", "type": "too_long"},
                {"loc": ["body", "state"], "msg": "field required", "type": "missing"},
            ]
        },
        None,
        "questions.q.criteria: at most 255 labels; state: field required",
        "too_long",
    ),
    # every reach refusal names what is over, on either path
    *(
        row
        for code, message, loc in (
            (
                "question_too_long",
                "question 'q' takes 900 tokens with its type line",
                ["body", "questions", "q", "noul", "instructions"],
            ),
            (
                "option_too_long",
                "option refund of question 'q' takes 600 tokens",
                ["body", "questions", "q", "choice", "criteria", "refund"],
            ),
            ("request_too_long", "the body is over 16777216 bytes", ["body"]),
        )
        for row in (
            (422, {"error": {"code": code, "message": message}}, None, message, code),
            (
                422,
                {"detail": [{"loc": loc, "msg": message, "type": code}]},
                None,
                ": ".join(filter(None, [".".join(loc[1:]), message])),
                code,
            ),
        )
    ),
    # a schema refusal keeps the status as its code
    (
        422,
        {"error": {"code": 422, "message": "questions: at least 1 question"}},
        None,
        "questions: at least 1 question",
        422,
    ),
]


@pytest.mark.parametrize(("status", "sent", "text", "message", "code"), BODIES)
def test_the_message_is_the_servers(
    client: Build, status: int, sent: dict[str, Any] | None, text: str | None, message: str, code: Any
) -> None:
    answer = reply(status, text=text) if text is not None else reply(status, sent)
    with pytest.raises(APIError) as caught:
        client(Wire(answer), retry=ONCE).decide("x", QUESTIONS)
    assert caught.value.message == message
    assert caught.value.code == code
    assert caught.value.body == (sent if text is None else (text or None))
    assert caught.value.request_id is None
    assert str(caught.value) == f"{status} {message}"


def test_retry_after_is_read(client: Build) -> None:
    with pytest.raises(RateLimitError) as caught:
        client(Wire(reply(429, {"error": {"message": "slow down"}}, headers={"Retry-After": "7"})), retry=ONCE).decide(
            "x", QUESTIONS
        )
    assert caught.value.retry_after == 7.0
    with pytest.raises(RateLimitError) as caught:
        client(
            Wire(reply(429, {"error": {"message": "slow down"}}, headers={"retry-after-ms": "1500"})), retry=ONCE
        ).decide("x", QUESTIONS)
    assert caught.value.retry_after == 1.5
    with pytest.raises(BadRequestError) as caught:
        client(Wire(reply(400, {"error": {"message": "no"}})), retry=ONCE).decide("x", QUESTIONS)
    assert caught.value.retry_after is None


def test_hierarchy() -> None:
    for kind in (
        BadRequestError,
        AuthenticationError,
        PaymentRequiredError,
        PermissionDeniedError,
        NotFoundError,
        UnprocessableEntityError,
        RateLimitError,
        InternalServerError,
        APIResponseValidationError,
    ):
        assert issubclass(kind, APIError) and issubclass(kind, KaiError)
    assert issubclass(APIConnectionError, KaiError) and issubclass(APIConnectionError, ConnectionError)
    assert not issubclass(APIConnectionError, APIError)
    assert issubclass(APITimeoutError, APIConnectionError) and issubclass(APITimeoutError, TimeoutError)


def test_errors_built_by_hand() -> None:
    error = RateLimitError(
        429, {"error": {"message": "slow down", "code": 429}}, {"retry-after": "2", "x-request-id": "r"}
    )
    assert (error.status, error.message, error.code, error.retry_after, error.request_id) == (
        429,
        "slow down",
        429,
        2.0,
        "r",
    )
    assert repr(error) == "RateLimitError('429 slow down (request r)')"
    assert APIError(418, None).message == "I'm a teapot"
    assert APIError(400, {"error": "bare string"}).message == "bare string"
    assert APIError(400, {"message": "top level"}).message == "top level"
    assert APIError(400, {"error": {"code": True}}).code is None
    assert APIError(502, "x" * 300).message == "x" * 200 + "…"
    assert APIError(500, {"long": "y" * 300}).message.endswith("…")
    timeout = APITimeoutError(1.5)
    assert str(timeout) == "the request timed out after 1.5 s" and timeout.timeout == 1.5
    assert str(APIConnectionError("no route")) == "no route"
    validation = APIResponseValidationError(200, {}, {}, "answers.q.noul")
    assert validation.field_path == "answers.q.noul" and "answers.q.noul" in validation.message
