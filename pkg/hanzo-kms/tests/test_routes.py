"""Pin the canonical luxfi/kms wire shape.

These tests are pure — no I/O — and they exist because two mistakes in this
SDK were invisible in production:

1. Infisical ``/api/*`` paths, which luxfi/kms has never served. They read as
   JSON decode errors instead of 404s while old builds answered every
   unmatched path with the console SPA (200 text/html).
2. Escaping the joined path instead of each segment, which percent-encodes
   the separators the server splits on.
"""

from urllib.parse import unquote

import pytest

from hanzo_kms import routes


def test_no_api_paths() -> None:
    """Every route lives under /v1/kms. Nothing under /api/ — ever."""
    urls = [
        routes.LOGIN,
        routes.HEALTH,
        routes.secrets_url("hanzo"),
        routes.secret_url("hanzo", "providers/lux", "deploy-mnemonic"),
    ]
    for url in urls:
        assert "/api/" not in url, f"{url} regressed onto an Infisical /api/ path"
        assert url.startswith("/v1/kms/"), url


def test_secret_url_shape() -> None:
    assert (
        routes.secret_url("lux", "providers/lux", "deploy-mnemonic")
        == "/v1/kms/orgs/lux/secrets/providers/lux/deploy-mnemonic"
    )
    assert routes.secrets_url("lux") == "/v1/kms/orgs/lux/secrets"


def test_each_segment_is_escaped_individually() -> None:
    """Separators survive; everything else inside a segment is encoded."""
    url = routes.secret_url("my org", "a b/c+d", "e f")
    assert url == "/v1/kms/orgs/my%20org/secrets/a%20b/c%2Bd/e%20f"
    # The joined-string mistake would have produced this instead:
    assert "a%20b%2Fc" not in url


@pytest.mark.parametrize(
    ("path", "name"),
    [
        ("providers/lux", "deploy-mnemonic"),
        ("a", "b"),
        ("a/b/c/d", "e"),
        ("weird path/with spaces", "name with spaces"),
        ("q?uery#frag", "amp&sand"),
    ],
)
def test_server_split_round_trip(path: str, name: str) -> None:
    """Model the server: unescape the trailing path, split at the LAST slash.

    cmd/kms/main.go does exactly this — ``strings.LastIndex(rest, "/")`` over
    the unescaped remainder — for both GET and DELETE. Whatever this SDK
    builds has to survive that split unchanged.
    """
    url = routes.secret_url("hanzo", path, name)
    rest = unquote(url.removeprefix("/v1/kms/orgs/hanzo/secrets/"))
    got_path, _, got_name = rest.rpartition("/")
    assert (got_path, got_name) == ("/".join(s for s in path.split("/") if s), name)


def test_name_with_slash_is_rejected() -> None:
    """A slashed name writes under one key and reads back under another."""
    with pytest.raises(ValueError, match="may not contain"):
        routes.secret_url("hanzo", "providers", "lux/deploy-mnemonic")
    with pytest.raises(ValueError, match="may not contain"):
        routes.upsert_body("providers", "lux/deploy-mnemonic", "v", "prod")


def test_path_is_required_for_a_single_secret() -> None:
    """No path means no slash to split on — the server 400s. Fail earlier."""
    for path in ("", "/", "///"):
        with pytest.raises(ValueError, match="path is required"):
            routes.secret_url("hanzo", path, "name")


def test_empty_name_is_rejected() -> None:
    with pytest.raises(ValueError, match="name is required"):
        routes.secret_url("hanzo", "providers", "")


def test_list_path_may_be_empty() -> None:
    """Listing is a prefix scan, so an empty path is legitimate there."""
    assert routes.list_params("", "prod") == {"path": "", "env": "prod"}


def test_env_defaults_to_default_and_may_not_be_blank() -> None:
    assert routes.DEFAULT_ENV == "default"
    assert routes.env_params(routes.DEFAULT_ENV) == {"env": "default"}
    for blank in ("", "   "):
        with pytest.raises(ValueError, match="env is required"):
            routes.env_params(blank)
        with pytest.raises(ValueError, match="env is required"):
            routes.upsert_body("providers", "name", "value", blank)


def test_upsert_body_shape() -> None:
    assert routes.upsert_body("/providers/lux/", "deploy-mnemonic", "abc", "prod") == {
        "path": "providers/lux",
        "name": "deploy-mnemonic",
        "env": "prod",
        "value": "abc",
    }


def test_version_read_is_refused() -> None:
    """KMS holds one value per (path, name, env) — a version can't be honored."""
    routes.check_version(None)
    with pytest.raises(routes.VersionUnsupportedError, match="one value"):
        routes.check_version(3)


def test_decoders_reject_anything_but_the_documented_shape() -> None:
    assert routes.names_of({"names": ["a", "b"]}) == ["a", "b"]
    assert routes.names_of({"names": []}) == []
    assert routes.value_of({"secret": {"value": "s3cret"}}) == "s3cret"

    # An SPA catch-all or a JSON 404 must not read as an empty result.
    for junk in ({"message": "not found", "path": "/api/v3/secrets/raw"}, {}, [], None):
        with pytest.raises(ValueError, match="unexpected KMS"):
            routes.names_of(junk)
        with pytest.raises(ValueError, match="unexpected KMS"):
            routes.value_of(junk)
