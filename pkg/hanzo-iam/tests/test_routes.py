"""The native-route migration, pinned.

These admin methods had NO coverage while they called the legacy verb surface,
which is why migrating them was the risk. The dangerous failure is not a crash:
it is `unwrap` returning [] for a well-formed response, so a caller sees "no
users" instead of an error. Every case asserts on the value.

Complements tests/test_endpoints.py, which pins that OIDC paths live under the
one /v1/iam prefix. This file pins that no legacy VERB survives anywhere.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from hanzo_iam import routes


class TestRoutesAreNative:
    def test_no_verb_paths_in_the_table(self):
        paths = [
            v for k, v in vars(routes).items()
            if k.isupper() and isinstance(v, str) and v.startswith("/v1/iam/")
        ]
        assert paths, "route table is empty — the constants moved"
        for p in paths:
            assert "/get-" not in p, f"{p} is a legacy verb; the server is removing it"
            assert "access_token" not in p, (
                f"{p} is the legacy token spelling; OIDC discovery advertises "
                "/v1/iam/oauth/token and only that"
            )

    def test_token_endpoint_is_the_advertised_one(self):
        assert routes.TOKEN == "/v1/iam/oauth/token"

    def test_every_list_route_declares_its_key(self):
        for name in ("USERS", "APPLICATIONS", "ORGANIZATIONS", "PROVIDERS", "ROLES"):
            path = getattr(routes, name)
            assert path in routes.LIST_KEY, (
                f"{name} has no LIST_KEY — its lists would unwrap to [] and read as empty"
            )


class TestUnwrapReadsBothShapes:
    def test_native_single_object(self):
        body = {"owner": "hanzo", "name": "alice", "id": "hanzo/alice"}
        assert routes.unwrap(body) == body

    def test_legacy_envelope_single_object(self):
        inner = {"owner": "hanzo", "name": "alice"}
        assert routes.unwrap({"status": "ok", "msg": "", "data": inner}) == inner

    def test_native_list(self):
        body = {"users": [{"name": "alice"}, {"name": "bob"}]}
        assert routes.unwrap(body, "users") == body["users"]

    def test_legacy_envelope_list(self):
        body = {"status": "ok", "msg": "", "data": [{"name": "alice"}]}
        assert routes.unwrap(body, "users") == body["data"]

    def test_native_null_list_is_a_list_not_none(self):
        assert routes.unwrap({"users": None}, "users") == []

    def test_legacy_error_envelope_raises(self):
        with pytest.raises(ValueError, match="user not found"):
            routes.unwrap({"status": "error", "msg": "user not found"})

    def test_legacy_error_raises_on_the_list_path_too(self):
        with pytest.raises(ValueError):
            routes.unwrap({"status": "error", "msg": "nope"}, "users")

    def test_a_native_row_with_a_data_column_is_not_unwrapped(self):
        body = {"owner": "hanzo", "name": "cfg", "data": {"k": "v"}}
        assert routes.unwrap(body) == body

    def test_non_dict_passes_through(self):
        assert routes.unwrap([1, 2]) == [1, 2]


class TestClientsCarryNoPathLiterals:
    @pytest.mark.parametrize("module", ["client", "async_client"])
    def test_no_legacy_verb_in_client_source(self, module):
        spec = importlib.util.find_spec(f"hanzo_iam.{module}")
        assert spec and spec.origin
        src = Path(spec.origin).read_text()
        for verb in ("get-user", "get-users", "get-application", "get-organization",
                     "get-provider", "get-role"):
            assert f"/{verb}" not in src, (
                f"{module}.py still names the legacy verb {verb}; the server is removing it"
            )
        assert "oauth/access_token" not in src, (
            f"{module}.py still uses the legacy token spelling"
        )
