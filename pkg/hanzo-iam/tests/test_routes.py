"""The canonical IAM addresses, pinned.

Two things must hold together, and pinning only the first is the dangerous half:

    path      a collection is a plural noun; one row of it is
              {collection}/{owner}/{name}. Verb-noun addresses answer 410.
    shape     a collection GET answers {"users": [...], "total": N}, a row GET
              answers the record itself, absence is 404, and a refusal is an
              RFC 9457 problem document. Only account, memberships, password
              and login answer the {status, msg, data} envelope.

The failure worth catching is not a crash: it is a reader that turns a
well-formed response into [] and reports "no users" for a healthy org. Every
case here asserts on the value.

Complements tests/test_endpoints.py, which pins that OIDC paths live under the
one /v1/iam prefix.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import httpx
import pytest

from hanzo_iam import routes
from hanzo_iam.client import IAMClient
from hanzo_iam.config import IAMConfig
from hanzo_iam.models import User

# Verb-noun addresses IAM retired. None may reappear in a path this SDK builds.
RETIRED = (
    "add-user",
    "update-user",
    "delete-user",
    "get-user",
    "get-users",
    "get-organization",
    "get-organizations",
    "get-application",
    "update-application",
    "get-applications",
    "get-role",
    "get-roles",
    "get-provider",
    "get-providers",
    "get-account",
    "add-user-role",
    "delete-user-role",
    "set-password",
    "enforce",
    "get-system-info",
)


class TestAddressTable:
    def test_every_collection_is_a_plural_noun_under_v1_iam(self):
        paths = [
            v
            for k, v in vars(routes).items()
            if k.isupper() and isinstance(v, str) and v.startswith("/v1/iam/")
        ]
        assert paths, "address table is empty — the constants moved"
        for p in paths:
            assert not p.startswith("/api/"), f"{p} names a prefix IAM does not serve"
            for verb in RETIRED:
                assert not p.endswith(f"/{verb}"), f"{p} is retired; it answers 410"

    def test_a_row_is_addressed_by_owner_and_name(self):
        assert routes.row(routes.USERS, "hanzo", "alice") == "/v1/iam/users/hanzo/alice"
        assert routes.row(routes.ROLES, "hanzo", "admin") == "/v1/iam/roles/hanzo/admin"

    def test_every_collection_declares_its_list_key(self):
        for name, path in vars(routes).items():
            if name in ("ACCOUNT", "MEMBERSHIPS", "PASSWORD", "LOGIN", "TOKEN"):
                continue
            if name.isupper() and isinstance(path, str) and path.startswith("/v1/iam/"):
                assert path in routes.LIST_KEY, (
                    f"{name} has no LIST_KEY — its lists would read as empty"
                )

    def test_token_endpoint_is_the_advertised_one(self):
        assert routes.TOKEN == "/v1/iam/oauth/token"

    def test_owner_name_fills_the_owner_only_when_absent(self):
        assert routes.owner_name("alice", "hanzo") == ("hanzo", "alice")
        assert routes.owner_name("zoo/alice", "hanzo") == ("zoo", "alice")


class TestReaders:
    def test_listing_returns_the_named_list(self):
        body = {"users": [{"name": "alice"}, {"name": "bob"}], "total": 2}
        assert routes.listing(body, "users") == body["users"]

    def test_listing_reads_a_null_list_as_empty(self):
        assert routes.listing({"users": None, "total": 0}, "users") == []

    def test_listing_refuses_a_bare_array(self):
        with pytest.raises(routes.IAMError, match="users"):
            routes.listing([{"name": "alice"}], "users")

    def test_listing_refuses_a_missing_key_instead_of_reading_it_as_empty(self):
        with pytest.raises(routes.IAMError, match="missing"):
            routes.listing({"total": 3}, "users")

    def test_envelope_returns_what_it_carries(self):
        assert routes.envelope({"status": "ok", "msg": "", "data": {"a": 1}}) == {"a": 1}

    def test_envelope_raises_on_a_stated_error(self):
        with pytest.raises(routes.IAMError, match="user not found"):
            routes.envelope({"status": "error", "msg": "user not found"})

    def test_check_returns_the_record_at_the_top_level(self):
        record = {"owner": "hanzo", "name": "alice", "email": "a@hanzo.ai"}
        response = httpx.Response(
            200, json=record, request=httpx.Request("GET", "https://hanzo.id/v1/iam/users/hanzo/alice")
        )
        assert routes.check(response) == record

    def test_check_raises_on_absence_and_keeps_the_status(self):
        request = httpx.Request("GET", "https://hanzo.id/v1/iam/users/hanzo/nobody")
        response = httpx.Response(404, json={"title": "not found"}, request=request)
        with pytest.raises(routes.IAMError) as caught:
            routes.check(response)
        assert caught.value.status == 404

    def test_check_carries_the_refusal_detail(self):
        request = httpx.Request("GET", "https://hanzo.id/v1/iam/users")
        response = httpx.Response(
            403,
            json={"type": "about:blank", "title": "forbidden", "detail": "org out of scope"},
            headers={"content-type": "application/problem+json"},
            request=request,
        )
        with pytest.raises(routes.IAMError, match="org out of scope"):
            routes.check(response)


def _client(handler) -> IAMClient:
    client = IAMClient(
        config=IAMConfig(
            server_url="https://hanzo.id",
            client_id="app-id",
            client_secret="app-secret",
            organization="hanzo",
            application="app",
        )
    )
    client._http = httpx.Client(
        base_url="https://hanzo.id", transport=httpx.MockTransport(handler)
    )
    return client


class TestClientAddressesAndAuth:
    @pytest.mark.parametrize(
        "call,method,path",
        [
            (lambda c: c.get_users(), "GET", "/v1/iam/users"),
            (lambda c: c.get_user("alice"), "GET", "/v1/iam/users/hanzo/alice"),
            (lambda c: c.get_user("zoo/alice"), "GET", "/v1/iam/users/zoo/alice"),
            (lambda c: c.get_user_count(), "GET", "/v1/iam/users"),
            (lambda c: c.get_organizations(), "GET", "/v1/iam/organizations"),
            (lambda c: c.get_organization("zoo"), "GET", "/v1/iam/organizations/admin/zoo"),
            (lambda c: c.get_providers(), "GET", "/v1/iam/providers"),
            (lambda c: c.get_roles(), "GET", "/v1/iam/roles"),
            (lambda c: c.get_role("admin"), "GET", "/v1/iam/roles/hanzo/admin"),
            (lambda c: c.get_application(), "GET", "/v1/iam/applications/hanzo/app"),
            (lambda c: c.get_applications("hanzo"), "GET", "/v1/iam/applications"),
            (
                lambda c: c.create_user(User(owner="hanzo", name="alice"), "pw"),
                "POST",
                "/v1/iam/users",
            ),
            (
                lambda c: c.update_user(User(owner="hanzo", name="alice")),
                "PUT",
                "/v1/iam/users/hanzo/alice",
            ),
            (
                lambda c: c.delete_user(User(owner="hanzo", name="alice")),
                "DELETE",
                "/v1/iam/users/hanzo/alice",
            ),
            (lambda c: c.set_password("hanzo", "alice", "pw"), "PUT", "/v1/iam/password"),
            (lambda c: c.login("alice", "pw"), "POST", "/v1/iam/login"),
        ],
    )
    def test_each_call_addresses_the_canonical_route(self, call, method, path):
        seen = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen["method"] = request.method
            seen["path"] = request.url.path
            return httpx.Response(
                200,
                json={
                    "users": [],
                    "organizations": [],
                    "providers": [],
                    "roles": [],
                    "applications": [],
                    "total": 0,
                    "deleted": True,
                    "status": "ok",
                    "data": {},
                    "owner": "hanzo",
                    "name": "alice",
                    "clientId": "app-id",
                },
            )

        call(_client(handler))
        assert (seen["method"], seen["path"]) == (method, path)

    def test_the_password_never_travels_as_a_user_row_field(self):
        seen = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen["body"] = request.read().decode()
            return httpx.Response(200, json={"owner": "hanzo", "name": "alice"})

        _client(handler).create_user(User(owner="hanzo", name="alice"), "secret-pw")
        body = __import__("json").loads(seen["body"])
        assert body["password"] == "secret-pw"
        assert "password" not in body["user"] or body["user"]["password"] is None

    def test_a_missing_user_raises_on_the_404_rather_than_reading_as_empty(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, json={"title": "not found"})

        with pytest.raises(routes.IAMError) as caught:
            _client(handler).get_user("nobody")
        assert caught.value.status == 404

    def test_role_membership_is_a_field_on_the_role_row(self):
        calls: list[tuple[str, str]] = []
        role = {"owner": "hanzo", "name": "admin", "users": ["hanzo/bob"]}

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append((request.method, request.url.path))
            if request.method == "PUT":
                role.update(__import__("json").loads(request.read()))
            return httpx.Response(200, json=role)

        client = _client(handler)
        assert client.add_role_for_user("alice", "admin") is True
        assert calls == [
            ("GET", "/v1/iam/roles/hanzo/admin"),
            ("PUT", "/v1/iam/roles/hanzo/admin"),
        ]
        assert role["users"] == ["hanzo/bob", "hanzo/alice"]

        assert client.remove_role_from_user("alice", "admin") is True
        assert role["users"] == ["hanzo/bob"]

        # Already absent: nothing to change, so no write.
        before = len(calls)
        assert client.remove_role_from_user("alice", "admin") is False
        assert [m for m, _ in calls[before:]] == ["GET"]


class TestClientsCarryNoRetiredAddress:
    @pytest.mark.parametrize("module", ["client", "async_client"])
    def test_no_retired_verb_in_client_source(self, module):
        spec = importlib.util.find_spec(f"hanzo_iam.{module}")
        assert spec and spec.origin
        src = Path(spec.origin).read_text()
        for verb in RETIRED:
            assert f'"{verb}"' not in src and f"/{verb}" not in src, (
                f"{module}.py still names {verb}, which IAM retired"
            )
        assert "oauth/access_token" not in src
        assert '"clientSecret"' not in src, (
            f"{module}.py names clientSecret as a request field; the credential "
            "belongs in the Authorization header and nowhere else"
        )
