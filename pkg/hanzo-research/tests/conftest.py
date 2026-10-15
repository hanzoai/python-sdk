from __future__ import annotations

import os
import sys
from typing import Iterator

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from fake import Server, jwt  # noqa: E402
from hanzo_research import wire, transport  # noqa: E402

HANZO = jwt(
    {
        "sub": "u-1",
        "owner": "hanzo",
        "orgs": [{"org": "hanzo", "role": "admin"}, {"org": "lux", "role": "admin"}],
        "exp": 4102444800,
    }
)
SUPER = jwt({"sub": "u-0", "owner": "admin", "orgs": [{"org": "admin", "role": "admin"}], "exp": 4102444800})
ATLAS = jwt({"sub": "u-2", "owner": "hanzo", "orgs": [{"org": "hanzo"}], "project": "atlas", "exp": 4102444800})


@pytest.fixture(autouse=True)
def quiet(monkeypatch: pytest.MonkeyPatch) -> None:
    """No test reads the caller's own credential or waits out a real backoff."""
    monkeypatch.delenv("HANZO_API_KEY", raising=False)
    monkeypatch.delenv("RESEARCH_BASE", raising=False)
    monkeypatch.delenv("RESEARCH_PROJECT", raising=False)
    monkeypatch.setattr(transport, "WAITS", (0, 0, 0))
    monkeypatch.setattr(wire, "token", lambda: "")


@pytest.fixture
def server() -> Iterator[Server]:
    with Server() as s:
        yield s
