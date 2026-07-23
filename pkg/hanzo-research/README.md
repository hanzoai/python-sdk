# hanzo-research

Record and query Hanzo R&D evidence in one import. The ONE way every producer
(enso-bench benchmarks, hanzo-engine/hanzo-ml kernel-perf, any research project) files
runs into the unified `/v1/research` plane (HIP-0512) — versioned, append-only,
idempotent by content, private by default.

```python
import hanzo_research as research

# get/create the experiment; provenance is auto-captured (see below)
exp = research.experiment("benchmark", "grok-4.5", "gpqa_diamond")
exp.record("q1", "grok-4.5", {"answer": "A", "correct": True})   # an attempt, idempotent
exp.snapshot(png_bytes)                                          # a board-snapshot artifact
exp.report(markdown_text)                                       # a generated-report artifact
exp.finish(value=94.3)                                          # seal the run

rows = research.query(project="enso-bench", kind="benchmark")    # read canonical
```

## Zero-config auto-instrumentation

The caller supplies **no** provenance. On `experiment()` the SDK reads the run's
environment and captures three self-documenting narrative sources, plus machine context:

- **the calling code's docstring** — *what this experiment is* (write a normal module
  docstring);
- **the commit messages since this experiment's last recorded run** — *what changed +
  why* (commit normally);
- an optional **`note=`** you pass.

Plus `git_sha` / `git_branch` / `git_dirty`, `lib_versions`, and host. The project
self-documents as a side effect of running.

## Importer-agnostic, idempotent

`ingest(experiments=…, attempts=…)` is one idempotent POST. Any source — a SQLite
backfill, git history, a kernel-perf campaign — maps its records to stable ids and calls
it; re-import is a no-op. "Load all research in" is just running importers.

## Config

`RESEARCH_BASE` (default `https://api.hanzo.ai`), `HANZO_API_KEY` (per-org key →
Bearer), `RESEARCH_PROJECT`. Uploads are private; public visibility, training, and
commons rights are each a separate grant. Stdlib only (urllib) — importable in any
zero-dep harness.
