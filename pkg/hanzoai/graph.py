"""Assertions with provenance and time.

Nothing overwrites anything. A retraction is an assertion, a superseded claim
and the one that superseded it both stay readable, and which of them wins is a
question you ask — :meth:`Graph.resolve` — rather than a state the store keeps.

`at` is when the thing was so; `seen` is when it became knowable, and defaults
to `at`. Both cross the wire as RFC 3339 and arrive here as `datetime`. Cloud
refuses an `at` more than five minutes ahead of its own clock.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Tuple, Iterable, Optional, Sequence
from datetime import datetime
from dataclasses import dataclass

from hanzoai import (
    wire,  # qualified: this module has its own `text`, the document's
    answer,
)
from hanzoai.wire import Reply
from hanzoai.answer import Answer

if TYPE_CHECKING:  # the capability layer is written over the wire, not the generated client
    from hanzoai.client import Client

__all__ = ["Fact", "Wrote", "Resolution", "Walk", "Triple", "Vocabulary", "Graph"]


@dataclass(frozen=True)
class Fact:
    """One assertion: `entity` `relation` `value`, and who said so, and when.

    `names` declares that `value` is another entity's key, which makes the
    assertion an edge — the only thing :meth:`Graph.walk` follows. `source` and
    `evidence` are the provenance; `confidence` is how sure the source was.
    """

    entity: str = ""
    relation: str = ""
    value: str = ""
    names: bool = False
    at: Optional[datetime] = None
    seen: Optional[datetime] = None
    source: str = ""
    evidence: str = ""
    confidence: float = 0.0

    def write(self) -> Dict[str, Any]:
        """This fact as cloud reads it."""
        return {
            "entity": self.entity,
            "relation": self.relation,
            "value": self.value,
            "names": self.names,
            "at": wire.stamp(self.at),
            "seen": wire.stamp(self.seen),
            "source": self.source,
            "evidence": self.evidence,
            "confidence": self.confidence,
        }

    @classmethod
    def read(cls, body: Any) -> "Fact":
        return cls(
            entity=wire.text(body, "entity"),
            relation=wire.text(body, "relation"),
            value=wire.text(body, "value"),
            names=wire.flag(body, "names"),
            at=wire.instant(body.get("at")) if isinstance(body, dict) else None,
            seen=wire.instant(body.get("seen")) if isinstance(body, dict) else None,
            source=wire.text(body, "source"),
            evidence=wire.text(body, "evidence"),
            confidence=wire.real(body, "confidence"),
        )


@dataclass(frozen=True)
class Wrote:
    """What a batch did, member by member.

    Each fact is judged on its own: one malformed assertion does not discard the
    batch. `reasons` says why the refused ones were refused.
    """

    recorded: int = 0
    duplicate: int = 0
    refused: int = 0
    reasons: Tuple[str, ...] = ()

    @classmethod
    def read(cls, body: Any) -> "Wrote":
        return cls(
            recorded=wire.number(body, "recorded"),
            duplicate=wire.number(body, "duplicate"),
            refused=wire.number(body, "refused"),
            reasons=wire.strings(body, "reasons"),
        )


@dataclass(frozen=True)
class Resolution:
    """Which claim wins, and what argued against it.

    `known` is `False` when nothing has been asserted — an answer, not an error.
    `contested` is `True` only when a conflict claims a value different from the
    winner's; two sources agreeing loudly are not a conflict.
    """

    entity: str = ""
    relation: str = ""
    at: Optional[datetime] = None
    known: bool = False
    winner: Optional[Fact] = None
    conflicts: Tuple[Fact, ...] = ()
    contested: bool = False
    truncated: bool = False

    @classmethod
    def read(cls, body: Any) -> "Resolution":
        winner = body.get("winner") if isinstance(body, dict) else None
        return cls(
            entity=wire.text(body, "entity"),
            relation=wire.text(body, "relation"),
            at=wire.instant(body.get("as_of")) if isinstance(body, dict) else None,
            known=wire.flag(body, "known"),
            winner=Fact.read(winner) if isinstance(winner, dict) else None,
            conflicts=tuple(Fact.read(c) for c in wire.rows(body, "conflicts")),
            contested=wire.flag(body, "contested"),
            truncated=wire.flag(body, "truncated"),
        )


@dataclass(frozen=True)
class Walk:
    """The entities a walk reached. `bound` is the ceiling it was allowed."""

    entities: Tuple[str, ...] = ()
    depth: int = 0
    bound: int = 0
    truncated: bool = False

    @classmethod
    def read(cls, body: Any) -> "Walk":
        return cls(
            entities=wire.strings(body, "entities"),
            depth=wire.number(body, "depth"),
            bound=wire.number(body, "bound"),
            truncated=wire.flag(body, "truncated"),
        )


@dataclass(frozen=True)
class Triple:
    """What a document states, before anyone decides to record it.

    `section` is where in the document it was found.
    """

    subject: str = ""
    predicate: str = ""
    object: str = ""
    names: bool = False
    section: int = 0

    @classmethod
    def read(cls, body: Any) -> "Triple":
        return cls(
            subject=wire.text(body, "subject"),
            predicate=wire.text(body, "predicate"),
            object=wire.text(body, "object"),
            names=wire.flag(body, "names"),
            section=wire.number(body, "section"),
        )


@dataclass(frozen=True)
class Vocabulary:
    """The relations in use, and the ordering that decides a conflict."""

    relations: Tuple[str, ...] = ()
    rule: Tuple[str, ...] = ()
    bound: int = 0

    @classmethod
    def read(cls, body: Any) -> "Vocabulary":
        return cls(
            relations=wire.strings(body, "relations"),
            rule=wire.strings(body, "rule"),
            bound=wire.number(body, "bound"),
        )


class Graph:
    """`c.graph`."""

    def __init__(self, client: "Client") -> None:
        self.client = client

    def assert_(self, facts: Iterable[Fact]) -> Answer[Wrote]:
        """Record assertions. The trailing underscore is PEP 8's escape for a keyword.

        Every member is judged on its own, so the three counts have to add up to
        what was sent. A batch that does not is a transport fault — the request
        and the answer are about different sets of facts — and raises rather
        than pretending to be an :class:`hanzoai.Ok`.
        """
        batch = tuple(facts)
        reply: Reply = self.client.send("POST", "/v1/graph", body={"assertions": [f.write() for f in batch]})
        a = answer.read(reply, Wrote.read)
        if a.denied is None and a.held is None:
            wrote = a.value
            counted = wrote.recorded + wrote.duplicate + wrote.refused
            if counted != len(batch):
                raise answer.fault(
                    Reply(
                        status=reply.status,
                        body="{0} assertions sent, {1} accounted for".format(len(batch), counted),
                        request=reply.request,
                    )
                )
        return a

    def read(
        self,
        *,
        entity: Optional[str] = None,
        relation: Optional[str] = None,
        value: Optional[str] = None,
        at: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> Tuple[Fact, ...]:
        """Assertions by key. Resolves nothing and withholds nothing.

        A superseded claim and the one that superseded it both appear.
        """
        body = self.client.read(
            "GET",
            "/v1/graph",
            query={"entity": entity, "relation": relation, "value": value, "as_of": at, "limit": limit},
        )
        return tuple(Fact.read(f) for f in wire.rows(body, "assertions"))

    def find(
        self,
        query: str,
        *,
        relation: Optional[str] = None,
        at: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> Tuple[Fact, ...]:
        """Assertions by text. The same word as :meth:`hanzoai.search.Search.find`,
        because it is the same act on a different corpus."""
        body = self.client.read(
            "GET",
            "/v1/graph/search",
            query={"q": query, "relation": relation, "as_of": at, "limit": limit},
        )
        return tuple(Fact.read(f) for f in wire.rows(body, "assertions"))

    def resolve(self, entity: str, relation: str, at: Optional[datetime] = None) -> Resolution:
        """Which claim about `entity`'s `relation` wins, as of `at`."""
        return Resolution.read(
            self.client.read(
                "POST",
                "/v1/graph/resolve",
                body={"entity": entity, "relation": relation, "as_of": wire.stamp(at)},
            )
        )

    def walk(
        self,
        seeds: Sequence[str],
        *,
        relation: Optional[str] = None,
        direction: str = "out",
        depth: Optional[int] = None,
        at: Optional[datetime] = None,
    ) -> Walk:
        """The entities reachable from `seeds`. Only edges are followed.

        `direction` is ``out``, ``in`` or ``both``.
        """
        return Walk.read(
            self.client.read(
                "POST",
                "/v1/graph/neighbors",
                body={
                    "seeds": list(seeds),
                    "relation": relation,
                    "direction": direction,
                    "depth": depth,
                    "as_of": wire.stamp(at),
                },
            )
        )

    def extract(
        self,
        text: str,
        *,
        source: str = "",
        subject: str = "",
        at: Optional[datetime] = None,
    ) -> Tuple[Triple, ...]:
        """Read what a document states, without recording any of it."""
        body = self.client.read("POST", "/v1/graph/extract", body=_source(text, source, subject, at))
        return tuple(Triple.read(t) for t in wire.rows(body, "triples"))

    def ingest(
        self,
        text: str,
        *,
        source: str = "",
        subject: str = "",
        at: Optional[datetime] = None,
    ) -> Answer[Wrote]:
        """Extract and record in one call, answering the same :class:`Wrote`."""
        reply = self.client.send("POST", "/v1/graph/ingest", body=_source(text, source, subject, at))
        return answer.read(reply, Wrote.read)

    def vocabulary(self) -> Vocabulary:
        """The relations in use and the ordering that decides a conflict."""
        return Vocabulary.read(self.client.read("GET", "/v1/graph/vocabulary"))


def _source(text: str, source: str, subject: str, at: Optional[datetime]) -> Dict[str, Any]:
    """The body both readers of a document take."""
    return {"text": text, "source": source, "subject": subject, "at": wire.stamp(at)}
