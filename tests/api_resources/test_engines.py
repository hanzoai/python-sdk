# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from hanzoai import Hanzo, AsyncHanzo
from tests.utils import assert_matches_type

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestEngines:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    def test_method_complete(self, client: Hanzo) -> None:
        engine = client.engines.complete(
            "model",
        )
        assert_matches_type(object, engine, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_complete(self, client: Hanzo) -> None:
        response = client.engines.with_raw_response.complete(
            "model",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        engine = response.parse()
        assert_matches_type(object, engine, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_complete(self, client: Hanzo) -> None:
        with client.engines.with_streaming_response.complete(
            "model",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            engine = response.parse()
            assert_matches_type(object, engine, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_path_params_complete(self, client: Hanzo) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `model` but received ''"):
            client.engines.with_raw_response.complete(
                "",
            )

    @pytest.mark.skip()
    @parametrize
    def test_method_embed(self, client: Hanzo) -> None:
        engine = client.engines.embed(
            "model",
        )
        assert_matches_type(object, engine, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_embed(self, client: Hanzo) -> None:
        response = client.engines.with_raw_response.embed(
            "model",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        engine = response.parse()
        assert_matches_type(object, engine, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_embed(self, client: Hanzo) -> None:
        with client.engines.with_streaming_response.embed(
            "model",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            engine = response.parse()
            assert_matches_type(object, engine, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_path_params_embed(self, client: Hanzo) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `model` but received ''"):
            client.engines.with_raw_response.embed(
                "",
            )


class TestAsyncEngines:
    parametrize = pytest.mark.parametrize("async_client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_complete(self, async_client: AsyncHanzo) -> None:
        engine = await async_client.engines.complete(
            "model",
        )
        assert_matches_type(object, engine, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_complete(self, async_client: AsyncHanzo) -> None:
        response = await async_client.engines.with_raw_response.complete(
            "model",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        engine = await response.parse()
        assert_matches_type(object, engine, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_complete(self, async_client: AsyncHanzo) -> None:
        async with async_client.engines.with_streaming_response.complete(
            "model",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            engine = await response.parse()
            assert_matches_type(object, engine, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_path_params_complete(self, async_client: AsyncHanzo) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `model` but received ''"):
            await async_client.engines.with_raw_response.complete(
                "",
            )

    @pytest.mark.skip()
    @parametrize
    async def test_method_embed(self, async_client: AsyncHanzo) -> None:
        engine = await async_client.engines.embed(
            "model",
        )
        assert_matches_type(object, engine, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_embed(self, async_client: AsyncHanzo) -> None:
        response = await async_client.engines.with_raw_response.embed(
            "model",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        engine = await response.parse()
        assert_matches_type(object, engine, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_embed(self, async_client: AsyncHanzo) -> None:
        async with async_client.engines.with_streaming_response.embed(
            "model",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            engine = await response.parse()
            assert_matches_type(object, engine, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_path_params_embed(self, async_client: AsyncHanzo) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `model` but received ''"):
            await async_client.engines.with_raw_response.embed(
                "",
            )
