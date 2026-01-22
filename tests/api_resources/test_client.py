# # Hanzo AI SDK Tests

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from hanzoai import Hanzo, AsyncHanzo
from tests.utils import assert_matches_type

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestClient:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_get_home(self, client: Hanzo) -> None:
        client_ = client.get_home()
        assert_matches_type(object, client_, path=["response"])

    @parametrize
    def test_raw_response_get_home(self, client: Hanzo) -> None:
        response = client.with_raw_response.get_home()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Hanzo-Lang") == "python"
        client_ = response.parse()
        assert_matches_type(object, client_, path=["response"])

    @parametrize
    def test_streaming_response_get_home(self, client: Hanzo) -> None:
        with client.with_streaming_response.get_home() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Hanzo-Lang") == "python"

            client_ = response.parse()
            assert_matches_type(object, client_, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncClient:
    parametrize = pytest.mark.parametrize("async_client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    async def test_method_get_home(self, async_client: AsyncHanzo) -> None:
        client = await async_client.get_home()
        assert_matches_type(object, client, path=["response"])

    @parametrize
    async def test_raw_response_get_home(self, async_client: AsyncHanzo) -> None:
        response = await async_client.with_raw_response.get_home()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Hanzo-Lang") == "python"
        client = await response.parse()
        assert_matches_type(object, client, path=["response"])

    @parametrize
    async def test_streaming_response_get_home(self, async_client: AsyncHanzo) -> None:
        async with async_client.with_streaming_response.get_home() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Hanzo-Lang") == "python"

            client = await response.parse()
            assert_matches_type(object, client, path=["response"])

        assert cast(Any, response.is_closed) is True
