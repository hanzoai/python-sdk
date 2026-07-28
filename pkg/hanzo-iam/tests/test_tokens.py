"""Tests for hanzo_iam.tokens — the credential judge.

The headline test is `test_fake_jwt_string_is_rejected`. Against the code this
replaced (`bool(token)` / `load_token() is not None`) it FAILS: that
implementation returned True for the literal string "fake.not.a.real.jwt".
"""

from __future__ import annotations

import json
import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

import hanzo_iam.tokens as v

ISSUER = "https://hanzo.id"
JWKS_URI = f"{ISSUER}/v1/iam/.well-known/jwks"

# The exact string the old is_authenticated() accepted.
FAKE = "fake.not.a.real.jwt"
# Garbage that IS shaped like a JWS compact serialization, so only a signature
# check can reject it. FAKE has four dots and does not even reach that stage.
FAKE_SHAPED = "eyJhbGciOiJSUzI1NiIsImtpZCI6InRlc3Qta2V5In0.eyJzdWIiOiJyb290In0.c2ln"


@pytest.fixture(scope="module")
def keypair():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture(scope="module")
def other_keypair():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _jwks(key, kid="test-key"):
    pub = key.public_key()
    algo = jwt.algorithms.RSAAlgorithm
    data = json.loads(algo.to_jwk(pub))
    data.update({"kid": kid, "use": "sig", "alg": "RS256"})
    return {"keys": [data]}


def _token(key, kid="test-key", **overrides):
    claims = {
        "iss": ISSUER,
        "sub": "hanzo/z",
        "aud": "hanzo-app",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
    }
    claims.update(overrides)
    return jwt.encode(claims, key, algorithm="RS256", headers={"kid": kid})


@pytest.fixture(autouse=True)
def _clean():
    v.reset_jwks_cache()
    yield
    v.reset_jwks_cache()


@pytest.fixture
def serve_jwks(monkeypatch):
    """Point PyJWKClient at an in-memory JWKS instead of the network."""

    def _serve(document):
        # fetch_data must hand back the parsed JSON dict; get_jwk_set builds
        # the PyJWKSet itself.
        monkeypatch.setattr(jwt.PyJWKClient, "fetch_data", lambda self: document)

    return _serve


# --- The defect -----------------------------------------------------------


def test_fake_jwt_string_is_rejected(serve_jwks, keypair):
    """'fake.not.a.real.jwt' must NOT verify.

    It is three dot-separated non-empty segments, so it survives every
    shape check. Only a signature check catches it. The old
    is_authenticated() returned True for exactly this string.
    """
    serve_jwks(_jwks(keypair))
    result = v.verify(FAKE, jwks_uri=JWKS_URI, issuer=ISSUER)
    assert result.valid is False
    assert bool(result) is False
    # Not even a JWT — which the old check never noticed, because it only ever
    # asked whether the string was non-empty.
    assert result.reason == v.OPAQUE


def test_jwt_shaped_garbage_is_rejected(serve_jwks, keypair):
    """A forgery that DOES have the JWS shape gets past every structural test.
    Only checking the signature against a published key rejects it."""
    serve_jwks(_jwks(keypair))
    result = v.verify(FAKE_SHAPED, jwks_uri=JWKS_URI, issuer=ISSUER)
    assert result.valid is False
    assert result.reason in (v.MALFORMED, v.BAD_SIGNATURE, v.UNKNOWN_KEY)


def test_shape_check_is_not_a_trust_check():
    """is_jwt() answers a question about punctuation, nothing more."""
    assert v.is_jwt(FAKE_SHAPED) is True
    assert v.verify(FAKE_SHAPED, jwks_uri=JWKS_URI, issuer=ISSUER).valid is False


@pytest.mark.parametrize("junk", ["", None, "not-a-token", "a.b", "....", "x" * 500])
def test_junk_is_rejected(junk):
    assert v.verify(junk, jwks_uri=JWKS_URI, issuer=ISSUER).valid is False


# --- The happy path -------------------------------------------------------


def test_genuine_token_verifies(serve_jwks, keypair):
    serve_jwks(_jwks(keypair))
    result = v.verify(_token(keypair), jwks_uri=JWKS_URI, issuer=ISSUER, audience="hanzo-app")
    assert result.valid is True
    assert result.reason == v.OK
    assert result.claims["sub"] == "hanzo/z"


# --- Every way a real-looking token can still be bad ----------------------


def test_expired_token_is_rejected(serve_jwks, keypair):
    serve_jwks(_jwks(keypair))
    stale = _token(keypair, exp=int(time.time()) - 3600)
    result = v.verify(stale, jwks_uri=JWKS_URI, issuer=ISSUER)
    assert result.valid is False
    assert result.reason == v.EXPIRED


def test_token_signed_by_a_stranger_is_rejected(serve_jwks, keypair, other_keypair):
    """Correct kid, correct claims, wrong private key."""
    serve_jwks(_jwks(keypair))
    forged = _token(other_keypair)
    result = v.verify(forged, jwks_uri=JWKS_URI, issuer=ISSUER)
    assert result.valid is False
    assert result.reason == v.BAD_SIGNATURE


def test_wrong_issuer_is_rejected(serve_jwks, keypair):
    serve_jwks(_jwks(keypair))
    result = v.verify(_token(keypair, iss="https://evil.example"), jwks_uri=JWKS_URI, issuer=ISSUER)
    assert result.valid is False
    assert result.reason == v.WRONG_ISSUER


def test_wrong_audience_is_rejected(serve_jwks, keypair):
    serve_jwks(_jwks(keypair))
    result = v.verify(
        _token(keypair, aud="someone-else"), jwks_uri=JWKS_URI, issuer=ISSUER, audience="hanzo-app"
    )
    assert result.valid is False
    assert result.reason == v.WRONG_AUDIENCE


def test_alg_none_token_is_rejected(serve_jwks, keypair):
    """The classic bypass: re-sign the claims with alg=none."""
    serve_jwks(_jwks(keypair))
    unsigned = jwt.encode({"iss": ISSUER, "sub": "hanzo/z", "exp": int(time.time()) + 3600},
                          key=None, algorithm="none", headers={"kid": "test-key"})
    assert v.verify(unsigned, jwks_uri=JWKS_URI, issuer=ISSUER).valid is False


def test_token_without_exp_is_rejected(serve_jwks, keypair):
    """A token that never expires is not a session."""
    serve_jwks(_jwks(keypair))
    claims = {"iss": ISSUER, "sub": "hanzo/z"}
    forever = jwt.encode(claims, keypair, algorithm="RS256", headers={"kid": "test-key"})
    assert v.verify(forever, jwks_uri=JWKS_URI, issuer=ISSUER).valid is False


def test_unknown_kid_is_rejected(serve_jwks, keypair):
    serve_jwks(_jwks(keypair, kid="rotated-away"))
    assert v.verify(_token(keypair), jwks_uri=JWKS_URI, issuer=ISSUER).reason == v.UNKNOWN_KEY


# --- Fail closed ----------------------------------------------------------


def test_html_jwks_does_not_verify_anything(monkeypatch, keypair):
    """hanzo.id serves its sign-in SPA on unmatched paths, so a JWKS URL with a
    missing /v1/iam prefix fetches 200 text/html. That must never read as
    'verified' — it is the exact trap that made /.well-known/jwks look fine."""

    def html(self, refresh=False):
        raise jwt.exceptions.PyJWKClientError("expecting value: line 1 column 1")

    monkeypatch.setattr(jwt.PyJWKClient, "fetch_data", html)
    result = v.verify(_token(keypair), jwks_uri=f"{ISSUER}/.well-known/jwks", issuer=ISSUER)
    assert result.valid is False
    assert result.reason == v.UNKNOWN_KEY


def test_unreachable_jwks_fails_closed(monkeypatch, keypair):
    def boom(self, refresh=False):
        raise jwt.exceptions.PyJWKClientConnectionError("network down")

    monkeypatch.setattr(jwt.PyJWKClient, "fetch_data", boom)
    result = v.verify(_token(keypair), jwks_uri=JWKS_URI, issuer=ISSUER)
    assert result.valid is False
    assert result.reason == v.JWKS_UNREACHABLE


def test_opaque_credential_is_not_silently_accepted():
    result = v.verify("hz_sk_live_abcdef123456", jwks_uri=JWKS_URI, issuer=ISSUER)
    assert result.valid is False
    assert result.reason == v.OPAQUE


def test_alg_none_is_not_in_the_accepted_list():
    assert "none" not in [a.lower() for a in v.ALGORITHMS]


def test_unverified_claims_does_not_imply_trust():
    """unverified_claims reads a forged token happily — which is why nothing
    that gates access may call it."""
    forged = jwt.encode({"sub": "root", "exp": 1}, "k" * 32, algorithm="HS256")
    assert v.unverified_claims(forged)["sub"] == "root"
    assert v.verify(forged, jwks_uri=JWKS_URI, issuer=ISSUER).valid is False
