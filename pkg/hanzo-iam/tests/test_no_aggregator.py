"""hanzo-iam does NOT route through the generated cloud client. Measured, not assumed.

A cleanup proposal asked for the opposite: delete this package's HTTP layer and
have it call `hanzoai.api.iam_*_api` underneath, "so there is one HTTP path".
The two have the same SHAPE and different SEMANTICS, and merging them would have
been a security regression. These tests are the receipts, so the next reader does
not have to re-derive them.

1. DIFFERENT HOST / TRUST BOUNDARY.
   `hanzoai` is generated from "Hanzo Cloud — Unified API", whose own header
   says *"Every route is https://api.hanzo.ai/v1/<service>/*"*, and whose
   `configuration.py` defaults `_base_path` to `https://api.hanzo.ai`. That is
   the cloud AGGREGATOR, not the issuer. This package talks to the ISSUER
   (hanzo.id / lux.id / zoo.id) because token exchange and JWKS must not be
   proxied: a proxy inside a credential exchange re-points the audience.
   Worse, cloud's `/v1/iam/*` edge forwards under ONE shared confidential
   client, so every tenant is answered with the edge credential's organization.
   Routing this package through it would put `hanzo login` behind that.

2. DIFFERENT CREDENTIAL.
   IAM's Guard resolves `Authorization: Basic <clientId>:<clientSecret>`
   (RFC 6749 2.3.1) into an application principal — that is how an M2M caller
   with IAM_CLIENT_ID + IAM_CLIENT_SECRET and no bearer authenticates at all.
   Measured over the generated client: **234 of 234** IAM operations declare
   `bearerAuth` and **zero** declare `basicAuth`. Merging would silently delete
   confidential-client auth from every M2M consumer.

3. DIFFERENT ROUTES.
   Measured against canonical IAM (hanzoai/iam origin/main, internal/routes +
   internal/compat): of the generated client's 150 distinct IAM paths, **15**
   are served and **135** are not. It is a REST re-shaping (`/v1/iam/users/{id}`,
   `/oauth/userinfo`) of a surface IAM serves as verb aliases
   (`/v1/iam/get-user`, `/v1/iam/oauth/userinfo`).

Same shape, different bounded context. The merge is the mistake.
"""

from __future__ import annotations

import ast
import inspect

import pytest

import hanzo_iam
from hanzo_iam import client, config, fastapi, oauth, response, store, tokens

# Every module in the package. If one appears here it is checked; adding a
# module without adding it here is what lets a dependency slip back in.
ALL_MODULES = [client, config, fastapi, oauth, response, store, tokens]


@pytest.mark.parametrize("module", ALL_MODULES, ids=lambda m: m.__name__)
def test_no_module_reaches_for_the_generated_cloud_client(module):
    """`hanzoai` is the aggregator SDK. This package must not import it.

    It is also a 125 MB, 495-api-module distribution; making the identity
    primitive that `hanzo login` depends on pull it in inverts the dependency
    as well as the trust boundary.
    """
    src = inspect.getsource(module)
    assert "import hanzoai" not in src
    assert "from hanzoai" not in src


def _string_literals(module) -> list[str]:
    """Every string constant in `module` that is not a docstring.

    Asserted over the AST, not the source text: this file's own reasoning names
    api.hanzo.ai in prose, and a check that cannot tell a comment from a URL
    would fail on an explanation of why the URL is absent.
    """
    tree = ast.parse(inspect.getsource(module))
    docstrings = {
        ast.get_docstring(n, clean=False)
        for n in ast.walk(tree)
        if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    }
    return [
        n.value
        for n in ast.walk(tree)
        if isinstance(n, ast.Constant)
        and isinstance(n.value, str)
        and n.value not in docstrings
    ]


@pytest.mark.parametrize("module", ALL_MODULES, ids=lambda m: m.__name__)
def test_no_module_hardcodes_the_aggregator_host(module):
    """The host comes from IAM_ENDPOINT. api.hanzo.ai is a different service."""
    assert not [s for s in _string_literals(module) if "api.hanzo.ai" in s]


def test_the_confidential_client_pair_is_still_sendable():
    """The credential the generated client cannot express, still expressed here.

    `_auth_headers` with no bearer must produce Basic — this is the only way an
    M2M caller holding IAM_CLIENT_ID + IAM_CLIENT_SECRET authenticates to IAM.
    """
    import base64

    c = client.IAMClient(
        config=config.IAMConfig(
            server_url="https://hanzo.id",
            client_id="cid",
            client_secret="csec",
            organization="acme",
        )
    )
    expected = base64.b64encode(b"cid:csec").decode()
    assert c._auth_headers()["Authorization"] == f"Basic {expected}"


def test_the_admin_verbs_are_the_spelling_iam_actually_serves():
    """Canonical IAM serves the verb aliases, not the REST re-shaping.

    Pinned from hanzoai/iam origin/main internal/compat/{aliases,writes}.go.
    `get_user` hitting `/v1/iam/users/{id}` (the generated spelling) is a 404.
    """
    src = inspect.getsource(client)
    for verb in (
        "get-user",
        "get-users",
        "get-organizations",
        "get-organization",
        "get-providers",
        "get-roles",
        "get-application",
        "get-applications",
        "update-application",
        "add-user",
        "update-user",
        "delete-user",
    ):
        assert f'"{verb}"' in src, f"{verb} is the canonical spelling"


def test_the_package_still_owns_its_own_http():
    """The seam this ticket proposed to delete is load-bearing; it stays."""
    assert hasattr(hanzo_iam, "IAMClient")
    assert callable(response.decode)
    assert callable(response.unwrap)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
