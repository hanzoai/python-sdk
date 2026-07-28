"""The KMS client must speak Hanzo KMS's surface, not Infisical's.

These fail against the shipped client, which called `/api/v3/secrets/raw`.
kms.hanzo.ai answers that path `404 {"message":"not found"}` — measured, not
inferred — so every secret read and write was dead on arrival.
"""

from __future__ import annotations

import pathlib

import pytest

from hanzo_kms import routes


def test_collection_path():
    assert routes.secrets_collection("hanzo") == "/v1/kms/orgs/hanzo/secrets"


def test_secret_path():
    assert (
        routes.secret("hanzo", "providers/alpaca/dev", "api_key")
        == "/v1/kms/orgs/hanzo/secrets/providers/alpaca/dev/api_key"
    )


def test_secret_path_with_empty_path_segment():
    assert routes.secret("hanzo", "/", "token") == "/v1/kms/orgs/hanzo/secrets/token"
    assert routes.secret("hanzo", "", "token") == "/v1/kms/orgs/hanzo/secrets/token"


def test_path_hierarchy_is_preserved_but_org_and_name_are_escaped():
    """A '/' inside the path is a real hierarchy level; one inside the org or
    the name is data and must not silently become a level."""
    assert routes.secret("liq/uid", "foo bar", "k+q") == (
        "/v1/kms/orgs/liq%2Fuid/secrets/foo%20bar/k%2Bq"
    )


def test_a_slash_in_the_name_is_escaped_not_promoted_to_a_path_level():
    assert routes.secret("hanzo", "a", "b/c") == "/v1/kms/orgs/hanzo/secrets/a/b%2Fc"


@pytest.mark.parametrize(
    "path,name",
    [("../..", "k"), ("a/../..", "k"), ("a", ".."), ("a", ".")],
)
def test_traversal_segments_are_rejected(path, name):
    """A bare '..' segment walks up to another org's collection the moment a
    proxy or server normalises the path, so it never reaches the URL."""
    with pytest.raises(ValueError):
        routes.secret("hanzo", path, name)


def test_traversal_inside_a_name_is_escaped_into_harmlessness():
    """The name is one segment, so its separators are encoded and the '..'
    cannot act as a path operator."""
    url = routes.secret("hanzo", "a", "../../other-org/secrets/x")
    assert url == "/v1/kms/orgs/hanzo/secrets/a/..%2F..%2Fother-org%2Fsecrets%2Fx"
    assert "/../" not in url


def test_auth_login_path_is_the_one_kms_actually_serves():
    """/v1/kms/auth/login answers 401 invalid credentials (it exists);
    /api/v3/auth/login answers 404 (it does not)."""
    assert routes.AUTH_LOGIN_PATH == "/v1/kms/auth/login"


def test_no_infisical_paths_remain_in_the_package():
    """No REQUEST may still target /api/v3. Prose about the old paths is fine —
    the check walks the AST and ignores docstrings and comments."""
    import ast

    root = pathlib.Path(__file__).resolve().parents[1] / "hanzo_kms"
    offenders = []
    for py in root.glob("*.py"):
        tree = ast.parse(py.read_text())
        docstrings = {
            id(n.body[0].value)
            for n in ast.walk(tree)
            if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
            and n.body
            and isinstance(n.body[0], ast.Expr)
            and isinstance(n.body[0].value, ast.Constant)
        }
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and "/api/v3/" in node.value
                and id(node) not in docstrings
            ):
                offenders.append(f"{py.name}:{node.lineno}: {node.value!r}")
    assert not offenders, "Infisical-legacy paths:\n" + "\n".join(offenders)


# --- The clients actually use them ----------------------------------------


_SECRET = {
    "id": "s1",
    "secretKey": "api_key",
    "secretValue": "v",
    "environment": "prod",
    "workspace": "hanzo",
}


class _Recorder:
    """Stands in for httpx.Client and records the request it was given."""

    def __init__(self, payload):
        self.payload = payload
        self.calls: list[dict] = []

    def _resp(self):
        class R:
            status_code = 200

            @staticmethod
            def raise_for_status():
                pass

            def json(_self):
                return self.payload

        return R()

    def get(self, url, params=None, headers=None):
        self.calls.append({"method": "GET", "url": url, "params": params})
        return self._resp()

    def post(self, url, json=None, headers=None):
        self.calls.append({"method": "POST", "url": url, "json": json})
        return self._resp()

    def request(self, method, url, params=None, json=None, headers=None):
        self.calls.append({"method": method, "url": url, "params": params, "json": json})
        return self._resp()


@pytest.fixture
def client(monkeypatch):
    from hanzo_kms import KMSClient
    from hanzo_kms.models import AuthenticationOptions, ClientSettings, TokenAuthMethod

    c = KMSClient(
        settings=ClientSettings(
            site_url="https://kms.hanzo.ai",
            organization="hanzo",
            auth=AuthenticationOptions(token=TokenAuthMethod(access_token="t")),
        )
    )
    rec = _Recorder({"secret": _SECRET})
    monkeypatch.setattr(type(c), "http", property(lambda self: rec))
    return c, rec


def test_get_secret_uses_the_canonical_path_and_env_query(client):
    c, rec = client
    c.get_secret(project_id="hanzo", environment="prod", secret_name="api_key", path="/providers")
    assert rec.calls[0]["url"] == "/v1/kms/orgs/hanzo/secrets/providers/api_key"
    assert rec.calls[0]["params"]["env"] == "prod"


def test_list_secrets_uses_the_collection_path(client):
    c, rec = client
    rec.payload = {"secrets": []}
    c.list_secrets(project_id="hanzo", environment="prod", path="/providers")
    assert rec.calls[0]["url"] == "/v1/kms/orgs/hanzo/secrets"
    assert rec.calls[0]["params"] == {"env": "prod", "prefix": "providers"}


def test_create_secret_posts_the_canonical_body_including_env(client):
    """env must be explicit on a write. The server defaults a missing one to
    "default", silently diverting a prod write into the wrong bucket."""
    c, rec = client
    c.create_secret(
        project_id="hanzo", environment="prod", secret_name="api_key", secret_value="v"
    )
    assert rec.calls[0]["url"] == "/v1/kms/orgs/hanzo/secrets"
    assert rec.calls[0]["json"] == {"path": "/", "name": "api_key", "env": "prod", "value": "v"}


def test_update_secret_is_the_same_upsert(client):
    """The server has ONE write verb; PATCH was an Infisical shape."""
    c, rec = client
    c.update_secret(
        project_id="hanzo", environment="prod", secret_name="api_key", secret_value="v2"
    )
    assert rec.calls[0]["method"] == "POST"
    assert rec.calls[0]["json"]["value"] == "v2"


def test_delete_secret_uses_the_canonical_path(client):
    c, rec = client
    c.delete_secret(project_id="hanzo", environment="prod", secret_name="api_key")
    assert rec.calls[0]["method"] == "DELETE"
    assert rec.calls[0]["url"] == "/v1/kms/orgs/hanzo/secrets/api_key"
    assert rec.calls[0]["params"]["env"] == "prod"


def test_org_prefixed_project_id_selects_the_org(client):
    c, rec = client
    c.get_secret(project_id="zoo/anything", environment="dev", secret_name="k")
    assert rec.calls[0]["url"].startswith("/v1/kms/orgs/zoo/secrets/")


def test_password_login_refuses_rather_than_calling_a_404(client):
    """Hanzo KMS has no email/password login; the endpoint the old client used
    is Infisical's and 404s."""
    c, _ = client
    with pytest.raises(NotImplementedError, match="no email/password login"):
        c._user_login("z@hanzo.ai", "pw")
