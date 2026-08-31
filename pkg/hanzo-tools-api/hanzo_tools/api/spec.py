"""Service catalog projected from cloud's live OpenAPI registry.

Cloud generates ``/v1/openapi.json`` from the router it actually serves, and
tags every operation with its product — the first path segment after ``/v1/``.
That document therefore already IS a service/action catalog, so we project the
MCP surface from it instead of hand-listing services in Python: a new app is
reachable the moment cloud serves it, with no Python release. Hand-listing is
precisely what lets a tool surface drift out of date with the platform.

The catalog is a pure function of the spec. Fetching/caching is separate (see
``load``) so the mapping can be tested without a network.
"""

from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.request
from collections.abc import Iterable
from functools import lru_cache
from pathlib import Path
from typing import Any, NamedTuple

DEFAULT_BASE = "https://api.hanzo.ai"
logger = logging.getLogger(__name__)

SPEC_PATH = "/v1/openapi.json"

# What an agent may reach, generated from cloud's own typed operations
# (`plugin/gen-mcp-catalog`) and shipped beside this module.
#
# The published contract is NOT that set. cloud keeps an operation off the agent
# surface when its name discloses a bearer secret at any verb, or when a mutating
# verb acts on identity or authority — and /v1/openapi.json carries them anyway,
# because it describes the API rather than what a model is handed. Measured:
# `post_iam_users` is in the contract and is refused at /v1/mcp.
#
# So the document supplies each operation's METHOD and PATH, which a caller needs
# to make the request, and the catalog supplies which operations are OFFERED. Two
# facts, one source each, and the rule itself is asked of cloud rather than
# restated here.
_OFFERED_FILE = Path(__file__).with_name("catalog.json")


@lru_cache(maxsize=1)
def offered() -> frozenset[str]:
    """Every operation id the fleet offers an agent."""
    try:
        raw = json.loads(_OFFERED_FILE.read_text())
    except (OSError, ValueError):
        # An unreadable catalog must not silently widen the surface, so nothing
        # is offered rather than everything.
        logger.warning("agent catalog unreadable at %s; offering nothing", _OFFERED_FILE)
        return frozenset()
    return frozenset(op for entry in raw.values() for op in entry.get("ops", ()))
CACHE_TTL = 24 * 3600
METHODS = ("get", "post", "put", "patch", "delete", "head", "options")
# Methods that carry input as a JSON body; everything else takes a query string.
BODY_METHODS = frozenset({"post", "put", "patch"})


def api_base() -> str:
    """Resolve the cloud base URL (no trailing slash)."""
    base = (
        os.environ.get("HANZO_API_BASE")
        or os.environ.get("HANZO_BASE_URL")
        or DEFAULT_BASE
    )
    return base.rstrip("/")


class Route(NamedTuple):
    """One concrete call: a method, a path with params already bound."""

    method: str
    path: str
    # Params consumed by the path template, so the caller does not resend them.
    bound: dict[str, str]


class Operation(NamedTuple):
    method: str
    path: str
    action: str
    typed: bool


def _segments(path: str) -> list[str]:
    return [s for s in path.strip("/").split("/") if s]


def action_of(path: str, tag: str) -> str:
    """The action name for a path within its service.

    ``/v1/billing/plans`` under tag ``billing`` is the action ``plans``. The
    version and the service segment are dropped because they are already
    implied by the service, leaving the shortest thing a caller can name.
    """
    segs = _segments(path)
    if segs and segs[0] == "v1":
        segs = segs[1:]
    if segs and segs[0] == tag:
        segs = segs[1:]
    return "/".join(segs)


def _bind(want: str, have: str) -> dict[str, str] | None:
    """Match a requested action against a (possibly templated) action.

    Returns the path-param bindings, or None if it does not match. A literal
    action wins over a template because an exact match binds nothing.
    """
    w, h = _segments(want), _segments(have)
    if len(w) != len(h):
        return None
    bound: dict[str, str] = {}
    for got, pat in zip(w, h, strict=True):  # lengths checked above
        if len(pat) > 2 and pat[0] == "{" and pat[-1] == "}":
            bound[pat[1:-1]] = got
        elif got != pat:
            return None
    return bound


class Catalog:
    """Services and actions derived from an OpenAPI document."""

    def __init__(self, spec: dict[str, Any], allow: frozenset[str] | None = None):
        self.spec = spec
        allow = offered() if allow is None else allow
        self._ops: dict[str, list[Operation]] = {}
        for path, item in (spec.get("paths") or {}).items():
            if not isinstance(item, dict):
                continue
            for method, op in item.items():
                if method not in METHODS or not isinstance(op, dict):
                    continue
                # An op is typed when cloud folded a real schema in; untyped ops
                # are router-shape only and take params on trust.
                typed = bool(op.get("requestBody") or op.get("responses"))
                # Withheld once, in cloud. An operation the fleet refuses to hand
                # an agent is not offered here either.
                if op.get("operationId") not in allow:
                    continue
                for tag in op.get("tags") or ["_untagged"]:
                    self._ops.setdefault(tag, []).append(
                        Operation(method, path, action_of(path, tag), typed)
                    )

    @property
    def services(self) -> list[str]:
        return sorted(self._ops)

    def operations(self, service: str) -> list[Operation]:
        return sorted(self._ops.get(service, []), key=lambda o: (o.action, o.method))

    def summary(self) -> dict[str, Any]:
        """Compact catalog: every service with its operation and typed counts."""
        return {
            svc: {
                "actions": len({o.action for o in ops}),
                "operations": len(ops),
                "typed": sum(1 for o in ops if o.typed),
            }
            for svc, ops in sorted(self._ops.items())
        }

    def describe(self, service: str) -> dict[str, Any]:
        ops = self.operations(service)
        if not ops:
            raise KeyError(service)
        actions: dict[str, dict[str, Any]] = {}
        for o in ops:
            entry = actions.setdefault(
                o.action, {"methods": [], "path": o.path, "typed": False}
            )
            entry["methods"].append(o.method.upper())
            entry["typed"] = entry["typed"] or o.typed
        return {"service": service, "actions": actions}

    def resolve(
        self,
        service: str,
        action: str,
        method: str | None = None,
        has_params: bool = False,
    ) -> Route:
        """Pick the one route named by (service, action).

        Exact action matches beat templated ones. When several methods share an
        action and the caller did not name one, params imply a write (POST) and
        their absence implies a read (GET) — the intent the caller expressed.
        """
        ops = self._ops.get(service)
        if not ops:
            raise KeyError(f"unknown service '{service}'")

        want = (action or "").strip("/")
        exact: list[tuple[Operation, dict[str, str]]] = []
        templated: list[tuple[Operation, dict[str, str]]] = []
        for o in ops:
            bound = _bind(want, o.action)
            if bound is None:
                continue
            (exact if not bound else templated).append((o, bound))

        candidates = exact or templated
        if not candidates:
            known = sorted({o.action for o in ops})[:20]
            raise KeyError(
                f"unknown action '{action}' for service '{service}'. "
                f"Known actions: {', '.join(known) or '(none)'}"
            )

        if method:
            m = method.lower()
            picked = [c for c in candidates if c[0].method == m]
            if not picked:
                have = sorted({c[0].method.upper() for c in candidates})
                raise KeyError(
                    f"{service}/{action} does not accept {m.upper()}; "
                    f"available: {', '.join(have)}"
                )
        elif len(candidates) == 1:
            picked = candidates
        else:
            prefer = "post" if has_params else "get"
            picked = [c for c in candidates if c[0].method == prefer] or candidates

        op, bound = picked[0]
        path = op.path
        for name, value in bound.items():
            path = path.replace("{" + name + "}", value)
        return Route(op.method.upper(), path, bound)


def cache_file(base: str) -> Path:
    """Cache location for a base URL. Distinct hosts must not share a file."""
    slug = base.split("://", 1)[-1].replace("/", "_").replace(":", "_")
    return Path.home() / ".hanzo" / "cache" / f"openapi-{slug}.json"


def spec_url(base: str) -> str:
    """Where to read the registry from.

    Normally the target itself publishes it. ``HANZO_OPENAPI_URL`` separates the
    two so a catalog can be read from one cloud while calls go to another — the
    case when driving a partial local host, which mounts only some apps and so
    cannot serve the whole registry.
    """
    return os.environ.get("HANZO_OPENAPI_URL") or (base.rstrip("/") + SPEC_PATH)


def fetch(base: str, timeout: float = 60.0) -> dict[str, Any]:
    """Fetch the spec straight from the running cloud."""
    url = spec_url(base)
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as e:
        raise RuntimeError(f"cannot fetch OpenAPI spec from {url}: {e}") from e


def load(
    base: str | None = None,
    refresh: bool = False,
    ttl: float = CACHE_TTL,
) -> tuple[dict[str, Any], str]:
    """Return (spec, source). Cache is a speed-up, never a source of truth.

    A stale cache is still preferred over failing the call outright: the
    catalog only names routes, and a name that has since moved fails loudly at
    call time anyway.
    """
    base = (base or api_base()).rstrip("/")
    path = cache_file(spec_url(base))
    fresh = (
        not refresh
        and path.exists()
        and (time.time() - path.stat().st_mtime) < ttl
    )
    if fresh:
        try:
            return json.loads(path.read_text()), f"cache:{path}"
        except (OSError, ValueError):
            pass  # corrupt cache: fall through and refetch

    try:
        spec = fetch(base)
    except RuntimeError:
        if path.exists():
            try:
                return json.loads(path.read_text()), f"cache-stale:{path}"
            except (OSError, ValueError):
                pass
        raise

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(spec))
    except OSError:
        pass  # a read-only home must not break the call
    return spec, spec_url(base)


def split_params(
    route: Route, params: dict[str, Any]
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Split caller params into (query, body) for a route.

    Params already consumed by the path template are dropped so they are not
    also sent as query/body noise.
    """
    rest: dict[str, Any] = {
        k: v for k, v in params.items() if k not in route.bound and v is not None
    }
    if route.method.lower() in BODY_METHODS:
        return None, rest
    return rest or None, None


def iter_actions(ops: Iterable[Operation]) -> list[str]:
    return sorted({o.action for o in ops})
