# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from Hanzo_AI import HanzoAI, AsyncHanzoAI
from tests.utils import assert_matches_type
from Hanzo_AI.types import ProviderListBudgetsResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestProvider:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    def test_method_list_budgets(self, client: HanzoAI) -> None:
        provider = client.provider.list_budgets()
        assert_matches_type(ProviderListBudgetsResponse, provider, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_list_budgets(self, client: HanzoAI) -> None:
        response = client.provider.with_raw_response.list_budgets()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        provider = response.parse()
        assert_matches_type(ProviderListBudgetsResponse, provider, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_list_budgets(self, client: HanzoAI) -> None:
        with client.provider.with_streaming_response.list_budgets() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            provider = response.parse()
            assert_matches_type(ProviderListBudgetsResponse, provider, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncProvider:
    parametrize = pytest.mark.parametrize("async_client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_list_budgets(self, async_client: AsyncHanzoAI) -> None:
        provider = await async_client.provider.list_budgets()
        assert_matches_type(ProviderListBudgetsResponse, provider, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_list_budgets(self, async_client: AsyncHanzoAI) -> None:
        response = await async_client.provider.with_raw_response.list_budgets()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        provider = await response.parse()
        assert_matches_type(ProviderListBudgetsResponse, provider, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_list_budgets(self, async_client: AsyncHanzoAI) -> None:
        async with async_client.provider.with_streaming_response.list_budgets() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            provider = await response.parse()
            assert_matches_type(ProviderListBudgetsResponse, provider, path=["response"])

        assert cast(Any, response.is_closed) is True
