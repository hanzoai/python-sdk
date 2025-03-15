# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from hanzoai import Hanzo, AsyncHanzo
from tests.utils import assert_matches_type

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestRerank:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    def test_method_create(self, client: Hanzo) -> None:
        rerank = client.rerank.create()
        assert_matches_type(object, rerank, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_create(self, client: Hanzo) -> None:
        response = client.rerank.with_raw_response.create()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        rerank = response.parse()
        assert_matches_type(object, rerank, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_create(self, client: Hanzo) -> None:
        with client.rerank.with_streaming_response.create() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            rerank = response.parse()
            assert_matches_type(object, rerank, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_create_v1(self, client: Hanzo) -> None:
        rerank = client.rerank.create_v1()
        assert_matches_type(object, rerank, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_create_v1(self, client: Hanzo) -> None:
        response = client.rerank.with_raw_response.create_v1()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        rerank = response.parse()
        assert_matches_type(object, rerank, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_create_v1(self, client: Hanzo) -> None:
        with client.rerank.with_streaming_response.create_v1() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            rerank = response.parse()
            assert_matches_type(object, rerank, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_create_v2(self, client: Hanzo) -> None:
        rerank = client.rerank.create_v2()
        assert_matches_type(object, rerank, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_create_v2(self, client: Hanzo) -> None:
        response = client.rerank.with_raw_response.create_v2()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        rerank = response.parse()
        assert_matches_type(object, rerank, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_create_v2(self, client: Hanzo) -> None:
        with client.rerank.with_streaming_response.create_v2() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            rerank = response.parse()
            assert_matches_type(object, rerank, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncRerank:
    parametrize = pytest.mark.parametrize("async_client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_create(self, async_client: AsyncHanzo) -> None:
        rerank = await async_client.rerank.create()
        assert_matches_type(object, rerank, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncHanzo) -> None:
        response = await async_client.rerank.with_raw_response.create()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        rerank = await response.parse()
        assert_matches_type(object, rerank, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncHanzo) -> None:
        async with async_client.rerank.with_streaming_response.create() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            rerank = await response.parse()
            assert_matches_type(object, rerank, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_create_v1(self, async_client: AsyncHanzo) -> None:
        rerank = await async_client.rerank.create_v1()
        assert_matches_type(object, rerank, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_create_v1(self, async_client: AsyncHanzo) -> None:
        response = await async_client.rerank.with_raw_response.create_v1()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        rerank = await response.parse()
        assert_matches_type(object, rerank, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_create_v1(self, async_client: AsyncHanzo) -> None:
        async with async_client.rerank.with_streaming_response.create_v1() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            rerank = await response.parse()
            assert_matches_type(object, rerank, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_create_v2(self, async_client: AsyncHanzo) -> None:
        rerank = await async_client.rerank.create_v2()
        assert_matches_type(object, rerank, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_create_v2(self, async_client: AsyncHanzo) -> None:
        response = await async_client.rerank.with_raw_response.create_v2()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        rerank = await response.parse()
        assert_matches_type(object, rerank, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_create_v2(self, async_client: AsyncHanzo) -> None:
        async with async_client.rerank.with_streaming_response.create_v2() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            rerank = await response.parse()
            assert_matches_type(object, rerank, path=["response"])

        assert cast(Any, response.is_closed) is True
