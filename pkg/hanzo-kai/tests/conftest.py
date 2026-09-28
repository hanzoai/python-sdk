import time
import asyncio
from typing import Any
from collections.abc import Callable

import pytest
from wire import Wire, Client
from hanzo_kai import constants


@pytest.fixture(autouse=True)
def clean(monkeypatch: pytest.MonkeyPatch) -> None:
    """No test reads the settings of the shell it runs in."""
    for name in (constants.API_KEY_ENV, constants.BASE_URL_ENV, constants.DEFAULT_MODEL_ENV, constants.LOG_LEVEL_ENV):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture(params=["sync", "async"])
def client(request: pytest.FixtureRequest) -> Callable[..., Client]:
    """Builds a client of each flavour over a wire, so every test that takes it runs twice."""

    def build(wire: Wire, **options: Any) -> Client:
        return Client(request.param, wire, **options)

    return build


@pytest.fixture
def slept(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    """Records the waits between retries instead of waiting them."""
    waits: list[float] = []

    async def nap(seconds: float) -> None:
        waits.append(seconds)

    monkeypatch.setattr(time, "sleep", waits.append)
    monkeypatch.setattr(asyncio, "sleep", nap)
    return waits
