"""Refusals the engine states, as exceptions.

The engine answers an error as ``{"error": "...", "code": <int>}`` — ``code``
is a NUMBER here, not the ``status`` string the rest of the Hanzo API uses, so
a generic client that reads ``status`` sees nothing. `raise_for` is the one
place that shape is read.
"""

from __future__ import annotations


class TasksError(Exception):
    """An error the engine reported, carrying its numeric code."""

    def __init__(self, message: str, code: int = 0) -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class Denied(TasksError):
    """No validated principal, or one carrying no org (401/403).

    The surface fails closed: a token that names no org is refused rather than
    served the shared unscoped store.
    """


class NotFound(TasksError):
    """No such activity in this namespace (404)."""


class Terminal(TasksError):
    """The activity already completed, failed or was canceled (409).

    Reported rather than swallowed: a second terminal call means two workers
    believe they own the same run, which is worth surfacing.
    """


def raise_for(status: int, body: object) -> None:
    """Raise the exception a non-2xx answer stands for."""
    message = str(body)
    code = status
    if isinstance(body, dict):
        message = str(body.get("error", body))
        raw = body.get("code")
        if isinstance(raw, int):
            code = raw
    if status in (401, 403):
        raise Denied(message, code)
    if status == 404:
        raise NotFound(message, code)
    if status == 409:
        raise Terminal(message, code)
    raise TasksError(message, code)
