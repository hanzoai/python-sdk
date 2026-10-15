"""Wire types of `/v1/research`: the records hanzo-inc/cloud `apps/research` stores and returns.

Field names, order and JSON are the server's (`record.go`, `research.go`) and the Rust
crate's (`wire.rs`, `lib.rs`) where the crate agrees with the server: `Comparison` carries
`a`, `b` and `config` (the crate reads `differences`, which the server never writes) and
`Stored` carries `ref`. Reads are tolerant as the crate's are: an unknown
key is ignored, a missing one takes its default, and a null list reads as empty. A
pointer the server declares (`k`, `temperature`, `questions`, a measure's `lo`) stays
`None` when absent, never 0: absence is the record declining to say.
"""

from __future__ import annotations

import os
import enum
import json
import math
import types
import base64
import typing
import binascii
import datetime
import subprocess
import dataclasses
from typing import Any, Mapping, TypeVar, Iterator
from dataclasses import field, dataclass

__all__ = [
    "Split",
    "Benchmark",
    "Measure",
    "Run",
    "Study",
    "Paper",
    "Difference",
    "Delta",
    "Comparison",
    "Census",
    "Gap",
    "Listing",
    "Batch",
    "Stored",
    "Artifact",
    "Record",
    "Ack",
    "KindTotal",
    "Totals",
    "Summary",
    "completion",
    "load",
    "dump",
    "token",
    "claims",
    "claimed",
    "left",
    "scope",
    "now",
]

T = TypeVar("T")


class Wire:
    """A record on the wire: `dump()` is its JSON object, `load(data)` reads one back."""

    def dump(self) -> dict[str, Any]:
        return {f.name: _out(getattr(self, f.name)) for f in dataclasses.fields(self)}  # type: ignore[arg-type]

    @classmethod
    def load(cls: type[T], data: Mapping[str, Any] | None) -> T:
        return load(cls, data)


@dataclass
class Split(Wire):
    """One named division of a benchmark's items, as the benchmark defines it."""

    name: str = ""
    items: int = 0
    definition: str = ""


@dataclass
class Benchmark(Wire):
    """The task: a standardized test, its dataset and terms, its splits, its official metric."""

    project: str = ""
    id: str = ""
    title: str = ""
    version: str = ""
    dataset: str = ""
    license: str = ""
    origin: str = ""
    splits: list[Split] = field(default_factory=list)
    metric: str = ""
    metrics: list[str] = field(default_factory=list)
    citation: str = ""
    notes: str = ""
    revision: str = ""
    canonical: bool = False
    when: str = ""


@dataclass
class Measure(Wire):
    """One reported number: the slice it covers, the quantity, its value and interval."""

    category: str = ""
    metric: str = ""
    value: float = 0.0
    lo: float | None = None
    hi: float | None = None
    n: int | None = None
    of: int | None = None


@dataclass
class Run(Wire):
    """One execution: what was measured, by which system, at which commit, over which data."""

    project: str = ""
    id: str = ""
    benchmark: str = ""
    split: str = ""
    system: str = ""
    version: str = ""
    baseline: bool = False
    study: str = ""
    embedder: str = ""
    reader: str = ""
    k: int | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    prompt: str = ""
    prompt_digest: str = ""
    dataset_digest: str = ""
    store_digest: str = ""
    facts_digest: str = ""
    commit: str = ""
    questions: int | None = None
    answered: int | None = None
    when: str = ""
    ended: str = ""
    by: str = ""
    completion: str = ""
    measures: list[Measure] = field(default_factory=list)
    notes: str = ""
    revision: str = ""
    canonical: bool = False
    visibility: str = ""
    trainable: bool = False
    publishable: bool = False

    def put(
        self,
        category: str,
        metric: str,
        value: Any,
        n: int | None = None,
        of: int | None = None,
        lo: float | None = None,
        hi: float | None = None,
    ) -> Run:
        """Record a measure when `value` is a finite number; anything else records nothing."""
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            return self
        self.measures.append(Measure(category, metric, float(value), lo, hi, n, of))
        return self

    def measure(self, category: str, metric: str) -> Measure | None:
        """The measure recorded for (category, metric), or None."""
        return next((m for m in self.measures if m.category == category and m.metric == metric), None)


def completion(run: Run) -> str:
    """Completion as the server derives it from `questions`, `answered` and `ended`."""
    q, a = run.questions, run.answered
    if q is None or a is None:
        return "unknown"
    if a > q:
        return "inconsistent"
    if a < q:
        return "partial"
    return "complete" if run.ended.strip() else "unknown"


@dataclass
class Study(Wire):
    """The question a set of runs was run to answer, and the answer it reached."""

    project: str = ""
    id: str = ""
    title: str = ""
    question: str = ""
    finding: str = ""
    revision: str = ""
    canonical: bool = False
    when: str = ""


@dataclass
class Paper(Wire):
    """Writing that cites runs; the edge points from the paper to the runs only."""

    project: str = ""
    id: str = ""
    title: str = ""
    authors: list[str] = field(default_factory=list)
    venue: str = ""
    doi: str = ""
    url: str = ""
    status: str = ""
    cites: list[str] = field(default_factory=list)
    study: str = ""
    revision: str = ""
    canonical: bool = False
    when: str = ""


@dataclass
class Difference(Wire):
    """One configuration field two runs disagree about, both values as text."""

    field: str = ""
    a: str = ""
    b: str = ""


@dataclass
class Delta(Wire):
    """One (category, metric) both runs measured, and the change from the first to the second."""

    category: str = ""
    metric: str = ""
    a: float = 0.0
    b: float = 0.0
    change: float = 0.0
    overlap: bool | None = None


@dataclass
class Comparison(Wire):
    """Two runs side by side; `blocks` are why they may not be compared, read first."""

    a: Run | None = None
    b: Run | None = None
    comparable: bool = False
    blocks: list[str] = dataclasses.field(default_factory=list)
    config: list[Difference] = dataclasses.field(default_factory=list)
    deltas: list[Delta] = dataclasses.field(default_factory=list)


@dataclass
class Census(Wire):
    """How many runs of a listing read complete, partial, inconsistent and unknown."""

    complete: int = 0
    partial: int = 0
    inconsistent: int = 0
    unknown: int = 0


@dataclass
class Gap(Wire):
    """A run field, and how many runs of a listing do not state it."""

    field: str = ""
    runs: int = 0


@dataclass
class Listing(Wire):
    """A listing's rows. A run listing also carries its completion census and its gaps."""

    data: list[Any] = dataclasses.field(default_factory=list)
    total: int = 0
    completion: Census | None = None
    gaps: list[Gap] = dataclasses.field(default_factory=list)

    def __iter__(self) -> Iterator[Any]:
        return iter(self.data)

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, i: int) -> Any:
        return self.data[i]


@dataclass
class Batch(Wire):
    """What a record write filed: the project, the versions new to it, the canonical count."""

    project: str = ""
    recorded: int = 0
    canonical: int = 0


@dataclass
class Stored(Wire):
    """An artifact write: the server's hash of the bytes, its address, and whether it was new."""

    sha256: str = ""
    ref: str = ""
    created: bool = False
    rolled_up: bool = False


@dataclass
class Artifact(Wire):
    """A diary artifact (a snapshot or a report), content-addressed by the server.

    The server reads the first block; the second is the crate's transport metadata,
    sent as the crate sends it and ignored by today's server.
    """

    sha256: str = ""
    content: str = ""
    kind: str = ""
    ref: str = ""
    run_id: str = ""
    project: str = ""
    visibility: str = ""
    retention_class: str = ""
    git_sha: str = ""
    git_branch: str = ""
    git_dirty: bool = False
    lib_versions: dict[str, str] = dataclasses.field(default_factory=dict)
    ts: int = 0
    artifact_id: str = ""
    content_sha256: str = ""
    media_type: str = ""
    canonicalization: str = ""
    compression: str = ""
    uncompressed_size: int = 0


@dataclass
class Record(Wire):
    """One stored experiment version, as the canonical experiment listing returns it."""

    project: str = ""
    id: str = ""
    revision: str = ""
    status: str = ""
    canonical: bool = False
    visibility: str = ""
    trainable: bool = False
    publishable: bool = False
    kind: str = ""
    subject: str = ""
    task: str = ""
    metric: str = ""
    value: float = 0.0
    n: int = 0
    n_total: int = 0
    cost_usd: float = 0.0
    meta: Any = None
    git_sha: str = ""
    git_branch: str = ""
    git_dirty: bool = False
    lib_versions: dict[str, str] = dataclasses.field(default_factory=dict)
    ts: int = 0


@dataclass
class Ack(Wire):
    """An experiment ingest: what this call added and what the org's store now holds."""

    project: str = ""
    experiments_ingested: int = 0
    attempts_ingested: int = 0
    canonical_experiments: int = 0
    experiments_retained: int = 0
    canonical_attempts: int = 0
    attempts_retained: int = 0
    rolled_up: bool = False


@dataclass
class KindTotal(Wire):
    """One experiment kind's slice of the totals."""

    kind: str = ""
    experiments: int = 0
    cost_usd: float = 0.0


@dataclass
class Totals(Wire):
    """The headline aggregate, canonical and retained side by side, with a per-kind breakdown."""

    project: str = ""
    projects: int = 0
    experiments: int = 0
    experiments_retained: int = 0
    attempts: int = 0
    attempts_retained: int = 0
    models: int = 0
    benchmarks: int = 0
    cost_usd: float = 0.0
    by_kind: list[KindTotal] = dataclasses.field(default_factory=list)


@dataclass
class Summary(Wire):
    """One project of the org with its canonical and retained counts."""

    project: str = ""
    experiments: int = 0
    experiments_retained: int = 0
    attempts: int = 0
    attempts_retained: int = 0
    models: int = 0
    benchmarks: int = 0
    cost_usd: float = 0.0
    kinds: list[str] = dataclasses.field(default_factory=list)


# ── (de)serialization ─────────────────────────────────────────────────────────


def dump(record: Any) -> Any:
    """A wire record, a mapping, or a list of either, as plain JSON values."""
    return _out(record)


def load(cls: type[T], data: Mapping[str, Any] | None) -> T:
    """Read a dataclass from JSON: unknown keys ignored, missing ones defaulted, null lists empty."""
    hints = typing.get_type_hints(cls)
    kw = {}
    src = data or {}
    for f in dataclasses.fields(cls):  # type: ignore[arg-type]
        if f.name in src:
            kw[f.name] = _in(hints[f.name], src[f.name])
    return cls(**kw)


def _out(v: Any) -> Any:
    if isinstance(v, Wire):
        return v.dump()
    if dataclasses.is_dataclass(v) and not isinstance(v, type):
        return {f.name: _out(getattr(v, f.name)) for f in dataclasses.fields(v)}
    if isinstance(v, enum.Enum):
        return v.value
    if isinstance(v, (list, tuple)):
        return [_out(x) for x in v]
    if isinstance(v, Mapping):
        return {k: _out(x) for k, x in v.items()}
    return v


def _in(tp: Any, v: Any) -> Any:
    origin = typing.get_origin(tp)
    args = typing.get_args(tp)
    if origin in (typing.Union, types.UnionType):
        if v is None:
            return None
        inner = [a for a in args if a is not type(None)]
        return _in(inner[0], v) if len(inner) == 1 else v
    if origin is list:
        return [_in(args[0], x) for x in (v or [])] if args else list(v or [])
    if origin is dict:
        return {k: _in(args[1], x) for k, x in (v or {}).items()} if args else dict(v or {})
    if isinstance(tp, type) and dataclasses.is_dataclass(tp):
        cls: Any = tp
        return load(cls, v) if isinstance(v, Mapping) else cls()
    if isinstance(tp, type) and issubclass(tp, enum.Enum):
        return tp(v)
    if tp is str:
        return "" if v is None else v
    if tp is bool:
        return bool(v)
    if tp is float:
        return 0.0 if v is None else float(v)
    if tp is int:
        return 0 if v is None else int(v)
    return v


# ── the token, its claims, and time ─────────────────────────────────────────────


def token() -> str:
    """`HANZO_API_KEY`, else what `hanzo auth token` prints; "" when neither gives one."""
    t = os.environ.get("HANZO_API_KEY", "").strip()
    if t:
        return t
    try:
        out = subprocess.run(["hanzo", "auth", "token"], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return ""
    return out.stdout.strip() if out.returncode == 0 else ""


def claims(tok: str) -> dict[str, Any] | None:
    """A JWT's claims, read without verifying it (the server verifies); None for a token that is not a JWT."""
    parts = tok.split(".")
    if len(parts) != 3:
        return None
    body = parts[1]
    try:
        out = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
    except (ValueError, binascii.Error):
        return None
    return out if isinstance(out, dict) else None


def claimed(tok: str) -> str | None:
    """The project a JWT's claims name, `default` when none; None for a token that is not a JWT."""
    c = claims(tok)
    return None if c is None else scope(str(c.get("project") or ""))


def left(tok: str) -> int | None:
    """Seconds until a JWT's `exp`; None for a token that is not a JWT or names no expiry."""
    c = claims(tok)
    exp = None if c is None else c.get("exp")
    if not isinstance(exp, (int, float)) or isinstance(exp, bool):
        return None
    return int(exp) - int(datetime.datetime.now(datetime.timezone.utc).timestamp())


def scope(project: str) -> str:
    """A project as the server scopes it: empty is the default project."""
    return project.strip() or "default"


def now() -> str:
    """Now as RFC 3339 in UTC, to the second."""
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
