# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from hanzoai import Hanzo, AsyncHanzo
from tests.utils import assert_matches_type

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestModelGroup:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    def test_method_retrieve_info(self, client: Hanzo) -> None:
        model_group = client.model_group.retrieve_info()
        assert_matches_type(object, model_group, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_retrieve_info_with_all_params(self, client: Hanzo) -> None:
        model_group = client.model_group.retrieve_info(
            model_group="model_group",
        )
        assert_matches_type(object, model_group, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_retrieve_info(self, client: Hanzo) -> None:
        response = client.model_group.with_raw_response.retrieve_info()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        model_group = response.parse()
        assert_matches_type(object, model_group, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_retrieve_info(self, client: Hanzo) -> None:
        with client.model_group.with_streaming_response.retrieve_info() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            model_group = response.parse()
            assert_matches_type(object, model_group, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncModelGroup:
    parametrize = pytest.mark.parametrize("async_client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_retrieve_info(self, async_client: AsyncHanzo) -> None:
        model_group = await async_client.model_group.retrieve_info()
        assert_matches_type(object, model_group, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_retrieve_info_with_all_params(self, async_client: AsyncHanzo) -> None:
        model_group = await async_client.model_group.retrieve_info(
            model_group="model_group",
        )
        assert_matches_type(object, model_group, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_retrieve_info(self, async_client: AsyncHanzo) -> None:
        response = await async_client.model_group.with_raw_response.retrieve_info()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        model_group = await response.parse()
        assert_matches_type(object, model_group, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_retrieve_info(self, async_client: AsyncHanzo) -> None:
        async with async_client.model_group.with_streaming_response.retrieve_info() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            model_group = await response.parse()
            assert_matches_type(object, model_group, path=["response"])

        assert cast(Any, response.is_closed) is True
