"""Tests for PKCE OAuth support in hanzoai.auth.

Run: .venv/bin/python -m pytest tests/test_auth_pkce.py -v
"""

import os
import json
import stat
import base64
import hashlib
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from unittest.mock import AsyncMock, MagicMock, patch

from hanzoai.auth import (
    OPENAI_ISSUER,
    HANZO_CLIENT_ID,
    OPENAI_CLIENT_ID,
    ANTHROPIC_CLIENT_ID,
    ANTHROPIC_TOKEN_URL,
    ANTHROPIC_AUTHORIZE_URL,
    HanzoAuth,
    PkceCodePair,
    OAuthTokenSet,
    OAuthCredentialStore,
    OAuthAuthorizationRequest,
    OAuthTokenExchangeRequest,
    generate_state,
    generate_pkce_pair,
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


class TestOAuthCredentialStoreMultiProvider(unittest.TestCase):
    """Tests for multi-provider credential storage."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.store = OAuthCredentialStore(config_home=self.tmpdir)

    def test_save_load_anthropic_provider(self):
        token_set = OAuthTokenSet(
            access_token="anth-tok", scopes=["openid"], refresh_token="anth-ref"
        )
        self.store.save(token_set, provider="anthropic")
        loaded = self.store.load(provider="anthropic")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.access_token, "anth-tok")
        self.assertEqual(loaded.refresh_token, "anth-ref")

    def test_save_load_openai_provider(self):
        token_set = OAuthTokenSet(
            access_token="oai-tok", scopes=["openid"], expires_at=123456
        )
        self.store.save(token_set, provider="openai")
        loaded = self.store.load(provider="openai")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.access_token, "oai-tok")
        self.assertEqual(loaded.expires_at, 123456)

    def test_default_provider_is_hanzo(self):
        token_set = OAuthTokenSet(access_token="hz-tok", scopes=["openid"])
        self.store.save(token_set)  # no provider arg
        loaded = self.store.load()  # no provider arg
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.access_token, "hz-tok")

    def test_providers_are_independent(self):
        """Saving to one provider does not affect another."""
        self.store.save(
            OAuthTokenSet(access_token="hz", scopes=["a"]), provider="hanzo"
        )
        self.store.save(
            OAuthTokenSet(access_token="anth", scopes=["b"]), provider="anthropic"
        )
        self.store.save(
            OAuthTokenSet(access_token="oai", scopes=["c"]), provider="openai"
        )

        self.assertEqual(self.store.load(provider="hanzo").access_token, "hz")
        self.assertEqual(self.store.load(provider="anthropic").access_token, "anth")
        self.assertEqual(self.store.load(provider="openai").access_token, "oai")

    def test_clear_only_affects_target_provider(self):
        self.store.save(
            OAuthTokenSet(access_token="hz", scopes=["a"]), provider="hanzo"
        )
        self.store.save(
            OAuthTokenSet(access_token="anth", scopes=["b"]), provider="anthropic"
        )

        self.store.clear(provider="hanzo")

        self.assertIsNone(self.store.load(provider="hanzo"))
        self.assertEqual(self.store.load(provider="anthropic").access_token, "anth")

    def test_backwards_compatible_json_key(self):
        """Default hanzo provider uses 'oauth' key in JSON for backwards compat."""
        self.store.save(
            OAuthTokenSet(access_token="hz", scopes=["a"]), provider="hanzo"
        )
        with open(self.store.credentials_path()) as f:
            data = json.load(f)
        self.assertIn("oauth", data)
        self.assertEqual(data["oauth"]["access_token"], "hz")

    def test_anthropic_uses_distinct_json_key(self):
        self.store.save(
            OAuthTokenSet(access_token="anth", scopes=["a"]), provider="anthropic"
        )
        with open(self.store.credentials_path()) as f:
            data = json.load(f)
        self.assertIn("oauth_anthropic", data)
        self.assertNotIn("oauth", data)

    def test_openai_uses_distinct_json_key(self):
        self.store.save(
            OAuthTokenSet(access_token="oai", scopes=["a"]), provider="openai"
        )
        with open(self.store.credentials_path()) as f:
            data = json.load(f)
        self.assertIn("oauth_openai", data)
        self.assertNotIn("oauth", data)

    def test_unknown_provider_raises(self):
        with self.assertRaises(ValueError):
            self.store.save(
                OAuthTokenSet(access_token="x", scopes=["a"]), provider="github"
            )
        with self.assertRaises(ValueError):
            self.store.load(provider="github")
        with self.assertRaises(ValueError):
            self.store.clear(provider="github")

    def test_load_returns_none_for_missing_provider(self):
        self.store.save(
            OAuthTokenSet(access_token="hz", scopes=["a"]), provider="hanzo"
        )
        self.assertIsNone(self.store.load(provider="anthropic"))
        self.assertIsNone(self.store.load(provider="openai"))


class TestProviderConstants(unittest.TestCase):
    """Verify provider constants match the Rust codex-rs values."""

    def test_openai_client_id(self):
        self.assertEqual(OPENAI_CLIENT_ID, "app_EMoamEEZ73f0CkXaXp7hrann")

    def test_openai_issuer(self):
        self.assertEqual(OPENAI_ISSUER, "https://auth.openai.com")

    def test_anthropic_client_id(self):
        self.assertEqual(ANTHROPIC_CLIENT_ID, "9d1c250a-e61b-44d9-88ed-5944d1962f5e")

    def test_anthropic_authorize_url(self):
        self.assertEqual(ANTHROPIC_AUTHORIZE_URL, "https://claude.ai/oauth/authorize")

    def test_anthropic_token_url(self):
        self.assertEqual(ANTHROPIC_TOKEN_URL, "https://platform.claude.com/v1/oauth/token")

    def test_hanzo_client_id(self):
        self.assertEqual(HANZO_CLIENT_ID, "hanzo-dev")


class TestLoginAuto(unittest.TestCase):
    """Tests for HanzoAuth.login_auto() env var detection."""

    def test_hanzo_api_key_takes_priority(self):
        import asyncio
        auth = HanzoAuth()
        env = {
            "HANZO_API_KEY": "hk-test",
            "ANTHROPIC_API_KEY": "sk-ant-test",
            "OPENAI_API_KEY": "sk-test",
        }
        with patch.dict(os.environ, env):
            result = asyncio.run(auth.login_auto())
        self.assertEqual(result["provider"], "hanzo")
        self.assertEqual(result["api_key"], "hk-test")
        self.assertEqual(auth.api_key, "hk-test")

    def test_anthropic_api_key_second_priority(self):
        import asyncio
        auth = HanzoAuth()
        env = {"ANTHROPIC_API_KEY": "sk-ant-test"}
        with patch.dict(os.environ, env, clear=False):
            # Ensure HANZO_API_KEY is not set
            os.environ.pop("HANZO_API_KEY", None)
            os.environ.pop("OPENAI_API_KEY", None)
            result = asyncio.run(auth.login_auto())
        self.assertEqual(result["provider"], "anthropic")
        self.assertEqual(result["api_key"], "sk-ant-test")

    def test_openai_api_key_third_priority(self):
        import asyncio
        auth = HanzoAuth()
        env = {"OPENAI_API_KEY": "sk-test"}
        with patch.dict(os.environ, env, clear=False):
            os.environ.pop("HANZO_API_KEY", None)
            os.environ.pop("ANTHROPIC_API_KEY", None)
            result = asyncio.run(auth.login_auto())
        self.assertEqual(result["provider"], "openai")
        self.assertEqual(result["api_key"], "sk-test")

    def test_saved_credentials_used_when_no_env(self):
        import asyncio
        tmpdir = tempfile.mkdtemp()
        store = OAuthCredentialStore(config_home=tmpdir)
        store.save(
            OAuthTokenSet(access_token="saved-anth", scopes=["openid"]),
            provider="anthropic",
        )
        auth = HanzoAuth()
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("HANZO_API_KEY", None)
            os.environ.pop("ANTHROPIC_API_KEY", None)
            os.environ.pop("OPENAI_API_KEY", None)
            # Patch the OAuthCredentialStore used inside login_auto
            with patch("hanzoai.auth.OAuthCredentialStore", return_value=store):
                result = asyncio.run(auth.login_auto())
        self.assertEqual(result["provider"], "anthropic")
        self.assertEqual(result["token"], "saved-anth")


if __name__ == "__main__":
    unittest.main()
