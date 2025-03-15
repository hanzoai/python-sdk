# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from Hanzo_AI import HanzoAI, AsyncHanzoAI
from tests.utils import assert_matches_type

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestEmbeddings:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    def test_method_create(self, client: HanzoAI) -> None:
        embedding = client.embeddings.create()
        assert_matches_type(object, embedding, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_create_with_all_params(self, client: HanzoAI) -> None:
        embedding = client.embeddings.create(
            model="model",
        )
        assert_matches_type(object, embedding, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_create(self, client: HanzoAI) -> None:
        response = client.embeddings.with_raw_response.create()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        embedding = response.parse()
        assert_matches_type(object, embedding, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_create(self, client: HanzoAI) -> None:
        with client.embeddings.with_streaming_response.create() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            embedding = response.parse()
            assert_matches_type(object, embedding, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncEmbeddings:
    parametrize = pytest.mark.parametrize("async_client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_create(self, async_client: AsyncHanzoAI) -> None:
        embedding = await async_client.embeddings.create()
        assert_matches_type(object, embedding, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncHanzoAI) -> None:
        embedding = await async_client.embeddings.create(
            model="model",
        )
        assert_matches_type(object, embedding, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncHanzoAI) -> None:
        response = await async_client.embeddings.with_raw_response.create()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        embedding = await response.parse()
        assert_matches_type(object, embedding, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncHanzoAI) -> None:
        async with async_client.embeddings.with_streaming_response.create() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            embedding = await response.parse()
            assert_matches_type(object, embedding, path=["response"])

        assert cast(Any, response.is_closed) is True
