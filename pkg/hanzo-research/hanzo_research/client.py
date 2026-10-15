"""`Research`: every route hanzo-inc/cloud `apps/research` serves at `/v1/research`.

Two planes on one client. The RECORD plane names what a number needs to be believed:
benchmarks (the task), runs (the execution, its completion derived by the server),
studies (the question) and papers (the writing that cites runs). The EXPERIMENT plane is
the older stream of one measured number per id plus its attempts and diary artifacts; the
`experiment()` handle files to it.

Everything a caller writes lands private, under the caller's org, in the token's project.
Visibility (private, org, public) and the training and commons consents are a separate
call, `grant`. Records are versioned and append-only: a correction is a new version under
the same id (`revise`), a withdrawal is a version marked retracted (`retract`), and every
earlier version stays retained.
"""

from __future__ import annotations

import base64
import hashlib
from typing import Any, Mapping, TypeVar, Iterable

from . import wire, canonical, provenance
from .wire import (
    Ack,
    Run,
    Batch,
    Paper,
    Study,
    Record,
    Stored,
    Totals,
    Listing,
    Summary,
    Artifact,
    Benchmark,
    Comparison,
    dump,
)
from .errors import Error, Invalid, Missing
from .transport import Transport

__all__ = ["Research", "Experiment", "DEFAULT_LIBS"]

DEFAULT_LIBS = [
    "hanzo-kernel",
    "hanzo-ml",
    "hanzo-engine",
    "hanzo-research",
    "enso-bench",
    "datasets",
    "huggingface-hub",
    "torch",
    "transformers",
]
VERDICTS = ("proven", "refuted", "inconclusive")

R = TypeVar("R", Benchmark, Run, Study, Paper)
# the batch key, and route, of each record kind
_KEYS: dict[type, str] = {Benchmark: "benchmarks", Run: "runs", Study: "studies", Paper: "papers"}


class Research:
    """A research client. Base URL, credential, project and acting org come from the environment
    by default (`RESEARCH_BASE`, `HANZO_API_KEY` else `hanzo auth token`, the token's `project`
    claim, the token's `owner`); `org` overrides the org, which the token must belong to.
    `repo` is the checkout whose git state stamps the experiment plane (default: the git
    toplevel of the working directory).
    """

    def __init__(
        self,
        base: str | None = None,
        api_key: str | None = None,
        project: str | None = None,
        repo: str | None = None,
        libs: list[str] | None = None,
        timeout: float = 120.0,
        org: str | None = None,
        transport: Transport | None = None,
    ):
        self.http = transport or Transport(base, api_key, org, project, timeout)
        self.repo = repo or provenance.find_repo()
        self.libs = libs if libs is not None else DEFAULT_LIBS
        self._git: dict[str, Any] | None = None

    @property
    def base(self) -> str:
        return self.http.base

    @property
    def project(self) -> str:
        return self.http.project

    @property
    def org(self) -> str | None:
        return self.http.org

    @property
    def arena(self) -> Any:
        """The `/v1/benchmark` arena on this client's credential and org."""
        from .benchmark import Arena

        return Arena(transport=self.http)

    def url(self, run_id: str, org: str | None = None) -> str:
        """The address that reads one run of an org's public runs, with no credential: a claim's source."""
        from urllib.parse import quote

        org = org or self.org
        if not org:
            raise ValueError("no org to read the run from: pass org=")
        return f"{self.base}/v1/research/runs?org={quote(org, safe='')}&id={quote(run_id, safe='')}"

    # ── record plane: writes ─────────────────────────────────────────────────────

    def record(
        self,
        benchmarks: Iterable[Benchmark | Mapping[str, Any]] = (),
        runs: Iterable[Run | Mapping[str, Any]] = (),
        studies: Iterable[Study | Mapping[str, Any]] = (),
        papers: Iterable[Paper | Mapping[str, Any]] = (),
    ) -> dict[str, Batch]:
        """File records: one write a non-empty kind, at most 20,000 records each, benchmarks and
        studies before the runs that name them and papers last. The answers by kind; nothing
        given sends nothing. A `Run` (or any record) is sent with every field, a mapping as given.
        """
        return self._write({"benchmarks": benchmarks, "studies": studies, "runs": runs, "papers": papers})

    def _write(self, batches: Mapping[str, Iterable[Any]]) -> dict[str, Batch]:
        out = {}
        for key, rows in batches.items():
            body = [dump(r) for r in rows]
            if body:
                batch = Batch.load(self.http.post(f"/v1/research/{key}", {key: body}))
                self._filed(batch.project, key)
                out[key] = batch
        return out

    def _filed(self, project: str, what: str) -> None:
        # the crate's `filed`: the server files under the credential's project, whatever was asked
        if wire.scope(project) != self.project:
            raise Error(f"{what} were committed under project {project}, not {self.project}")

    def _again(self, rec: Any, revision: str) -> Batch:
        """File `rec` as its next version, marked `revision`, in the project it lives in."""
        if rec.project and wire.scope(rec.project) != self.project:
            raise Invalid(f"{rec.id} is in project {rec.project}; this client files under {self.project}")
        rec.revision = revision
        key = _KEYS[type(rec)]
        batch = self._write({key: [rec]})[key]
        if batch.recorded == 0:
            raise Invalid(f"the server already holds this version of {rec.id}: nothing was filed")
        if isinstance(rec, Run) and (rec.visibility not in ("", "private") or rec.trainable or rec.publishable):
            # a new version lands private; the run's grants carry over to it
            self.grant(rec.id, visibility=rec.visibility or None, trainable=rec.trainable, publishable=rec.publishable)
        return batch

    def revise(self, record: R, notes: str | None = None) -> Batch:
        """File a correction: the record's next version, marked corrected, keeping the run's grants.

        A record read from this client's project (`get_run`) or built here; one from another
        project is refused, since the server would file the version beside it, not over it.
        """
        if notes is not None and isinstance(record, Run):
            record.notes = notes
        return self._again(record, "corrected")

    def retract(self, record: str | R, why: str) -> Batch:
        """Withdraw a record: its next version, marked retracted. A run id reads its canonical run first.

        A retracted latest version takes the id out of every listing; the earlier versions stay
        retained. `why` becomes the version's notes for a run (the only kind with notes).
        """
        if not why.strip():
            raise Invalid("a retraction says why")
        rec: Any = self.get_run(record) if isinstance(record, str) else record
        if isinstance(rec, Run):
            rec.notes = why
        return self._again(rec, "retracted")

    def grant(
        self,
        id: str | None = None,
        *,
        sha256: str | None = None,
        visibility: str | None = None,
        trainable: bool | None = None,
        publishable: bool | None = None,
        project: str | None = None,
    ) -> int:
        """Set a run's visibility (private, org, public) and consents, or an artifact's visibility.

        Lands on every retained version of the id. `None` leaves a field as it is. Returns how
        many records it moved; none is `Missing`.
        """
        body: dict[str, Any] = {"project": project or self.project}
        if sha256:
            body["sha256"] = sha256
        else:
            body["id"] = id
        for k, v in (("visibility", visibility), ("trainable", trainable), ("publishable", publishable)):
            if v is not None:
                body[k] = v
        return int(self.http.post("/v1/research/grants", body).get("updated", 0))

    # ── record plane: reads ──────────────────────────────────────────────────────

    def benchmarks(self, id: str | None = None, project: str | None = None) -> list[Benchmark]:
        """Canonical benchmark definitions of the org (`project` narrows; empty reads every project)."""
        out = self.http.get("/v1/research/benchmarks", {"id": id, "project": project})
        return [Benchmark.load(x) for x in out.get("data") or []]

    def get_benchmark(self, id: str, project: str | None = None) -> Benchmark:
        """One benchmark's canonical version in a project (default this client's), or `Missing`."""
        return _one(self.benchmarks(id=id, project=project or self.project), "benchmark", id)

    def runs(
        self,
        id: str | None = None,
        benchmark: str | None = None,
        system: str | None = None,
        study: str | None = None,
        completion: str | None = None,
        since: str | None = None,
        until: str | None = None,
        project: str | None = None,
        org: str | None = None,
    ) -> Listing:
        """Canonical runs, with the completion census and the fields runs leave unstated.

        Without `org`, the caller's own org, private runs included. With `org`, that org's
        PUBLIC runs, read with no credential: the server answers `?org=` only to a caller
        that names no org of its own. `since`/`until` bound `when` (RFC 3339).
        """
        q = {
            "id": id,
            "benchmark": benchmark,
            "system": system,
            "study": study,
            "completion": completion,
            "since": since,
            "until": until,
            "project": project,
            "org": org,
        }
        out = Listing.load(self.http.get("/v1/research/runs", q, auth=not org))
        out.data = [Run.load(x) for x in out.data]
        return out

    def get_run(self, id: str, org: str | None = None, project: str | None = None) -> Run:
        """One run's canonical version, or `Missing`: in a project of your org (default this
        client's; an id is unique only within a project), or with `org`, of that org's public runs."""
        project = project or (None if org else self.project)
        return _one(self.runs(id=id, org=org, project=project).data, "run", id)

    def studies(self, id: str | None = None, project: str | None = None) -> list[Study]:
        out = self.http.get("/v1/research/studies", {"id": id, "project": project})
        return [Study.load(x) for x in out.get("data") or []]

    def papers(
        self, id: str | None = None, study: str | None = None, cites: str | None = None, project: str | None = None
    ) -> list[Paper]:
        out = self.http.get("/v1/research/papers", {"id": id, "study": study, "cites": cites, "project": project})
        return [Paper.load(x) for x in out.get("data") or []]

    def compare(self, a: str, b: str, project: str | None = None) -> Comparison:
        """Two canonical runs side by side: what blocks the comparison, the config they differ in, the deltas."""
        return Comparison.load(self.http.get("/v1/research/compare", {"a": a, "b": b, "project": project}))

    # ── experiment plane ─────────────────────────────────────────────────────────

    def ingest(
        self, experiments: list[Mapping[str, Any]] | None = None, attempts: list[Mapping[str, Any]] | None = None
    ) -> Ack:
        """File experiment and attempt versions in one batch, idempotent by content."""
        ack = Ack.load(
            self.http.post("/v1/research/experiments", {"experiments": experiments or [], "attempts": attempts or []})
        )
        self._filed(ack.project, "experiments and attempts")
        return ack

    def query(self, project: str | None = None, kind: str | None = None) -> list[Record]:
        """Canonical experiments of a project (default the client's), narrowed to one kind."""
        out = self.http.get("/v1/research/experiments", {"project": project or self.project, "kind": kind})
        return [Record.load(x) for x in out.get("data") or []]

    def totals(self, project: str | None = None) -> Totals:
        return Totals.load(self.http.get("/v1/research/totals", {"project": project}))

    def projects(self) -> list[Summary]:
        return [Summary.load(x) for x in self.http.get("/v1/research/projects").get("data") or []]

    def artifact(self, art: Artifact | Mapping[str, Any]) -> Stored:
        """File an artifact record whose `content` is base64; the server hashes the bytes."""
        return Stored.load(self.http.post("/v1/research/artifacts", dump(art)))

    def upload_artifact(
        self,
        kind: str,
        run_id: str,
        data: bytes,
        media_type: str = "application/octet-stream",
        canonicalization: str = "raw",
        compression: str = "none",
        artifact_id: str | None = None,
    ) -> Stored:
        """File bytes as a `snapshot` or `report` of a run, stamped with this checkout's git state."""
        sha = hashlib.sha256(data).hexdigest()
        g = self._state()
        return self.artifact(
            Artifact(
                sha256=sha,
                content=base64.b64encode(data).decode(),
                kind=kind,
                run_id=run_id,
                git_sha=g["git_sha"],
                git_branch=g["git_branch"],
                git_dirty=g["git_dirty"],
                lib_versions=provenance.lib_versions(self.libs),
                artifact_id=artifact_id or f"{run_id}:{kind}",
                content_sha256=sha,
                media_type=media_type,
                canonicalization=canonicalization,
                compression=compression,
                uncompressed_size=len(data),
            )
        )

    def upload_json_artifact(self, kind: str, run_id: str, value: Any) -> Stored:
        """File a value as RFC 8785 JSON; its SHA-256 is `canonical.digest(value)`."""
        return self.upload_artifact(kind, run_id, canonical.canonicalize(value), "application/json", "rfc8785")

    def artifacts(self, run: str | None = None, since: int | None = None, project: str | None = None) -> list[Artifact]:
        """The diary feed, newest first, as metadata; bytes are read by `get_artifact`."""
        out = self.http.get("/v1/research/artifacts", {"run": run, "since": since, "project": project})
        return [Artifact.load(x) for x in out.get("data") or []]

    def get_artifact(self, sha256: str, project: str | None = None) -> bytes:
        """An artifact's bytes by content hash, within the caller's org and project."""
        from urllib.parse import quote

        return self.http.call(
            "GET", f"/v1/research/artifacts/{quote(sha256, safe='')}", {"project": project}, None, True
        )

    def experiment(
        self,
        kind: str,
        subject: str,
        task: str,
        metric: str = "accuracy",
        n_total: int = 0,
        note: str = "",
        hypothesis: str = "",
        predict: str = "",
    ) -> Experiment:
        """Get or create the experiment `kind:subject:task` and post it in flight (see `Experiment`)."""
        return Experiment(
            self, kind, subject, task, metric=metric, n_total=n_total, note=note, hypothesis=hypothesis, predict=predict
        )

    def _state(self) -> dict[str, Any]:
        if self._git is None:
            self._git = provenance.git_state(self.repo)
        return self._git

    def _last_run_sha(self, exp_id: str) -> str:
        try:
            return next((e.git_sha for e in self.query() if e.id == exp_id), "")
        except Exception:
            return ""


def _one(rows: list[Any], what: str, id: str) -> Any:
    if not rows:
        raise Missing(f"no canonical {what} {id!r}", 404)
    return rows[0]


class Experiment:
    """One experiment `kind:subject:task` on the experiment plane, structured as a falsifiable test.

    Posts itself in flight on creation; `record` files attempts, `snapshot`/`report` file
    artifacts, `log` keeps a running trail, `conclude`/`finish` seal it. The git state, the
    commit subjects since its last recorded run, the installed versions and the host are
    stamped without being asked for. A context manager seals it complete, or faulted on an
    exception.
    """

    def __init__(
        self,
        client: Research,
        kind: str,
        subject: str,
        task: str,
        metric: str = "accuracy",
        n_total: int = 0,
        note: str = "",
        hypothesis: str = "",
        predict: str = "",
    ):
        self.c = client
        self.kind, self.subject, self.task, self.metric = kind, subject, task, metric
        self.id = f"{kind}:{subject}:{task}"
        self.n_total = n_total
        self._ok = 0
        self._n = 0
        self.hypothesis = hypothesis
        self.predict = predict
        self.verdict = ""
        self.because = ""
        self._log: list[str] = []
        self.prov = client._state()
        self.doc = provenance.caller_doc()
        self.note = note
        self.commits = provenance.commit_narrative(client.repo, since_sha=client._last_run_sha(self.id))
        self.libs = provenance.lib_versions(client.libs)
        self.host = provenance.host()
        self._post(status="running", value=0.0)

    def log(self, text: str) -> Experiment:
        """Append to the running log that travels with the run."""
        self._log.append(text)
        return self

    def conclude(self, verdict: str, because: str = "", value: float | None = None) -> Ack:
        """Seal with a verdict (proven, refuted or inconclusive) and the reasoning that earns it."""
        if verdict not in VERDICTS:
            raise ValueError(f"verdict must be proven|refuted|inconclusive, got {verdict!r}")
        self.verdict = verdict
        self.because = because
        return self.finish(value=value)

    def record(self, item: str, model: str, result: Mapping[str, Any]) -> Ack:
        """File one attempt: `result` holds answer, correct, and optionally response, gold, source, status.
        A `faulted` or `failed` attempt is kept and left out of the score."""
        a = {
            "benchmark": self.task,
            "item": item,
            "model": model,
            "answer": result.get("answer", ""),
            "correct": bool(result.get("correct")),
            "response": result.get("response", ""),
            "gold": result.get("gold", ""),
            "source": result.get("source", "hanzo-measured"),
            "status": result.get("status", "complete"),
        }
        if a["status"] not in ("faulted", "failed"):
            self._n += 1
            self._ok += int(a["correct"])
        return self.c.ingest(attempts=[a])

    def snapshot(self, data: bytes | str, run_id: str | None = None) -> Stored:
        """File PNG bytes (or a path to them) as a snapshot of this run."""
        raw = data if isinstance(data, (bytes, bytearray)) else open(data, "rb").read()
        return self.c.upload_artifact(
            "snapshot", run_id or self.id, bytes(raw), "image/png", artifact_id=f"{self.id}:snapshot"
        )

    def report(self, data: bytes | str, run_id: str | None = None) -> Stored:
        """File HTML or Markdown as a report of this run."""
        raw = data if isinstance(data, (bytes, bytearray)) else str(data).encode()
        return self.c.upload_artifact(
            "report", run_id or self.id, bytes(raw), "text/plain", artifact_id=f"{self.id}:report"
        )

    def finish(self, value: float | None = None) -> Ack:
        """Seal complete with the final number (from the recorded attempts when not given). A stated
        hypothesis with no verdict seals inconclusive: a finished run never reads as a proof by default."""
        if value is None:
            value = round(100.0 * self._ok / self._n, 2) if self._n else 0.0
        if self.hypothesis and not self.verdict:
            self.verdict = "inconclusive"
        return self._post(status="complete", value=value)

    def _post(self, status: str, value: float) -> Ack:
        e = {
            "id": self.id,
            "kind": self.kind,
            "subject": self.subject,
            "task": self.task,
            "metric": self.metric,
            "value": value,
            "n": self._n,
            "n_total": self.n_total,
            "status": status,
            "git_sha": self.prov["git_sha"],
            "git_branch": self.prov["git_branch"],
            "git_dirty": self.prov["git_dirty"],
            "lib_versions": self.libs,
            "meta": {
                "doc": self.doc,
                "commits": self.commits,
                "note": self.note,
                "host": self.host,
                "hypothesis": self.hypothesis,
                "predict": self.predict,
                "verdict": self.verdict,
                "because": self.because,
                "log": self._log,
            },
        }
        return self.c.ingest(experiments=[e])

    def __enter__(self) -> Experiment:
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if exc_type is not None:
            self._post(status="faulted", value=0.0)
        else:
            self.finish()
