"""`Arena`: the `/v1/benchmark` routes hanzo-inc/cloud `apps/benchmark` serves.

Two planes, never blended. The MEASURED plane is per-item attempts the arena's own harness
made; `leaderboard` reads each model's latest run of them, and `history` and `compare`
read every run of them (`compare` pairs two models on the items both answered and gives an
exact McNemar p). The PUBLISHED plane is claims: someone's reported score, each with the
source it was read from.

What reads where:
  * `leaderboard` shows, beside the measured score, only claims an org-`admin` SuperAdmin
    wrote, and those public. Every other org's claims are at `claims`, labelled with their
    org, and never on the board.
  * `claims` shows public claims of every org, plus the caller's own org's private ones.
  * `post_claims` writes under the caller's acting org, private unless `visibility="public"`.
    Writing under org `admin` needs a SuperAdmin token (owner `admin`).
  * `post_run` asks the arena to measure a model: a PAID execution, so it is refused here
    unless `confirm=True`. The answer is an admission, not a result.
  * `post_preset` validates a blend and echoes it as `enso-<name>`; the arena stores nothing.
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Iterable
from dataclasses import field, dataclass

from .wire import Wire, dump
from .errors import Invalid
from .transport import Transport

__all__ = [
    "Arena",
    "Entry",
    "Row",
    "Board",
    "Pairing",
    "Point",
    "History",
    "Claim",
    "Filed",
    "Admission",
    "Preset",
    "Accepted",
]

DEFAULT = "gpqa_diamond"


@dataclass
class Entry(Wire):
    """One canonical public test of the catalog; `native` marks the ones the harness runs today."""

    id: str = ""
    title: str = ""
    axis: str = ""
    items: int = 0
    native: bool = False
    source: str = ""


@dataclass
class Row(Wire):
    """One model on a board: its measured score (latest run, Wilson 95%) beside the platform's claim."""

    model: str = ""
    measured: float | None = None
    n: int = 0
    published: float | None = None
    gap: float | None = None
    protocol: str = ""
    claims: int = 0
    spread: float | None = None
    mean: float | None = None
    run: str = ""
    measuredAt: str | None = None  # noqa: N815  (the wire's name)
    ciLow: float | None = None  # noqa: N815
    ciHigh: float | None = None  # noqa: N815


@dataclass
class Board(Wire):
    """A benchmark's leaderboard, measured score descending."""

    benchmark: str = ""
    rows: list[Row] = field(default_factory=list)


@dataclass
class Pairing(Wire):
    """Two models paired on the items both completed: rescues each way and an exact McNemar p."""

    benchmark: str = ""
    a: str = ""
    b: str = ""
    n_common: int = 0
    a_correct: int = 0
    b_correct: int = 0
    rescue_a_over_b: int = 0
    rescue_b_over_a: int = 0
    net_a_minus_b: int = 0
    mcnemar_p: float = 1.0


@dataclass
class Point(Wire):
    """One run of a model on a benchmark: its score, items, and change from the run before."""

    run: str = ""
    at: str | None = None
    score: float = 0.0
    n: int = 0
    delta: float | None = None


@dataclass
class History(Wire):
    """A model's runs on a benchmark in time order, and the first-to-last change."""

    model: str = ""
    points: list[Point] = field(default_factory=list)
    trend: float | None = None


@dataclass
class Claim(Wire):
    """A reported score and its source. A write sends the first six fields; a read fills the rest."""

    benchmark: str = ""
    provider: str = ""
    model: str = ""
    score: float = 0.0
    protocol: str = ""
    source: str = ""
    org: str = ""
    visibility: str = ""
    origin: str = ""
    at: str | None = None
    by: str = ""


@dataclass
class Filed(Wire):
    """A claims write: how many rows landed, which were refused and why, under which org and visibility."""

    recorded: int = 0
    rejected: list[str] = field(default_factory=list)
    org: str = ""
    visibility: str = ""


@dataclass
class Admission(Wire):
    """A queued arena run: admitted, not finished."""

    status: str = ""
    org: str = ""
    by: str = ""
    model: str = ""
    endpoint: str = ""
    benchmarks: list[str] = field(default_factory=list)
    note: str = ""


@dataclass
class Preset(Wire):
    """A router blend served as `enso-<name>`: its arms, escalation rank and panel width."""

    name: str = ""
    owner: str = ""
    arms: list[str] = field(default_factory=list)
    rank: list[str] = field(default_factory=list)
    panel: int = 0
    note: str = ""


@dataclass
class Accepted(Wire):
    """A preset write's echo: validated, not stored."""

    status: str = ""
    served_as: str = ""
    preset: Preset = field(default_factory=Preset)
    by: str = ""
    note: str = ""


_CLAIM = ("benchmark", "provider", "model", "score", "protocol", "source")


class Arena:
    """The benchmark arena on a credential and an acting org (both as `Research` resolves them)."""

    def __init__(
        self,
        base: str | None = None,
        api_key: str | None = None,
        org: str | None = None,
        timeout: float = 120.0,
        transport: Transport | None = None,
    ):
        self.http = transport or Transport(base, api_key, org, None, timeout)

    def catalog(self) -> list[Entry]:
        return [Entry.load(x) for x in self.http.get("/v1/benchmark/catalog").get("data") or []]

    def leaderboard(self, benchmark: str = DEFAULT) -> Board:
        return Board.load(self.http.get("/v1/benchmark/leaderboard", {"benchmark": benchmark}))

    def compare(self, a: str, b: str, benchmark: str = DEFAULT) -> Pairing:
        return Pairing.load(self.http.get("/v1/benchmark/compare", {"benchmark": benchmark, "a": a, "b": b}))

    def history(self, benchmark: str = DEFAULT, model: str | None = None) -> list[History]:
        out = self.http.get("/v1/benchmark/history", {"benchmark": benchmark, "model": model})
        return [History.load(x) for x in out.get("data") or []]

    def claims(
        self,
        benchmark: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        source: str | None = None,
        protocol: str | None = None,
        org: str | None = None,
    ) -> list[Claim]:
        q = {
            "benchmark": benchmark,
            "model": model,
            "provider": provider,
            "source": source,
            "protocol": protocol,
            "org": org,
        }
        return [Claim.load(x) for x in self.http.get("/v1/benchmark/claims", q).get("data") or []]

    def post_claims(self, rows: Iterable[Claim | Mapping[str, Any]], visibility: str = "private") -> Filed:
        """Write claims under the acting org (at most 500 a call, 2,000 an org a UTC day).

        Every row names its `protocol` (how the score was made: hanzo-measured, provider-reported,
        oracle-ceiling, ...) and its `source` (for a measured score, the research run it came from:
        `Research.url(run_id)`); a row without either is refused here. The server refuses a row
        outside the catalog or a score outside 0..100 and says which in `rejected`.
        """
        body = []
        for i, r in enumerate(rows):
            d = dump(r)
            row = {k: d.get(k, "") for k in _CLAIM}
            if not str(row["protocol"]).strip() or not str(row["source"]).strip():
                raise Invalid(f"claim row {i} needs a protocol and a source")
            score = row["score"]
            if isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score):
                # absent or null would be filed as 0
                raise Invalid(f"claim row {i} needs a score, a number")
            body.append(row)
        return Filed.load(self.http.post("/v1/benchmark/claims", {"data": body, "visibility": visibility}))

    def presets(self) -> list[Preset]:
        return [Preset.load(x) for x in self.http.get("/v1/benchmark/presets").get("data") or []]

    def post_preset(self, preset: Preset | Mapping[str, Any]) -> Accepted:
        return Accepted.load(self.http.post("/v1/benchmark/presets", dump(preset)))

    def post_run(
        self,
        benchmarks: list[str],
        model: str | None = None,
        endpoint: str | None = None,
        attempts: int | None = None,
        *,
        confirm: bool = False,
    ) -> Admission:
        """Queue the arena's harness on a model or your endpoint. It spends money: `confirm=True` or it is refused."""
        if confirm is not True:
            raise Invalid("POST /v1/benchmark/runs queues a paid execution; pass confirm=True to queue it")
        body: dict[str, Any] = {"benchmarks": benchmarks}
        for k, v in (("model", model), ("endpoint", endpoint), ("attempts", attempts)):
            if v:
                body[k] = v
        return Admission.load(self.http.post("/v1/benchmark/runs", body))
