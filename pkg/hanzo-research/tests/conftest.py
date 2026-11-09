from __future__ import annotations

import os
import sys
from typing import Iterator

import pytest

sys.path.insert(0, os.path.dirname(__file__))

import hanzo_login as login  # noqa: E402
from fake import Server, jwt  # noqa: E402
from hanzo_research import transport  # noqa: E402

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
def quiet(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """No test reads the caller's own credential (key, config, hanzo CLI) or waits out a real backoff."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("HANZO_API_KEY", raising=False)
    monkeypatch.delenv("HANZO_KEY", raising=False)
    monkeypatch.delenv("RESEARCH_BASE", raising=False)
    monkeypatch.delenv("RESEARCH_PROJECT", raising=False)
    monkeypatch.setattr(transport, "WAITS", (0, 0, 0))
    monkeypatch.setattr(login, "cli", lambda: tmp_path / "absent")
    login.forget()


@pytest.fixture
def server() -> Iterator[Server]:
    with Server() as s:
        yield s
