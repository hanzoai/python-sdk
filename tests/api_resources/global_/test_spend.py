# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from Hanzo_AI import HanzoAI, AsyncHanzoAI
from tests.utils import assert_matches_type
from Hanzo_AI.types.global_ import (
    SpendListTagsResponse,
    SpendRetrieveReportResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestSpend:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    def test_method_list_tags(self, client: HanzoAI) -> None:
        spend = client.global_.spend.list_tags()
        assert_matches_type(SpendListTagsResponse, spend, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_list_tags_with_all_params(self, client: HanzoAI) -> None:
        spend = client.global_.spend.list_tags(
            end_date="end_date",
            start_date="start_date",
            tags="tags",
        )
        assert_matches_type(SpendListTagsResponse, spend, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_list_tags(self, client: HanzoAI) -> None:
        response = client.global_.spend.with_raw_response.list_tags()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        spend = response.parse()
        assert_matches_type(SpendListTagsResponse, spend, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_list_tags(self, client: HanzoAI) -> None:
        with client.global_.spend.with_streaming_response.list_tags() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            spend = response.parse()
            assert_matches_type(SpendListTagsResponse, spend, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_reset(self, client: HanzoAI) -> None:
        spend = client.global_.spend.reset()
        assert_matches_type(object, spend, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_reset(self, client: HanzoAI) -> None:
        response = client.global_.spend.with_raw_response.reset()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        spend = response.parse()
        assert_matches_type(object, spend, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_reset(self, client: HanzoAI) -> None:
        with client.global_.spend.with_streaming_response.reset() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            spend = response.parse()
            assert_matches_type(object, spend, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_retrieve_report(self, client: HanzoAI) -> None:
        spend = client.global_.spend.retrieve_report()
        assert_matches_type(SpendRetrieveReportResponse, spend, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_retrieve_report_with_all_params(self, client: HanzoAI) -> None:
        spend = client.global_.spend.retrieve_report(
            api_key="api_key",
            customer_id="customer_id",
            end_date="end_date",
            group_by="team",
            internal_user_id="internal_user_id",
            start_date="start_date",
            team_id="team_id",
        )
        assert_matches_type(SpendRetrieveReportResponse, spend, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_retrieve_report(self, client: HanzoAI) -> None:
        response = client.global_.spend.with_raw_response.retrieve_report()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        spend = response.parse()
        assert_matches_type(SpendRetrieveReportResponse, spend, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_retrieve_report(self, client: HanzoAI) -> None:
        with client.global_.spend.with_streaming_response.retrieve_report() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            spend = response.parse()
            assert_matches_type(SpendRetrieveReportResponse, spend, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncSpend:
    parametrize = pytest.mark.parametrize("async_client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_list_tags(self, async_client: AsyncHanzoAI) -> None:
        spend = await async_client.global_.spend.list_tags()
        assert_matches_type(SpendListTagsResponse, spend, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_list_tags_with_all_params(self, async_client: AsyncHanzoAI) -> None:
        spend = await async_client.global_.spend.list_tags(
            end_date="end_date",
            start_date="start_date",
            tags="tags",
        )
        assert_matches_type(SpendListTagsResponse, spend, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_list_tags(self, async_client: AsyncHanzoAI) -> None:
        response = await async_client.global_.spend.with_raw_response.list_tags()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        spend = await response.parse()
        assert_matches_type(SpendListTagsResponse, spend, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_list_tags(self, async_client: AsyncHanzoAI) -> None:
        async with async_client.global_.spend.with_streaming_response.list_tags() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            spend = await response.parse()
            assert_matches_type(SpendListTagsResponse, spend, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_reset(self, async_client: AsyncHanzoAI) -> None:
        spend = await async_client.global_.spend.reset()
        assert_matches_type(object, spend, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_reset(self, async_client: AsyncHanzoAI) -> None:
        response = await async_client.global_.spend.with_raw_response.reset()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        spend = await response.parse()
        assert_matches_type(object, spend, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_reset(self, async_client: AsyncHanzoAI) -> None:
        async with async_client.global_.spend.with_streaming_response.reset() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            spend = await response.parse()
            assert_matches_type(object, spend, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_retrieve_report(self, async_client: AsyncHanzoAI) -> None:
        spend = await async_client.global_.spend.retrieve_report()
        assert_matches_type(SpendRetrieveReportResponse, spend, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_retrieve_report_with_all_params(self, async_client: AsyncHanzoAI) -> None:
        spend = await async_client.global_.spend.retrieve_report(
            api_key="api_key",
            customer_id="customer_id",
            end_date="end_date",
            group_by="team",
            internal_user_id="internal_user_id",
            start_date="start_date",
            team_id="team_id",
        )
        assert_matches_type(SpendRetrieveReportResponse, spend, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_retrieve_report(self, async_client: AsyncHanzoAI) -> None:
        response = await async_client.global_.spend.with_raw_response.retrieve_report()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        spend = await response.parse()
        assert_matches_type(SpendRetrieveReportResponse, spend, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_retrieve_report(self, async_client: AsyncHanzoAI) -> None:
        async with async_client.global_.spend.with_streaming_response.retrieve_report() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            spend = await response.parse()
            assert_matches_type(SpendRetrieveReportResponse, spend, path=["response"])

        assert cast(Any, response.is_closed) is True
