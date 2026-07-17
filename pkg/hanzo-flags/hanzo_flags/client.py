# Copyright 2026 Hanzo AI, Inc. All rights reserved.
"""Zero-dependency Python client for the Hanzo native flags engine.

It POSTs an evaluation context to ``<host>/v1/flags`` (the same PostHog-compatible
endpoint @hanzo/flags and the Go/Rust cores speak) and answers ``is_enabled`` /
``variant`` / ``payload`` from the response.

Two invariants, identical to @hanzo/flags:

  * **Fail-open.** A flag client must never take a request down. Any transport or
    decode error returns the last good result (or an empty one), with
    ``errors_while_computing`` set — never a raised exception on ``load``.
  * **Cached by context + TTL.** Re-evaluating the same context inside the TTL
    returns the cached result, so a hot path can call ``load`` freely.

Stdlib only (``urllib``) — a flag check should not drag httpx/pydantic into a
service and risk a version conflict.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

from .models import EvalContext, EvalResult, Group

_DEFAULT_TTL_MS = 15_000
_DEFAULT_TIMEOUT_S = 3.0


class HanzoFlags:
    """A flags client bound to one cloud host.

    Args:
        host: the cloud base URL, e.g. ``https://api.hanzo.ai``. Required.
        token: a bearer token; when absent the request relies on ambient
            (cookie/gateway) auth, exactly like the browser client.
        project: an optional ``X-Project-Id`` scope.
        ttl_ms: cache lifetime for a given context (default 15s).
        timeout_s: per-request timeout (default 3s).
    """

    def __init__(
        self,
        host: str,
        *,
        token: Optional[str] = None,
        project: Optional[str] = None,
        ttl_ms: int = _DEFAULT_TTL_MS,
        timeout_s: float = _DEFAULT_TIMEOUT_S,
    ) -> None:
        if not host:
            raise ValueError("hanzo-flags: host is required")
        self._host = host.rstrip("/")
        self._token = token
        self._project = project
        self._ttl_ms = ttl_ms
        self._timeout_s = timeout_s
        self._result = EvalResult()
        self._ctx_key = ""
        self._loaded_at = 0.0

    def load(
        self,
        distinct_id: str,
        *,
        person_properties: Optional[Dict[str, Any]] = None,
        groups: Optional[Dict[str, Group]] = None,
    ) -> EvalResult:
        """Evaluate flags for ``distinct_id`` and cache the result.

        Returns the same :class:`EvalResult` the convenience accessors read; call
        :meth:`is_enabled` / :meth:`variant` / :meth:`payload` after, or read the
        returned result directly.
        """
        ctx = EvalContext(distinct_id, person_properties=person_properties, groups=groups)
        key = json.dumps(ctx.wire(), sort_keys=True)
        if self._ctx_key == key and (time.monotonic() - self._loaded_at) * 1000 < self._ttl_ms:
            return self._result

        try:
            body = self._post(ctx.wire())
            self._result = EvalResult.from_wire(body)
        except Exception:
            # Fail-open: keep the last good result, flag the soft error.
            self._result.errors_while_computing = True
        finally:
            self._ctx_key = key
            self._loaded_at = time.monotonic()
        return self._result

    def _post(self, wire: Dict[str, Any]) -> Dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        if self._project:
            headers["X-Project-Id"] = self._project
        req = urllib.request.Request(
            f"{self._host}/v1/flags",
            data=json.dumps(wire).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self._timeout_s) as resp:
            if resp.status >= 400:
                raise urllib.error.HTTPError(req.full_url, resp.status, "flags", resp.headers, None)
            return json.loads(resp.read().decode("utf-8"))

    # ---- accessors read the last loaded result (call load() first) ----

    def is_enabled(self, key: str) -> bool:
        """True when ``key`` is on (boolean True or any non-empty variant)."""
        return self._result.is_enabled(key)

    def variant(self, key: str) -> Optional[str]:
        """The active variant of a multivariate flag, or ``None``."""
        return self._result.variant(key)

    def payload(self, key: str) -> Any:
        """The flag's JSON payload, or ``None``."""
        return self._result.payload(key)

    def all(self) -> EvalResult:
        """The last loaded result."""
        return self._result


def evaluate(
    host: str,
    distinct_id: str,
    *,
    token: Optional[str] = None,
    project: Optional[str] = None,
    person_properties: Optional[Dict[str, Any]] = None,
    groups: Optional[Dict[str, Group]] = None,
    timeout_s: float = _DEFAULT_TIMEOUT_S,
) -> EvalResult:
    """One-shot evaluation — the module-level convenience, like @hanzo/flags evaluateFlags."""
    client = HanzoFlags(host, token=token, project=project, timeout_s=timeout_s)
    return client.load(distinct_id, person_properties=person_properties, groups=groups)
