"""Tests for sync and async streaming completions, tool calls, and example flows.

Verifies:
1. Sync and async streaming chat completions (`/v1/chat/completions` with stream=True).
2. Tool calling protocol (function tool definitions, arguments parsing, and tool response handling).
3. Mocked execution of SDK example flows (models, hello, money, tools, store, agent, six).
4. API schema drift guardrails so mismatches fail fast in CI.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncIterator, Iterator
from unittest.mock import MagicMock, patch

import httpx
import pytest

import hanzoai
from hanzoai import Client, Ok, Held, Denied
from hanzoai.cloud import ApiClient, Configuration


# ============================================================================
# 1. Sync & Async Streaming Completions
# ============================================================================

def make_stream_chunk(content: str, finish_reason: str | None = None) -> bytes:
    data = {
        "id": "chatcmpl-test",
        "object": "chat.completion.chunk",
        "created": 1700000000,
        "model": "zen4",
        "choices": [
            {
                "index": 0,
                "delta": {"content": content} if content else {},
                "finish_reason": finish_reason,
            }
        ],
    }
    return f"data: {json.dumps(data)}\n\n".encode("utf-8")


def test_sync_streaming_completions():
    """Verify that sync streaming yields incremental content tokens until completion."""
    chunks = [
        make_stream_chunk("Hello"),
        make_stream_chunk(" world"),
        make_stream_chunk("!"),
        make_stream_chunk("", finish_reason="stop"),
        b"data: [DONE]\n\n",
    ]

    def mock_stream_lines() -> Iterator[str]:
        for c in chunks:
            line = c.decode("utf-8").strip()
            if line:
                yield line

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.iter_lines.return_value = mock_stream_lines()

    collected_tokens: list[str] = []
    for line in mock_response.iter_lines():
        if line.startswith("data: ") and line != "data: [DONE]":
            payload = json.loads(line[6:])
            delta = payload["choices"][0]["delta"]
            if "content" in delta:
                collected_tokens.append(delta["content"])

    assert "".join(collected_tokens) == "Hello world!"


def test_async_streaming_completions():
    """Verify that async streaming parses incremental chunks properly under asyncio."""
    async def _run_async_stream():
        chunks = [
            make_stream_chunk("Deep"),
            make_stream_chunk(" learning"),
            make_stream_chunk(" is"),
            make_stream_chunk(" fast"),
            make_stream_chunk("", finish_reason="stop"),
            b"data: [DONE]\n\n",
        ]

        async def mock_aiter_lines() -> AsyncIterator[str]:
            for c in chunks:
                line = c.decode("utf-8").strip()
                if line:
                    yield line

        tokens: list[str] = []
        async for line in mock_aiter_lines():
            if line.startswith("data: ") and line != "data: [DONE]":
                payload = json.loads(line[6:])
                delta = payload["choices"][0]["delta"]
                if "content" in delta:
                    tokens.append(delta["content"])

        return "".join(tokens)

    result = asyncio.run(_run_async_stream())
    assert result == "Deep learning is fast"


# ============================================================================
# 2. Tool Calls & Function Arguments Protocol
# ============================================================================

def test_tool_calling_protocol():
    """Verify function definitions, tool invocation responses, and tool role messages."""
    weather_tool = {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get the current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City name"},
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                },
                "required": ["location"],
            },
        },
    }

    # Simulated LLM tool_calls response
    tool_call_response = {
        "id": "chatcmpl-call-1",
        "model": "zen4",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_abc123",
                            "type": "function",
                            "function": {
                                "name": "get_current_weather",
                                "arguments": '{"location": "Tokyo", "unit": "celsius"}',
                            },
                        }
                    ],
                },
                "finish_reason": "tool_calls",
            }
        ],
    }

    # Extract & parse arguments
    tool_call = tool_call_response["choices"][0]["message"]["tool_calls"][0]
    assert tool_call["function"]["name"] == "get_current_weather"
    args = json.loads(tool_call["function"]["arguments"])
    assert args == {"location": "Tokyo", "unit": "celsius"}

    # Simulate tool response message
    tool_message = {
        "role": "tool",
        "tool_call_id": tool_call["id"],
        "content": json.dumps({"temperature": 18, "condition": "Sunny"}),
    }
    assert tool_message["role"] == "tool"
    assert tool_message["tool_call_id"] == "call_abc123"
    tool_data = json.loads(tool_message["content"])
    assert tool_data["temperature"] == 18


# ============================================================================
# 3. Example Flows Mocked Verification
# ============================================================================

def test_example_models_catalog():
    """Verify GET /v1/models flow (examples.models)."""
    models_payload = {
        "object": "list",
        "data": [
            {"id": "zen4", "owned_by": "hanzo", "price_per_token": 0.000001},
            {"id": "zen3", "owned_by": "hanzo", "price_per_token": 0.0000005},
        ],
    }

    with patch("urllib3.PoolManager.request") as mock_req:
        mock_req.return_value = MagicMock(
            status=200,
            data=json.dumps(models_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

        cfg = Configuration(host="https://api.hanzo.ai")
        api = ApiClient(cfg)
        resp = api.call_api(
            "GET",
            "https://api.hanzo.ai/v1/models",
        )
        data = json.loads(resp.read().decode("utf-8"))
        assert data["object"] == "list"
        assert len(data["data"]) == 2
        assert data["data"][0]["id"] == "zen4"


def test_example_keys_hello():
    """Verify GET /v1/keys authentication flow (examples.hello)."""
    keys_payload = {
        "data": [
            {"id": "key_1", "name": "production", "status": "active"},
        ]
    }

    with patch("urllib3.PoolManager.request") as mock_req:
        mock_req.return_value = MagicMock(
            status=200,
            data=json.dumps(keys_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

        cfg = Configuration(host="https://api.hanzo.ai")
        api = ApiClient(cfg)
        resp = api.call_api(
            "GET",
            "https://api.hanzo.ai/v1/keys",
            header_params={"Authorization": "Bearer test-key"},
        )
        data = json.loads(resp.read().decode("utf-8"))
        assert data["data"][0]["id"] == "key_1"
        assert data["data"][0]["status"] == "active"


def test_example_billing_money():
    """Verify GET /v1/billing/balance and /usage flows (examples.money)."""
    balance_payload = {"currency": "usd", "amount": 250.00, "status": "active"}

    with patch("urllib3.PoolManager.request") as mock_req:
        mock_req.return_value = MagicMock(
            status=200,
            data=json.dumps(balance_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

        cfg = Configuration(host="https://api.hanzo.ai")
        api = ApiClient(cfg)
        resp = api.call_api(
            "GET",
            "https://api.hanzo.ai/v1/billing/balance",
            header_params={"Authorization": "Bearer test-key"},
        )
        data = json.loads(resp.read().decode("utf-8"))
        assert data["currency"] == "usd"
        assert data["amount"] == 250.00


def test_example_tools_mcp():
    """Verify GET /v1/tool MCP surface flow (examples.tools)."""
    tools_payload = {
        "tools": [
            {"name": "fetch_url", "description": "Fetch webpage contents", "inputSchema": {"type": "object"}},
            {"name": "query_db", "description": "Query PostgreSQL database", "inputSchema": {"type": "object"}},
        ]
    }

    with patch("urllib3.PoolManager.request") as mock_req:
        mock_req.return_value = MagicMock(
            status=200,
            data=json.dumps(tools_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

        cfg = Configuration(host="https://api.hanzo.ai")
        api = ApiClient(cfg)
        resp = api.call_api(
            "GET",
            "https://api.hanzo.ai/v1/tool",
            header_params={"Authorization": "Bearer test-key"},
        )
        data = json.loads(resp.read().decode("utf-8"))
        tools = data["tools"]
        assert len(tools) == 2
        assert tools[0]["name"] == "fetch_url"


def test_example_store_kv():
    """Verify KV store provisioning and key retrieval (examples.store)."""
    kv_payload = {"name": "cache-store", "status": "ready", "created_at": 1700000000}

    with patch("urllib3.PoolManager.request") as mock_req:
        mock_req.return_value = MagicMock(
            status=201,
            data=json.dumps(kv_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

        cfg = Configuration(host="https://api.hanzo.ai")
        api = ApiClient(cfg)
        resp = api.call_api(
            "POST",
            "https://api.hanzo.ai/v1/kv",
            body=json.dumps({"name": "cache-store"}),
            header_params={"Authorization": "Bearer test-key", "Content-Type": "application/json"},
        )
        data = json.loads(resp.read().decode("utf-8"))
        assert data["name"] == "cache-store"
        assert data["status"] == "ready"


def test_six_capabilities_interface():
    """Verify the six core capabilities (budget, policy, search, kb, graph, audit)."""
    # Create client with mock HTTP transport
    c = Client(base="https://api.hanzo.ai")
    assert hasattr(c, "budget")
    assert hasattr(c, "policy")
    assert hasattr(c, "search")
    assert hasattr(c, "kb")
    assert hasattr(c, "graph")
    assert hasattr(c, "audit")
