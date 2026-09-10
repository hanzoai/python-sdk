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

__all__ = ["Fact", "Wrote", "Resolution", "Walk", "Triple", "Vocabulary", "Source", "Graph"]


@dataclass(frozen=True)
class Fact:
    """One assertion: `entity` `relation` `value`, and who said so, and when.

    `names` declares that `value` is another entity's key, which makes the
    assertion an edge — the only thing :meth:`Graph.walk` follows. `source` and
    `evidence` are the provenance; `confidence` is how sure the source was.

    `id`, `by` and `knowable` are the server's: it mints the content address,
    stamps the filer from the validated principal, and derives when the row
    became knowable. They arrive on a read and :meth:`write` never sends them,
    so a fact read back and asserted again states the nine members an asserter
    states and none of the three it cannot.
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
    #: The assertion's content address. Two callers who assert the identical
    #: thing land on one id and one row. Read only.
    id: str = ""
    #: The identity that filed it — ``owner`` or ``owner/user``. Read only.
    by: str = ""
    #: The first instant this plane could have answered with the assertion,
    #: which is what an as-of read is bounded by. Read only.
    knowable: Optional[datetime] = None

    def write(self) -> Dict[str, Any]:
        """This fact as an asserter states it.

        An instant nobody set is left out rather than sent as ``""``: cloud
        reads an absent `seen` as `at`, and an empty string as a timestamp that
        is not RFC 3339. `id`, `by` and `knowable` are the server's and are
        never sent.
        """
        out: Dict[str, Any] = {
            "entity": self.entity,
            "relation": self.relation,
            "value": self.value,
            "names": self.names,
            "source": self.source,
            "evidence": self.evidence,
            "confidence": self.confidence,
        }
        return {**out, **_when(at=self.at, seen=self.seen)}

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
            id=wire.text(body, "id"),
            by=wire.text(body, "by"),
            knowable=wire.instant(body.get("knowable")) if isinstance(body, dict) else None,
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
class Source:
    """A document to read relations out of, and where it came from.

    Both :meth:`Graph.extract` and :meth:`Graph.ingest` take it, because they
    take the same thing and differ only in what they do with what they found.
    """

    #: Where the text came from — a URL, a document id, a page title. Stamped
    #: on every assertion as its source, and with the section number as its
    #: evidence, so a claim can be traced back to the passage that made it.
    source: str = ""
    #: The document. A line written ``relation:: value`` states one relation;
    #: prose states none.
    text: str = ""
    #: When what the source says was so. Part of every resulting assertion's
    #: content address, so re-reading one source at one instant records one set
    #: of rows however many times it is delivered.
    at: Optional[datetime] = None
    #: The entity the text is about before any heading names one.
    subject: str = ""

    def write(self) -> Dict[str, Any]:
        """This source as cloud reads it."""
        return {"source": self.source, "text": self.text, "subject": self.subject, **_when(at=self.at)}


@dataclass(frozen=True)
class Vocabulary:
    """The relations in use, and the ordering that decides a conflict."""

    relations: Tuple[str, ...] = ()
    #: The terms of the precedence order, in the order they apply. The wire
    #: member is ``rule``; this is plural because it is a list.
    rules: Tuple[str, ...] = ()
    bound: int = 0

    @classmethod
    def read(cls, body: Any) -> "Vocabulary":
        return cls(
            relations=wire.strings(body, "relations"),
            rules=wire.strings(body, "rule"),
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
        """Which claim about `entity`'s `relation` wins, as of `at`. No `at` asks about now."""
        return Resolution.read(
            self.client.read(
                "POST",
                "/v1/graph/resolve",
                body={"entity": entity, "relation": relation, **_when(as_of=at)},
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
                    **_when(as_of=at),
                },
            )
        )

    def extract(self, source: Source) -> Tuple[Triple, ...]:
        """Read what a document states, without recording any of it."""
        body = self.client.read("POST", "/v1/graph/extract", body=source.write())
        return tuple(Triple.read(t) for t in wire.rows(body, "triples"))

    def ingest(self, source: Source) -> Answer[Wrote]:
        """Extract and record in one call, answering the same :class:`Wrote`."""
        reply = self.client.send("POST", "/v1/graph/ingest", body=source.write())
        return answer.read(reply, Wrote.read)

    def vocabulary(self) -> Vocabulary:
        """The relations in use and the ordering that decides a conflict."""
        return Vocabulary.read(self.client.read("GET", "/v1/graph/vocabulary"))


def _when(**instants: Optional[datetime]) -> Dict[str, str]:
    """The instants that were set, RFC 3339.

    An instant nobody set is left off the body. Cloud reads an absent one as its
    own default — now, or `at` for a `seen` — and an empty string as a timestamp
    it refuses.
    """
    return {name: wire.stamp(t) for name, t in instants.items() if t is not None}
