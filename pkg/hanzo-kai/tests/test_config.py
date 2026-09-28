import time
import socket
import asyncio
import logging
import threading
from collections.abc import Callable, Iterator

import httpx
import pytest
from wire import KEY, Wire, Client, reply, refuse
from hanzo_kai import Kai, Noul, AsyncKai, KaiError, RetryPolicy, APITimeoutError, APIConnectionError, constants
from hanzo_kai._log import logger, configure

Build = Callable[..., Client]
QUESTIONS = {"q": Noul(instructions="Is this about billing?")}


def test_settings_from_the_environment(client: Build, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HANZO_API_KEY", "  sk-from-env  ")
    monkeypatch.setenv("HANZO_BASE_URL", "http://localhost:8080/")
    monkeypatch.setenv("KAI_MODEL", "hanzo/kai")
    wire = Wire()
    client(wire, api_key=None).decide("x", QUESTIONS)
    request = wire.requests[0]
    assert request.headers["authorization"] == "Bearer sk-from-env"
    assert str(request.url) == "http://localhost:8080/v1/decisions"
    assert wire.json()["model"] == "hanzo/kai"


def test_arguments_win_over_the_environment(client: Build, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HANZO_API_KEY", "sk-from-env")
    monkeypatch.setenv("HANZO_BASE_URL", "http://localhost:8080")
    monkeypatch.setenv("KAI_MODEL", "hanzo/kai")
    wire = Wire()
    client(wire, api_key="sk-argument", base_url="https://decide.example.com/", model="kai").decide("x", QUESTIONS)
    request = wire.requests[0]
    assert request.headers["authorization"] == "Bearer sk-argument"
    assert str(request.url) == "https://decide.example.com/v1/decisions"
    assert wire.json()["model"] == "kai"


def test_defaults_and_blank_environment(client: Build, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HANZO_BASE_URL", "   ")
    monkeypatch.setenv("KAI_MODEL", "")
    wire = Wire()
    client(wire).decide("x", QUESTIONS)
    assert str(wire.requests[0].url) == "https://api.hanzo.ai/v1/decisions"
    assert wire.json()["model"] == "kai"
    assert (constants.DEFAULT_BASE_URL, constants.DEFAULT_MODEL, constants.DEFAULT_TIMEOUT) == (
        "https://api.hanzo.ai",
        "kai",
        60.0,
    )


@pytest.mark.parametrize("kind", [Kai, AsyncKai])
def test_missing_or_unusable_key(kind: type[Kai] | type[AsyncKai], monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(KaiError, match="HANZO_API_KEY"):
        kind()
    monkeypatch.setenv("HANZO_API_KEY", " \t ")
    with pytest.raises(KaiError, match="HANZO_API_KEY"):
        kind()
    for bad in ("", "sk-has space", "sk-new\nline", "sk-ключ", "sk-\x00"):
        with pytest.raises(KaiError):
            kind(bad)


@pytest.mark.parametrize("base", ["api.hanzo.ai", "ftp://api.hanzo.ai", "https://", "http://[::1"])
def test_unusable_base_url(base: str) -> None:
    with pytest.raises(KaiError, match="base URL"):
        Kai(KEY, base_url=base)


@pytest.mark.parametrize("timeout", [0, -1, float("nan"), float("inf"), True, "60"])
def test_unusable_timeout(timeout: object) -> None:
    with pytest.raises(KaiError, match="timeout"):
        Kai(KEY, timeout=timeout)  # type: ignore[arg-type]


def test_transport_and_http_client_exclude_each_other() -> None:
    with pytest.raises(ValueError):
        Kai(KEY, transport=httpx.MockTransport(Wire()), http_client=httpx.Client())
    with pytest.raises(ValueError):
        AsyncKai(KEY, transport=httpx.MockTransport(Wire()), http_client=httpx.AsyncClient())


def timeouts(wire: Wire) -> list[dict[str, float]]:
    return [request.extensions["timeout"] for request in wire.requests]


def test_timeout_per_attempt(client: Build) -> None:
    wire = Wire()
    client(wire).decide("x", QUESTIONS)
    client(wire, timeout=5).decide("x", QUESTIONS)
    client(wire, timeout=5).decide("x", QUESTIONS, timeout=2.5)
    client(wire).decide("x", QUESTIONS, timeout=httpx.Timeout(3.0, connect=1.0))
    assert timeouts(wire) == [
        {"connect": 60.0, "read": 60.0, "write": 60.0, "pool": 60.0},
        {"connect": 5.0, "read": 5.0, "write": 5.0, "pool": 5.0},
        {"connect": 2.5, "read": 2.5, "write": 2.5, "pool": 2.5},
        {"connect": 1.0, "read": 3.0, "write": 3.0, "pool": 3.0},
    ]
    with pytest.raises(KaiError, match="timeout"):
        client(wire).decide("x", QUESTIONS, timeout=0)


def test_supplied_http_client() -> None:
    wire = Wire()
    http = httpx.Client(transport=httpx.MockTransport(wire), timeout=7.0)
    with Kai(KEY, http_client=http) as kai:
        kai.decide("x", QUESTIONS)
    assert timeouts(wire) == [{"connect": 7.0, "read": 7.0, "write": 7.0, "pool": 7.0}]
    assert http.is_closed

    async def run() -> httpx.AsyncClient:
        http = httpx.AsyncClient(transport=httpx.MockTransport(wire), timeout=httpx.Timeout(9.0))
        async with AsyncKai(KEY, http_client=http) as kai:
            await kai.decide("x", QUESTIONS)
        return http

    assert asyncio.run(run()).is_closed
    assert timeouts(wire)[-1] == {"connect": 9.0, "read": 9.0, "write": 9.0, "pool": 9.0}


def test_context_managers_close() -> None:
    with Kai(KEY, transport=httpx.MockTransport(Wire())) as kai:
        pass
    assert kai._http.is_closed

    async def run() -> AsyncKai:
        async with AsyncKai(KEY, transport=httpx.MockTransport(Wire())) as kai:
            pass
        return kai

    assert asyncio.run(run())._http.is_closed


@pytest.fixture
def silent() -> Iterator[str]:
    """A loopback server that accepts connections and never answers."""
    server = socket.create_server(("127.0.0.1", 0))
    held: list[socket.socket] = []
    stop = threading.Event()

    def accept() -> None:
        server.settimeout(0.1)
        while not stop.is_set():
            try:
                held.append(server.accept()[0])
            except TimeoutError:
                continue

    thread = threading.Thread(target=accept, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.getsockname()[1]}"
    stop.set()
    thread.join()
    for connection in held:
        connection.close()
    server.close()


def test_a_real_timeout(silent: str) -> None:
    started = time.monotonic()
    with (
        Kai(KEY, base_url=silent, timeout=0.2, retry=RetryPolicy(max_retries=0)) as kai,
        pytest.raises(APITimeoutError) as caught,
    ):
        kai.decide("x", QUESTIONS)
    assert time.monotonic() - started < 5
    assert caught.value.timeout == 0.2
    assert isinstance(caught.value, TimeoutError)

    async def run() -> None:
        async with AsyncKai(KEY, base_url=silent, timeout=0.2, retry=RetryPolicy(max_retries=0)) as kai:
            await kai.decide("x", QUESTIONS)

    with pytest.raises(APITimeoutError):
        asyncio.run(run())


def test_a_refused_connection() -> None:
    port = socket.create_server(("127.0.0.1", 0))
    address = f"http://127.0.0.1:{port.getsockname()[1]}"
    port.close()
    with Kai(KEY, base_url=address, retry=RetryPolicy(max_retries=0)) as kai, pytest.raises(APIConnectionError):
        kai.decide("x", QUESTIONS)


@pytest.mark.parametrize(
    ("value", "level"),
    [
        (None, logging.WARNING),
        ("debug", logging.DEBUG),
        ("INFO", logging.INFO),
        (" warn ", logging.WARNING),
        ("error", logging.ERROR),
        ("off", logging.CRITICAL + 1),
        ("loud", logging.WARNING),
    ],
)
def test_log_level_from_the_environment(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, value: str | None, level: int
) -> None:
    if value is not None:
        monkeypatch.setenv("KAI_LOG_LEVEL", value)
    try:
        with caplog.at_level(logging.WARNING):
            configure()
        assert logger.level == level
        assert ("names no level" in caplog.text) == (value == "loud")
    finally:
        monkeypatch.delenv("KAI_LOG_LEVEL", raising=False)
        configure()


def test_secrets_never_reach_the_log(client: Build, caplog: pytest.LogCaptureFixture, slept: list[float]) -> None:
    secret = "sk-very-secret-0042"
    wire = Wire(
        refuse(httpx.ConnectError, "dropped"),
        reply(headers={"Set-Cookie": "session=server-secret", "x-request-id": "req-7"}),
    )
    kai = client(
        wire,
        api_key=secret,
        headers={
            "Cookie": "session=cookie-secret",
            "X-Api-Key": "other-secret",
            "X-Session-Token": "token-secret",
            "X-Team": "ops",
        },
    )
    with caplog.at_level(logging.DEBUG, logger="hanzo_kai"):
        kai.decide("x", QUESTIONS)
    text = caplog.text
    for leaked in (secret, "cookie-secret", "other-secret", "token-secret", "server-secret"):
        assert leaked not in text
    assert "<redacted>" in text and "'x-team': 'ops'" in text
    assert "retry 1 of 2" in text and "req-7" in text
    assert wire.requests[1].headers["authorization"] == f"Bearer {secret}"
