"""Every IAM endpoint must live under the one /v1/iam prefix.

These fail against the shipped code, which composed OAuth URLs from the server
root: `/oauth/token`, `/oauth/authorize`, `/oauth/introspect`,
`/.well-known/jwks`. hanzo.id serves its sign-in SPA on every unmatched path,
so all four answered **200 text/html**. Nothing 404'd, nothing raised for
status, and the failure only surfaced deep inside `.json()`.
"""

from __future__ import annotations

import pytest

from hanzo_iam import models
from hanzo_iam.config import IAMConfig

SERVER = "https://hanzo.id"

PATHS = [
    models.OIDC_AUTHORIZE_PATH,
    models.OIDC_TOKEN_PATH,
    models.OIDC_USERINFO_PATH,
    models.OIDC_INTROSPECT_PATH,
    models.OIDC_REVOKE_PATH,
    models.OIDC_DEVICE_PATH,
    models.OIDC_JWKS_PATH,
]


@pytest.mark.parametrize("path", PATHS)
def test_every_endpoint_is_under_the_prefix(path):
    assert path.startswith(models.IAM_ROUTE_PREFIX + "/")


def test_paths_are_composed_from_the_prefix_not_retyped():
    """One seam: changing IAM_ROUTE_PREFIX must move every endpoint."""
    for path in PATHS:
        assert path.count("/v1/iam") == 1


def test_discovery_is_the_one_root_relative_path():
    """RFC 8414 pins /.well-known/openid-configuration at the origin root; it
    is the only IAM path that is NOT prefixed, and it does resolve live."""
    assert models.OIDC_DISCOVERY_PATH == "/.well-known/openid-configuration"


@pytest.mark.parametrize(
    "attr,expected",
    [
        ("token_endpoint", "/v1/iam/oauth/token"),
        ("authorize_endpoint", "/v1/iam/oauth/authorize"),
        ("userinfo_endpoint", "/v1/iam/oauth/userinfo"),
        ("device_endpoint", "/v1/iam/oauth/device"),
        ("jwks_uri", "/v1/iam/.well-known/jwks"),
    ],
)
def test_config_endpoints(attr, expected):
    config = IAMConfig(server_url=SERVER, client_id="hanzo-app", organization="hanzo")
    assert getattr(config, attr) == SERVER + expected


def test_config_tolerates_a_trailing_slash():
    """A doubled slash is a different path, and hanzo.id would answer it with
    the SPA rather than a 404."""
    config = IAMConfig(server_url=SERVER + "/", client_id="hanzo-app", organization="hanzo")
    assert config.token_endpoint == f"{SERVER}/v1/iam/oauth/token"
    assert "//v1" not in config.token_endpoint


def test_jwks_uri_is_not_the_unprefixed_well_known_path():
    """The exact trap: https://hanzo.id/.well-known/jwks returns 200 text/html,
    so a JWKS client pointed there fetches a web page and verifies nothing."""
    config = IAMConfig(server_url=SERVER, client_id="hanzo-app", organization="hanzo")
    assert config.jwks_uri != f"{SERVER}/.well-known/jwks"
    assert config.jwks_uri != f"{SERVER}/.well-known/jwks.json"


def test_no_module_still_spells_a_bare_oauth_path():
    """Guards against a regression creeping back into any client module."""
    import pathlib

    import hanzo_iam

    root = pathlib.Path(hanzo_iam.__file__).parent
    offenders = []
    for py in root.glob("*.py"):
        for lineno, line in enumerate(py.read_text().splitlines(), 1):
            if line.lstrip().startswith("#"):
                continue
            for bad in ('"/oauth/', "'/oauth/", '"/.well-known/jwks', "'/.well-known/jwks"):
                if bad in line:
                    offenders.append(f"{py.name}:{lineno}: {line.strip()}")
    assert not offenders, "unprefixed IAM paths:\n" + "\n".join(offenders)
