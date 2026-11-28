"""Tests for Python 3.12+ async streaming, mock OpenAPI drift resilience, and MCP/IAM verification.
Addresses Issue #55: [Intern] Quickstart, async streaming & MCP/IAM example verification on Python 3.12+
"""

import sys
import json
import pytest
from unittest.mock import MagicMock
from hanzoai.protocols import AssistantEvent, _build_assistant_message, TokenUsage
from hanzoai.cloud import Configuration, ApiClient, ToolApi, AccountApi


def test_python_312_runtime_environment():
    """Verify test execution strictly runs on Python 3.12+."""
    assert sys.version_info >= (3, 12), f"Expected Python 3.12+, found {sys.version}"


def test_mcp_catalog_mock_drift_at_transport_layer():
    """Verify ToolApi MCP endpoint at HTTP transport layer with realistic OpenAPI JSON deserialization."""
    config = Configuration(host="https://api.hanzo.ai")
    client = ApiClient(config)

    # Realistic OpenAPI response payload for /v1/tool
    tool_payload = {
        "incomplete": None,
        "tools": [
            {
                "name": "web_search",
                "description": "Searches the live web for verified facts"
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.data = json.dumps(tool_payload).encode("utf-8")
    mock_resp.getheader.return_value = "application/json"
    mock_resp.getheaders.return_value = {"Content-Type": "application/json"}

    client.call_api = MagicMock(return_value=mock_resp)

    api = ToolApi(client)
    res = api.get_tool()

    # Asserts that generated SDK methods successfully constructed request and deserialized OpenAPI shape
    assert client.call_api.called
    assert res.tools is not None
    assert len(res.tools) == 1
    assert res.tools[0].name == "web_search"
    assert "web" in res.tools[0].description


def test_iam_account_keys_verification_at_transport_layer():
    """Verify AccountApi at HTTP transport layer with realistic OpenAPI JSON deserialization."""
    config = Configuration(host="https://api.hanzo.ai")
    client = ApiClient(config)

    # Realistic OpenAPI response payload for /v1/account/keys
    keys_payload = {
        "keys": [
            {
                "id": "key_01jh89f0293hf82h",
                "prefix": "hz_live_abc123",
                "name": "production-key",
                "role": "admin"
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.data = json.dumps(keys_payload).encode("utf-8")
    mock_resp.getheader.return_value = "application/json"
    mock_resp.getheaders.return_value = {"Content-Type": "application/json"}

    client.call_api = MagicMock(return_value=mock_resp)

    api = AccountApi(client)
    res = api.get_account_keys()

    assert client.call_api.called
    assert res.keys is not None
    assert len(res.keys) == 1
    assert res.keys[0].prefix.startswith("hz_live_")


@pytest.mark.asyncio
async def test_async_streaming_event_protocol_and_sse_parser():
    """Verify asynchronous SSE / event stream chunk parsing into assistant message, tool calls, and usage."""
    # Simulated realistic SSE chunks as pushed by the gateway/API
    raw_sse_chunks = [
        'event: text_delta\ndata: {"text": "Hello, "}\n\n',
        'event: text_delta\ndata: {"text": "world!"}\n\n',
        'event: tool_use\ndata: {"id": "call_123", "name": "calculator", "input": {"a": 2, "b": 2}}\n\n',
        'event: usage\ndata: {"input_tokens": 15, "output_tokens": 8}\n\n',
        'event: message_stop\ndata: {}\n\n'
    ]

    async def sse_chunk_stream():
        for chunk in raw_sse_chunks:
            yield chunk

    # Parse SSE stream into structured SDK AssistantEvent objects
    parsed_events = []
    async for chunk in sse_chunk_stream():
        lines = chunk.strip().split("\n")
        ev_type = ""
        ev_data = {}
        for line in lines:
            if line.startswith("event: "):
                ev_type = line[len("event: "):].strip()
            elif line.startswith("data: "):
                ev_data = json.loads(line[len("data: "):].strip())

        if ev_type == "text_delta":
            parsed_events.append(AssistantEvent(kind="text_delta", text=ev_data.get("text", "")))
        elif ev_type == "tool_use":
            parsed_events.append(AssistantEvent(
                kind="tool_use",
                tool_use_id=ev_data.get("id"),
                tool_name=ev_data.get("name"),
                tool_input=ev_data.get("input")
            ))
        elif ev_type == "usage":
            parsed_events.append(AssistantEvent(
                kind="usage",
                usage=TokenUsage(
                    input_tokens=ev_data.get("input_tokens", 0),
                    output_tokens=ev_data.get("output_tokens", 0)
                )
            ))
        elif ev_type == "message_stop":
            parsed_events.append(AssistantEvent(kind="message_stop"))

    # Pass the parsed event stream through the SDK's message assembler
    msg, tool_uses, usage = _build_assistant_message(parsed_events)

    assert msg["role"] == "assistant"
    assert len(msg["blocks"]) == 2
    assert msg["blocks"][0] == {"type": "text", "text": "Hello, world!"}
    assert msg["blocks"][1]["type"] == "tool_use"
    assert msg["blocks"][1]["name"] == "calculator"
    assert len(tool_uses) == 1
    assert tool_uses[0].tool_name == "calculator"
    assert usage.input_tokens == 15
    assert usage.output_tokens == 8
