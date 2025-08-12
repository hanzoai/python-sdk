"""Tests for authentication."""

from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials

from hanzo_memory.api.auth import (
    get_api_key,
    get_or_verify_user_id,
    require_auth,
    verify_api_key,
)


class TestAuth:
    """Test authentication functions."""

    def test_get_api_key_from_header(self):
        """Test getting API key from Authorization header."""
        request = Mock(spec=Request)
        request.headers = {}
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="test-key"
        )

        api_key = get_api_key(request, credentials)
        assert api_key == "test-key"

    def test_get_api_key_from_header_value(self):
        """Test getting API key from X-API-Key header."""
        request = Mock(spec=Request)
        request.headers = {"x-api-key": "header-key"}

        api_key = get_api_key(request, None)
        assert api_key == "header-key"

    def test_get_api_key_none(self):
        """Test getting API key when none provided."""
        request = Mock(spec=Request)
        request.headers = {}

        api_key = get_api_key(request, None)
        assert api_key is None

    @patch("hanzo_memory.api.auth.settings")
    def test_verify_api_key_valid(self, mock_settings):
        """Test verifying valid API key."""
        mock_settings.disable_auth = False
        mock_settings.api_key = "valid-key"
        assert verify_api_key("valid-key") is True

    @patch("hanzo_memory.api.auth.settings")
    def test_verify_api_key_invalid(self, mock_settings):
        """Test verifying invalid API key."""
        mock_settings.disable_auth = False
        mock_settings.api_key = "valid-key"
        assert verify_api_key("invalid-key") is False

    @patch("hanzo_memory.api.auth.settings")
    def test_verify_api_key_none_configured(self, mock_settings):
        """Test verifying API key when none configured."""
        mock_settings.disable_auth = False
        mock_settings.api_key = None
        assert verify_api_key("any-key") is False

    @patch("hanzo_memory.api.auth.settings")
    def test_verify_api_key_none_provided(self, mock_settings):
        """Test verifying when no API key provided."""
        mock_settings.disable_auth = False
        mock_settings.api_key = "valid-key"
        assert verify_api_key(None) is False

    @patch("hanzo_memory.api.auth.settings")
    def test_require_auth_disabled(self, mock_settings):
        """Test require_auth when auth is disabled."""
        mock_settings.disable_auth = True
        request = Mock(spec=Request)
        request.headers = {}

        result = require_auth(request, None)
        assert result == "disabled"

    @patch("hanzo_memory.api.auth.settings")
    def test_require_auth_valid_key(self, mock_settings):
        """Test require_auth with valid API key."""
        mock_settings.disable_auth = False
        mock_settings.api_key = "valid-key"
        request = Mock(spec=Request)
        request.headers = {"x-api-key": "valid-key"}

        result = require_auth(request, None)
        assert result == "valid-key"

    @patch("hanzo_memory.api.auth.settings")
    def test_require_auth_invalid_key(self, mock_settings):
        """Test require_auth with invalid API key."""
        mock_settings.disable_auth = False
        mock_settings.api_key = "valid-key"
        request = Mock(spec=Request)
        request.headers = {"x-api-key": "invalid-key"}

        with pytest.raises(HTTPException) as exc_info:
            require_auth(request, None)
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @patch("hanzo_memory.api.auth.settings")
    async def test_get_or_verify_user_id_auth_disabled(self, mock_settings):
        """Test get_or_verify_user_id when auth is disabled."""
        mock_settings.disable_auth = True
        request = Mock(spec=Request)

        result = await get_or_verify_user_id("user123", None, request)
        assert result == "user123"

    @patch("hanzo_memory.api.auth.settings")
    @patch("hanzo_memory.api.auth.require_auth")
    async def test_get_or_verify_user_id_auth_enabled(
        self, mock_require_auth, mock_settings
    ):
        """Test get_or_verify_user_id when auth is enabled."""
        mock_settings.disable_auth = False
        mock_require_auth.return_value = "valid-key"
        request = Mock(spec=Request)
        credentials = Mock(spec=HTTPAuthorizationCredentials)

        result = await get_or_verify_user_id("user123", credentials, request)
        assert result == "user123"
        mock_require_auth.assert_called_once_with(request, credentials)
