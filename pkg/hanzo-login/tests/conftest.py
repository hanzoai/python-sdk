"""A machine with nothing on it but what a test puts there: an empty HOME, no key in the
environment, and a stub ``hanzo`` shell script standing in for ~/.local/bin/hanzo."""

from __future__ import annotations

import json
import stat
import shlex
import base64
from pathlib import Path

import pytest
import hanzo_login as login


def jwt(claims: dict) -> str:
    def part(obj: dict) -> str:
        return base64.urlsafe_b64encode(json.dumps(obj).encode()).decode().rstrip("=")

    return f"{part({'alg': 'none'})}.{part(claims)}.sig"


class Machine:
    def __init__(self, root: Path, monkeypatch: pytest.MonkeyPatch):
        self.home = root / "home"
        self.home.mkdir()
        self.bin = root / "bin"
        self.bin.mkdir()
        self.log = root / "argv.log"
        self.monkeypatch = monkeypatch

    def hanzo(self, answers: dict[str, tuple[int, str, str]]) -> Path:
        """Install a stub CLI. ``answers`` maps an argv ("auth token --as a/b") to (exit, stdout, stderr)."""
        cases = "".join(
            f"  {shlex.quote(argv)}) printf '%s' {shlex.quote(out)}; printf '%s' {shlex.quote(err)} >&2; exit {code};;\n"
            for argv, (code, out, err) in answers.items()
        )
        script = (
            f'#!/bin/sh\necho "$*" >> {shlex.quote(str(self.log))}\n'
            f'case "$*" in\n{cases}  *) echo "unknown: $*" >&2; exit 2;;\nesac\n'
        )
        exe = self.bin / "hanzo"
        exe.write_text(script)
        exe.chmod(exe.stat().st_mode | stat.S_IXUSR)
        self.monkeypatch.setattr(login, "cli", lambda: exe)
        return exe

    def config(self, key: str) -> None:
        (self.home / ".hanzo").mkdir(exist_ok=True)
        (self.home / ".hanzo" / "config.json").write_text(json.dumps({"apiKey": key}))

    def runs(self) -> list[str]:
        return self.log.read_text().splitlines() if self.log.exists() else []


@pytest.fixture
def machine(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Machine:
    m = Machine(tmp_path, monkeypatch)
    monkeypatch.setenv("HOME", str(m.home))
    monkeypatch.delenv("HANZO_API_KEY", raising=False)
    monkeypatch.delenv("HANZO_KEY", raising=False)
    # no CLI unless a test installs one; never one found on PATH
    monkeypatch.setattr(login, "cli", lambda: m.bin / "absent")
    login.forget()
    login.use(None)
    yield m
    login.forget()
    login.use(None)
