# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from hanzoai import Hanzo, AsyncHanzo
from tests.utils import assert_matches_type

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestBatches:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    def test_method_create(self, client: Hanzo) -> None:
        batch = client.batches.create()
        assert_matches_type(object, batch, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_create_with_all_params(self, client: Hanzo) -> None:
        batch = client.batches.create(
            provider="provider",
        )
        assert_matches_type(object, batch, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_create(self, client: Hanzo) -> None:
        response = client.batches.with_raw_response.create()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        batch = response.parse()
        assert_matches_type(object, batch, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_create(self, client: Hanzo) -> None:
        with client.batches.with_streaming_response.create() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            batch = response.parse()
            assert_matches_type(object, batch, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_retrieve(self, client: Hanzo) -> None:
        batch = client.batches.retrieve(
            batch_id="batch_id",
        )
        assert_matches_type(object, batch, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_retrieve_with_all_params(self, client: Hanzo) -> None:
        batch = client.batches.retrieve(
            batch_id="batch_id",
            provider="provider",
        )
        assert_matches_type(object, batch, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_retrieve(self, client: Hanzo) -> None:
        response = client.batches.with_raw_response.retrieve(
            batch_id="batch_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        batch = response.parse()
        assert_matches_type(object, batch, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_retrieve(self, client: Hanzo) -> None:
        with client.batches.with_streaming_response.retrieve(
            batch_id="batch_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            batch = response.parse()
            assert_matches_type(object, batch, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_path_params_retrieve(self, client: Hanzo) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `batch_id` but received ''"):
            client.batches.with_raw_response.retrieve(
                batch_id="",
            )

    @pytest.mark.skip()
    @parametrize
    def test_method_list(self, client: Hanzo) -> None:
        batch = client.batches.list()
        assert_matches_type(object, batch, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_list_with_all_params(self, client: Hanzo) -> None:
        batch = client.batches.list(
            after="after",
            limit=0,
            provider="provider",
        )
        assert_matches_type(object, batch, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_list(self, client: Hanzo) -> None:
        response = client.batches.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        batch = response.parse()
        assert_matches_type(object, batch, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_list(self, client: Hanzo) -> None:
        with client.batches.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            batch = response.parse()
            assert_matches_type(object, batch, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_cancel_with_provider(self, client: Hanzo) -> None:
        batch = client.batches.cancel_with_provider(
            batch_id="batch_id",
            provider="provider",
        )
        assert_matches_type(object, batch, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_cancel_with_provider(self, client: Hanzo) -> None:
        response = client.batches.with_raw_response.cancel_with_provider(
            batch_id="batch_id",
            provider="provider",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        batch = response.parse()
        assert_matches_type(object, batch, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_cancel_with_provider(self, client: Hanzo) -> None:
        with client.batches.with_streaming_response.cancel_with_provider(
            batch_id="batch_id",
            provider="provider",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            batch = response.parse()
            assert_matches_type(object, batch, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_path_params_cancel_with_provider(self, client: Hanzo) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `provider` but received ''"):
            client.batches.with_raw_response.cancel_with_provider(
                batch_id="batch_id",
                provider="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `batch_id` but received ''"):
            client.batches.with_raw_response.cancel_with_provider(
                batch_id="",
                provider="provider",
            )

    @pytest.mark.skip()
    @parametrize
    def test_method_create_with_provider(self, client: Hanzo) -> None:
        batch = client.batches.create_with_provider(
            "provider",
        )
        assert_matches_type(object, batch, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_create_with_provider(self, client: Hanzo) -> None:
        response = client.batches.with_raw_response.create_with_provider(
            "provider",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        batch = response.parse()
        assert_matches_type(object, batch, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_create_with_provider(self, client: Hanzo) -> None:
        with client.batches.with_streaming_response.create_with_provider(
            "provider",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            batch = response.parse()
            assert_matches_type(object, batch, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_path_params_create_with_provider(self, client: Hanzo) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `provider` but received ''"):
            client.batches.with_raw_response.create_with_provider(
                "",
            )

    @pytest.mark.skip()
    @parametrize
    def test_method_list_with_provider(self, client: Hanzo) -> None:
        batch = client.batches.list_with_provider(
            provider="provider",
        )
        assert_matches_type(object, batch, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_list_with_provider_with_all_params(self, client: Hanzo) -> None:
        batch = client.batches.list_with_provider(
            provider="provider",
            after="after",
            limit=0,
        )
        assert_matches_type(object, batch, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_list_with_provider(self, client: Hanzo) -> None:
        response = client.batches.with_raw_response.list_with_provider(
            provider="provider",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        batch = response.parse()
        assert_matches_type(object, batch, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_list_with_provider(self, client: Hanzo) -> None:
        with client.batches.with_streaming_response.list_with_provider(
            provider="provider",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            batch = response.parse()
            assert_matches_type(object, batch, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_path_params_list_with_provider(self, client: Hanzo) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `provider` but received ''"):
            client.batches.with_raw_response.list_with_provider(
                provider="",
            )

    @pytest.mark.skip()
    @parametrize
    def test_method_retrieve_with_provider(self, client: Hanzo) -> None:
        batch = client.batches.retrieve_with_provider(
            batch_id="batch_id",
            provider="provider",
        )
        assert_matches_type(object, batch, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_retrieve_with_provider(self, client: Hanzo) -> None:
        response = client.batches.with_raw_response.retrieve_with_provider(
            batch_id="batch_id",
            provider="provider",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        batch = response.parse()
        assert_matches_type(object, batch, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_retrieve_with_provider(self, client: Hanzo) -> None:
        with client.batches.with_streaming_response.retrieve_with_provider(
            batch_id="batch_id",
            provider="provider",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            batch = response.parse()
            assert_matches_type(object, batch, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_path_params_retrieve_with_provider(self, client: Hanzo) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `provider` but received ''"):
            client.batches.with_raw_response.retrieve_with_provider(
                batch_id="batch_id",
                provider="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `batch_id` but received ''"):
            client.batches.with_raw_response.retrieve_with_provider(
                batch_id="",
                provider="provider",
            )


class TestAsyncBatches:
    parametrize = pytest.mark.parametrize("async_client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_create(self, async_client: AsyncHanzo) -> None:
        batch = await async_client.batches.create()
        assert_matches_type(object, batch, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncHanzo) -> None:
        batch = await async_client.batches.create(
            provider="provider",
        )
        assert_matches_type(object, batch, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncHanzo) -> None:
        response = await async_client.batches.with_raw_response.create()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        batch = await response.parse()
        assert_matches_type(object, batch, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncHanzo) -> None:
        async with async_client.batches.with_streaming_response.create() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            batch = await response.parse()
            assert_matches_type(object, batch, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncHanzo) -> None:
        batch = await async_client.batches.retrieve(
            batch_id="batch_id",
        )
        assert_matches_type(object, batch, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_retrieve_with_all_params(self, async_client: AsyncHanzo) -> None:
        batch = await async_client.batches.retrieve(
            batch_id="batch_id",
            provider="provider",
        )
        assert_matches_type(object, batch, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncHanzo) -> None:
        response = await async_client.batches.with_raw_response.retrieve(
            batch_id="batch_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        batch = await response.parse()
        assert_matches_type(object, batch, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncHanzo) -> None:
        async with async_client.batches.with_streaming_response.retrieve(
            batch_id="batch_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            batch = await response.parse()
            assert_matches_type(object, batch, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncHanzo) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `batch_id` but received ''"):
            await async_client.batches.with_raw_response.retrieve(
                batch_id="",
            )

    @pytest.mark.skip()
    @parametrize
    async def test_method_list(self, async_client: AsyncHanzo) -> None:
        batch = await async_client.batches.list()
        assert_matches_type(object, batch, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncHanzo) -> None:
        batch = await async_client.batches.list(
            after="after",
            limit=0,
            provider="provider",
        )
        assert_matches_type(object, batch, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncHanzo) -> None:
        response = await async_client.batches.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        batch = await response.parse()
        assert_matches_type(object, batch, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncHanzo) -> None:
        async with async_client.batches.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            batch = await response.parse()
            assert_matches_type(object, batch, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_cancel_with_provider(self, async_client: AsyncHanzo) -> None:
        batch = await async_client.batches.cancel_with_provider(
            batch_id="batch_id",
            provider="provider",
        )
        assert_matches_type(object, batch, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_cancel_with_provider(self, async_client: AsyncHanzo) -> None:
        response = await async_client.batches.with_raw_response.cancel_with_provider(
            batch_id="batch_id",
            provider="provider",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        batch = await response.parse()
        assert_matches_type(object, batch, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_cancel_with_provider(self, async_client: AsyncHanzo) -> None:
        async with async_client.batches.with_streaming_response.cancel_with_provider(
            batch_id="batch_id",
            provider="provider",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            batch = await response.parse()
            assert_matches_type(object, batch, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_path_params_cancel_with_provider(self, async_client: AsyncHanzo) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `provider` but received ''"):
            await async_client.batches.with_raw_response.cancel_with_provider(
                batch_id="batch_id",
                provider="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `batch_id` but received ''"):
            await async_client.batches.with_raw_response.cancel_with_provider(
                batch_id="",
                provider="provider",
            )

    @pytest.mark.skip()
    @parametrize
    async def test_method_create_with_provider(self, async_client: AsyncHanzo) -> None:
        batch = await async_client.batches.create_with_provider(
            "provider",
        )
        assert_matches_type(object, batch, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_create_with_provider(self, async_client: AsyncHanzo) -> None:
        response = await async_client.batches.with_raw_response.create_with_provider(
            "provider",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        batch = await response.parse()
        assert_matches_type(object, batch, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_create_with_provider(self, async_client: AsyncHanzo) -> None:
        async with async_client.batches.with_streaming_response.create_with_provider(
            "provider",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            batch = await response.parse()
            assert_matches_type(object, batch, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_path_params_create_with_provider(self, async_client: AsyncHanzo) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `provider` but received ''"):
            await async_client.batches.with_raw_response.create_with_provider(
                "",
            )

    @pytest.mark.skip()
    @parametrize
    async def test_method_list_with_provider(self, async_client: AsyncHanzo) -> None:
        batch = await async_client.batches.list_with_provider(
            provider="provider",
        )
        assert_matches_type(object, batch, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_list_with_provider_with_all_params(self, async_client: AsyncHanzo) -> None:
        batch = await async_client.batches.list_with_provider(
            provider="provider",
            after="after",
            limit=0,
        )
        assert_matches_type(object, batch, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_list_with_provider(self, async_client: AsyncHanzo) -> None:
        response = await async_client.batches.with_raw_response.list_with_provider(
            provider="provider",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        batch = await response.parse()
        assert_matches_type(object, batch, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_list_with_provider(self, async_client: AsyncHanzo) -> None:
        async with async_client.batches.with_streaming_response.list_with_provider(
            provider="provider",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            batch = await response.parse()
            assert_matches_type(object, batch, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_path_params_list_with_provider(self, async_client: AsyncHanzo) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `provider` but received ''"):
            await async_client.batches.with_raw_response.list_with_provider(
                provider="",
            )

    @pytest.mark.skip()
    @parametrize
    async def test_method_retrieve_with_provider(self, async_client: AsyncHanzo) -> None:
        batch = await async_client.batches.retrieve_with_provider(
            batch_id="batch_id",
            provider="provider",
        )
        assert_matches_type(object, batch, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_retrieve_with_provider(self, async_client: AsyncHanzo) -> None:
        response = await async_client.batches.with_raw_response.retrieve_with_provider(
            batch_id="batch_id",
            provider="provider",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        batch = await response.parse()
        assert_matches_type(object, batch, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_retrieve_with_provider(self, async_client: AsyncHanzo) -> None:
        async with async_client.batches.with_streaming_response.retrieve_with_provider(
            batch_id="batch_id",
            provider="provider",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            batch = await response.parse()
            assert_matches_type(object, batch, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_path_params_retrieve_with_provider(self, async_client: AsyncHanzo) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `provider` but received ''"):
            await async_client.batches.with_raw_response.retrieve_with_provider(
                batch_id="batch_id",
                provider="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `batch_id` but received ''"):
            await async_client.batches.with_raw_response.retrieve_with_provider(
                batch_id="",
                provider="provider",
            )
