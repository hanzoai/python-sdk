"""Reading what the server sent.

One decoded JSON object arrives and the six capabilities take fields out of it.
These are the readers. Each answers the type its name says, and answers that
type's empty value when the field is absent or carries something else — cloud
omits an empty field, so absent and empty are one fact and neither is a fault.

Instants cross the wire as RFC 3339 strings, except where cloud counts seconds
instead of stamping them. :func:`instant` reads both and answers a
timezone-aware ``datetime``; :func:`stamp` writes the RFC 3339 form back.
"""

from __future__ import annotations

from typing import Any, List, Tuple, Optional
from datetime import datetime, timezone
from dataclasses import dataclass

__all__ = ["Reply", "text", "number", "real", "flag", "rows", "strings", "instant", "stamp", "query"]


@dataclass(frozen=True)
class Reply:
    """One call's answer: the status, the decoded body, and the id that names it.

    `request` is ``x-request-id``, which every response carries. It is the join
    to :attr:`hanzoai.audit.Event.request`, so it rides every arm of
    :data:`hanzoai.Answer` and every fault raised from a reply.
    """

    status: int
    body: Any = None
    request: str = ""
    #: Retry-After in seconds: how long the server asked the caller to wait
    #: before trying again, and 0 when it named no wait.
    retry_after: float = 0


def query(params: Optional[dict]) -> dict:
    """The query cloud reads: nothing nobody asked for, and instants stamped.

    A `None` or an empty string is not a narrowing, so it is left out rather
    than sent as a filter matching everything with an empty value.
    """
    return {
        k: stamp(v) if isinstance(v, datetime) else v for k, v in (params or {}).items() if v is not None and v != ""
    }


def text(body: Any, key: str) -> str:
    """The string at `key`, or ``""``."""
    v = body.get(key) if isinstance(body, dict) else None
    return v if isinstance(v, str) else ""


def number(body: Any, key: str) -> int:
    """The integer at `key`, or ``0``. A JSON number arrives as a float when it has a point."""
    v = body.get(key) if isinstance(body, dict) else None
    return int(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else 0


def real(body: Any, key: str) -> float:
    """The float at `key`, or ``0.0``. Scores are reals; counts are not."""
    v = body.get(key) if isinstance(body, dict) else None
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else 0.0


def flag(body: Any, key: str) -> bool:
    """The boolean at `key`, or `False`."""
    v = body.get(key) if isinstance(body, dict) else None
    return v is True


def rows(body: Any, key: str) -> List[Any]:
    """The list at `key`, or ``[]``."""
    v = body.get(key) if isinstance(body, dict) else None
    return v if isinstance(v, list) else []


def strings(body: Any, key: str) -> Tuple[str, ...]:
    """The list of strings at `key`, with anything that is not one dropped."""
    return tuple(v for v in rows(body, key) if isinstance(v, str))


def instant(v: Any) -> Optional[datetime]:
    """An instant from RFC 3339, or from unix seconds where cloud counts.

    Answers `None` for an absent, empty or unreadable value, which is the
    honest reading: a time nobody recorded is not the epoch.
    """
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return datetime.fromtimestamp(v, timezone.utc) if v else None
    if not isinstance(v, str) or not v:
        return None
    try:
        t = datetime.fromisoformat(v)
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


def stamp(t: Optional[datetime]) -> str:
    """RFC 3339, UTC, `Z`-suffixed. A naive datetime is read as UTC.

    Cloud refuses an instant more than five minutes ahead of its own clock, so
    a caller stamping a fact from a fast machine gets a refusal, not a silent
    correction.
    """
    if t is None:
        return ""
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    return t.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
