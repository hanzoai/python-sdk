# Copyright 2026 Hanzo AI, Inc. All rights reserved.
"""hanzo-flags client tests — no network: a local stub HTTP server stands in for
cloud /v1/flags, so the request shape, response decode, caching, fail-open, and
accessors are all exercised deterministically.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from hanzo_flags import EvalResult, Group, HanzoFlags, evaluate

# ---- a tiny stub of the /v1/flags endpoint ---------------------------------

_RESPONSE = {
    "featureFlags": {"checkout-exp": True, "pricing-test": "variant-b", "off-flag": False},
    "featureFlagPayloads": {"pricing-test": {"price": 9}},
    "errorsWhileComputingFlags": False,
}


class _Handler(BaseHTTPRequestHandler):
    last_body = None
    last_headers = None
    status = 200

    def do_POST(self):  # noqa: N802
        n = int(self.headers.get("Content-Length", 0))
        _Handler.last_body = json.loads(self.rfile.read(n) or b"{}")
        _Handler.last_headers = dict(self.headers)
        self.send_response(_Handler.status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(_RESPONSE).encode())

    def log_message(self, *_):  # silence
        pass


@pytest.fixture()
def server():
    srv = HTTPServer(("127.0.0.1", 0), _Handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    _Handler.status = 200
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


# ---- the deliverable: login/usage accessors resolve correctly --------------


def test_is_enabled_variant_payload(server):
    flags = HanzoFlags(server, token="tok")
    flags.load("user-123", person_properties={"plan": "pro"})

    assert flags.is_enabled("checkout-exp") is True
    # A variant flag is "enabled" AND exposes its variant + payload.
    assert flags.is_enabled("pricing-test") is True
    assert flags.variant("pricing-test") == "variant-b"
    assert flags.payload("pricing-test") == {"price": 9}
    # A false flag is off; an unknown flag is off and yields no variant/payload.
    assert flags.is_enabled("off-flag") is False
    assert flags.is_enabled("nope") is False
    assert flags.variant("nope") is None
    assert flags.payload("nope") is None


def test_request_shape_is_posthog_compatible(server):
    flags = HanzoFlags(server, token="tok", project="proj-1")
    flags.load(
        "u1",
        person_properties={"plan": "pro"},
        groups={"0": Group(key="acme", properties={"tier": "gold"})},
    )
    body = _Handler.last_body
    assert body["distinct_id"] == "u1"
    assert body["person_properties"] == {"plan": "pro"}
    assert body["groups"] == {"0": {"key": "acme", "properties": {"tier": "gold"}}}
    # Auth + project scoping ride as headers.
    assert _Handler.last_headers.get("Authorization") == "Bearer tok"
    assert _Handler.last_headers.get("X-Project-Id") == "proj-1"


def test_caches_within_ttl(server):
    flags = HanzoFlags(server, ttl_ms=60_000)
    flags.load("u1")
    _Handler.last_body = None  # a second load with the same ctx must NOT hit the server
    flags.load("u1")
    assert _Handler.last_body is None
    # A different context DOES re-evaluate.
    flags.load("u2")
    assert _Handler.last_body is not None


def test_fail_open_on_server_error(server):
    _Handler.status = 500
    flags = HanzoFlags(server)
    res = flags.load("u1")  # must NOT raise
    assert isinstance(res, EvalResult)
    assert res.errors_while_computing is True
    assert flags.is_enabled("anything") is False  # empty, fail-open


def test_fail_open_on_unreachable_host():
    # Nothing is listening — load must fail open, never raise.
    flags = HanzoFlags("http://127.0.0.1:9", timeout_s=0.2)
    res = flags.load("u1")
    assert res.errors_while_computing is True
    assert flags.is_enabled("x") is False


def test_module_evaluate_oneshot(server):
    res = evaluate(server, "u1", token="tok")
    assert res.is_enabled("checkout-exp") is True
    assert res.variant("pricing-test") == "variant-b"


def test_host_required():
    with pytest.raises(ValueError):
        HanzoFlags("")
