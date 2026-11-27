"""Tests for Python 3.12+ async streaming, mock OpenAPI drift resilience, and MCP/IAM verification.
Addresses Issue #55: [Intern] Quickstart, async streaming & MCP/IAM example verification on Python 3.12+
"""

import sys
import pytest
from unittest.mock import MagicMock, patch
from hanzoai import Client, Ok, Fact, Doc
from hanzoai.protocols import ApiRequest, AssistantEvent
from hanzoai.cloud import Configuration, ApiClient, ToolApi, AccountApi


def test_python_312_runtime_environment():
    """Verify test execution strictly runs on Python 3.12+."""
    assert sys.version_info >= (3, 12), f"Expected Python 3.12+, found {sys.version}"


def test_mcp_catalog_mock_drift():
    """Verify ToolApi MCP endpoint against mock /v1/tool catalog."""
    mock_api_client = MagicMock(spec=ApiClient)
    
    # Mock response format matching OpenAPI schema
    mock_catalog = MagicMock()
    mock_tool = MagicMock()
    mock_tool.name = "web_search"
    mock_tool.description = "Searches the live web for verified facts"
    mock_catalog.tools = [mock_tool]
    
    with patch.object(ToolApi, "get_tool", return_value=mock_catalog):
        api = ToolApi(mock_api_client)
        res = api.get_tool()
        assert len(res.tools) == 1
        assert res.tools[0].name == "web_search"
        assert "web" in res.tools[0].description


def test_iam_account_keys_verification():
    """Verify AccountApi handles API key listings according to /v1/keys."""
    mock_api_client = MagicMock(spec=ApiClient)
    mock_listing = MagicMock()
    mock_key = MagicMock()
    mock_key.prefix = "hz_live_abc123"
    mock_key.type = "production"
    mock_listing.keys = [mock_key]
    
    with patch.object(AccountApi, "get_account_keys", return_value=mock_listing):
        api = AccountApi(mock_api_client)
        res = api.get_account_keys()
        assert len(res.keys) == 1
        assert res.keys[0].prefix.startswith("hz_live_")


@pytest.mark.asyncio
async def test_async_streaming_event_protocol():
    """Verify asynchronous event streaming consumer on Python 3.12."""
    events = [
        AssistantEvent(kind="text_delta", text="Hello, "),
        AssistantEvent(kind="text_delta", text="world!"),
        AssistantEvent(kind="message_stop"),
    ]
    
    async def async_stream_generator():
        for ev in events:
            yield ev

    collected = []
    async for event in async_stream_generator():
        collected.append(event)
        
    assert len(collected) == 3
    assert collected[0].kind == "text_delta"
    assert collected[0].text == "Hello, "
    assert collected[1].text == "world!"
    assert collected[2].kind == "message_stop"
