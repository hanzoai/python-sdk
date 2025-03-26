# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from hanzoai import Hanzo, AsyncHanzo
from tests.utils import assert_matches_type
from hanzoai.types.organization import InfoRetrieveResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestInfo:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    def test_method_retrieve(self, client: Hanzo) -> None:
        info = client.organization.info.retrieve(
            organization_id="organization_id",
        )
        assert_matches_type(InfoRetrieveResponse, info, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_retrieve(self, client: Hanzo) -> None:
        response = client.organization.info.with_raw_response.retrieve(
            organization_id="organization_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        info = response.parse()
        assert_matches_type(InfoRetrieveResponse, info, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_retrieve(self, client: Hanzo) -> None:
        with client.organization.info.with_streaming_response.retrieve(
            organization_id="organization_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            info = response.parse()
            assert_matches_type(InfoRetrieveResponse, info, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_deprecated(self, client: Hanzo) -> None:
        info = client.organization.info.deprecated(
            organizations=["string"],
        )
        assert_matches_type(object, info, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_deprecated(self, client: Hanzo) -> None:
        response = client.organization.info.with_raw_response.deprecated(
            organizations=["string"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        info = response.parse()
        assert_matches_type(object, info, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_deprecated(self, client: Hanzo) -> None:
        with client.organization.info.with_streaming_response.deprecated(
            organizations=["string"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            info = response.parse()
            assert_matches_type(object, info, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncInfo:
    parametrize = pytest.mark.parametrize("async_client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncHanzo) -> None:
        info = await async_client.organization.info.retrieve(
            organization_id="organization_id",
        )
        assert_matches_type(InfoRetrieveResponse, info, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncHanzo) -> None:
        response = await async_client.organization.info.with_raw_response.retrieve(
            organization_id="organization_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        info = await response.parse()
        assert_matches_type(InfoRetrieveResponse, info, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncHanzo) -> None:
        async with async_client.organization.info.with_streaming_response.retrieve(
            organization_id="organization_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            info = await response.parse()
            assert_matches_type(InfoRetrieveResponse, info, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_deprecated(self, async_client: AsyncHanzo) -> None:
        info = await async_client.organization.info.deprecated(
            organizations=["string"],
        )
        assert_matches_type(object, info, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_deprecated(self, async_client: AsyncHanzo) -> None:
        response = await async_client.organization.info.with_raw_response.deprecated(
            organizations=["string"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        info = await response.parse()
        assert_matches_type(object, info, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_deprecated(self, async_client: AsyncHanzo) -> None:
        async with async_client.organization.info.with_streaming_response.deprecated(
            organizations=["string"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            info = await response.parse()
            assert_matches_type(object, info, path=["response"])

        assert cast(Any, response.is_closed) is True
