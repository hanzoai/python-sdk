# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from Hanzo_AI import HanzoAI, AsyncHanzoAI
from tests.utils import assert_matches_type

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestGenerations:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    def test_method_create(self, client: HanzoAI) -> None:
        generation = client.images.generations.create()
        assert_matches_type(object, generation, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_create(self, client: HanzoAI) -> None:
        response = client.images.generations.with_raw_response.create()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        generation = response.parse()
        assert_matches_type(object, generation, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_create(self, client: HanzoAI) -> None:
        with client.images.generations.with_streaming_response.create() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            generation = response.parse()
            assert_matches_type(object, generation, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncGenerations:
    parametrize = pytest.mark.parametrize("async_client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_create(self, async_client: AsyncHanzoAI) -> None:
        generation = await async_client.images.generations.create()
        assert_matches_type(object, generation, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncHanzoAI) -> None:
        response = await async_client.images.generations.with_raw_response.create()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        generation = await response.parse()
        assert_matches_type(object, generation, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncHanzoAI) -> None:
        async with async_client.images.generations.with_streaming_response.create() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            generation = await response.parse()
            assert_matches_type(object, generation, path=["response"])

        assert cast(Any, response.is_closed) is True
