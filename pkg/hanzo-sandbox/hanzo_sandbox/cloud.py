"""Client for the sandboxes cloud serves at /v1/sandboxes.

The package is named for the cloud app it speaks to — cloud `apps/sandbox` is
`hanzo-sandbox` here — so the two move together and there is one name per
concept across the two languages.

This is the REMOTE half. `hanzo_sandbox.sandbox` is the local one: unshare,
namespaces, a boundary drawn on this machine. They share a word and nothing
else, so they stay separate modules rather than one class that means both.

The API key carries the org. cloud resolves it with principal.OrgOf(user, org),
which returns nothing unless a VALIDATED principal came with the request — "no
validated principal, so the org claim is untrusted" — and the gateway strips
client-supplied X-Org-Id before a handler ever sees it. So a caller sends its
key and nothing else; an org passed by hand would be ignored at best.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any

DEFAULT_BASE_URL = "https://api.hanzo.ai"


class SandboxError(RuntimeError):
    """A sandbox call that cloud refused, carrying the status it refused with."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(f"{status}: {message}")
        self.status = status
        self.message = message


@dataclass(frozen=True)
class Sandbox:
    """One sandbox, as cloud reports it.

    `runtime` is the isolation boundary the sandbox GOT, which is not always the
    one it asked for — cloud answers with what it could actually give. Empty
    means the node's default, which is an answer and not a gap.
    """

    id: str
    org: str = ""
    kind: str = ""
    cls: str = ""
    project: str = ""
    status: str = ""
    image: str = ""
    runtime: str = ""
    volume: str = ""
    error: str = ""
    created_at: int = 0
    last_used_at: int = 0
    expires_at: int = 0

    @classmethod
    def of(cls, d: dict[str, Any]) -> Sandbox:
        return cls(
            id=d.get("id", ""),
            org=d.get("org", ""),
            kind=d.get("kind", ""),
            cls=d.get("class", ""),
            project=d.get("project", ""),
            status=d.get("status", ""),
            image=d.get("image", ""),
            runtime=d.get("runtime", ""),
            volume=d.get("volume", ""),
            error=d.get("error", ""),
            created_at=d.get("createdAt", 0),
            last_used_at=d.get("lastUsedAt", 0),
            expires_at=d.get("expiresAt", 0),
        )

    @property
    def running(self) -> bool:
        return self.status == "running"


@dataclass(frozen=True)
class Exec:
    """What a command left behind."""

    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""

    @property
    def ok(self) -> bool:
        return self.exit_code == 0


@dataclass
class Sandboxes:
    """Cloud's sandboxes, over HTTP.

        boxes = Sandboxes(api_key=os.environ["HANZO_API_KEY"])   # pk-… or sk-…
        box = boxes.create(image="ghcr.io/hanzoai/base:latest")
        boxes.exec(box.id, argv=["python", "-c", "print(1)"])
        boxes.delete(box.id)
    """

    api_key: str = field(default_factory=lambda: os.environ.get("HANZO_API_KEY", ""))
    base_url: str = field(default_factory=lambda: os.environ.get("HANZO_API_URL", DEFAULT_BASE_URL))
    timeout: float = 30.0

    def list(self) -> list[Sandbox]:
        got = self._call("GET", "")
        rows = got.get("sandboxes", got) if isinstance(got, dict) else got
        return [Sandbox.of(r) for r in (rows or [])]

    def get(self, id: str) -> Sandbox:
        return Sandbox.of(self._call("GET", f"/{id}"))

    def create(self, *, image: str = "", kind: str = "", cls: str = "", project: str = "") -> Sandbox:
        body = {"image": image, "kind": kind, "class": cls, "project": project}
        return Sandbox.of(self._call("POST", "", {k: v for k, v in body.items() if v}))

    def delete(self, id: str) -> None:
        self._call("DELETE", f"/{id}")

    def exec(
        self,
        id: str,
        *,
        argv: list[str] | None = None,
        command: str = "",
        stdin: str = "",
        dir: str = "",
        timeout_sec: int = 0,
    ) -> Exec:
        """Run something. `argv` runs it directly; `command` runs it through a shell."""
        if not argv and not command:
            raise ValueError("exec needs argv or command")
        body: dict[str, Any] = {}
        if argv:
            body["argv"] = argv
        if command:
            body["command"] = command
        if stdin:
            body["stdin"] = stdin
        if dir:
            body["dir"] = dir
        if timeout_sec:
            body["timeoutSec"] = timeout_sec
        got = self._call("POST", f"/{id}/exec", body)
        return Exec(
            exit_code=got.get("exitCode", got.get("exit_code", 0)),
            stdout=got.get("stdout", ""),
            stderr=got.get("stderr", ""),
        )

    def read(self, id: str, path: str) -> str:
        return self._call("GET", f"/{id}/fs?path={urllib.parse.quote(path)}").get("content", "")

    def write(self, id: str, path: str, content: str) -> None:
        self._call("POST", f"/{id}/fs", {"path": path, "content": content})

    def _call(self, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
        url = f"{self.base_url.rstrip('/')}/v1/sandboxes{path}"
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Content-Type", "application/json")
        # An empty bearer is worse than none: it reads as a credential to anything
        # counting headers, and hides "no key configured" behind whatever the
        # server says about a bad one.
        if self.api_key:
            req.add_header("Authorization", f"Bearer {self.api_key}")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                raw = r.read()
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:400]
            raise SandboxError(e.code, detail or e.reason) from None
        return json.loads(raw) if raw else {}
