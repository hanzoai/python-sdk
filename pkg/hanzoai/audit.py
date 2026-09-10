"""The org's own trail, newest first. Read-only by construction.

There is no write method. The server writes the trail; an SDK that offered a
write would let a caller forge its own evidence.

Every field of a :class:`Filter` is optional and every one narrows within the
caller's own org, which is the validated principal's and can never be widened
by a request.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Tuple, Iterator, Optional
from datetime import datetime
from dataclasses import replace, dataclass

from hanzoai.page import Page
from hanzoai.wire import rows, text, number, instant

if TYPE_CHECKING:  # the capability layer is written over the wire, not the generated client
    from hanzoai.client import Client

__all__ = ["Event", "Filter", "Audit", "SIZE"]

#: Events per page when a filter names no size.
SIZE = 100


@dataclass(frozen=True)
class Event:
    """One row of the trail.

    Six wire fields are renamed and each rename buys something: `actor` because
    ``sub`` is token jargon and the reader wants who did it; `at` because one
    word for an instant is shared with :attr:`hanzoai.graph.Fact.at`; `id`
    because it sits beside `resource` and the compound says nothing more;
    `request` because it is the same word as :attr:`hanzoai.Ok.request`, which
    is what makes a call findable in the trail; `ip` and `agent` because there
    is no other ip and no other agent on the row.

    `result` is ``success``, ``deny`` or ``error``. `home` is present only on a
    cross-org action and marks it as an impersonation.
    """

    seq: int = 0
    org: str = ""
    actor: str = ""
    email: str = ""
    home: str = ""
    action: str = ""
    resource: str = ""
    id: str = ""
    method: str = ""
    path: str = ""
    result: str = ""
    status: int = 0
    reason: str = ""
    at: Optional[datetime] = None
    request: str = ""
    ip: str = ""
    agent: str = ""

    @classmethod
    def read(cls, body: Any) -> "Event":
        return cls(
            seq=number(body, "seq"),
            org=text(body, "org"),
            actor=text(body, "sub"),
            email=text(body, "email"),
            home=text(body, "home"),
            action=text(body, "action"),
            resource=text(body, "resource"),
            id=text(body, "resourceId"),
            method=text(body, "method"),
            path=text(body, "path"),
            result=text(body, "result"),
            status=number(body, "status"),
            reason=text(body, "reason"),
            at=instant(body.get("time")) if isinstance(body, dict) else None,
            request=text(body, "requestId"),
            ip=text(body, "sourceIp"),
            agent=text(body, "userAgent"),
        )


@dataclass(frozen=True)
class Filter:
    """What to narrow the trail to. A value, because two methods take it.

    `request` is the ``x-request-id`` every :data:`hanzoai.Answer` carries, and
    it is what joins a call to the row the server wrote for it. Cloud's filter
    declares no such field although every row has one, so it is matched here
    after a page arrives — correct, and a scan. Every other field is sent.
    """

    actor: str = ""
    action: str = ""
    resource: str = ""
    id: str = ""
    result: str = ""
    since: Optional[datetime] = None
    until: Optional[datetime] = None
    request: str = ""
    size: int = 0
    page: int = 0

    def query(self, page: int = 0) -> dict:
        """The query cloud reads, in cloud's own spelling.

        A term nobody set is left out: the route's own defaults are 100 rows and
        page 1, so sending them again asks for the same trail in a different
        request.
        """
        return {
            "sub": self.actor,
            "action": self.action,
            "resource": self.resource,
            "resourceId": self.id,
            "result": self.result,
            "since": self.since,
            "until": self.until,
            "pageSize": self.size or None,
            "p": page or self.page or None,
        }

    def matches(self, event: Event) -> bool:
        """Whether `event` survives the narrowing cloud could not do."""
        return not self.request or event.request == self.request


class Audit:
    """`c.audit`."""

    def __init__(self, client: "Client") -> None:
        self.client = client

    def list(self, filter: Optional[Filter] = None) -> Page[Event]:
        """One page of the trail.

        `total` is the server's count for the filter the server applied. Where
        :attr:`Filter.request` narrows further, `items` are this page's matches
        and the total still counts what the server was asked.
        """
        f = filter or Filter()
        events, total = self._page(f, f.page)
        return Page(items=tuple(e for e in events if f.matches(e)), total=total)

    def all(self, filter: Optional[Filter] = None) -> Iterator[Event]:
        """Every event the filter matches, page after page.

        Asks for page 1 at the filter's size and stops when a page comes back
        empty or when the server's own rows reach the total it reported. What is
        counted is what the server sent, not what survived
        :attr:`Filter.request` here — a page where nothing matched is not the
        end of the trail.

        The size is pinned so the walk advances by a page it knows the length
        of, rather than by whatever the route defaults to today.
        """
        f = filter or Filter()
        walked = replace(f, size=f.size or SIZE)
        seen = 0
        page = f.page or 1
        while True:
            events, total = self._page(walked, page)
            for event in events:
                if f.matches(event):
                    yield event
            seen += len(events)
            if not events or (total and seen >= total):
                return
            page += 1

    def _page(self, filter: Filter, page: int) -> Tuple[Tuple[Event, ...], int]:
        """One page as the server sent it, before any narrowing of ours."""
        body = self.client.read("GET", "/v1/audit", query=filter.query(page))
        return tuple(Event.read(r) for r in rows(body, "data")), number(body, "total")
