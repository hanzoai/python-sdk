"""Hanzo Brain — typed-link extractor (Python port of @hanzo/bot-graph-links).

Zero-LLM. Pure regex + role inference. Mirrors the TS extractor 1:1 so a
brain.db written by the bot is consumed identically by the Python SDK
and vice versa. Suitable for >10K pages/sec.

Edge types: mentions / attended / works_at / invested_in / founded / advises.

Schema target — `edges` table:
    source TEXT, target TEXT, type TEXT, evidence TEXT,
    PRIMARY KEY (source, target, type)
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Iterable, Literal

EdgeType = Literal["mentions", "attended", "works_at", "invested_in", "founded", "advises"]


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    type: EdgeType
    evidence: str | None = None


# ── Patterns ────────────────────────────────────────────────────────

_MD_LINK = re.compile(r"\[([^\]]+)\]\(([^)#\s]+)\)")
_BARE_SLUG = re.compile(
    r"(?<![/\w])@?((?:people|companies|deals|projects|investors|firms)/[a-z0-9][a-z0-9-]*)",
    re.IGNORECASE,
)
_CODE_FENCE = re.compile(r"```[\s\S]*?```")
_INLINE_CODE = re.compile(r"`[^`\n]+`")

# Order matters — first match wins per (source, target).
_ROLE_PATTERNS: list[tuple[re.Pattern[str], EdgeType]] = [
    # FOUNDED
    (re.compile(r"\b(?:co-?)?founded\s+([^.\n]+?)(?:[.\n]|$)", re.IGNORECASE), "founded"),
    (re.compile(r"\bfounder\s+(?:and\s+\w+\s+)?of\s+([^.\n]+?)(?:[.\n]|$)", re.IGNORECASE), "founded"),
    # INVESTED_IN
    (re.compile(r"\binvested\s+in\s+([^.\n]+?)(?:[.\n]|$)", re.IGNORECASE), "invested_in"),
    (re.compile(r"\bled\s+([^.\n]+?)['’]s\s+(?:seed|series|round)", re.IGNORECASE), "invested_in"),
    (re.compile(r"\bwrote\s+(?:a\s+)?check\s+into\s+([^.\n]+?)(?:[.\n]|$)", re.IGNORECASE), "invested_in"),
    # ADVISES
    (re.compile(r"\badvises\s+([^.\n]+?)(?:[.\n]|$)", re.IGNORECASE), "advises"),
    (re.compile(r"\badvisor\s+(?:to|at|for)\s+([^.\n]+?)(?:[.\n]|$)", re.IGNORECASE), "advises"),
    # WORKS_AT
    (
        re.compile(
            r"\b(?:CEO|CTO|COO|CFO|VP|head\s+of\s+\w+|director)\s+of\s+([^.\n]+?)(?:[.\n]|$)",
            re.IGNORECASE,
        ),
        "works_at",
    ),
    (
        re.compile(
            r"\bjoined\s+([A-Z][^\s.]*(?:\s+[A-Z][^\s.]*)*)(?=\s+(?:as|in)\b|[\s.,;:!?\n]|$)"
        ),
        "works_at",
    ),
    (re.compile(r"\bworks\s+at\s+([^.\n]+?)(?:[.\n]|$)", re.IGNORECASE), "works_at"),
]


def slugify(s: str) -> str:
    """Match gbrain's slug convention — lowercase ascii dashes."""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s[:80]


def _strip_code(md: str) -> str:
    md = _CODE_FENCE.sub("", md)
    md = _INLINE_CODE.sub("", md)
    return md


def _infer_category(edge_type: EdgeType) -> str:
    if edge_type in ("founded", "invested_in", "works_at"):
        return "companies"
    if edge_type == "advises":
        return "people"
    return "entities"


def extract_edges(
    slug: str,
    content: str,
    page_type: str | None = None,
) -> list[Edge]:
    """Extract typed edges from one page. Pure — no I/O, no LLM."""
    cleaned = _strip_code(content)
    seen: dict[tuple[str, EdgeType], Edge] = {}

    def add(e: Edge) -> None:
        key = (e.target, e.type)
        seen.setdefault(key, e)

    # 1. Markdown links — `mentions`, or `attended` on meeting pages.
    for m in _MD_LINK.finditer(cleaned):
        target = m.group(2).strip()
        if target.startswith("http") or target.startswith("/") or "/" not in target:
            continue
        et: EdgeType = "attended" if page_type == "meeting" else "mentions"
        add(Edge(source=slug, target=target, type=et, evidence=m.group(0)))

    # 2. Bare slug refs (`people/alice`).
    for m in _BARE_SLUG.finditer(cleaned):
        et = "attended" if page_type == "meeting" else "mentions"
        add(Edge(source=slug, target=m.group(1).lower(), type=et, evidence=m.group(0)))

    # 3. Role inference.
    for pat, etype in _ROLE_PATTERNS:
        m = pat.search(cleaned)
        if not m:
            continue
        raw = m.group(1).strip().rstrip(".,;:!?")
        target_slug = f"{_infer_category(etype)}/{slugify(raw)}"
        if target_slug.endswith("/"):
            continue
        add(Edge(source=slug, target=target_slug, type=etype, evidence=m.group(0)))

    return list(seen.values())


def reconcile(prior: Iterable[Edge], next_: Iterable[Edge]) -> tuple[list[Edge], list[Edge]]:
    """Return (add, remove) deltas between two edge sets.

    Used by the persistence layer to stale-delete dropped refs when a
    page is edited — same contract as the TS extractor's `reconcile`.
    """
    prior_set = {(e.source, e.target, e.type) for e in prior}
    next_list = list(next_)
    next_set = {(e.source, e.target, e.type) for e in next_list}
    prior_list = [e for e in prior if (e.source, e.target, e.type) not in next_set]
    add = [e for e in next_list if (e.source, e.target, e.type) not in prior_set]
    return add, prior_list
