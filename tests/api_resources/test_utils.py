# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from hanzoai import Hanzo, AsyncHanzo
from tests.utils import assert_matches_type
from hanzoai.types import (
    UtilTokenCounterResponse,
    UtilTransformRequestResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestUtils:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    def test_method_get_supported_openai_params(self, client: Hanzo) -> None:
        util = client.utils.get_supported_openai_params(
            model="model",
        )
        assert_matches_type(object, util, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_get_supported_openai_params(self, client: Hanzo) -> None:
        response = client.utils.with_raw_response.get_supported_openai_params(
            model="model",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        util = response.parse()
        assert_matches_type(object, util, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_get_supported_openai_params(self, client: Hanzo) -> None:
        with client.utils.with_streaming_response.get_supported_openai_params(
            model="model",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            util = response.parse()
            assert_matches_type(object, util, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_token_counter(self, client: Hanzo) -> None:
        util = client.utils.token_counter(
            model="model",
        )
        assert_matches_type(UtilTokenCounterResponse, util, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_token_counter_with_all_params(self, client: Hanzo) -> None:
        util = client.utils.token_counter(
            model="model",
            messages=[{}],
            prompt="prompt",
        )
        assert_matches_type(UtilTokenCounterResponse, util, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_token_counter(self, client: Hanzo) -> None:
        response = client.utils.with_raw_response.token_counter(
            model="model",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        util = response.parse()
        assert_matches_type(UtilTokenCounterResponse, util, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_token_counter(self, client: Hanzo) -> None:
        with client.utils.with_streaming_response.token_counter(
            model="model",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            util = response.parse()
            assert_matches_type(UtilTokenCounterResponse, util, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_transform_request(self, client: Hanzo) -> None:
        util = client.utils.transform_request(
            call_type="embedding",
            request_body={},
        )
        assert_matches_type(UtilTransformRequestResponse, util, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_transform_request(self, client: Hanzo) -> None:
        response = client.utils.with_raw_response.transform_request(
            call_type="embedding",
            request_body={},
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        util = response.parse()
        assert_matches_type(UtilTransformRequestResponse, util, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_transform_request(self, client: Hanzo) -> None:
        with client.utils.with_streaming_response.transform_request(
            call_type="embedding",
            request_body={},
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            util = response.parse()
            assert_matches_type(UtilTransformRequestResponse, util, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncUtils:
    parametrize = pytest.mark.parametrize("async_client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_get_supported_openai_params(self, async_client: AsyncHanzo) -> None:
        util = await async_client.utils.get_supported_openai_params(
            model="model",
        )
        assert_matches_type(object, util, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_get_supported_openai_params(self, async_client: AsyncHanzo) -> None:
        response = await async_client.utils.with_raw_response.get_supported_openai_params(
            model="model",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        util = await response.parse()
        assert_matches_type(object, util, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_get_supported_openai_params(self, async_client: AsyncHanzo) -> None:
        async with async_client.utils.with_streaming_response.get_supported_openai_params(
            model="model",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            util = await response.parse()
            assert_matches_type(object, util, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_token_counter(self, async_client: AsyncHanzo) -> None:
        util = await async_client.utils.token_counter(
            model="model",
        )
        assert_matches_type(UtilTokenCounterResponse, util, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_token_counter_with_all_params(self, async_client: AsyncHanzo) -> None:
        util = await async_client.utils.token_counter(
            model="model",
            messages=[{}],
            prompt="prompt",
        )
        assert_matches_type(UtilTokenCounterResponse, util, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_token_counter(self, async_client: AsyncHanzo) -> None:
        response = await async_client.utils.with_raw_response.token_counter(
            model="model",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        util = await response.parse()
        assert_matches_type(UtilTokenCounterResponse, util, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_token_counter(self, async_client: AsyncHanzo) -> None:
        async with async_client.utils.with_streaming_response.token_counter(
            model="model",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            util = await response.parse()
            assert_matches_type(UtilTokenCounterResponse, util, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_transform_request(self, async_client: AsyncHanzo) -> None:
        util = await async_client.utils.transform_request(
            call_type="embedding",
            request_body={},
        )
        assert_matches_type(UtilTransformRequestResponse, util, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_transform_request(self, async_client: AsyncHanzo) -> None:
        response = await async_client.utils.with_raw_response.transform_request(
            call_type="embedding",
            request_body={},
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        util = await response.parse()
        assert_matches_type(UtilTransformRequestResponse, util, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_transform_request(self, async_client: AsyncHanzo) -> None:
        async with async_client.utils.with_streaming_response.transform_request(
            call_type="embedding",
            request_body={},
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            util = await response.parse()
            assert_matches_type(UtilTransformRequestResponse, util, path=["response"])

        assert cast(Any, response.is_closed) is True
