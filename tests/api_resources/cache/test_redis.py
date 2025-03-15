# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from hanzoai import Hanzo, AsyncHanzo
from tests.utils import assert_matches_type

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestRedis:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    def test_method_retrieve_info(self, client: Hanzo) -> None:
        redi = client.cache.redis.retrieve_info()
        assert_matches_type(object, redi, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_retrieve_info(self, client: Hanzo) -> None:
        response = client.cache.redis.with_raw_response.retrieve_info()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        redi = response.parse()
        assert_matches_type(object, redi, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_retrieve_info(self, client: Hanzo) -> None:
        with client.cache.redis.with_streaming_response.retrieve_info() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            redi = response.parse()
            assert_matches_type(object, redi, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncRedis:
    parametrize = pytest.mark.parametrize("async_client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_retrieve_info(self, async_client: AsyncHanzo) -> None:
        redi = await async_client.cache.redis.retrieve_info()
        assert_matches_type(object, redi, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_retrieve_info(self, async_client: AsyncHanzo) -> None:
        response = await async_client.cache.redis.with_raw_response.retrieve_info()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        redi = await response.parse()
        assert_matches_type(object, redi, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_retrieve_info(self, async_client: AsyncHanzo) -> None:
        async with async_client.cache.redis.with_streaming_response.retrieve_info() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            redi = await response.parse()
            assert_matches_type(object, redi, path=["response"])

        assert cast(Any, response.is_closed) is True
