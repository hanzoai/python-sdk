"""One ranked result set over everything the org has stored.

Degradation is stated, never silent. A leg that is down produces the surviving
legs' results plus a :class:`Backend` entry carrying the failure — it is not a
refusal and not an exception. A caller that ignores :attr:`Hits.partial` reads a
truncated corpus as a complete one, so `partial` is a field, never a shrug.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Tuple, Optional, Sequence
from datetime import timedelta
from dataclasses import dataclass

from hanzoai import answer
from hanzoai.wire import Reply, real, rows, text, number
from hanzoai.answer import Answer

if TYPE_CHECKING:  # the capability layer is written over the wire, not the generated client
    from hanzoai.client import Client

__all__ = ["Match", "Backend", "Hit", "Hits", "Search"]


@dataclass(frozen=True)
class Match:
    """One leg's own view of a hit: where it ranked it and what it scored it.

    More than one match means the legs agreed, which is why the hit outranks one
    a single leg found. `score` is the leg's native score, on that leg's own
    scale, reported for explanation and never used in ranking.
    """

    backend: str = ""
    rank: int = 0
    score: float = 0.0

    @classmethod
    def read(cls, body: Any) -> "Match":
        return cls(backend=text(body, "backend"), rank=number(body, "rank"), score=real(body, "score"))


@dataclass(frozen=True)
class Backend:
    """One leg's report. `status` is ok, degraded, disabled or skipped.

    Four distinct operational facts, never collapsed: it answered; it is
    configured and failed, and `error` says how; this deployment never
    provisioned it; the request's mode excluded it. Only `degraded` is a fault.
    """

    name: str = ""
    status: str = ""
    hits: int = 0
    took: timedelta = timedelta()
    error: str = ""

    @classmethod
    def read(cls, body: Any) -> "Backend":
        return cls(
            name=text(body, "name"),
            status=text(body, "status"),
            hits=number(body, "hits"),
            took=timedelta(milliseconds=number(body, "took_ms")),
            error=text(body, "error"),
        )


@dataclass(frozen=True)
class Hit:
    """One document. `score` compares only within this response.

    It is a reciprocal-rank fusion sum: comparable against the other hits here,
    never across queries and never against a backend's own score, which stays in
    `matched`. `corpus` is provenance — read it to say where a hit came from,
    not to branch on.
    """

    id: str = ""
    corpus: str = ""
    kind: str = ""
    title: str = ""
    url: str = ""
    project: str = ""
    score: float = 0.0
    matched: Tuple[Match, ...] = ()

    @classmethod
    def read(cls, body: Any) -> "Hit":
        return cls(
            id=text(body, "id"),
            corpus=text(body, "corpus"),
            kind=_kind(text(body, "doctype")),
            title=text(body, "title"),
            url=text(body, "url"),
            project=text(body, "project"),
            score=real(body, "score"),
            matched=tuple(Match.read(m) for m in rows(body, "matched")),
        )


@dataclass(frozen=True)
class Hits:
    """The fused result set and the honesty signal that says how complete it is.

    `status` is ``ok`` (every consulted leg answered), ``partial`` (at least one
    failed and these are the survivors' results) or ``unavailable`` (every leg
    failed and the emptiness is stated rather than implied). `partial` is that
    same fact as the one boolean a caller must read.
    """

    status: str = ""
    partial: bool = False
    mode: str = ""
    items: Tuple[Hit, ...] = ()
    backends: Tuple[Backend, ...] = ()
    took: timedelta = timedelta()

    @classmethod
    def read(cls, body: Any) -> "Hits":
        status = text(body, "status")
        return cls(
            status=status,
            partial=status != "ok",
            mode=text(body, "mode"),
            items=tuple(Hit.read(h) for h in rows(body, "hits")),
            backends=tuple(Backend.read(b) for b in rows(body, "backends")),
            took=timedelta(milliseconds=number(body, "took_ms")),
        )


class Search:
    """`c.search`."""

    def __init__(self, client: "Client") -> None:
        self.client = client

    def find(
        self,
        query: str,
        *,
        mode: str = "auto",
        project: Optional[str] = None,
        kinds: Optional[Sequence[str]] = None,
        index: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Answer[Hits]:
        """Search everything the org has stored.

        `mode` is ``auto``, ``text``, ``semantic`` or ``hybrid``. The modes name
        retrieval kinds, not backends: a caller chooses how to search, never
        which subsystem answers. `kinds` narrows to ``page``, ``memory`` or
        ``source`` — the same word :attr:`hanzoai.kb.Doc.kind` uses.

        The rerank leg runs through the AI gateway, which is metered, so this
        can come back refused on money. That is an arm, not an exception.
        """
        reply: Reply = self.client.send(
            "POST",
            "/v1/search",
            body={
                "query": query,
                "mode": mode,
                "project": project,
                "doctypes": [_doctype(k) for k in kinds] if kinds else None,
                "index": index,
                "limit": limit,
                "offset": offset,
            },
        )
        return answer.read(reply, Hits.read)


def _doctype(kind: str) -> str:
    """``page`` addresses ``kb.page``. A caller who already wrote the address keeps it."""
    return kind if "." in kind else "kb." + kind


def _kind(doctype: str) -> str:
    """The inverse, so `kind` means the same word here as it does in `kb`.

    A hit out of the code corpus carries its own type and keeps it — only the
    knowledge address is unwrapped.
    """
    return doctype[3:] if doctype.startswith("kb.") else doctype
