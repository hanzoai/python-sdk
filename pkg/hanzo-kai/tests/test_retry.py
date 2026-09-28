import time
import random
from email.utils import formatdate
from collections.abc import Callable

import httpx
import pytest
from wire import Wire, Client, reply, refuse
from hanzo_kai import (
    Noul,
    KaiError,
    RetryPolicy,
    RateLimitError,
    APITimeoutError,
    BadRequestError,
    APIConnectionError,
    InternalServerError,
)

Build = Callable[..., Client]
QUESTIONS = {"q": Noul(instructions="Is this about billing?")}


def counts(wire: Wire) -> list[str | None]:
    return [request.headers.get("x-kai-retry-count") for request in wire.requests]


@pytest.mark.parametrize("status", [408, 409, 429, 500, 502, 503, 504, 599])
def test_retried_statuses(client: Build, slept: list[float], status: int) -> None:
    failure = reply(status, {"error": {"code": status, "message": "try again"}})
    wire = Wire(failure, failure, reply())
    d = client(wire).decide("x", QUESTIONS)
    assert d.nouls["billing"].noul == 0.746
    assert counts(wire) == [None, "1", "2"]
    assert len(slept) == 2
    assert 0.375 <= slept[0] <= 0.5 and 0.75 <= slept[1] <= 1.0


@pytest.mark.parametrize("status", [400, 401, 402, 403, 404, 405, 422])
def test_statuses_not_retried(client: Build, slept: list[float], status: int) -> None:
    wire = Wire(reply(status, {"error": {"code": status, "message": "no"}}))
    with pytest.raises(Exception) as caught:
        client(wire).decide("x", QUESTIONS)
    assert getattr(caught.value, "status", None) == status
    assert len(wire.requests) == 1 and slept == []


def test_gives_up_with_the_last_error(client: Build, slept: list[float]) -> None:
    wire = Wire(
        reply(503, {"error": {"code": 503, "message": "first"}}),
        reply(502, {"error": {"code": 502, "message": "last"}}),
    )
    with pytest.raises(InternalServerError) as caught:
        client(wire).decide("x", QUESTIONS)
    assert caught.value.message == "last" and caught.value.status == 502
    assert len(wire.requests) == 3 and len(slept) == 2


@pytest.mark.parametrize(
    ("headers", "wait"),
    [
        ({"Retry-After": "3"}, 3.0),
        ({"Retry-After": "0"}, 0.0),
        ({"retry-after-ms": "250"}, 0.25),
        ({"retry-after-ms": "250", "Retry-After": "9"}, 0.25),
        ({"Retry-After": "3600"}, 60.0),
        ({"retry-after-ms": "120000"}, 60.0),
    ],
)
def test_retry_after_is_honoured_up_to_a_minute(
    client: Build, slept: list[float], headers: dict[str, str], wait: float
) -> None:
    wire = Wire(reply(429, {"error": {"message": "slow down"}}, headers=headers), reply())
    client(wire).decide("x", QUESTIONS)
    assert slept == [wait]


def test_retry_after_as_a_date(client: Build, slept: list[float]) -> None:
    wire = Wire(
        reply(503, {"error": {"message": "busy"}}, headers={"Retry-After": formatdate(time.time() + 30, usegmt=True)}),
        reply(),
    )
    client(wire).decide("x", QUESTIONS)
    assert 28 <= slept[0] <= 30


@pytest.mark.parametrize("value", ["soon", "-5", "nan", "inf", "Mon, 99 Foo 2026 00:00:00 GMT"])
def test_unreadable_retry_after_falls_back_to_backoff(client: Build, slept: list[float], value: str) -> None:
    wire = Wire(reply(429, {"error": {"message": "slow down"}}, headers={"Retry-After": value}), reply())
    client(wire).decide("x", QUESTIONS)
    assert 0.375 <= slept[0] <= 0.5


def test_retry_after_can_be_ignored(client: Build, slept: list[float]) -> None:
    wire = Wire(reply(429, {"error": {"message": "slow down"}}, headers={"Retry-After": "30"}), reply())
    client(wire, retry=RetryPolicy(respect_retry_after=False)).decide("x", QUESTIONS)
    assert 0.375 <= slept[0] <= 0.5


def test_connection_errors_are_retried(client: Build, slept: list[float]) -> None:
    wire = Wire(refuse(httpx.ConnectError), refuse(httpx.RemoteProtocolError, "closed"), reply())
    assert client(wire).decide("x", QUESTIONS).id.startswith("dec_")
    assert counts(wire) == [None, "1", "2"]

    wire = Wire(refuse(httpx.ConnectError, "connection refused"))
    with pytest.raises(APIConnectionError) as caught:
        client(wire, retry=RetryPolicy(api_connection_error=False)).decide("x", QUESTIONS)
    assert not isinstance(caught.value, APITimeoutError)
    assert "ConnectError: connection refused" in str(caught.value)
    assert isinstance(caught.value.__cause__, httpx.ConnectError)
    assert len(wire.requests) == 1


def test_timeouts_are_retried(client: Build, slept: list[float]) -> None:
    wire = Wire(refuse(httpx.ReadTimeout), refuse(httpx.ConnectTimeout), reply())
    assert client(wire).decide("x", QUESTIONS).id.startswith("dec_")
    assert len(wire.requests) == 3

    wire = Wire(refuse(httpx.ReadTimeout))
    with pytest.raises(APITimeoutError) as caught:
        client(wire, timeout=4, retry=RetryPolicy(api_timeout_error=False)).decide("x", QUESTIONS)
    assert caught.value.timeout == 4.0
    assert len(wire.requests) == 1

    wire = Wire(refuse(httpx.ReadTimeout))
    with pytest.raises(APITimeoutError):
        client(wire).decide("x", QUESTIONS)
    assert len(wire.requests) == 3


def test_per_call_policy(client: Build, slept: list[float]) -> None:
    failure = reply(503, {"error": {"message": "busy"}})
    wire = Wire(failure)
    kai = client(wire, retry=RetryPolicy(max_retries=4))
    with pytest.raises(InternalServerError):
        kai.decide("x", QUESTIONS, retry=RetryPolicy(max_retries=0))
    assert len(wire.requests) == 1
    with pytest.raises(InternalServerError):
        kai.decide("x", QUESTIONS)
    assert len(wire.requests) == 1 + 5

    wire = Wire(reply(418, {"error": {"message": "teapot"}}), reply())
    client(wire).decide("x", QUESTIONS, retry=RetryPolicy(http_statuses={418}))
    assert len(wire.requests) == 2


def test_models_list_retries(client: Build, slept: list[float]) -> None:
    wire = Wire(reply(502, {"error": {"message": "upstream"}}), reply(json_body={"data": []}))
    assert client(wire).models() == []
    assert counts(wire) == [None, "1"]


def test_predicate_and_exceptions(client: Build, slept: list[float]) -> None:
    teapot = reply(400, {"error": {"message": "retry me"}})
    wire = Wire(teapot, reply())
    client(
        wire, retry=RetryPolicy(predicate=lambda error: isinstance(error, BadRequestError) and "retry me" in str(error))
    ).decide("x", QUESTIONS)
    assert len(wire.requests) == 2

    wire = Wire(teapot, reply())
    client(wire, retry=RetryPolicy(exceptions={BadRequestError})).decide("x", QUESTIONS)
    assert len(wire.requests) == 2


def test_budget_stops_a_retry_that_would_end_past_it(client: Build, slept: list[float]) -> None:
    wire = Wire(reply(429, {"error": {"message": "slow down"}}, headers={"Retry-After": "5"}), reply())
    with pytest.raises(RateLimitError):
        client(wire, retry=RetryPolicy(timeout=2.0)).decide("x", QUESTIONS)
    assert len(wire.requests) == 1 and slept == []


def test_backoff_doubles_to_eight_seconds(client: Build, slept: list[float], monkeypatch: pytest.MonkeyPatch) -> None:
    failure = reply(500, {"error": {"message": "down"}})
    monkeypatch.setattr(random, "random", lambda: 0.0)
    with pytest.raises(InternalServerError):
        client(Wire(failure), retry=RetryPolicy(max_retries=7)).decide("x", QUESTIONS)
    assert slept == [0.5, 1.0, 2.0, 4.0, 8.0, 8.0, 8.0]
    slept.clear()
    monkeypatch.setattr(random, "random", lambda: 1.0)
    with pytest.raises(InternalServerError):
        client(Wire(failure), retry=RetryPolicy(max_retries=3)).decide("x", QUESTIONS)
    assert slept == [0.375, 0.75, 1.5]
    slept.clear()
    with pytest.raises(InternalServerError):
        client(Wire(failure), retry=RetryPolicy(max_retries=2, backoff_initial=0)).decide("x", QUESTIONS)
    assert slept == [0.0, 0.0]


def test_defaults() -> None:
    policy = RetryPolicy()
    assert (policy.max_retries, policy.backoff_initial, policy.backoff_max, policy.backoff_jitter) == (
        2,
        0.5,
        8.0,
        0.25,
    )
    assert set(policy.http_statuses) == {408, 409, 429, *range(500, 600)}
    assert policy.respect_retry_after and policy.api_connection_error and policy.api_timeout_error
    assert policy.timeout is None and policy.predicate is None and not policy.exceptions


@pytest.mark.parametrize(
    "options",
    [
        {"max_retries": -1},
        {"max_retries": 1.5},
        {"max_retries": True},
        {"backoff_initial": -0.1},
        {"backoff_max": float("inf")},
        {"backoff_jitter": 1.5},
        {"timeout": 0},
        {"timeout": float("nan")},
    ],
)
def test_policy_validation(options: dict[str, object]) -> None:
    with pytest.raises(KaiError):
        RetryPolicy(**options)  # type: ignore[arg-type]
