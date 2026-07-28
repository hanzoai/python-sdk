"""Tests for HanzoSession's authentication state.

`test_fake_token_is_not_authenticated` is THE regression. Against the shipped
implementation —

    def is_authenticated(self) -> bool:
        return self.load_token() is not None

— it FAILS: a stored token of "fake.not.a.real.jwt" made it return True, and
every tool that gated on it believed the caller was signed in.
"""

from __future__ import annotations

import json
import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from hanzo_iam import store
from hanzo_iam import tokens
from hanzo_tools.auth.session import HanzoSession

ISSUER = "https://hanzo.id"
FAKE = "fake.not.a.real.jwt"


@pytest.fixture(scope="module")
def keypair():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _jwks(key, kid="test-key"):
    data = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key()))
    data.update({"kid": kid, "use": "sig", "alg": "RS256"})
    return {"keys": [data]}


def _token(key, **overrides):
    claims = {
        "iss": ISSUER,
        "sub": "hanzo/z",
        "aud": "hanzo-app",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
    }
    claims.update(overrides)
    return jwt.encode(claims, key, algorithm="RS256", headers={"kid": "test-key"})


@pytest.fixture(autouse=True)
def clean_session(tmp_path, monkeypatch):
    """Isolate the store, clear env credentials, reset the singleton."""
    monkeypatch.setattr(store, "TOKEN_DIR", tmp_path / "auth")
    monkeypatch.setattr(store, "TOKEN_FILE", tmp_path / "auth" / "token.json")
    monkeypatch.setattr(store, "_keyring", lambda: None)
    monkeypatch.delenv("HANZO_AUTH_TOKEN", raising=False)
    monkeypatch.delenv("HANZO_API_KEY", raising=False)
    tokens.reset_jwks_cache()
    HanzoSession.reset()
    yield
    HanzoSession.reset()
    tokens.reset_jwks_cache()


@pytest.fixture
def serve_jwks(monkeypatch):
    def _serve(document):
        monkeypatch.setattr(jwt.PyJWKClient, "fetch_data", lambda self: document)

    return _serve


@pytest.fixture
def no_network(monkeypatch):
    """Any HTTP call is a test bug unless the test opted into one."""
    import httpx

    def forbidden(*a, **kw):
        raise AssertionError("unexpected network call")

    monkeypatch.setattr(httpx, "get", forbidden)


def _store(token: str, **extra):
    store.save({"access_token": token, "server_url": ISSUER, **extra})


# --- The defect -----------------------------------------------------------


def test_fake_token_is_not_authenticated(monkeypatch):
    """A stored token of 'fake.not.a.real.jwt' must not authenticate anybody.

    It is not a JWT, so it is treated as an opaque credential and put to the
    issuer, which rejects it. Under the old presence check this returned True.
    """
    import httpx

    class Rejected:
        status_code = 401
        headers = {"content-type": "application/json"}

    monkeypatch.setattr(httpx, "get", lambda *a, **kw: Rejected())
    _store(FAKE)

    session = HanzoSession.get()
    assert session.has_credential() is True  # the string IS there
    assert session.is_authenticated() is False  # but it proves nothing
    assert session.get_token_info()["authenticated"] is False


def test_fake_token_in_env_is_not_authenticated(monkeypatch):
    """Same defect via HANZO_AUTH_TOKEN, which bypasses the store entirely."""
    import httpx

    class Rejected:
        status_code = 401
        headers = {"content-type": "application/json"}

    monkeypatch.setattr(httpx, "get", lambda *a, **kw: Rejected())
    monkeypatch.setenv("HANZO_AUTH_TOKEN", FAKE)

    assert HanzoSession.get().is_authenticated() is False


def test_presence_and_validity_are_different_questions(serve_jwks, keypair, no_network):
    """The two used to be one method. Keeping them apart is the fix."""
    serve_jwks(_jwks(keypair))
    _store(_token(keypair, exp=int(time.time()) - 3600))
    session = HanzoSession.get()
    assert session.has_credential() is True
    assert session.is_authenticated() is False
    assert session.verify().reason == tokens.EXPIRED


# --- Genuine credentials --------------------------------------------------


def test_real_token_authenticates(serve_jwks, keypair, no_network):
    serve_jwks(_jwks(keypair))
    _store(_token(keypair))
    session = HanzoSession.get()
    assert session.is_authenticated() is True
    info = session.get_token_info()
    assert info["authenticated"] is True
    assert info["expired"] is False
    assert session.verify().claims["sub"] == "hanzo/z"


def test_no_credential_at_all(no_network):
    session = HanzoSession.get()
    assert session.has_credential() is False
    assert session.is_authenticated() is False
    assert session.get_token_info() == {
        "authenticated": False,
        "reason": tokens.NO_CREDENTIAL,
    }


# --- Forgeries ------------------------------------------------------------


def test_token_from_another_issuer_is_rejected(serve_jwks, keypair, no_network):
    """Correctly signed, wrong issuer: still not a Hanzo session."""
    serve_jwks(_jwks(keypair))
    _store(_token(keypair, iss="https://evil.example"))
    assert HanzoSession.get().verify().reason == tokens.WRONG_ISSUER


def test_self_signed_token_is_rejected(serve_jwks, keypair, no_network):
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    serve_jwks(_jwks(keypair))
    _store(_token(other))
    assert HanzoSession.get().is_authenticated() is False


def test_expiry_comes_from_the_token_not_from_local_bookkeeping(
    serve_jwks, keypair, no_network
):
    """A caller could otherwise claim a fresh session by editing login_time in
    the stored JSON. `exp` is signed; login_time is not."""
    serve_jwks(_jwks(keypair))
    exp = int(time.time()) + 60
    store.save(
        {
            "access_token": _token(keypair, exp=exp),
            "server_url": ISSUER,
            "login_time": int(time.time()) + 10**6,
            "expires_in": 10**6,
        }
    )
    assert HanzoSession.get().get_token_info()["expires_at"] == exp


# --- Fail closed ----------------------------------------------------------


def test_offline_does_not_grant_access(monkeypatch, keypair):
    """No JWKS, no verification, no session — an unreachable IdP must not be a
    free pass."""

    def down(self):
        raise jwt.exceptions.PyJWKClientConnectionError("network down")

    monkeypatch.setattr(jwt.PyJWKClient, "fetch_data", down)
    _store(_token(keypair))
    session = HanzoSession.get()
    assert session.is_authenticated() is False
    assert session.verify().reason == tokens.JWKS_UNREACHABLE


def test_jwks_path_carries_the_v1_iam_prefix(serve_jwks, keypair, monkeypatch):
    """The unprefixed /.well-known/jwks answers 200 text/html on hanzo.id, so
    verification would silently have nothing to check against."""
    seen: list[str] = []
    monkeypatch.setattr(
        jwt.PyJWKClient,
        "fetch_data",
        lambda self: (seen.append(self.uri), _jwks(keypair))[1],
    )
    _store(_token(keypair))
    HanzoSession.get().verify()
    assert seen == [f"{ISSUER}/v1/iam/.well-known/jwks"]


# --- Storage --------------------------------------------------------------


def test_session_persists_tokens_privately(serve_jwks, keypair, no_network):
    import stat

    serve_jwks(_jwks(keypair))
    HanzoSession.get()._save_token({"access_token": _token(keypair), "server_url": ISSUER})
    assert stat.S_IMODE(store.TOKEN_FILE.stat().st_mode) == 0o600


def test_logout_clears_the_credential(serve_jwks, keypair, no_network):
    serve_jwks(_jwks(keypair))
    _store(_token(keypair))
    session = HanzoSession.get()
    assert session.is_authenticated() is True
    session.logout()
    HanzoSession.reset()
    assert HanzoSession.get().is_authenticated() is False


def test_login_refuses_to_store_a_token_it_cannot_verify(monkeypatch, keypair):
    """If IAM hands back something unverifiable, that is a bug to surface, not
    a credential to keep and present as proof of identity later."""
    from hanzo_iam import oauth

    monkeypatch.setattr(
        oauth,
        "login",
        lambda **kw: {"access_token": FAKE, "server_url": ISSUER, "client_id": "hanzo-app"},
    )
    monkeypatch.setattr(
        jwt.PyJWKClient, "fetch_data", lambda self: _jwks(keypair)
    )
    with pytest.raises(RuntimeError, match="cannot verify"):
        HanzoSession.get().login()
    assert store.load() is None
