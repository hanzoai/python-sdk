# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from hanzoai import Hanzo, AsyncHanzo
from tests.utils import assert_matches_type

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestCancel:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    def test_method_cancel(self, client: Hanzo) -> None:
        cancel = client.batches.cancel.cancel(
            batch_id="batch_id",
        )
        assert_matches_type(object, cancel, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_cancel_with_all_params(self, client: Hanzo) -> None:
        cancel = client.batches.cancel.cancel(
            batch_id="batch_id",
            provider="provider",
        )
        assert_matches_type(object, cancel, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_cancel(self, client: Hanzo) -> None:
        response = client.batches.cancel.with_raw_response.cancel(
            batch_id="batch_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        cancel = response.parse()
        assert_matches_type(object, cancel, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_cancel(self, client: Hanzo) -> None:
        with client.batches.cancel.with_streaming_response.cancel(
            batch_id="batch_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            cancel = response.parse()
            assert_matches_type(object, cancel, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_path_params_cancel(self, client: Hanzo) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `batch_id` but received ''"):
            client.batches.cancel.with_raw_response.cancel(
                batch_id="",
            )


class TestAsyncCancel:
    parametrize = pytest.mark.parametrize("async_client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_cancel(self, async_client: AsyncHanzo) -> None:
        cancel = await async_client.batches.cancel.cancel(
            batch_id="batch_id",
        )
        assert_matches_type(object, cancel, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_cancel_with_all_params(self, async_client: AsyncHanzo) -> None:
        cancel = await async_client.batches.cancel.cancel(
            batch_id="batch_id",
            provider="provider",
        )
        assert_matches_type(object, cancel, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_cancel(self, async_client: AsyncHanzo) -> None:
        response = await async_client.batches.cancel.with_raw_response.cancel(
            batch_id="batch_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        cancel = await response.parse()
        assert_matches_type(object, cancel, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_cancel(self, async_client: AsyncHanzo) -> None:
        async with async_client.batches.cancel.with_streaming_response.cancel(
            batch_id="batch_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            cancel = await response.parse()
            assert_matches_type(object, cancel, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_path_params_cancel(self, async_client: AsyncHanzo) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `batch_id` but received ''"):
            await async_client.batches.cancel.with_raw_response.cancel(
                batch_id="",
            )
