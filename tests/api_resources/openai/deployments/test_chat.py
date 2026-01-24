# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from hanzoai import Hanzo, AsyncHanzo
from tests.utils import assert_matches_type

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestChat:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_complete(self, client: Hanzo) -> None:
        chat = client.openai.deployments.chat.complete(
            path_model="model",
            messages=[
                {
                    "content": "Hello, how are you?",
                    "role": "user",
                }
            ],
            body_model="model",
        )
        assert_matches_type(object, chat, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_complete_with_all_params(self, client: Hanzo) -> None:
        chat = client.openai.deployments.chat.complete(
            path_model="model",
            messages=[
                {
                    "content": "Hello, how are you?",
                    "role": "user",
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            body_model="model",
            caching=True,
            context_window_fallback_dict={"foo": "string"},
            fallbacks=["string"],
            frequency_penalty=0,
            function_call="string",
            functions=[{"foo": "bar"}],
            guardrails=["string"],
            logit_bias={"foo": 0},
            logprobs=True,
            max_tokens=0,
            metadata={"foo": "bar"},
            n=0,
            num_retries=0,
            parallel_tool_calls=True,
            presence_penalty=0,
            response_format={"foo": "bar"},
            seed=0,
            service_tier="service_tier",
            stop="string",
            stream=True,
            stream_options={"foo": "bar"},
            temperature=0,
            tool_choice="string",
            tools=[{"foo": "bar"}],
            top_logprobs=0,
            top_p=0,
            user="user",
        )
        assert_matches_type(object, chat, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_complete(self, client: Hanzo) -> None:
        response = client.openai.deployments.chat.with_raw_response.complete(
            path_model="model",
            messages=[
                {
                    "content": "Hello, how are you?",
                    "role": "user",
                }
            ],
            body_model="model",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        chat = response.parse()
        assert_matches_type(object, chat, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_complete(self, client: Hanzo) -> None:
        with client.openai.deployments.chat.with_streaming_response.complete(
            path_model="model",
            messages=[
                {
                    "content": "Hello, how are you?",
                    "role": "user",
                }
            ],
            body_model="model",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            chat = response.parse()
            assert_matches_type(object, chat, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_complete(self, client: Hanzo) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `path_model` but received ''"):
            client.openai.deployments.chat.with_raw_response.complete(
                path_model="",
                messages=[
                    {
                        "content": "Hello, how are you?",
                        "role": "user",
                    }
                ],
                body_model="model",
            )


class TestAsyncChat:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_complete(self, async_client: AsyncHanzo) -> None:
        chat = await async_client.openai.deployments.chat.complete(
            path_model="model",
            messages=[
                {
                    "content": "Hello, how are you?",
                    "role": "user",
                }
            ],
            body_model="model",
        )
        assert_matches_type(object, chat, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_complete_with_all_params(self, async_client: AsyncHanzo) -> None:
        chat = await async_client.openai.deployments.chat.complete(
            path_model="model",
            messages=[
                {
                    "content": "Hello, how are you?",
                    "role": "user",
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            body_model="model",
            caching=True,
            context_window_fallback_dict={"foo": "string"},
            fallbacks=["string"],
            frequency_penalty=0,
            function_call="string",
            functions=[{"foo": "bar"}],
            guardrails=["string"],
            logit_bias={"foo": 0},
            logprobs=True,
            max_tokens=0,
            metadata={"foo": "bar"},
            n=0,
            num_retries=0,
            parallel_tool_calls=True,
            presence_penalty=0,
            response_format={"foo": "bar"},
            seed=0,
            service_tier="service_tier",
            stop="string",
            stream=True,
            stream_options={"foo": "bar"},
            temperature=0,
            tool_choice="string",
            tools=[{"foo": "bar"}],
            top_logprobs=0,
            top_p=0,
            user="user",
        )
        assert_matches_type(object, chat, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_complete(self, async_client: AsyncHanzo) -> None:
        response = await async_client.openai.deployments.chat.with_raw_response.complete(
            path_model="model",
            messages=[
                {
                    "content": "Hello, how are you?",
                    "role": "user",
                }
            ],
            body_model="model",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        chat = await response.parse()
        assert_matches_type(object, chat, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_complete(self, async_client: AsyncHanzo) -> None:
        async with async_client.openai.deployments.chat.with_streaming_response.complete(
            path_model="model",
            messages=[
                {
                    "content": "Hello, how are you?",
                    "role": "user",
                }
            ],
            body_model="model",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            chat = await response.parse()
            assert_matches_type(object, chat, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_complete(self, async_client: AsyncHanzo) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `path_model` but received ''"):
            await async_client.openai.deployments.chat.with_raw_response.complete(
                path_model="",
                messages=[
                    {
                        "content": "Hello, how are you?",
                        "role": "user",
                    }
                ],
                body_model="model",
            )
