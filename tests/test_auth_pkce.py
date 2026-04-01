"""Tests for PKCE OAuth support in hanzoai.auth.

Run: .venv/bin/python -m pytest tests/test_auth_pkce.py -v
"""

import base64
import hashlib
import json
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from hanzoai.auth import (
    OAuthAuthorizationRequest,
    OAuthCredentialStore,
    OAuthTokenExchangeRequest,
    OAuthTokenSet,
    PkceCodePair,
    generate_pkce_pair,
    generate_state,
)


class TestPkceCodePair(unittest.TestCase):
    def test_fields(self):
        pair = PkceCodePair(verifier="v", challenge="c")
        self.assertEqual(pair.verifier, "v")
        self.assertEqual(pair.challenge, "c")
        self.assertEqual(pair.challenge_method, "S256")

    def test_custom_method(self):
        pair = PkceCodePair(verifier="v", challenge="c", challenge_method="plain")
        self.assertEqual(pair.challenge_method, "plain")


class TestGeneratePkcePair(unittest.TestCase):
    def test_returns_pkce_pair(self):
        pair = generate_pkce_pair()
        self.assertIsInstance(pair, PkceCodePair)
        self.assertEqual(pair.challenge_method, "S256")

    def test_verifier_is_base64url_no_padding(self):
        pair = generate_pkce_pair()
        self.assertNotIn("=", pair.verifier)
        self.assertNotIn("+", pair.verifier)
        self.assertNotIn("/", pair.verifier)
        # 32 bytes -> 43 base64url chars (no padding)
        self.assertEqual(len(pair.verifier), 43)

    def test_challenge_is_sha256_of_verifier(self):
        pair = generate_pkce_pair()
        # SHA-256 of the verifier string (ASCII), then base64url no padding
        expected_hash = hashlib.sha256(pair.verifier.encode("ascii")).digest()
        expected_challenge = base64.urlsafe_b64encode(expected_hash).rstrip(b"=").decode("ascii")
        self.assertEqual(pair.challenge, expected_challenge)

    def test_challenge_length(self):
        pair = generate_pkce_pair()
        # SHA-256 is 32 bytes -> 43 base64url chars (no padding)
        self.assertEqual(len(pair.challenge), 43)

    def test_pairs_are_unique(self):
        a = generate_pkce_pair()
        b = generate_pkce_pair()
        self.assertNotEqual(a.verifier, b.verifier)
        self.assertNotEqual(a.challenge, b.challenge)

    def test_deterministic_with_known_input(self):
        """Verify against a known PKCE test vector."""
        # Use a fixed 32-byte input to verify the encoding chain
        fixed_bytes = b"\x00" * 32
        verifier = base64.urlsafe_b64encode(fixed_bytes).rstrip(b"=").decode("ascii")
        challenge_hash = hashlib.sha256(verifier.encode("ascii")).digest()
        challenge = base64.urlsafe_b64encode(challenge_hash).rstrip(b"=").decode("ascii")

        with patch("os.urandom", return_value=fixed_bytes):
            pair = generate_pkce_pair()

        self.assertEqual(pair.verifier, verifier)
        self.assertEqual(pair.challenge, challenge)


class TestGenerateState(unittest.TestCase):
    def test_returns_string(self):
        state = generate_state()
        self.assertIsInstance(state, str)

    def test_base64url_no_padding(self):
        state = generate_state()
        self.assertNotIn("=", state)
        self.assertNotIn("+", state)
        self.assertNotIn("/", state)
        # 32 bytes -> 43 base64url chars
        self.assertEqual(len(state), 43)

    def test_unique(self):
        a = generate_state()
        b = generate_state()
        self.assertNotEqual(a, b)


class TestOAuthAuthorizationRequest(unittest.TestCase):
    def _make_req(self, **kwargs):
        defaults = dict(
            authorize_url="https://hanzo.id/oauth/authorize",
            client_id="app-hanzo",
            redirect_uri="http://localhost:4545/callback",
            scopes=["openid", "profile"],
            state="test-state",
            code_challenge="test-challenge",
            code_challenge_method="S256",
        )
        defaults.update(kwargs)
        return OAuthAuthorizationRequest(**defaults)

    def test_build_url_contains_all_params(self):
        req = self._make_req()
        url = req.build_url()
        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        self.assertEqual(parsed.scheme, "https")
        self.assertEqual(parsed.netloc, "hanzo.id")
        self.assertEqual(parsed.path, "/oauth/authorize")
        self.assertEqual(params["client_id"], ["app-hanzo"])
        self.assertEqual(params["redirect_uri"], ["http://localhost:4545/callback"])
        self.assertEqual(params["response_type"], ["code"])
        self.assertEqual(params["scope"], ["openid profile"])
        self.assertEqual(params["state"], ["test-state"])
        self.assertEqual(params["code_challenge"], ["test-challenge"])
        self.assertEqual(params["code_challenge_method"], ["S256"])

    def test_build_url_scopes_joined(self):
        req = self._make_req(scopes=["openid", "profile", "email"])
        url = req.build_url()
        params = parse_qs(urlparse(url).query)
        self.assertEqual(params["scope"], ["openid profile email"])

    def test_build_url_starts_with_authorize_url(self):
        req = self._make_req(authorize_url="https://custom.example.com/auth")
        url = req.build_url()
        self.assertTrue(url.startswith("https://custom.example.com/auth?"))


class TestOAuthTokenExchangeRequest(unittest.TestCase):
    def test_form_params(self):
        req = OAuthTokenExchangeRequest(
            code="auth-code-123",
            redirect_uri="http://localhost:4545/callback",
            client_id="app-hanzo",
            code_verifier="verifier-abc",
            state="state-xyz",
        )
        params = req.form_params()
        self.assertEqual(params["grant_type"], "authorization_code")
        self.assertEqual(params["code"], "auth-code-123")
        self.assertEqual(params["redirect_uri"], "http://localhost:4545/callback")
        self.assertEqual(params["client_id"], "app-hanzo")
        self.assertEqual(params["code_verifier"], "verifier-abc")
        self.assertEqual(params["state"], "state-xyz")

    def test_default_grant_type(self):
        req = OAuthTokenExchangeRequest(
            code="c", redirect_uri="r", client_id="ci", code_verifier="cv", state="s"
        )
        self.assertEqual(req.grant_type, "authorization_code")

    def test_form_params_keys(self):
        req = OAuthTokenExchangeRequest(
            code="c", redirect_uri="r", client_id="ci", code_verifier="cv", state="s"
        )
        params = req.form_params()
        expected_keys = {"grant_type", "code", "redirect_uri", "client_id", "code_verifier", "state"}
        self.assertEqual(set(params.keys()), expected_keys)


class TestOAuthTokenSet(unittest.TestCase):
    def test_required_fields(self):
        ts = OAuthTokenSet(access_token="tok123", scopes=["openid"])
        self.assertEqual(ts.access_token, "tok123")
        self.assertEqual(ts.scopes, ["openid"])
        self.assertIsNone(ts.refresh_token)
        self.assertIsNone(ts.expires_at)

    def test_all_fields(self):
        ts = OAuthTokenSet(
            access_token="tok",
            scopes=["openid"],
            refresh_token="ref",
            expires_at=1234567890,
        )
        self.assertEqual(ts.refresh_token, "ref")
        self.assertEqual(ts.expires_at, 1234567890)


class TestOAuthCredentialStore(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.store = OAuthCredentialStore(config_home=self.tmpdir)

    def test_credentials_path_default(self):
        with patch.dict(os.environ, {}, clear=False):
            # Remove HANZO_CONFIG_HOME if set
            env = os.environ.copy()
            env.pop("HANZO_CONFIG_HOME", None)
            with patch.dict(os.environ, env, clear=True):
                store = OAuthCredentialStore()
                expected = Path.home() / ".hanzo" / "credentials.json"
                self.assertEqual(store.credentials_path(), expected)

    def test_credentials_path_custom_config_home(self):
        self.assertEqual(
            self.store.credentials_path(),
            Path(self.tmpdir) / "credentials.json",
        )

    def test_credentials_path_env_override(self):
        with patch.dict(os.environ, {"HANZO_CONFIG_HOME": "/custom/path"}):
            store = OAuthCredentialStore()
            self.assertEqual(store.credentials_path(), Path("/custom/path/credentials.json"))

    def test_save_and_load_roundtrip(self):
        token_set = OAuthTokenSet(
            access_token="access123",
            refresh_token="refresh456",
            expires_at=9999999999,
            scopes=["openid", "profile"],
        )
        self.store.save(token_set)

        loaded = self.store.load()
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.access_token, "access123")
        self.assertEqual(loaded.refresh_token, "refresh456")
        self.assertEqual(loaded.expires_at, 9999999999)
        self.assertEqual(loaded.scopes, ["openid", "profile"])

    def test_save_preserves_other_keys(self):
        creds_path = self.store.credentials_path()
        creds_path.parent.mkdir(parents=True, exist_ok=True)
        with open(creds_path, "w") as f:
            json.dump({"api_key": "keep-me", "other": "data"}, f)

        token_set = OAuthTokenSet(access_token="tok", scopes=["openid"])
        self.store.save(token_set)

        with open(creds_path) as f:
            data = json.load(f)

        self.assertEqual(data["api_key"], "keep-me")
        self.assertEqual(data["other"], "data")
        self.assertIn("oauth", data)

    def test_load_returns_none_when_no_file(self):
        self.assertIsNone(self.store.load())

    def test_load_returns_none_when_no_oauth_key(self):
        creds_path = self.store.credentials_path()
        creds_path.parent.mkdir(parents=True, exist_ok=True)
        with open(creds_path, "w") as f:
            json.dump({"api_key": "something"}, f)

        self.assertIsNone(self.store.load())

    def test_clear_removes_oauth_preserves_rest(self):
        creds_path = self.store.credentials_path()
        creds_path.parent.mkdir(parents=True, exist_ok=True)
        with open(creds_path, "w") as f:
            json.dump({"api_key": "keep", "oauth": {"access_token": "remove"}}, f)

        self.store.clear()

        with open(creds_path) as f:
            data = json.load(f)

        self.assertEqual(data["api_key"], "keep")
        self.assertNotIn("oauth", data)

    def test_clear_noop_when_no_file(self):
        self.store.clear()  # should not raise

    def test_save_atomic_no_tmp_left(self):
        """After save, .tmp file should not exist."""
        token_set = OAuthTokenSet(access_token="tok", scopes=["openid"])
        self.store.save(token_set)

        creds_path = self.store.credentials_path()
        tmp_path = creds_path.with_suffix(".json.tmp")
        self.assertTrue(creds_path.exists())
        self.assertFalse(tmp_path.exists())

    def test_save_sets_restrictive_permissions(self):
        token_set = OAuthTokenSet(access_token="tok", scopes=["openid"])
        self.store.save(token_set)

        creds_path = self.store.credentials_path()
        mode = os.stat(creds_path).st_mode
        self.assertEqual(stat.S_IMODE(mode), 0o600)

    def test_save_creates_parent_dirs(self):
        nested = os.path.join(self.tmpdir, "deep", "nested")
        store = OAuthCredentialStore(config_home=nested)
        token_set = OAuthTokenSet(access_token="tok", scopes=["openid"])
        store.save(token_set)
        self.assertTrue(store.credentials_path().exists())


if __name__ == "__main__":
    unittest.main()
