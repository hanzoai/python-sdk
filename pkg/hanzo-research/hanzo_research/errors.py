"""Errors a call raises, one class a kind of refusal, each carrying the server's own sentence."""

from __future__ import annotations

import json
from typing import Any

__all__ = ["Error", "Denied", "Missing", "Invalid", "Limited", "Unavailable", "refusal"]


class Error(Exception):
    """A call that did not succeed: the HTTP status (0 when no answer came), what the server said, and where."""

    def __init__(self, message: str, status: int = 0, method: str = "", path: str = "", body: Any = None):
        super().__init__(f"{method} {path}: {status}: {message}" if method else message)
        self.message = message
        self.status = status
        self.method = method
        self.path = path
        self.body = body


class Denied(Error):
    """401 or 403: no credential, an expired one, or a caller this org or route does not admit."""


class Missing(Error):
    """404: no such record. A record another org holds reads the same, by design."""


class Invalid(Error):
    """400, 409 or 422: the request does not fit the route; the message names the field."""


class Limited(Error):
    """413 or 429: too large, or too many; `retry` is the server's wait in seconds when it gave one."""

    retry: float | None = None


class Unavailable(Error):
    """502, 503, 504, or no answer at all: retry later."""


def refusal(status: int, raw: bytes, method: str, path: str, retry: float | None = None) -> Error:
    """The typed error for a non-2xx answer, its message read from whichever envelope the server used."""
    body: Any = None
    message = ""
    try:
        body = json.loads(raw)
    except ValueError:
        message = raw[:1024].decode("utf-8", "replace").strip()
    if isinstance(body, dict):
        e = body.get("error")
        if isinstance(e, dict):
            message = str(e.get("message") or e.get("code") or "")
        elif e:
            message = str(e)
        # typed ops answer RFC 7807 ({detail, title}); the blob route and the gateway {error}
        message = message or str(
            body.get("detail") or body.get("message") or body.get("msg") or body.get("title") or ""
        )
    message = message or f"HTTP {status}"
    cls: type[Error] = Error
    if status in (401, 403):
        cls = Denied
    elif status == 404:
        cls = Missing
    elif status in (400, 409, 422):
        cls = Invalid
    elif status in (413, 429):
        cls = Limited
    elif status in (502, 503, 504):
        cls = Unavailable
    err = cls(message, status, method, path, body)
    if isinstance(err, Limited):
        err.retry = retry
    return err
