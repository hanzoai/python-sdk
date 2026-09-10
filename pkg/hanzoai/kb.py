"""The corpus you write, and the connectors that fill it.

Searching it belongs to :mod:`hanzoai.search`. This is what puts documents in
and what keeps them coming.

Cloud's shape is awkward here and this capability's is not. Writes are generic
doctype CRUD at ``/v1/framework/kb.page``, ``kb.memory`` and ``kb.source``,
while connectors, import and reindex live under ``/v1/knowledge``. One `kb`
covers both. The three doctypes also spell their text field differently —
`page` and `source` call it ``body``, `memory` calls it ``content`` — so
:class:`Doc` carries one `body` and the mapping happens once, here.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Dict, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass

from hanzoai import answer
from hanzoai.page import Page
from hanzoai.wire import Reply, flag, rows, text, number, instant
from hanzoai.answer import Answer

if TYPE_CHECKING:  # the capability layer is written over the wire, not the generated client
    from hanzoai.client import Client

__all__ = ["Doc", "Import", "Reindex", "Connector", "Link", "Sync", "Node", "Edge", "Links", "Kb", "KINDS"]

#: The three doctypes that hold knowledge. `kind` is one of these everywhere.
KINDS = ("page", "memory", "source")

#: Where each doctype keeps its text.
_TEXT = {"page": "body", "memory": "content", "source": "body"}


@dataclass(frozen=True)
class Doc:
    """One knowledge document. `kind` is page, memory or source.

    `name` is its id within the kind — a slug for a page, a hash for a memory or
    a source. A `put` with a name replaces that document; a `put` without one
    creates a document and cloud names it.
    """

    kind: str = ""
    name: str = ""
    title: str = ""
    body: str = ""
    project: str = ""
    url: str = ""

    def write(self) -> Dict[str, Any]:
        """The document's own field data, in the doctype's spelling."""
        out: Dict[str, Any] = {"title": self.title, _TEXT.get(self.kind, "body"): self.body}
        if self.project:
            out["project"] = self.project
        if self.url:
            out["url"] = self.url
        if self.name and self.kind == "page":
            out["slug"] = self.name  # a page is named by its slug
        return out

    @classmethod
    def read(cls, body: Any, kind: str) -> "Doc":
        return cls(
            kind=kind,
            name=text(body, "name"),
            title=text(body, "title"),
            body=text(body, _TEXT.get(kind, "body")),
            project=text(body, "project"),
            url=text(body, "url"),
        )


@dataclass(frozen=True)
class Import:
    """What an uploaded export actually filed.

    `imported` counts pages that were stored, not pages that were sent — the
    bounds drop pages past the five-thousandth and skip a page the store
    refused. Modelled here because cloud declares no response schema.
    """

    imported: int = 0

    @classmethod
    def read(cls, body: Any) -> "Import":
        return cls(imported=number(body, "imported"))


@dataclass(frozen=True)
class Reindex:
    """What a rebuild touched."""

    lexical: int = 0
    vectors: int = 0
    removed: int = 0
    failed: int = 0

    @classmethod
    def read(cls, body: Any) -> "Reindex":
        return cls(
            lexical=number(body, "lexical"),
            vectors=number(body, "vectors"),
            removed=number(body, "removed"),
            failed=number(body, "failed"),
        )


@dataclass(frozen=True)
class Connector:
    """One source of documents. `status` is disconnected, connected, syncing or error."""

    provider: str = ""
    kind: str = ""
    status: str = ""
    account: str = ""
    configured: bool = False
    docs: int = 0
    synced: Optional[datetime] = None
    error: str = ""

    @classmethod
    def read(cls, body: Any) -> "Connector":
        return cls(
            provider=text(body, "provider"),
            kind=text(body, "kind"),
            status=text(body, "status"),
            account=text(body, "account"),
            configured=flag(body, "configured"),
            docs=number(body, "docCount"),
            synced=instant(body.get("lastSync")) if isinstance(body, dict) else None,
            error=text(body, "error"),
        )


@dataclass(frozen=True)
class Link:
    """Where to send a person so they can grant the connector access.

    The SDK never follows it. An OAuth consent screen is not a client's to
    complete.
    """

    url: str = ""

    @classmethod
    def read(cls, body: Any) -> "Link":
        return cls(url=text(body, "authorizeUrl"))


@dataclass(frozen=True)
class Sync:
    """What one pull from a connector ingested."""

    provider: str = ""
    ingested: int = 0

    @classmethod
    def read(cls, body: Any) -> "Sync":
        return cls(provider=text(body, "provider"), ingested=number(body, "ingested"))


@dataclass(frozen=True)
class Node:
    """A document in the corpus map."""

    id: str = ""
    name: str = ""
    title: str = ""
    kind: str = ""
    project: str = ""

    @classmethod
    def read(cls, body: Any) -> "Node":
        return cls(
            id=text(body, "id"),
            name=text(body, "name"),
            title=text(body, "title"),
            kind=text(body, "type"),
            project=text(body, "project"),
        )


@dataclass(frozen=True)
class Edge:
    """A link between two documents: a parent, a wikilink, a provenance edge."""

    source: str = ""
    target: str = ""
    kind: str = ""

    @classmethod
    def read(cls, body: Any) -> "Edge":
        return cls(source=text(body, "from"), target=text(body, "to"), kind=text(body, "kind"))


@dataclass(frozen=True)
class Links:
    """The corpus's own shape: which documents exist and what points at what.

    This is not :mod:`hanzoai.graph`. It describes documents, not assertions,
    and the two never share a type.
    """

    nodes: Tuple[Node, ...] = ()
    edges: Tuple[Edge, ...] = ()
    partial: bool = False

    @classmethod
    def read(cls, body: Any) -> "Links":
        return cls(
            nodes=tuple(Node.read(n) for n in rows(body, "nodes")),
            edges=tuple(Edge.read(e) for e in rows(body, "edges")),
            partial=flag(body, "degraded"),
        )


class Kb:
    """`c.kb`."""

    def __init__(self, client: "Client") -> None:
        self.client = client

    def put(self, doc: Doc) -> Answer[Doc]:
        """Write a document. A name that already exists is replaced; absent, one is created."""
        path = _path(doc.kind)
        reply: Reply = (
            self.client.send("PUT", path + "/" + doc.name, body=doc.write())
            if doc.name
            else self.client.send("POST", path, body=doc.write())
        )
        return answer.read(reply, lambda body: Doc.read(body, doc.kind))

    def get(self, kind: str, name: str) -> Doc:
        """One document by name."""
        return Doc.read(self.client.read("GET", _path(kind) + "/" + name), kind)

    def list(self, kind: str, *, project: Optional[str] = None, limit: Optional[int] = None) -> Page[Doc]:
        """The org's documents of one kind, newest-updated first.

        `total` is this page's count: cloud's document list reports no total of
        its own, and a number invented here would be a number nobody counted.
        """
        body = self.client.read(
            "GET",
            _path(kind),
            query={"filters": json.dumps({"project": project}) if project else None, "limit": limit},
        )
        docs = tuple(Doc.read(d, kind) for d in rows(body, "data"))
        return Page(items=docs, total=len(docs))

    def drop(self, kind: str, name: str) -> Answer[None]:
        """Remove one document."""
        return answer.read(self.client.send("DELETE", _path(kind) + "/" + name), lambda _: None)

    def import_(self, export: bytes, *, format: str, project: Optional[str] = None) -> Answer[Import]:
        """File an exported vault as a tree of pages, links intact.

        `format` picks the normalizer — obsidian, notion, roam or evernote. The
        trailing underscore is PEP 8's escape for a keyword; the word is
        ``import``.
        """
        reply = self.client.send(
            "POST",
            "/v1/knowledge/import",
            query={"format": format, "project": project},
            body=export,
            media="application/octet-stream",
        )
        return answer.read(reply, Import.read)

    def reindex(self) -> Answer[Reindex]:
        """Rebuild retrieval over the corpus."""
        return answer.read(self.client.send("POST", "/v1/knowledge/reindex"), Reindex.read)

    def connectors(self) -> Tuple[Connector, ...]:
        """Every connector this org has, connected or not."""
        body = self.client.read("GET", "/v1/knowledge/connectors")
        return tuple(Connector.read(c) for c in rows(body, "connectors"))

    def connect(self, provider: str) -> Link:
        """Where to send a person to authorize `provider`."""
        return Link.read(self.client.read("GET", "/v1/knowledge/connectors/" + provider + "/connect"))

    def sync(self, provider: str) -> Answer[Sync]:
        """Pull what `provider` has now."""
        return answer.read(self.client.send("POST", "/v1/knowledge/connectors/" + provider + "/sync"), Sync.read)

    def revoke(self, provider: str) -> Answer[None]:
        """Disconnect `provider`."""
        return answer.read(self.client.send("DELETE", "/v1/knowledge/connectors/" + provider), lambda _: None)

    def links(self) -> Links:
        """The corpus's own parent, wikilink and provenance edges."""
        return Links.read(self.client.read("GET", "/v1/knowledge/graph"))

    def install(self) -> Answer[None]:
        """Create the kb doctypes in this org. Once, before the first `put`.

        It is in the surface only because cloud requires it: a first write to a
        module's doctype could install it and nobody would have to know.
        """
        return answer.read(self.client.send("POST", "/v1/framework/modules/kb/install"), lambda _: None)


def _path(kind: str) -> str:
    """Where one kind's documents live."""
    if kind not in KINDS:
        raise ValueError("kind is one of {0}, not {1!r}".format(", ".join(KINDS), kind))
    return "/v1/framework/kb." + kind
