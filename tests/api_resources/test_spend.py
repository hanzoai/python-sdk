# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from hanzoai import Hanzo, AsyncHanzo
from tests.utils import assert_matches_type
from hanzoai.types import (
    SpendListLogsResponse,
    SpendListTagsResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestSpend:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    def test_method_calculate_spend(self, client: Hanzo) -> None:
        spend = client.spend.calculate_spend()
        assert_matches_type(object, spend, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_calculate_spend_with_all_params(self, client: Hanzo) -> None:
        spend = client.spend.calculate_spend(
            completion_response={},
            messages=[{}],
            model="model",
        )
        assert_matches_type(object, spend, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_calculate_spend(self, client: Hanzo) -> None:
        response = client.spend.with_raw_response.calculate_spend()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        spend = response.parse()
        assert_matches_type(object, spend, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_calculate_spend(self, client: Hanzo) -> None:
        with client.spend.with_streaming_response.calculate_spend() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            spend = response.parse()
            assert_matches_type(object, spend, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_list_logs(self, client: Hanzo) -> None:
        spend = client.spend.list_logs()
        assert_matches_type(SpendListLogsResponse, spend, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_list_logs_with_all_params(self, client: Hanzo) -> None:
        spend = client.spend.list_logs(
            api_key="api_key",
            end_date="end_date",
            request_id="request_id",
            start_date="start_date",
            user_id="user_id",
        )
        assert_matches_type(SpendListLogsResponse, spend, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_list_logs(self, client: Hanzo) -> None:
        response = client.spend.with_raw_response.list_logs()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        spend = response.parse()
        assert_matches_type(SpendListLogsResponse, spend, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_list_logs(self, client: Hanzo) -> None:
        with client.spend.with_streaming_response.list_logs() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            spend = response.parse()
            assert_matches_type(SpendListLogsResponse, spend, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_list_tags(self, client: Hanzo) -> None:
        spend = client.spend.list_tags()
        assert_matches_type(SpendListTagsResponse, spend, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_list_tags_with_all_params(self, client: Hanzo) -> None:
        spend = client.spend.list_tags(
            end_date="end_date",
            start_date="start_date",
        )
        assert_matches_type(SpendListTagsResponse, spend, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_list_tags(self, client: Hanzo) -> None:
        response = client.spend.with_raw_response.list_tags()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        spend = response.parse()
        assert_matches_type(SpendListTagsResponse, spend, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_list_tags(self, client: Hanzo) -> None:
        with client.spend.with_streaming_response.list_tags() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            spend = response.parse()
            assert_matches_type(SpendListTagsResponse, spend, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncSpend:
    parametrize = pytest.mark.parametrize("async_client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_calculate_spend(self, async_client: AsyncHanzo) -> None:
        spend = await async_client.spend.calculate_spend()
        assert_matches_type(object, spend, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_calculate_spend_with_all_params(self, async_client: AsyncHanzo) -> None:
        spend = await async_client.spend.calculate_spend(
            completion_response={},
            messages=[{}],
            model="model",
        )
        assert_matches_type(object, spend, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_calculate_spend(self, async_client: AsyncHanzo) -> None:
        response = await async_client.spend.with_raw_response.calculate_spend()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        spend = await response.parse()
        assert_matches_type(object, spend, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_calculate_spend(self, async_client: AsyncHanzo) -> None:
        async with async_client.spend.with_streaming_response.calculate_spend() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            spend = await response.parse()
            assert_matches_type(object, spend, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_list_logs(self, async_client: AsyncHanzo) -> None:
        spend = await async_client.spend.list_logs()
        assert_matches_type(SpendListLogsResponse, spend, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_list_logs_with_all_params(self, async_client: AsyncHanzo) -> None:
        spend = await async_client.spend.list_logs(
            api_key="api_key",
            end_date="end_date",
            request_id="request_id",
            start_date="start_date",
            user_id="user_id",
        )
        assert_matches_type(SpendListLogsResponse, spend, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_list_logs(self, async_client: AsyncHanzo) -> None:
        response = await async_client.spend.with_raw_response.list_logs()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        spend = await response.parse()
        assert_matches_type(SpendListLogsResponse, spend, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_list_logs(self, async_client: AsyncHanzo) -> None:
        async with async_client.spend.with_streaming_response.list_logs() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            spend = await response.parse()
            assert_matches_type(SpendListLogsResponse, spend, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_list_tags(self, async_client: AsyncHanzo) -> None:
        spend = await async_client.spend.list_tags()
        assert_matches_type(SpendListTagsResponse, spend, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_list_tags_with_all_params(self, async_client: AsyncHanzo) -> None:
        spend = await async_client.spend.list_tags(
            end_date="end_date",
            start_date="start_date",
        )
        assert_matches_type(SpendListTagsResponse, spend, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_list_tags(self, async_client: AsyncHanzo) -> None:
        response = await async_client.spend.with_raw_response.list_tags()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        spend = await response.parse()
        assert_matches_type(SpendListTagsResponse, spend, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_list_tags(self, async_client: AsyncHanzo) -> None:
        async with async_client.spend.with_streaming_response.list_tags() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            spend = await response.parse()
            assert_matches_type(SpendListTagsResponse, spend, path=["response"])

        assert cast(Any, response.is_closed) is True
