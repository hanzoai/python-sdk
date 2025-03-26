# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from hanzoai import Hanzo, AsyncHanzo
from tests.utils import assert_matches_type
from hanzoai.types import (
    CustomerListResponse,
    CustomerRetrieveInfoResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestCustomer:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    def test_method_create(self, client: Hanzo) -> None:
        customer = client.customer.create(
            user_id="user_id",
        )
        assert_matches_type(object, customer, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_create_with_all_params(self, client: Hanzo) -> None:
        customer = client.customer.create(
            user_id="user_id",
            alias="alias",
            allowed_model_region="eu",
            blocked=True,
            budget_duration="budget_duration",
            budget_id="budget_id",
            default_model="default_model",
            max_budget=0,
            max_parallel_requests=0,
            model_max_budget={
                "foo": {
                    "budget_duration": "budget_duration",
                    "max_budget": 0,
                    "rpm_limit": 0,
                    "tpm_limit": 0,
                }
            },
            rpm_limit=0,
            soft_budget=0,
            tpm_limit=0,
        )
        assert_matches_type(object, customer, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_create(self, client: Hanzo) -> None:
        response = client.customer.with_raw_response.create(
            user_id="user_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        customer = response.parse()
        assert_matches_type(object, customer, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_create(self, client: Hanzo) -> None:
        with client.customer.with_streaming_response.create(
            user_id="user_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            customer = response.parse()
            assert_matches_type(object, customer, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_update(self, client: Hanzo) -> None:
        customer = client.customer.update(
            user_id="user_id",
        )
        assert_matches_type(object, customer, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_update_with_all_params(self, client: Hanzo) -> None:
        customer = client.customer.update(
            user_id="user_id",
            alias="alias",
            allowed_model_region="eu",
            blocked=True,
            budget_id="budget_id",
            default_model="default_model",
            max_budget=0,
        )
        assert_matches_type(object, customer, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_update(self, client: Hanzo) -> None:
        response = client.customer.with_raw_response.update(
            user_id="user_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        customer = response.parse()
        assert_matches_type(object, customer, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_update(self, client: Hanzo) -> None:
        with client.customer.with_streaming_response.update(
            user_id="user_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            customer = response.parse()
            assert_matches_type(object, customer, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_list(self, client: Hanzo) -> None:
        customer = client.customer.list()
        assert_matches_type(CustomerListResponse, customer, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_list(self, client: Hanzo) -> None:
        response = client.customer.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        customer = response.parse()
        assert_matches_type(CustomerListResponse, customer, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_list(self, client: Hanzo) -> None:
        with client.customer.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            customer = response.parse()
            assert_matches_type(CustomerListResponse, customer, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_delete(self, client: Hanzo) -> None:
        customer = client.customer.delete(
            user_ids=["string"],
        )
        assert_matches_type(object, customer, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_delete(self, client: Hanzo) -> None:
        response = client.customer.with_raw_response.delete(
            user_ids=["string"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        customer = response.parse()
        assert_matches_type(object, customer, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_delete(self, client: Hanzo) -> None:
        with client.customer.with_streaming_response.delete(
            user_ids=["string"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            customer = response.parse()
            assert_matches_type(object, customer, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_block(self, client: Hanzo) -> None:
        customer = client.customer.block(
            user_ids=["string"],
        )
        assert_matches_type(object, customer, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_block(self, client: Hanzo) -> None:
        response = client.customer.with_raw_response.block(
            user_ids=["string"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        customer = response.parse()
        assert_matches_type(object, customer, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_block(self, client: Hanzo) -> None:
        with client.customer.with_streaming_response.block(
            user_ids=["string"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            customer = response.parse()
            assert_matches_type(object, customer, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_retrieve_info(self, client: Hanzo) -> None:
        customer = client.customer.retrieve_info(
            end_user_id="end_user_id",
        )
        assert_matches_type(CustomerRetrieveInfoResponse, customer, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_retrieve_info(self, client: Hanzo) -> None:
        response = client.customer.with_raw_response.retrieve_info(
            end_user_id="end_user_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        customer = response.parse()
        assert_matches_type(CustomerRetrieveInfoResponse, customer, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_retrieve_info(self, client: Hanzo) -> None:
        with client.customer.with_streaming_response.retrieve_info(
            end_user_id="end_user_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            customer = response.parse()
            assert_matches_type(CustomerRetrieveInfoResponse, customer, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_unblock(self, client: Hanzo) -> None:
        customer = client.customer.unblock(
            user_ids=["string"],
        )
        assert_matches_type(object, customer, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_unblock(self, client: Hanzo) -> None:
        response = client.customer.with_raw_response.unblock(
            user_ids=["string"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        customer = response.parse()
        assert_matches_type(object, customer, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_unblock(self, client: Hanzo) -> None:
        with client.customer.with_streaming_response.unblock(
            user_ids=["string"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            customer = response.parse()
            assert_matches_type(object, customer, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncCustomer:
    parametrize = pytest.mark.parametrize("async_client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_create(self, async_client: AsyncHanzo) -> None:
        customer = await async_client.customer.create(
            user_id="user_id",
        )
        assert_matches_type(object, customer, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncHanzo) -> None:
        customer = await async_client.customer.create(
            user_id="user_id",
            alias="alias",
            allowed_model_region="eu",
            blocked=True,
            budget_duration="budget_duration",
            budget_id="budget_id",
            default_model="default_model",
            max_budget=0,
            max_parallel_requests=0,
            model_max_budget={
                "foo": {
                    "budget_duration": "budget_duration",
                    "max_budget": 0,
                    "rpm_limit": 0,
                    "tpm_limit": 0,
                }
            },
            rpm_limit=0,
            soft_budget=0,
            tpm_limit=0,
        )
        assert_matches_type(object, customer, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncHanzo) -> None:
        response = await async_client.customer.with_raw_response.create(
            user_id="user_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        customer = await response.parse()
        assert_matches_type(object, customer, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncHanzo) -> None:
        async with async_client.customer.with_streaming_response.create(
            user_id="user_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            customer = await response.parse()
            assert_matches_type(object, customer, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_update(self, async_client: AsyncHanzo) -> None:
        customer = await async_client.customer.update(
            user_id="user_id",
        )
        assert_matches_type(object, customer, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncHanzo) -> None:
        customer = await async_client.customer.update(
            user_id="user_id",
            alias="alias",
            allowed_model_region="eu",
            blocked=True,
            budget_id="budget_id",
            default_model="default_model",
            max_budget=0,
        )
        assert_matches_type(object, customer, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_update(self, async_client: AsyncHanzo) -> None:
        response = await async_client.customer.with_raw_response.update(
            user_id="user_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        customer = await response.parse()
        assert_matches_type(object, customer, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncHanzo) -> None:
        async with async_client.customer.with_streaming_response.update(
            user_id="user_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            customer = await response.parse()
            assert_matches_type(object, customer, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_list(self, async_client: AsyncHanzo) -> None:
        customer = await async_client.customer.list()
        assert_matches_type(CustomerListResponse, customer, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncHanzo) -> None:
        response = await async_client.customer.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        customer = await response.parse()
        assert_matches_type(CustomerListResponse, customer, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncHanzo) -> None:
        async with async_client.customer.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            customer = await response.parse()
            assert_matches_type(CustomerListResponse, customer, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_delete(self, async_client: AsyncHanzo) -> None:
        customer = await async_client.customer.delete(
            user_ids=["string"],
        )
        assert_matches_type(object, customer, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncHanzo) -> None:
        response = await async_client.customer.with_raw_response.delete(
            user_ids=["string"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        customer = await response.parse()
        assert_matches_type(object, customer, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncHanzo) -> None:
        async with async_client.customer.with_streaming_response.delete(
            user_ids=["string"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            customer = await response.parse()
            assert_matches_type(object, customer, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_block(self, async_client: AsyncHanzo) -> None:
        customer = await async_client.customer.block(
            user_ids=["string"],
        )
        assert_matches_type(object, customer, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_block(self, async_client: AsyncHanzo) -> None:
        response = await async_client.customer.with_raw_response.block(
            user_ids=["string"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        customer = await response.parse()
        assert_matches_type(object, customer, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_block(self, async_client: AsyncHanzo) -> None:
        async with async_client.customer.with_streaming_response.block(
            user_ids=["string"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            customer = await response.parse()
            assert_matches_type(object, customer, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_retrieve_info(self, async_client: AsyncHanzo) -> None:
        customer = await async_client.customer.retrieve_info(
            end_user_id="end_user_id",
        )
        assert_matches_type(CustomerRetrieveInfoResponse, customer, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_retrieve_info(self, async_client: AsyncHanzo) -> None:
        response = await async_client.customer.with_raw_response.retrieve_info(
            end_user_id="end_user_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        customer = await response.parse()
        assert_matches_type(CustomerRetrieveInfoResponse, customer, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_retrieve_info(self, async_client: AsyncHanzo) -> None:
        async with async_client.customer.with_streaming_response.retrieve_info(
            end_user_id="end_user_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            customer = await response.parse()
            assert_matches_type(CustomerRetrieveInfoResponse, customer, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_unblock(self, async_client: AsyncHanzo) -> None:
        customer = await async_client.customer.unblock(
            user_ids=["string"],
        )
        assert_matches_type(object, customer, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_unblock(self, async_client: AsyncHanzo) -> None:
        response = await async_client.customer.with_raw_response.unblock(
            user_ids=["string"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        customer = await response.parse()
        assert_matches_type(object, customer, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_unblock(self, async_client: AsyncHanzo) -> None:
        async with async_client.customer.with_streaming_response.unblock(
            user_ids=["string"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            customer = await response.parse()
            assert_matches_type(object, customer, path=["response"])

        assert cast(Any, response.is_closed) is True
