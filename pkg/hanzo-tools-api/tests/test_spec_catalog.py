"""Tests for the OpenAPI -> service/action projection.

Pure mapping tests: no network. These pin the contract that lets one MCP tool
stand in for every cloud service, so a regression here silently mis-routes
calls rather than failing loudly.
"""

import json

import pytest

from pathlib import Path

from hanzo_tools.api import spec as openapi


class _All(frozenset):  # type: ignore[type-arg]
    """An allow-set that contains everything, for specs that name no operations."""

    def __contains__(self, item: object) -> bool:
        return True


_EVERYTHING = _All()

SPEC = {
    "paths": {
        "/v1/billing/plans": {"get": {"tags": ["billing"]}},
        "/v1/billing/spend-alerts/{id}": {"delete": {"tags": ["billing"]}},
        "/v1/code/ask": {"get": {"tags": ["code"]}, "post": {"tags": ["code"]}},
        "/v1/kb/search": {"post": {"tags": ["kb"], "responses": {"200": {}}}},
        "/v1/iam": {"get": {"tags": ["iam"]}},
        "/v1/vector/{name}": {"get": {"tags": ["vector"]}},
        "/v1/vector/stats": {"get": {"tags": ["vector"]}},
        "/healthz": {"get": {}},  # untagged: still addressable
    }
}


@pytest.fixture
def catalog():
    # These exercise ROUTING — how a path and method are found — not which
    # operations the fleet offers an agent. This spec carries no operationIds, so
    # the offer rule would filter every one of them; it is asked for explicitly
    # elsewhere (test_the_offer_rule_filters) rather than weakened here.
    return openapi.Catalog(SPEC, allow=_EVERYTHING)


class TestActionNaming:
    @pytest.mark.parametrize(
        "path,tag,expected",
        [
            ("/v1/billing/plans", "billing", "plans"),
            ("/v1/iam", "iam", ""),
            ("/v1/vector/{name}", "vector", "{name}"),
            ("/v1/billing/spend-alerts/{id}", "billing", "spend-alerts/{id}"),
            ("/healthz", "_untagged", "healthz"),
        ],
    )
    def test_action_of(self, path, tag, expected):
        assert openapi.action_of(path, tag) == expected


class TestCatalog:
    def test_services_are_tags(self, catalog):
        assert catalog.services == [
            "_untagged",
            "billing",
            "code",
            "iam",
            "kb",
            "vector",
        ]

    def test_summary_counts_typed_ops(self, catalog):
        summary = catalog.summary()
        assert summary["kb"]["typed"] == 1  # has responses
        assert summary["billing"]["typed"] == 0  # router-shape only
        assert summary["code"]["operations"] == 2

    def test_describe_groups_methods_per_action(self, catalog):
        actions = catalog.describe("code")["actions"]
        assert actions["ask"]["methods"] == ["GET", "POST"]

    def test_unknown_service_raises(self, catalog):
        with pytest.raises(KeyError):
            catalog.resolve("nope", "x")

    def test_unknown_action_lists_known_ones(self, catalog):
        with pytest.raises(KeyError, match="plans"):
            catalog.resolve("billing", "nope")


class TestResolution:
    def test_exact_action(self, catalog):
        assert catalog.resolve("billing", "plans") == openapi.Route(
            "GET", "/v1/billing/plans", {}
        )

    def test_root_action(self, catalog):
        assert catalog.resolve("iam", "").path == "/v1/iam"

    def test_template_binds_from_action(self, catalog):
        route = catalog.resolve("vector", "my-coll")
        assert route.path == "/v1/vector/my-coll"
        assert route.bound == {"name": "my-coll"}

    def test_literal_beats_template(self, catalog):
        """`stats` is a real route; it must not be swallowed by {name}."""
        route = catalog.resolve("vector", "stats")
        assert route.path == "/v1/vector/stats" and route.bound == {}

    def test_nested_template(self, catalog):
        route = catalog.resolve("billing", "spend-alerts/a1")
        assert route.path == "/v1/billing/spend-alerts/a1"

    def test_method_override(self, catalog):
        assert catalog.resolve("code", "ask", method="post").method == "POST"

    def test_bad_method_reports_available(self, catalog):
        with pytest.raises(KeyError, match="GET"):
            catalog.resolve("billing", "plans", method="delete")

    def test_params_imply_write_absence_implies_read(self, catalog):
        assert catalog.resolve("code", "ask", has_params=True).method == "POST"
        assert catalog.resolve("code", "ask", has_params=False).method == "GET"


class TestParamSplit:
    def test_body_methods_get_a_body(self):
        route = openapi.Route("POST", "/v1/kb/search", {})
        query, body = openapi.split_params(route, {"query": "x"})
        assert query is None and body == {"query": "x"}

    def test_read_methods_get_a_query(self):
        route = openapi.Route("GET", "/v1/billing/plans", {})
        query, body = openapi.split_params(route, {"limit": 5})
        assert query == {"limit": 5} and body is None

    def test_bound_path_params_are_not_resent(self):
        route = openapi.Route("GET", "/v1/vector/c1", {"name": "c1"})
        query, _ = openapi.split_params(route, {"name": "c1", "limit": 2})
        assert query == {"limit": 2}


class TestSpecSource:
    def test_default_is_the_target_itself(self, monkeypatch):
        monkeypatch.delenv("HANZO_OPENAPI_URL", raising=False)
        assert openapi.spec_url("https://api.hanzo.ai") == (
            "https://api.hanzo.ai/v1/openapi.json"
        )

    def test_override_decouples_catalog_from_target(self, monkeypatch):
        monkeypatch.setenv("HANZO_OPENAPI_URL", "https://api.hanzo.ai/v1/openapi.json")
        assert openapi.spec_url("http://127.0.0.1:18080").startswith("https://")

    def test_cache_file_is_per_source(self, monkeypatch):
        monkeypatch.delenv("HANZO_OPENAPI_URL", raising=False)
        a = openapi.cache_file("https://api.hanzo.ai")
        b = openapi.cache_file("http://127.0.0.1:18080")
        assert a != b

    def test_stale_cache_beats_failing_the_call(self, monkeypatch, tmp_path):
        """A catalog is only route names; a stale one still routes."""
        cached = tmp_path / "openapi.json"
        cached.write_text(json.dumps(SPEC))
        monkeypatch.setattr(openapi, "cache_file", lambda _: cached)
        monkeypatch.setattr(
            openapi, "fetch", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("down"))
        )
        document, source = openapi.load("https://api.hanzo.ai", refresh=True)
        assert document == SPEC and source.startswith("cache-stale:")


def test_the_offer_rule_filters() -> None:
    """An operation the fleet withholds is not routable here either.

    The rule is cloud's and is applied once, there; this asserts it reaches the
    client through the shipped catalog rather than being restated.
    """
    spec = {
        "paths": {
            "/v1/iam/users": {
                "get": {"operationId": "get_iam_users", "tags": ["iam"]},
                "post": {"operationId": "post_iam_users", "tags": ["iam"]},
            }
        }
    }
    catalog = openapi.Catalog(spec)
    methods = {op.method for op in catalog.operations("iam")}
    assert "get" in methods, "reading who holds a role is offered"
    assert "post" not in methods, "mutating identity is withheld by the fleet"


def test_an_unreadable_catalog_offers_nothing(monkeypatch) -> None:
    """Failing open would widen the surface silently, so it fails closed."""
    monkeypatch.setattr(openapi, "_OFFERED_FILE", Path("/nonexistent/catalog.json"))
    openapi.offered.cache_clear()
    try:
        assert openapi.offered() == frozenset()
    finally:
        openapi.offered.cache_clear()
