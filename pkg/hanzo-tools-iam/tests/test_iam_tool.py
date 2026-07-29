"""The IAM tool must never invent a tenant.

This is an MCP tool: the caller is a language model, so the tenant it acts in
is not a deployment constant a reviewer can eyeball -- it is whatever identity
the running agent holds. The tool therefore has exactly ONE source for "which
organization am I": IAM's own /v1/iam/whoami, which resolves the token subject
to the live user row and returns the same `owner` its authorization layer pins
every request to. No literal, no configuration, no token claim.

The defect these tests pin shut: `owner = owner or "hanzo"` in the list/create
paths, `params={"owner": "hanzo"}` with no parameter at all for roles and
permissions, and `params={"owner": "admin"}` for orgs/providers/apps/tokens/
sessions/invitations/records. An agent running as any other tenant addressed
hanzo's rows and reported them as its own.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import httpx
import pytest
from hanzo_iam.models import IAM_WHOAMI_PATH, IAM_ROUTE_PREFIX, OIDC_DISCOVERY_PATH
from hanzo_tools.iam.iam_tool import IAM_BASE_URL, IAMTool

SOURCE = Path(__file__).resolve().parents[1] / "hanzo_tools" / "iam" / "iam_tool.py"

# Endpoints are imported from hanzo_iam, never re-spelled -- here least of all.
# A test that re-derives the path it is checking passes when both copies drift
# together, and this module must be importable against the OLD source for its
# failures to mean "the behaviour is wrong" rather than "a symbol is missing".
WHOAMI = IAM_WHOAMI_PATH

# The two listings the verb-alias layer does not cover; they use the REST
# surface, which answers with a named collection instead of an envelope.
TYPED = {
    f"{IAM_ROUTE_PREFIX}/tokens": "tokens",
    f"{IAM_ROUTE_PREFIX}/sessions/list": "sessions",
}
FREE = (WHOAMI, OIDC_DISCOVERY_PATH)


# --------------------------------------------------------------------------
# Harness: a fake IAM that records every request and answers in IAM's shapes.
# --------------------------------------------------------------------------


class FakeIAM:
    """Records requests; answers whoami as `principal` and lists as `rows`."""

    def __init__(self, principal: str | None = "acme", rows: list | None = None):
        self.principal = principal
        self.rows = rows if rows is not None else []
        self.seen: list[httpx.Request] = []
        self.envelope: dict | None = None  # override the entity answer

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.seen.append(request)
        path = request.url.path
        if path == WHOAMI:
            if self.principal is None:
                return httpx.Response(200, json={"status": "error", "msg": "please sign in first"})
            return httpx.Response(200, json={
                "status": "ok",
                "sub": f"{self.principal}/agent",
                "name": "agent",
                "data": {"owner": self.principal, "name": "agent", "isAdmin": False},
            })
        if path == OIDC_DISCOVERY_PATH:
            return httpx.Response(200, json={"issuer": IAM_BASE_URL})
        if self.envelope is not None:
            return httpx.Response(200, json=self.envelope)
        if path in TYPED:
            return httpx.Response(200, json={TYPED[path]: self.rows})
        return httpx.Response(200, json={"status": "ok", "msg": "", "data": self.rows})

    # -- assertions -------------------------------------------------------

    def scoped(self) -> list[httpx.Request]:
        """Every request that was not the identity or health probe."""
        return [r for r in self.seen if r.url.path not in FREE]

    def owners(self) -> list[str | None]:
        """The organization each entity request addressed, query or body."""
        out: list[str | None] = []
        for r in self.scoped():
            if r.url.params.get("owner") is not None:
                out.append(r.url.params.get("owner"))
            elif r.content:
                body = json.loads(r.content)
                out.append(body.get("owner") or body.get("user", {}).get("owner"))
            else:
                out.append(None)
        return out


def _credential(monkeypatch, token: str | None):
    """Give the tool a bearer by patching the SEAM, not a private helper.

    The credential comes from hanzo-tools-auth's session singleton -- the one
    thing `hanzo login` writes. Patching that (rather than some `_token` inside
    the module under test) keeps these tests aimed at behaviour: they run
    against any arrangement of the tool's internals, so a failure means the
    tenant handling is wrong, never that a private name was renamed.
    """
    monkeypatch.setattr(
        "hanzo_tools.auth.session.HanzoSession.get_iam_token",
        lambda self: token,
        raising=True,
    )


@pytest.fixture
def iam(monkeypatch):
    """Point the tool at a fake IAM and give it a credential."""
    fake = FakeIAM()
    real_init = httpx.AsyncClient.__init__

    def init(self, *args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(fake)
        real_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "__init__", init)
    _credential(monkeypatch, "test-bearer")
    return fake


async def call(action: str, **kw) -> dict:
    return json.loads(await IAMTool().call(None, action=action, **kw))


# --------------------------------------------------------------------------
# The literal is gone -- from the source, not merely from one code path.
# --------------------------------------------------------------------------


def _code_strings(path: Path) -> list[str]:
    """Every string literal the module EXECUTES, docstrings excluded.

    Prose may name a tenant -- the comments here have to, to say what the
    defect was. Code may not.
    """
    tree = ast.parse(path.read_text())
    docstrings = {
        id(node.body[0].value)
        for node in ast.walk(tree)
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        and node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
        and isinstance(node.body[0].value.value, str)
    }
    return [
        node.value for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and id(node) not in docstrings
    ]


class TestNoTenantLiteral:
    """A tenant name must not appear in this module's CODE at all.

    Pinning behaviour per action would leave the next action free to reinvent
    the default. Checking every executed string literal is the guard that cannot
    be routed around by adding an eleventh action.
    """

    @pytest.mark.parametrize("tenant", ["hanzo", "admin", "built-in", "lux", "zoo"])
    def test_source_carries_no_tenant_literal(self, tenant):
        assert tenant not in _code_strings(SOURCE)

    def test_the_guard_would_catch_a_reintroduction(self, tmp_path):
        """The guard is only worth having if it fails on the original defect."""
        planted = tmp_path / "planted.py"
        planted.write_text('"""hanzo in a docstring is fine."""\nowner = owner or "hanzo"\n')
        assert "hanzo" in _code_strings(planted)


# --------------------------------------------------------------------------
# Every org-scoped action asks IAM who it is, and sends THAT.
# --------------------------------------------------------------------------


ORG_SCOPED = [
    "users", "orgs", "roles", "permissions", "providers", "apps",
    "tokens", "sessions", "invitations", "records",
]


class TestOwnerComesFromThePrincipal:
    @pytest.mark.parametrize("action", ORG_SCOPED)
    async def test_sends_the_principals_owner(self, iam, action):
        iam.principal = "acme"
        await call(action)
        assert iam.owners() == ["acme"], f"{action} must scope to the caller's org"

    @pytest.mark.parametrize("action", ORG_SCOPED)
    async def test_never_substitutes_a_literal(self, iam, action):
        iam.principal = "zoo"
        await call(action)
        assert "hanzo" not in iam.owners()
        assert "admin" not in iam.owners()

    async def test_roles_and_permissions_accept_an_owner_at_all(self, iam):
        """They took no owner parameter, so a caller could not name its tenant."""
        iam.principal = "acme"
        await call("roles", owner="other")
        await call("permissions", owner="other")
        assert iam.owners() == ["other", "other"]

    async def test_an_explicit_owner_is_honoured(self, iam):
        """A superadmin agent legitimately names a tenant; IAM refuses if not.

        The client's job is to send the org the caller MEANT -- honour-or-refuse
        is the server's decision (internal/authz authz.Scope), not a reason to
        drop the parameter.
        """
        iam.principal = "admin"
        await call("users", owner="lux")
        assert iam.owners() == ["lux"]

    async def test_an_omitted_owner_is_never_sent_as_empty(self, iam):
        """For a SUPERADMIN, an empty owner means EVERY tenant.

        authz.Scope returns the requested owner verbatim for a super, and the
        listers apply no Owner filter when it is empty. So omitting the
        parameter -- which scopes a normal user correctly -- silently widens a
        superadmin's read to the whole fleet and labels it the caller's own org.
        """
        iam.principal = "admin"
        await call("users")
        assert iam.owners() == ["admin"]

    async def test_create_user_scopes_to_the_principal(self, iam):
        iam.principal = "acme"
        await call("create_user", name="newhire", email="n@acme.test")
        body = json.loads(iam.scoped()[0].content)
        assert body["owner"] == "acme"

    async def test_invite_scopes_to_the_principal(self, iam):
        iam.principal = "acme"
        await call("invite", email="new@acme.test")
        body = json.loads(iam.scoped()[0].content)
        assert body["owner"] == "acme"

    async def test_a_password_never_becomes_a_user_column(self, iam):
        """IAM hashes it at the one create path; it is a sibling of the fields."""
        iam.principal = "acme"
        await call("create_user", name="n", email="n@acme.test", password="s3cret")
        body = json.loads(iam.scoped()[0].content)
        assert body["password"] == "s3cret"
        assert body["name"] == "n"


class TestWriteBodyIsBare:
    """add-/update-/delete-user take the user's fields at TOP LEVEL.

    The verb aliases decode `userBody` -- schema.User EMBEDDED, plus an optional
    password -- which is explicitly "distinct from the REST twin's {user,password}
    envelope" (iam internal/compat/writes.go). IAM's own tests post the bare
    shape: {"owner":"hanzo","name":"newbie","password":"..."}.

    Wrapping it in {"user": ...} is not a shape quibble. Go decodes an object
    with no matching keys into a ZERO struct, so the write arrives addressing
    owner "" / name "" -- and the authorization seam runs on that DECODED input.
    The request the agent authored is not the request IAM authorizes.
    """

    async def test_create_sends_fields_at_top_level(self, iam):
        iam.principal = "acme"
        await call("create_user", name="newhire", email="n@acme.test")
        body = json.loads(iam.scoped()[0].content)
        assert "user" not in body, "add-user takes a bare user, not {'user': ...}"
        assert (body["owner"], body["name"]) == ("acme", "newhire")

    @pytest.mark.parametrize("action", ["update_user", "delete_user"])
    async def test_update_and_delete_send_the_addressable_key(self, iam, action):
        """delete-user reads in.Owner/in.Name straight off the decoded body."""
        iam.envelope = {"status": "ok", "data": {"owner": "acme", "name": "alice"}}
        await call(action, id="acme/alice")
        body = json.loads(iam.scoped()[-1].content)
        assert "user" not in body
        assert (body["owner"], body["name"]) == ("acme", "alice")


class TestMissingTenantIsARefusal:
    """No principal is a refusal, never a fallback."""

    @pytest.mark.parametrize("action", ORG_SCOPED)
    async def test_anonymous_caller_is_refused(self, iam, action):
        iam.principal = None
        out = await call(action)
        assert "error" in out

    @pytest.mark.parametrize("action", ORG_SCOPED)
    async def test_anonymous_caller_reads_nothing(self, iam, action):
        """The refusal must happen BEFORE any org-scoped request is sent."""
        iam.principal = None
        await call(action)
        assert iam.scoped() == []

    async def test_no_credential_is_refused_without_a_request(self, monkeypatch, iam):
        _credential(monkeypatch, None)
        out = await call("users")
        assert "error" in out
        assert iam.seen == []


# --------------------------------------------------------------------------
# The response envelope is unwrapped.
# --------------------------------------------------------------------------


class TestEnvelopeIsUnwrapped:
    """IAM answers {status, msg, data}; the rows are in `data`.

    Every list action used to test `isinstance(response, list)` against the
    envelope dict, so all ten of them reported zero rows always. That masked
    the tenant defect: the wrong org was addressed but nothing was ever shown.
    Fixing one without the other is what turns a broken read into a leak.
    """

    async def test_rows_come_from_the_data_field(self, iam):
        iam.rows = [{"name": "alice", "email": "a@acme.test"}]
        out = await call("users")
        assert out["count"] == 1
        assert out["users"][0]["name"] == "alice"

    async def test_typed_rows_come_from_the_named_collection(self, iam):
        iam.rows = [{"name": "tok-1", "owner": "acme"}]
        out = await call("tokens")
        assert out["count"] == 1
        assert out["tokens"][0]["name"] == "tok-1"

    async def test_a_wider_answer_than_the_request_is_refused(self, iam):
        """A superadmin's typed listing is NOT narrowed by `?owner=`.

        A zip typed GET binds nothing from the request, so /v1/iam/tokens reaches
        its handler with an empty owner and authz.Scope hands a SuperAdmin every
        tenant's rows. The Guard still authorized the read from the query string,
        so this is not a 403 -- it is a 200 that is wider than what was asked
        for. Stamping it `owner: admin` would republish every tenant's tokens as
        one tenant's, which is the exact failure this tool is built against.
        """
        iam.principal = "admin"
        iam.rows = [
            {"name": "tok-admin", "owner": "admin"},
            {"name": "tok-acme", "owner": "acme"},
        ]
        out = await call("tokens")
        assert "refusing" in out["error"]
        assert "acme" in out["error"]
        assert "tok-acme" not in json.dumps(out)

    async def test_the_matching_tenants_rows_still_come_back(self, iam):
        """The guard must not fire on a correctly scoped answer."""
        iam.principal = "acme"
        iam.rows = [{"name": "tok-1", "owner": "acme"}, {"name": "tok-2", "owner": "acme"}]
        out = await call("tokens")
        assert out["count"] == 2

    async def test_an_error_envelope_is_an_error(self, iam):
        """A refusal rides on HTTP 200; status is the contract, not the code."""
        iam.envelope = {
            "status": "error",
            "msg": "forbidden: this credential is scoped to organization acme",
        }
        out = await call("users")
        assert "scoped to organization acme" in out["error"]

    async def test_an_html_answer_is_not_data(self, monkeypatch):
        """hanzo.id serves its SPA on unmatched paths with a 200."""
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, text="<!doctype html>",
                                  headers={"content-type": "text/html"})

        _transport(monkeypatch, handler)
        _credential(monkeypatch, "t")
        out = await call("users")
        assert "not the API" in out["error"]


# --------------------------------------------------------------------------
# Health probes a route that exists.
# --------------------------------------------------------------------------


def _transport(monkeypatch, handler):
    real_init = httpx.AsyncClient.__init__

    def init(self, *args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        real_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "__init__", init)


class TestHealth:
    """/v1/iam/healthz is behind IAM's Guard and answers 401 unauthenticated.

    The probe it replaced sent no credential to that path, so `iam health`
    reported "error" against a perfectly healthy IAM. OIDC discovery is the
    public, JSON, standards-defined liveness surface of an identity provider.
    """

    async def test_probes_public_discovery(self, iam):
        out = await call("health")
        assert out["status"] == "ok"
        assert [r.url.path for r in iam.seen] == [OIDC_DISCOVERY_PATH]

    async def test_needs_no_credential(self, monkeypatch, iam):
        _credential(monkeypatch, None)
        assert (await call("health"))["status"] == "ok"

    async def test_rejects_the_html_spa_catch_all(self, monkeypatch):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, text="<!doctype html><html></html>",
                                  headers={"content-type": "text/html; charset=utf-8"})

        _transport(monkeypatch, handler)
        assert (await call("health"))["status"] == "error"

    async def test_rejects_json_that_is_not_an_issuer(self, monkeypatch):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"hello": "world"})

        _transport(monkeypatch, handler)
        assert (await call("health"))["status"] == "error"


# --------------------------------------------------------------------------
# One door to IAM, and no action that cannot work.
# --------------------------------------------------------------------------


class TestOneDoor:
    async def test_requests_land_on_the_canonical_prefix(self, iam):
        """Asserted on the WIRE, not on a helper's return value.

        hanzo.id answers 200 text/html on every unmatched path, so a wrong
        prefix fails inside .json() rather than like a wrong path. And /api/ is
        never a prefix here: the surface is /v1/<service>/<resource>.
        """
        await call("users")
        urls = [str(r.url) for r in iam.seen]
        assert f"{IAM_BASE_URL}{IAM_ROUTE_PREFIX}/get-users" in " ".join(urls)
        assert all("/api/" not in u for u in urls)

    def test_no_second_request_helper(self):
        """There was a _iam_get, a _iam_post and a _iam_delete -- and the
        delete one POSTed. One door, one body argument."""
        import hanzo_tools.iam.iam_tool as m

        assert not hasattr(m, "_iam_get")
        assert not hasattr(m, "_iam_post")
        assert not hasattr(m, "_iam_delete")

    @pytest.mark.parametrize("action", ["enforce", "system_info"])
    async def test_actions_with_no_route_are_gone(self, iam, action):
        """IAM v2 registers neither /v1/iam/enforce nor get-system-info.

        An `enforce` that cannot reach a policy engine is worse than absent: an
        agent asking "is this allowed?" gets an error it may read as an answer.
        """
        out = await call(action)
        assert out["error"].startswith("Unknown action")
        assert action not in out["available"]
