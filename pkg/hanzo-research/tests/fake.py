"""An in-process stand-in for api.hanzo.ai's `/v1/research` and `/v1/benchmark`.

It answers as hanzo-inc/cloud `apps/research` (research.go, record.go, store.go) and
`apps/benchmark` (benchmark.go, claims.go, presets.go, history.go) do at the rules a client
can observe: the batch keys and their bounds, required fields, versions appended by
content and read back canonical (the latest that is not retracted), completion derived,
writes forced private, grants on every version, the public `?org=` read only to a caller
with no org, RFC 7807 refusals, the acting org chosen from the token's signed `orgs`, and
claims on the leaderboard only from org admin. JWTs are read, not verified.
"""

from __future__ import annotations

import json
import base64
import hashlib
import threading
import urllib.parse
from typing import Any
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

CATALOG = [
    {
        "id": "gpqa_diamond",
        "title": "GPQA-Diamond",
        "axis": "science-reasoning",
        "items": 198,
        "native": True,
        "source": "hendrydong/gpqa_diamond_mc",
    },
    {
        "id": "livecodebench",
        "title": "LiveCodeBench (v6)",
        "axis": "competitive-coding",
        "native": True,
        "source": "livecodebench/code_generation_lite test6",
    },
]
KEYS = {"benchmarks": "benchmarks", "runs": "runs", "studies": "studies", "papers": "papers"}
NEEDS = {"benchmarks": ("id",), "runs": ("id", "benchmark"), "studies": ("id",), "papers": ("id",)}
DERIVED = ("project", "canonical", "completion", "visibility", "trainable", "publishable")
GAPS = (
    "embedder",
    "facts_digest",
    "k",
    "prompt",
    "prompt_digest",
    "store_digest",
    "reader",
    "temperature",
    "max_tokens",
    "dataset_digest",
    "commit",
    "questions",
    "answered",
    "when",
    "ended",
    "by",
    "split",
    "system",
    "version",
)


def jwt(claims: dict[str, Any]) -> str:
    """An unsigned JWT carrying `claims` (the fake reads, never verifies)."""
    enc = lambda d: base64.urlsafe_b64encode(json.dumps(d).encode()).decode().rstrip("=")  # noqa: E731
    return f"{enc({'alg': 'none'})}.{enc(claims)}.sig"


def completion(r: dict[str, Any]) -> str:
    q, a = r.get("questions"), r.get("answered")
    if q is None or a is None:
        return "unknown"
    if a > q:
        return "inconsistent"
    if a < q:
        return "partial"
    return "complete" if (r.get("ended") or "").strip() else "unknown"


class Problem(Exception):
    def __init__(self, status: int, detail: str):
        super().__init__(detail)
        self.status, self.detail = status, detail


class Fake:
    """The server's state and its handlers; `requests` records every request it answered."""

    def __init__(self) -> None:
        self.versions: dict[tuple[str, str], list[dict[str, Any]]] = {}  # (org, kind) -> versions
        self.experiments: dict[str, list[dict[str, Any]]] = {}
        self.attempts: dict[str, list[dict[str, Any]]] = {}
        self.artifacts: dict[str, dict[str, dict[str, Any]]] = {}
        self.claims: list[dict[str, Any]] = []
        self.attempt_rows: list[dict[str, Any]] = []
        self.requests: list[dict[str, Any]] = []
        self.unavailable = 0  # answer the next N requests 503
        self.expired: set[str] = set()  # bearer tokens answered 401
        self.seq = 0
        self.lock = threading.Lock()

    # ── identity ────────────────────────────────────────────────────────────────

    def principal(self, headers: Any) -> dict[str, Any] | None:
        auth = headers.get("Authorization") or ""
        if not auth.startswith("Bearer "):
            return None
        parts = auth[7:].split(".")
        if len(parts) != 3:
            return None
        c = json.loads(base64.urlsafe_b64decode(parts[1] + "=" * (-len(parts[1]) % 4)))
        orgs = [m["org"] for m in c.get("orgs") or []] or [c.get("owner", "")]
        home = orgs[0]
        want = headers.get("X-Org-Id") or ""
        org = want if want and (home == "admin" or (want != "admin" and want in orgs)) else home
        return {
            "org": org,
            "home": home,
            "super": home == "admin",
            "user": c.get("sub", ""),
            "project": c.get("project") or "default",
        }

    # ── research: records ───────────────────────────────────────────────────────

    def canonical(self, org: str, kind: str) -> list[dict[str, Any]]:
        latest: dict[tuple[str, str], dict[str, Any]] = {}
        for v in self.versions.get((org, kind), []):
            latest[(v["project"], v["id"])] = v
        out = []
        for v in latest.values():
            if (v.get("revision") or "") == "retracted":
                continue
            r = dict(v)
            r.pop("_hash", None)
            r.pop("_seq", None)
            r["canonical"] = True
            if kind == "runs":
                r["completion"] = completion(r)
            out.append(r)
        return sorted(out, key=lambda r: (r["project"], r["id"]))

    def put(self, who: dict[str, Any], kind: str, body: dict[str, Any]) -> dict[str, Any]:
        rows = body.get(KEYS[kind]) or []
        if not rows:
            raise Problem(400, "nothing to record")
        if len(rows) > 20000:
            raise Problem(413, "batch too large; split the upload")
        for r in rows:
            if any(not r.get(f) for f in NEEDS[kind]):
                raise Problem(422, {"runs": "run needs an id and a benchmark"}.get(kind, f"{kind[:-1]} needs an id"))
        added = 0
        store = self.versions.setdefault((who["org"], kind), [])
        for r in rows:
            rec = {k: v for k, v in r.items() if k not in DERIVED}
            rec["revision"] = (
                (rec.get("revision") or "").strip().lower()
                if (rec.get("revision") or "").strip().lower() in ("corrected", "retracted")
                else "original"
            )
            h = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
            if any(v["_hash"] == h and v["id"] == r["id"] and v["project"] == who["project"] for v in store):
                continue
            self.seq += 1
            store.append(
                {
                    **rec,
                    "project": who["project"],
                    "visibility": "private",
                    "trainable": False,
                    "publishable": False,
                    "_hash": h,
                    "_seq": self.seq,
                }
            )
            added += 1
        return {"project": who["project"], "recorded": added, "canonical": len(self.canonical(who["org"], kind))}

    def runs(self, who: dict[str, Any] | None, q: dict[str, str]) -> dict[str, Any]:
        if who is None:
            if not q.get("org"):
                raise Problem(403, "a validated principal is required")
            rows = [r for r in self.canonical(q["org"], "runs") if r["visibility"] == "public"]
            if not rows:
                raise Problem(404, "Not Found")
        else:
            rows = self.canonical(who["org"], "runs")
        if q.get("completion") and q["completion"] not in ("complete", "partial", "inconsistent", "unknown"):
            raise Problem(422, "completion must be complete, partial, inconsistent, or unknown")
        for f in ("project", "id", "benchmark", "system", "study", "completion"):
            if q.get(f):
                rows = [r for r in rows if r.get(f) == q[f]]
        if q.get("since"):
            rows = [r for r in rows if (r.get("when") or "") >= q["since"]]
        if q.get("until"):
            rows = [r for r in rows if r.get("when") and r["when"] <= q["until"]]
        census = {
            k: sum(1 for r in rows if r["completion"] == k) for k in ("complete", "partial", "inconsistent", "unknown")
        }
        gaps = [{"field": f, "runs": n} for f in GAPS if (n := sum(1 for r in rows if r.get(f) in (None, "")))]
        return {"data": rows, "total": len(rows), "completion": census, "gaps": gaps}

    def compare(self, who: dict[str, Any], q: dict[str, str]) -> dict[str, Any]:
        if not q.get("a") or not q.get("b"):
            raise Problem(400, "compare needs two run ids, a and b")
        rows = {
            r["id"]: r
            for r in self.canonical(who["org"], "runs")
            if r["project"] == (q.get("project") or who["project"])
        }
        for k in ("a", "b"):
            if q[k] not in rows:
                raise Problem(404, f'no canonical run "{q[k]}"')
        a, b = rows[q["a"]], rows[q["b"]]
        blocks = []
        if a.get("benchmark") != b.get("benchmark"):
            blocks.append(f'different benchmarks: "{a.get("benchmark")}" and "{b.get("benchmark")}"')
        for r in (a, b):
            if r["completion"] != "complete":
                blocks.append(f'run "{r["id"]}" is not established as complete (completion {r["completion"]})')
        config = [
            {"field": f, "a": str(a.get(f) or ""), "b": str(b.get(f) or "")}
            for f in ("system", "version", "commit", "dataset_digest")
            if (a.get(f) or "") != (b.get(f) or "")
        ]
        index = {(m["category"], m["metric"]): m for m in b.get("measures") or []}
        deltas = []
        for m in a.get("measures") or []:
            n = index.get((m["category"], m["metric"]))
            if n:
                overlap = (
                    None
                    if None in (m.get("lo"), m.get("hi"), n.get("lo"), n.get("hi"))
                    else max(m["lo"], n["lo"]) <= min(m["hi"], n["hi"])
                )
                deltas.append(
                    {
                        "category": m["category"],
                        "metric": m["metric"],
                        "a": m["value"],
                        "b": n["value"],
                        "change": n["value"] - m["value"],
                        "overlap": overlap,
                    }
                )
        return {
            "a": a,
            "b": b,
            "comparable": not blocks,
            "blocks": blocks or None,
            "config": config or None,
            "deltas": deltas or None,
        }

    def grant(self, who: dict[str, Any], body: dict[str, Any]) -> dict[str, Any]:
        if not body.get("id") and not body.get("sha256"):
            raise Problem(400, "grant needs a stable id or an artifact sha256")
        vis = body.get("visibility")
        if vis is not None and vis not in ("private", "org", "public"):
            raise Problem(422, "visibility must be private, org, or public")
        project = body.get("project") or who["project"]
        n = 0
        if body.get("sha256"):
            if vis is None:
                raise Problem(400, "artifact grant needs a visibility")
            a = self.artifacts.get(who["org"], {}).get(body["sha256"])
            if a and a["project"] == project:
                a["visibility"], n = vis, 1
        else:
            for v in self.versions.get((who["org"], "runs"), []):
                if v["id"] == body["id"] and v["project"] == project:
                    for k in ("visibility", "trainable", "publishable"):
                        if body.get(k) is not None:
                            v[k] = body[k]
                    n += 1
        if n == 0:
            raise Problem(404, "no records for that target")
        return {"updated": n}

    # ── research: experiments and artifacts ─────────────────────────────────────

    def ingest(self, who: dict[str, Any], body: dict[str, Any]) -> dict[str, Any]:
        exps, atts = body.get("experiments") or [], body.get("attempts") or []
        if not exps and not atts:
            raise Problem(400, "ingest needs at least one experiment or attempt")
        for e in exps:
            if not (e.get("id") and e.get("kind") and e.get("subject")):
                raise Problem(422, "experiment needs id, kind, and subject")
        for a in atts:
            if not (a.get("benchmark") and a.get("item") and a.get("model")):
                raise Problem(422, "attempt needs benchmark, item, and model")
        ex = self.experiments.setdefault(who["org"], [])
        at = self.attempts.setdefault(who["org"], [])
        e_added = a_added = 0
        for e in exps:
            if {**e, "project": who["project"]} not in ex:
                ex.append({**e, "project": who["project"]})
                e_added += 1
        for a in atts:
            if a not in at:
                at.append(a)
                a_added += 1
        return {
            "project": who["project"],
            "experiments_ingested": e_added,
            "attempts_ingested": a_added,
            "canonical_experiments": len({e["id"] for e in ex}),
            "experiments_retained": len(ex),
            "canonical_attempts": len(at),
            "attempts_retained": len(at),
            "rolled_up": True,
        }

    def put_artifact(self, who: dict[str, Any], a: dict[str, Any]) -> dict[str, Any]:
        if a.get("kind") not in ("snapshot", "report"):
            raise Problem(422, "kind must be snapshot or report")
        raw = base64.b64decode(a.get("content") or "")
        if not raw:
            raise Problem(422, "content must be non-empty base64")
        h = hashlib.sha256(raw).hexdigest()
        if a.get("sha256") and a["sha256"].lower() != h:
            raise Problem(422, "sha256 does not match the content bytes")
        store = self.artifacts.setdefault(who["org"], {})
        created = h not in store
        rec = {k: a.get(k) for k in ("kind", "run_id", "git_sha", "git_branch", "git_dirty", "lib_versions", "ts")}
        store.setdefault(
            h,
            {
                **rec,
                "sha256": h,
                "ref": "sha256:" + h,
                "project": who["project"],
                "visibility": "private",
                "retention_class": "raw-artifact",
                "_bytes": raw,
            },
        )
        return {"sha256": h, "ref": "sha256:" + h, "created": created, "rolled_up": True}

    # ── the arena ───────────────────────────────────────────────────────────────

    def put_claims(self, who: dict[str, Any] | None, body: dict[str, Any]) -> dict[str, Any]:
        if who is None:
            raise Problem(401, "sign in")
        if who["org"] == "admin" and not who["super"]:
            raise Problem(403, "SuperAdmin required")
        vis = body.get("visibility") or "private"
        if vis not in ("private", "public"):
            raise Problem(400, 'visibility is "private" or "public"')
        out = {"recorded": 0, "rejected": [], "org": who["org"], "visibility": vis}
        known = {c["id"] for c in CATALOG}
        for i, c in enumerate(body.get("data") or []):
            if not c.get("benchmark") or not c.get("model"):
                out["rejected"].append(f"row {i}: needs a benchmark and a model")
            elif c["benchmark"] not in known:
                out["rejected"].append(f"row {i}: unknown benchmark")
            elif not str(c.get("source") or "").strip():
                out["rejected"].append(f"row {i}: a claim needs its source")
            elif not 0 <= float(c.get("score", -1)) <= 100:
                out["rejected"].append(f"row {i}: a score is a percentage from 0 to 100")
            else:
                self.claims.append(
                    {
                        **c,
                        "org": who["org"],
                        "visibility": vis,
                        "origin": "stored",
                        "at": "2026-10-15T00:00:00Z",
                        "by": who["user"],
                    }
                )
                out["recorded"] += 1
        if not out["rejected"]:
            del out["rejected"]
        return out

    def leaderboard(self, q: dict[str, str]) -> dict[str, Any]:
        bench = q.get("benchmark") or "gpqa_diamond"
        rows = []
        for c in self.claims:
            if c["benchmark"] == bench and c["org"] == "admin" and c["visibility"] == "public":
                rows.append(
                    {
                        "model": c["model"],
                        "measured": None,
                        "n": 0,
                        "published": c["score"],
                        "gap": None,
                        "protocol": c["protocol"],
                        "claims": 1,
                        "mean": c["score"],
                    }
                )
        return {"benchmark": bench, "rows": rows}

    # ── dispatch ────────────────────────────────────────────────────────────────

    def handle(self, method: str, url: str, headers: Any, raw: bytes) -> tuple[int, str, bytes]:
        parts = urllib.parse.urlsplit(url)
        path = parts.path
        q = {k: v[-1] for k, v in urllib.parse.parse_qs(parts.query).items()}
        body = json.loads(raw) if raw else None
        with self.lock:
            self.requests.append(
                {"method": method, "path": path, "query": q, "headers": dict(headers.items()), "body": body}
            )
            if self.unavailable:
                self.unavailable -= 1
                return 503, "application/json", b'{"detail":"research store failover in progress; retry","status":503}'
            if (headers.get("Authorization") or "").removeprefix("Bearer ") in self.expired:
                return 401, "application/json", b'{"detail":"token expired","status":401}'
            if path == "/redirect":
                return 302, "text/plain", b""
            who = self.principal(headers)
            try:
                out = self.route(method, path, q, body, who)
            except Problem as p:
                doc = {"detail": p.detail, "status": p.status, "title": "x", "type": "about:blank"}
                return p.status, "application/json", json.dumps(doc).encode()
            if isinstance(out, bytes):
                return 200, "application/octet-stream", out
            return out[0], "application/json", json.dumps(out[1]).encode()

    def route(self, method: str, path: str, q: dict[str, str], body: Any, who: dict[str, Any] | None) -> Any:
        ok = lambda x: (200, x)  # noqa: E731
        if path == "/v1/research/runs" and method == "GET":
            return ok(self.runs(who, q))
        if path.startswith("/v1/benchmark/"):
            return self.arena(method, path, q, body, who)
        if who is None:
            raise Problem(403, "a validated principal is required")
        name = path.removeprefix("/v1/research/")
        if method == "POST" and name in KEYS:
            return ok(self.put(who, name, body or {}))
        if method == "GET" and name in ("benchmarks", "studies", "papers"):
            rows = self.canonical(who["org"], name)
            for f in ("id", "project", "study"):
                if q.get(f):
                    rows = [r for r in rows if r.get(f) == q[f]]
            if q.get("cites"):
                rows = [r for r in rows if q["cites"] in (r.get("cites") or [])]
            return ok({"data": rows, "total": len(rows)})
        if name == "compare":
            return ok(self.compare(who, q))
        if name == "grants":
            return ok(self.grant(who, body or {}))
        if name == "experiments" and method == "POST":
            return ok(self.ingest(who, body or {}))
        if name == "experiments":
            rows = [
                e for e in self.experiments.get(who["org"], []) if not q.get("project") or e["project"] == q["project"]
            ]
            return ok({"data": rows, "total": len(rows)})
        if name == "totals":
            ex = self.experiments.get(who["org"], [])
            return ok(
                {
                    "projects": 1,
                    "experiments": len({e["id"] for e in ex}),
                    "experiments_retained": len(ex),
                    "attempts": len(self.attempts.get(who["org"], [])),
                    "by_kind": None,
                }
            )
        if name == "projects":
            return ok(
                {"data": [{"project": "default", "experiments": len(self.experiments.get(who["org"], []))}], "total": 1}
            )
        if name == "artifacts" and method == "POST":
            return ok(self.put_artifact(who, body or {}))
        if name == "artifacts":
            rows = [
                {k: v for k, v in a.items() if k != "_bytes"}
                for a in self.artifacts.get(who["org"], {}).values()
                if not q.get("run") or a["run_id"] == q["run"]
            ]
            return ok({"data": rows, "total": len(rows)})
        if name.startswith("artifacts/"):
            a = self.artifacts.get(who["org"], {}).get(name.removeprefix("artifacts/"))
            if not a:
                raise Problem(404, "artifact not found")
            return a["_bytes"]
        raise Problem(404, "Not Found")

    def arena(self, method: str, path: str, q: dict[str, str], body: Any, who: dict[str, Any] | None) -> Any:
        name = path.removeprefix("/v1/benchmark/")
        if name == "catalog":
            return 200, {"data": CATALOG, "total": len(CATALOG)}
        if name == "leaderboard":
            return 200, self.leaderboard(q)
        if name == "compare":
            if not q.get("a") or not q.get("b"):
                raise Problem(400, "compare needs ?a= and ?b= model ids")
            return 200, {
                "benchmark": q.get("benchmark") or "gpqa_diamond",
                "a": q["a"],
                "b": q["b"],
                "n_common": 0,
                "a_correct": 0,
                "b_correct": 0,
                "rescue_a_over_b": 0,
                "rescue_b_over_a": 0,
                "net_a_minus_b": 0,
                "mcnemar_p": 1,
            }
        if name == "history":
            return 200, {"benchmark": q.get("benchmark") or "gpqa_diamond", "data": [], "total": 0}
        if name == "claims" and method == "POST":
            return 200, self.put_claims(who, body or {})
        if name == "claims":
            rows = [c for c in self.claims if c["visibility"] == "public" or (who and c["org"] == who["org"])]
            for f in ("benchmark", "model", "provider", "source", "protocol", "org"):
                if q.get(f):
                    rows = [c for c in rows if c.get(f) == q[f]]
            return 200, {"data": rows, "total": len(rows)}
        if name == "presets" and method == "POST":
            if who is None:
                raise Problem(401, "sign in")
            p = dict(body or {}, owner=who["org"])
            if not p.get("name") or not p.get("arms"):
                raise Problem(400, "preset needs a name and at least one arm")
            p["rank"] = p.get("rank") or p["arms"]
            p["panel"] = max(1, int(p.get("panel") or 1))
            return 202, {
                "status": "accepted",
                "served_as": "enso-" + p["name"],
                "preset": p,
                "by": who["user"],
                "note": "n",
            }
        if name == "presets":
            return 200, {"data": [{"name": "ultra", "owner": "hanzo", "arms": ["a"], "rank": ["a"], "panel": 3}]}
        if name == "runs" and method == "POST":
            if who is None:
                raise Problem(401, "sign in")
            return 202, {
                "status": "queued",
                "org": who["org"],
                "by": who["user"],
                "benchmarks": (body or {}).get("benchmarks"),
            }
        raise Problem(404, "Not Found")


class Server:
    """The fake on a loopback port: `with Server() as s: Research(base=s.url, api_key=...)`."""

    def __init__(self) -> None:
        self.fake = Fake()
        fake = self.fake

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *a: Any) -> None:
                pass

            def answer(self) -> None:
                n = int(self.headers.get("Content-Length") or 0)
                status, ctype, out = fake.handle(
                    self.command, self.path, self.headers, self.rfile.read(n) if n else b""
                )
                self.send_response(status)
                if status == 302:
                    self.send_header("Location", "https://example.com/elsewhere")
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(out)))
                self.end_headers()
                self.wfile.write(out)

            do_GET = do_POST = answer

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}"
        self.thread = threading.Thread(target=self.httpd.serve_forever, args=(0.01,), daemon=True)

    def __enter__(self) -> Server:
        self.thread.start()
        return self

    def __exit__(self, *a: Any) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
