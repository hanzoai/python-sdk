# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from hanzoai import Hanzo, AsyncHanzo
from tests.utils import assert_matches_type

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestActive:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    def test_method_list_callbacks(self, client: Hanzo) -> None:
        active = client.active.list_callbacks()
        assert_matches_type(object, active, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_list_callbacks(self, client: Hanzo) -> None:
        response = client.active.with_raw_response.list_callbacks()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        active = response.parse()
        assert_matches_type(object, active, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_list_callbacks(self, client: Hanzo) -> None:
        with client.active.with_streaming_response.list_callbacks() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            active = response.parse()
            assert_matches_type(object, active, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncActive:
    parametrize = pytest.mark.parametrize("async_client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_list_callbacks(self, async_client: AsyncHanzo) -> None:
        active = await async_client.active.list_callbacks()
        assert_matches_type(object, active, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_list_callbacks(self, async_client: AsyncHanzo) -> None:
        response = await async_client.active.with_raw_response.list_callbacks()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        active = await response.parse()
        assert_matches_type(object, active, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_list_callbacks(self, async_client: AsyncHanzo) -> None:
        async with async_client.active.with_streaming_response.list_callbacks() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            active = await response.parse()
            assert_matches_type(object, active, path=["response"])

        assert cast(Any, response.is_closed) is True
