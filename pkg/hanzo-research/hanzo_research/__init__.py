"""Hanzo Research: file measurements to `/v1/research` and `/v1/benchmark` with their provenance.

    from hanzo_research import Research, Run, capture, now

    r = Research()                                   # HANZO_API_KEY, else `hanzo auth token`
    p = capture(model="kai-1.3", weights="/models/kai-1.3", device="cpu", dtype="f32")
    run = Run(id="demo.latency-dev-cpu-kai", benchmark="demo.latency", split="dev",
              questions=200, answered=200, when=p.date)
    run.put("all", "p50_ms", 38.3, n=200, of=200)
    run.ended = now()
    p.apply(run)                                     # commit, system, version, by, notes
    r.record(runs=[run])
    r.grant(run.id, visibility="public", publishable=True)
    r.get_run(run.id, org="hanzo")                   # the public read, no credential

The Rust peer is the `hanzo-research` crate (hanzoai/ml): the same wire records, the same
RFC 8785 digests, the same lineage and WAL records.
"""

from . import wal, wire, lineage, benchmark, canonical, provenance
from .wal import ResearchWal
from .wire import (
    Ack,
    Gap,
    Run,
    Batch,
    Delta,
    Paper,
    Split,
    Study,
    Census,
    Record,
    Stored,
    Totals,
    Listing,
    Measure,
    Summary,
    Artifact,
    Benchmark,
    KindTotal,
    Comparison,
    Difference,
    now,
    left,
    scope,
    token,
    claimed,
    completion,
)
from .client import DEFAULT_LIBS, Research, Experiment
from .errors import Error, Denied, Invalid, Limited, Missing, Unavailable
from .benchmark import Arena
from .canonical import digest, canonicalize
from .transport import VERSION
from .provenance import Provenance, capture

__version__ = VERSION

__all__ = [
    "Research",
    "Experiment",
    "Arena",
    "DEFAULT_LIBS",
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
    "token",
    "claimed",
    "left",
    "scope",
    "now",
    "canonicalize",
    "digest",
    "Provenance",
    "capture",
    "ResearchWal",
    "Error",
    "Denied",
    "Missing",
    "Invalid",
    "Limited",
    "Unavailable",
    "benchmark",
    "canonical",
    "lineage",
    "provenance",
    "wal",
    "wire",
    "configure",
    "client",
    "experiment",
    "query",
    "totals",
    "record",
    "benchmarks",
    "runs",
    "studies",
    "papers",
    "compare",
]

_default: Research | None = None


def configure(**kwargs) -> Research:  # type: ignore[no-untyped-def]
    """Set the process-wide default client (base, api_key, project, repo, libs, timeout, org)."""
    global _default
    _default = Research(**kwargs)
    return _default


def client() -> Research:
    """The process-wide default client, built from the environment on first use."""
    global _default
    if _default is None:
        _default = Research()
    return _default


def experiment(
    kind: str,
    subject: str,
    task: str,
    metric: str = "accuracy",
    n_total: int = 0,
    note: str = "",
    hypothesis: str = "",
    predict: str = "",
) -> Experiment:
    """An experiment handle on the default client (see `Experiment`)."""
    return client().experiment(
        kind, subject, task, metric=metric, n_total=n_total, note=note, hypothesis=hypothesis, predict=predict
    )


def query(project: str | None = None, kind: str | None = None) -> list[Record]:
    """Canonical experiments on the default client."""
    return client().query(project=project, kind=kind)


def totals(project: str | None = None) -> Totals:
    """The headline totals on the default client."""
    return client().totals(project=project)


def record(benchmarks=(), runs=(), studies=(), papers=()) -> dict[str, Batch]:  # type: ignore[no-untyped-def]
    """File benchmarks, studies, runs and papers on the default client (see `Research.record`)."""
    return client().record(benchmarks=benchmarks, runs=runs, studies=studies, papers=papers)


def benchmarks(**filters) -> list[Benchmark]:  # type: ignore[no-untyped-def]
    """Canonical benchmark definitions on the default client."""
    return client().benchmarks(**filters)


def runs(**filters) -> Listing:  # type: ignore[no-untyped-def]
    """Canonical runs on the default client; `org=` reads another org's public runs."""
    return client().runs(**filters)


def studies(**filters) -> list[Study]:  # type: ignore[no-untyped-def]
    """Canonical studies on the default client."""
    return client().studies(**filters)


def papers(**filters) -> list[Paper]:  # type: ignore[no-untyped-def]
    """Canonical papers on the default client."""
    return client().papers(**filters)


def compare(a: str, b: str) -> Comparison:
    """Two runs side by side on the default client."""
    return client().compare(a, b)
