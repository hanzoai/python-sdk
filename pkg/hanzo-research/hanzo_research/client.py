"""Hanzo Research SDK — the ONE way every producer records and queries research.

Generated-shape from the openapi/research contract, wrapped in a tiny, intuitive,
ZERO-CONFIG surface so hand-rolling is obviously the worse choice:

    import hanzo_research as research

    exp = research.experiment("benchmark", "grok-4.5", "gpqa_diamond")  # get/create → handle
    exp.record("q1", "grok-4.5", {"answer": "A", "correct": True})       # an attempt, idempotent
    exp.snapshot(png_bytes)                                              # a board snapshot artifact
    exp.report(markdown_text)                                           # a generated report artifact
    exp.finish(value=94.3)                                              # seal the run (or use `with`)

    rows = research.query(project="enso-bench", kind="benchmark")       # read canonical

Auto-instrumentation (the caller supplies NO provenance): on experiment()/finish() the
SDK reads git sha/branch/dirty, the commit messages SINCE the last recorded run of this
experiment (the narrative of what changed), the installed lib versions, and the host —
and weaves them into the record. Research self-documents as a side effect of running.

Auth is the per-org key (private-by-default is enforced server-side). Records mirror to
the cloud /v1/research surface (HIP-0512), which is versioned + append-only + idempotent
by content, so re-recording the same result is a no-op.
"""
import base64
import hashlib
import json
import os
import urllib.error
import urllib.parse
import urllib.request

from . import provenance

DEFAULT_LIBS = [
    "hanzo-kernel", "hanzo-ml", "hanzo-engine", "hanzo-research",
    "enso-bench", "datasets", "huggingface-hub", "torch", "transformers",
]


class Research:
    """A configured research client. Base URL, per-org key, and project come from the
    environment by default (HANZO_API_KEY, RESEARCH_BASE, RESEARCH_PROJECT); the repo the
    caller runs in is auto-detected for provenance."""

    def __init__(self, base=None, api_key=None, project=None, repo=None, libs=None, timeout=120):
        self.base = (base or os.environ.get("RESEARCH_BASE", "https://api.hanzo.ai")).rstrip("/")
        self.api_key = api_key or os.environ.get("HANZO_API_KEY", "")
        self.project = project or os.environ.get("RESEARCH_PROJECT", "default")
        self.repo = repo or provenance.find_repo()
        self.libs = libs if libs is not None else DEFAULT_LIBS
        self.timeout = timeout

    # ── transport ──────────────────────────────────────────────────────────────
    def _headers(self):
        # Auth is ONLY the per-org key (the gateway mints the validated principal from it).
        # The client NEVER mints X-User-Id/X-Org-Id — that is a cross-tenant forge the
        # gateway strips anyway (SanitizeIdentity); any local/dev bypass belongs SERVER-side
        # behind an explicit unsafe flag, never in the client.
        h = {"Content-Type": "application/json", "X-Project-Id": self.project}
        if self.api_key:
            h["Authorization"] = "Bearer " + self.api_key
        return h

    def _req(self, method, path, payload=None):
        data = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(self.base + path, data=data, headers=self._headers(), method=method)
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            return json.loads(r.read() or b"{}")

    # ── low-level surface (mirrors the contract; used by the bulk uploader) ──────
    def ingest(self, experiments=None, attempts=None):
        """POST a batch of experiments + attempts. Idempotent by content; returns the
        cloud counts (canonical + retained)."""
        return self._req("POST", "/v1/research/experiments",
                         {"experiments": experiments or [], "attempts": attempts or []})

    def artifact(self, art):
        return self._req("POST", "/v1/research/artifacts", art)

    def grant(self, **g):
        return self._req("POST", "/v1/research/grants", g)

    # ── ergonomic surface ───────────────────────────────────────────────────────
    def experiment(self, kind, subject, task, metric="accuracy", n_total=0, note=""):
        """Get/create the experiment for (kind, subject, task) and return a handle. Auto-
        captures provenance + the self-documenting narrative (the caller's docstring, the
        commit messages since this experiment's last run, and an optional note)."""
        return Experiment(self, kind, subject, task, metric=metric, n_total=n_total, note=note)

    def query(self, project=None, kind=None, canonical=True):
        """Read canonical experiments (the answered latest-run view). canonical=False is
        reserved for the full retained-version history (a follow-up endpoint; the retained
        COUNTS are already on /v1/research/totals)."""
        q = []
        if project or self.project:
            q.append("project=" + urllib.parse.quote(project or self.project))
        if kind:
            q.append("kind=" + urllib.parse.quote(kind))
        path = "/v1/research/experiments" + ("?" + "&".join(q) if q else "")
        out = self._req("GET", path)
        return out.get("data", [])

    def totals(self, project=None):
        path = "/v1/research/totals" + ("?project=" + urllib.parse.quote(project) if project else "")
        return self._req("GET", path)

    # ── internal ────────────────────────────────────────────────────────────────
    def _last_run_sha(self, exp_id):
        """The git sha of this experiment's last recorded run, for the since-narrative."""
        try:
            for e in self.query():
                if e.get("id") == exp_id:
                    return e.get("git_sha", "")
        except Exception:
            return ""
        return ""


class Experiment:
    """A handle to one experiment (a run of kind:subject:task). record() files attempts;
    snapshot()/report() file diary artifacts; finish() seals the run with its final
    number + the auto-captured narrative. Usable as a context manager (finish on exit)."""

    def __init__(self, client, kind, subject, task, metric="accuracy", n_total=0, note=""):
        self.c = client
        self.kind, self.subject, self.task, self.metric = kind, subject, task, metric
        self.id = f"{kind}:{subject}:{task}"
        self.n_total = n_total
        self._ok = 0
        self._n = 0
        # Zero-config, self-documenting provenance. THREE narrative sources, captured with
        # nothing asked of the caller: (a) the calling code's docstring — what this
        # experiment IS; (b) the commit messages since this experiment's last recorded run
        # — what changed + why; (c) an optional note. Plus git state, lib versions, host.
        self.prov = provenance.git_state(self.c.repo)
        self.doc = provenance.caller_doc()
        self.note = note
        last = self.c._last_run_sha(self.id)
        self.commits = provenance.commit_narrative(self.c.repo, since_sha=last)
        self.libs = provenance.lib_versions(self.c.libs)
        self.host = provenance.host()
        # Post the run as in-flight so the ops board sees it immediately.
        self._post(status="running", value=0.0)

    def _post(self, status, value):
        e = {
            "id": self.id, "kind": self.kind, "subject": self.subject, "task": self.task,
            "metric": self.metric, "value": value, "n": self._n, "n_total": self.n_total,
            "status": status, "git_sha": self.prov["git_sha"], "git_branch": self.prov["git_branch"],
            "git_dirty": self.prov["git_dirty"], "lib_versions": self.libs,
            "meta": {"doc": self.doc, "commits": self.commits, "note": self.note, "host": self.host},
        }
        return self.c.ingest(experiments=[e])

    def record(self, item, model, result):
        """File one attempt (idempotent by stable id). `result` is a dict:
        {answer, correct, response?, gold?, source?, status?}."""
        a = {
            "benchmark": self.task, "item": item, "model": model,
            "answer": result.get("answer", ""), "correct": bool(result.get("correct")),
            "response": result.get("response", ""), "gold": result.get("gold", ""),
            "source": result.get("source", "hanzo-measured"), "status": result.get("status", "complete"),
        }
        if a["status"] not in ("faulted", "failed"):
            self._n += 1
            if a["correct"]:
                self._ok += 1
        return self.c.ingest(attempts=[a])

    def snapshot(self, data, run_id=None):
        """File a board-snapshot artifact. `data` is the PNG bytes (or a path to the PNG).
        The SDK submits the bytes; the SERVER content-addresses them by sha256."""
        raw = data if isinstance(data, (bytes, bytearray)) else _read_bytes(data)
        return self._artifact("snapshot", raw, run_id)

    def report(self, data, run_id=None):
        """File a generated-report artifact — HTML/Markdown TEXT (or bytes)."""
        raw = data if isinstance(data, (bytes, bytearray)) else str(data).encode()
        return self._artifact("report", raw, run_id)

    def _artifact(self, kind, raw, run_id):
        # Submit the BYTES; the server hashes them and owns the sha256 + ref. The client
        # sha256 travels only so the server can reject a mismatch (a mis-hash or tamper).
        return self.c.artifact({
            "content": base64.b64encode(raw).decode(),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "kind": kind, "run_id": run_id or self.id,
            "git_sha": self.prov["git_sha"], "git_branch": self.prov["git_branch"],
            "git_dirty": self.prov["git_dirty"], "lib_versions": self.libs,
        })

    def finish(self, value=None):
        """Seal the run: post the final number (computed from recorded attempts if not
        given) + status complete. A new version supersedes the in-flight one; the prior
        is retained."""
        if value is None:
            value = round(100.0 * self._ok / self._n, 2) if self._n else 0.0
        return self._post(status="complete", value=value)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        # A run that raised is sealed faulted (retained), else complete.
        if exc_type is not None:
            self._post(status="faulted", value=0.0)
        else:
            self.finish()
        return False


def _read_bytes(path):
    with open(path, "rb") as f:
        return f.read()
