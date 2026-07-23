"""Hanzo Research SDK — record and query R&D evidence in one import.

    import hanzo_research as research

    exp = research.experiment("benchmark", "grok-4.5", "gpqa_diamond")
    exp.record("q1", "grok-4.5", {"answer": "A", "correct": True})
    exp.snapshot(png_bytes)
    exp.report(markdown_text)
    exp.finish(value=94.3)

    rows = research.query(project="enso-bench", kind="benchmark")

Zero-config: provenance (git sha/branch + the commit-message narrative since the last
recorded run, lib versions, host) is auto-captured — the caller supplies none. Records
mirror to cloud /v1/research (HIP-0512): versioned, append-only, idempotent by content,
private by default.
"""
from .client import Research, Experiment

__all__ = ["Research", "Experiment", "experiment", "query", "totals", "configure", "client"]

_default = None


def configure(**kwargs):
    """Set the process-wide default client (base, api_key, project, repo, libs)."""
    global _default
    _default = Research(**kwargs)
    return _default


def client():
    """The process-wide default client, built from the environment on first use."""
    global _default
    if _default is None:
        _default = Research()
    return _default


def experiment(kind, subject, task, metric="accuracy", n_total=0, note=""):
    """Get/create an experiment handle on the default client."""
    return client().experiment(kind, subject, task, metric=metric, n_total=n_total, note=note)


def query(project=None, kind=None, canonical=True):
    """Read canonical experiments on the default client."""
    return client().query(project=project, kind=kind, canonical=canonical)


def totals(project=None):
    """Read the headline totals (canonical + retained) on the default client."""
    return client().totals(project=project)
