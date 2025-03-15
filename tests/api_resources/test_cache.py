# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from hanzoai import Hanzo, AsyncHanzo
from tests.utils import assert_matches_type
from hanzoai.types import CachePingResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestCache:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    def test_method_delete(self, client: Hanzo) -> None:
        cache = client.cache.delete()
        assert_matches_type(object, cache, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_delete(self, client: Hanzo) -> None:
        response = client.cache.with_raw_response.delete()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        cache = response.parse()
        assert_matches_type(object, cache, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_delete(self, client: Hanzo) -> None:
        with client.cache.with_streaming_response.delete() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            cache = response.parse()
            assert_matches_type(object, cache, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_flush_all(self, client: Hanzo) -> None:
        cache = client.cache.flush_all()
        assert_matches_type(object, cache, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_flush_all(self, client: Hanzo) -> None:
        response = client.cache.with_raw_response.flush_all()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        cache = response.parse()
        assert_matches_type(object, cache, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_flush_all(self, client: Hanzo) -> None:
        with client.cache.with_streaming_response.flush_all() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            cache = response.parse()
            assert_matches_type(object, cache, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_ping(self, client: Hanzo) -> None:
        cache = client.cache.ping()
        assert_matches_type(CachePingResponse, cache, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_ping(self, client: Hanzo) -> None:
        response = client.cache.with_raw_response.ping()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        cache = response.parse()
        assert_matches_type(CachePingResponse, cache, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_ping(self, client: Hanzo) -> None:
        with client.cache.with_streaming_response.ping() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            cache = response.parse()
            assert_matches_type(CachePingResponse, cache, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncCache:
    parametrize = pytest.mark.parametrize("async_client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_delete(self, async_client: AsyncHanzo) -> None:
        cache = await async_client.cache.delete()
        assert_matches_type(object, cache, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncHanzo) -> None:
        response = await async_client.cache.with_raw_response.delete()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        cache = await response.parse()
        assert_matches_type(object, cache, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncHanzo) -> None:
        async with async_client.cache.with_streaming_response.delete() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            cache = await response.parse()
            assert_matches_type(object, cache, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_flush_all(self, async_client: AsyncHanzo) -> None:
        cache = await async_client.cache.flush_all()
        assert_matches_type(object, cache, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_flush_all(self, async_client: AsyncHanzo) -> None:
        response = await async_client.cache.with_raw_response.flush_all()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        cache = await response.parse()
        assert_matches_type(object, cache, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_flush_all(self, async_client: AsyncHanzo) -> None:
        async with async_client.cache.with_streaming_response.flush_all() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            cache = await response.parse()
            assert_matches_type(object, cache, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_ping(self, async_client: AsyncHanzo) -> None:
        cache = await async_client.cache.ping()
        assert_matches_type(CachePingResponse, cache, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_ping(self, async_client: AsyncHanzo) -> None:
        response = await async_client.cache.with_raw_response.ping()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        cache = await response.parse()
        assert_matches_type(CachePingResponse, cache, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_ping(self, async_client: AsyncHanzo) -> None:
        async with async_client.cache.with_streaming_response.ping() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            cache = await response.parse()
            assert_matches_type(CachePingResponse, cache, path=["response"])

        assert cast(Any, response.is_closed) is True
