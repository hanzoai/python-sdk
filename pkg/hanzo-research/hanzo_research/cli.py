"""`hanzo-research`: file, grant, read and compare research records from a shell.

    hanzo-research post runs.jsonl --grant public --publishable
    hanzo-research post plan.json                 # {"benchmarks": [...], "runs": [...], ...}
    hanzo-research list runs --benchmark decision.latency
    hanzo-research list runs --org hanzo          # an org's public runs, no credential
    hanzo-research get decision.latency-loopback-dgx.cpu-kai --org hanzo
    hanzo-research grant RUN_ID ... --visibility public --publishable
    hanzo-research retract RUN_ID --why "read on the wrong split"
    hanzo-research compare RUN_A RUN_B
    hanzo-research provenance --model kai-1.3 --weights /models/kai-1.3 --device cpu
    hanzo-research arena leaderboard --benchmark gpqa_diamond

Every answer is JSON on stdout. The token is HANZO_API_KEY, else `hanzo auth token`.
"""

from __future__ import annotations

import os
import sys
import json
import argparse
from typing import Any, Iterable

from .wire import Run, Paper, Study, Benchmark, dump
from .client import Research
from .errors import Error
from .benchmark import Arena
from .provenance import capture

KINDS = {"run": "runs", "benchmark": "benchmarks", "study": "studies", "paper": "papers"}


def read(path: str) -> Any:
    """A JSON document, or the records of a JSON Lines file, from a path or `-` for stdin."""
    text = sys.stdin.read() if path == "-" else open(path, encoding="utf-8").read()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return [json.loads(line) for line in text.splitlines() if line.strip()]


def plan(doc: Any, kind: str) -> dict[str, list[Any]]:
    """What a document files, by kind: a plan's keys, else its records as one kind."""
    if isinstance(doc, dict) and any(k in doc for k in KINDS.values()):
        return {k: list(doc[k]) for k in ("benchmarks", "studies", "runs", "papers") if doc.get(k)}
    return {KINDS[kind]: doc if isinstance(doc, list) else [doc]}


def main(argv: Iterable[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="hanzo-research", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--base", help="API base (RESEARCH_BASE, else https://api.hanzo.ai)")
    p.add_argument("--org", help="act in this org (X-Org-Id); the token must belong to it")
    p.add_argument("--project", help="the token's project (default: its claim)")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("post", help="file records from a JSON or JSON Lines file")
    s.add_argument("file")
    s.add_argument("--kind", choices=KINDS, default="run", help="what a bare record or list is (default run)")
    s.add_argument("--grant", choices=("private", "org", "public"), help="then set the filed runs' visibility")
    s.add_argument("--publishable", action=argparse.BooleanOptionalAction, help="with the grant: commons consent")
    s.add_argument("--trainable", action=argparse.BooleanOptionalAction, help="with the grant: training consent")
    s.add_argument("--dry", action="store_true", help="print the bodies, file nothing")

    s = sub.add_parser("list", help="canonical records")
    s.add_argument(
        "what",
        nargs="?",
        default="runs",
        choices=("runs", "benchmarks", "studies", "papers", "experiments", "artifacts", "projects", "totals"),
    )
    for f in ("id", "benchmark", "system", "study", "completion", "since", "until", "kind", "run", "cites"):
        s.add_argument(f"--{f}")
    s.add_argument("--org", dest="public", help="runs: that org's public runs, no credential")
    s.add_argument("--in", dest="scope", help="narrow to one project of the org")

    s = sub.add_parser("get", help="one record's canonical version")
    s.add_argument("id")
    s.add_argument("--kind", choices=KINDS, default="run")
    s.add_argument("--org", dest="public", help="read that org's public runs, no credential")

    s = sub.add_parser("grant", help="visibility and consent for runs, or an artifact by --sha256")
    s.add_argument("ids", nargs="*")
    s.add_argument("--sha256")
    s.add_argument("--visibility", choices=("private", "org", "public"))
    s.add_argument("--publishable", action=argparse.BooleanOptionalAction)
    s.add_argument("--trainable", action=argparse.BooleanOptionalAction)

    s = sub.add_parser("retract", help="withdraw a run: a version marked retracted")
    s.add_argument("id")
    s.add_argument("--why", required=True)

    s = sub.add_parser("compare", help="two runs side by side")
    s.add_argument("a")
    s.add_argument("b")

    s = sub.add_parser("provenance", help="print what capture() reads here")
    s.add_argument("--repo")
    s.add_argument("--model", default="")
    s.add_argument("--weights")
    s.add_argument("--device", default="")
    s.add_argument("--dtype", default="")
    s.add_argument("--package", action="append", help="a distribution whose version pins the result")
    s.add_argument("--no-gpu", action="store_true")

    s = sub.add_parser("arena", help="the /v1/benchmark arena")
    s.add_argument("what", choices=("catalog", "leaderboard", "claims", "history", "compare", "presets"))
    s.add_argument("models", nargs="*", help="compare: two model ids")
    for f in ("benchmark", "model", "provider", "source", "protocol"):
        s.add_argument(f"--{f}")
    s.add_argument("--of", dest="owner", help="claims: only this org's")

    a = p.parse_args(list(argv) if argv is not None else None)
    try:
        out = run(a)
    except Error as e:
        print(f"hanzo-research: {e}", file=sys.stderr)
        return 1
    except (OSError, ValueError) as e:
        print(f"hanzo-research: {e}", file=sys.stderr)
        return 2
    try:
        json.dump(dump(out), sys.stdout, indent=1, ensure_ascii=False)
        sys.stdout.write("\n")
        sys.stdout.flush()
    except BrokenPipeError:
        # the reader stopped early (`| head`): end quietly
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
    return 0


def run(a: argparse.Namespace) -> Any:
    r = Research(base=a.base, project=a.project, org=a.org, repo=".")
    if a.cmd == "post":
        filed = plan(read(a.file), a.kind)
        if a.dry:
            return filed
        out: dict[str, Any] = dict(r.record(**filed))
        if a.grant or a.publishable is not None or a.trainable is not None:
            ids = [dump(x)["id"] for x in filed.get("runs", [])]
            out["granted"] = {
                i: r.grant(i, visibility=a.grant, publishable=a.publishable, trainable=a.trainable) for i in ids
            }
        return out
    if a.cmd == "list":
        w = a.what
        if w == "runs":
            return r.runs(
                id=a.id,
                benchmark=a.benchmark,
                system=a.system,
                study=a.study,
                completion=a.completion,
                since=a.since,
                until=a.until,
                project=a.scope,
                org=a.public,
            )
        if w == "benchmarks":
            return r.benchmarks(id=a.id, project=a.scope)
        if w == "studies":
            return r.studies(id=a.id, project=a.scope)
        if w == "papers":
            return r.papers(id=a.id, study=a.study, cites=a.cites, project=a.scope)
        if w == "experiments":
            return r.query(project=a.scope, kind=a.kind)
        if w == "artifacts":
            return r.artifacts(run=a.run, project=a.scope)
        if w == "projects":
            return r.projects()
        return r.totals(project=a.scope)
    if a.cmd == "get":
        if a.kind == "run":
            return r.get_run(a.id, org=a.public)
        if a.kind == "benchmark":
            return r.get_benchmark(a.id)
        rows: list[Any] = list(r.studies(id=a.id)) if a.kind == "study" else list(r.papers(id=a.id))
        if not rows:
            raise Error(f"no canonical {a.kind} {a.id!r}", 404)
        return rows[0]
    if a.cmd == "grant":
        if a.sha256:
            return {a.sha256: r.grant(sha256=a.sha256, visibility=a.visibility)}
        if not a.ids:
            raise ValueError("grant needs run ids or --sha256")
        return {i: r.grant(i, visibility=a.visibility, publishable=a.publishable, trainable=a.trainable) for i in a.ids}
    if a.cmd == "retract":
        return r.retract(a.id, a.why)
    if a.cmd == "compare":
        return r.compare(a.a, a.b)
    if a.cmd == "provenance":
        return capture(
            repo=a.repo,
            model=a.model,
            weights=a.weights,
            device=a.device,
            dtype=a.dtype,
            packages=a.package,
            gpu=not a.no_gpu,
        )
    arena = Arena(transport=r.http)
    bench = a.benchmark or "gpqa_diamond"
    if a.what == "catalog":
        return arena.catalog()
    if a.what == "leaderboard":
        return arena.leaderboard(bench)
    if a.what == "claims":
        return arena.claims(
            benchmark=a.benchmark, model=a.model, provider=a.provider, source=a.source, protocol=a.protocol, org=a.owner
        )
    if a.what == "history":
        return arena.history(bench, a.model)
    if a.what == "compare":
        if len(a.models) != 2:
            raise ValueError("arena compare needs two model ids")
        return arena.compare(a.models[0], a.models[1], bench)
    return arena.presets()


if __name__ == "__main__":
    sys.exit(main())
