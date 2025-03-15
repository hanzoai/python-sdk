# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from Hanzo_AI import HanzoAI, AsyncHanzoAI
from tests.utils import assert_matches_type
from Hanzo_AI.types import GuardrailListResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestGuardrails:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    def test_method_list(self, client: HanzoAI) -> None:
        guardrail = client.guardrails.list()
        assert_matches_type(GuardrailListResponse, guardrail, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_list(self, client: HanzoAI) -> None:
        response = client.guardrails.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        guardrail = response.parse()
        assert_matches_type(GuardrailListResponse, guardrail, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_list(self, client: HanzoAI) -> None:
        with client.guardrails.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            guardrail = response.parse()
            assert_matches_type(GuardrailListResponse, guardrail, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncGuardrails:
    parametrize = pytest.mark.parametrize("async_client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_list(self, async_client: AsyncHanzoAI) -> None:
        guardrail = await async_client.guardrails.list()
        assert_matches_type(GuardrailListResponse, guardrail, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncHanzoAI) -> None:
        response = await async_client.guardrails.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        guardrail = await response.parse()
        assert_matches_type(GuardrailListResponse, guardrail, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncHanzoAI) -> None:
        async with async_client.guardrails.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            guardrail = await response.parse()
            assert_matches_type(GuardrailListResponse, guardrail, path=["response"])

        assert cast(Any, response.is_closed) is True
