# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from hanzoai import Hanzo, AsyncHanzo
from tests.utils import assert_matches_type

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestBudget:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    def test_method_create(self, client: Hanzo) -> None:
        budget = client.budget.create()
        assert_matches_type(object, budget, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_create_with_all_params(self, client: Hanzo) -> None:
        budget = client.budget.create(
            budget_duration="budget_duration",
            budget_id="budget_id",
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
        assert_matches_type(object, budget, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_create(self, client: Hanzo) -> None:
        response = client.budget.with_raw_response.create()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        budget = response.parse()
        assert_matches_type(object, budget, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_create(self, client: Hanzo) -> None:
        with client.budget.with_streaming_response.create() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            budget = response.parse()
            assert_matches_type(object, budget, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_update(self, client: Hanzo) -> None:
        budget = client.budget.update()
        assert_matches_type(object, budget, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_update_with_all_params(self, client: Hanzo) -> None:
        budget = client.budget.update(
            budget_duration="budget_duration",
            budget_id="budget_id",
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
        assert_matches_type(object, budget, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_update(self, client: Hanzo) -> None:
        response = client.budget.with_raw_response.update()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        budget = response.parse()
        assert_matches_type(object, budget, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_update(self, client: Hanzo) -> None:
        with client.budget.with_streaming_response.update() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            budget = response.parse()
            assert_matches_type(object, budget, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_list(self, client: Hanzo) -> None:
        budget = client.budget.list()
        assert_matches_type(object, budget, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_list(self, client: Hanzo) -> None:
        response = client.budget.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        budget = response.parse()
        assert_matches_type(object, budget, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_list(self, client: Hanzo) -> None:
        with client.budget.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            budget = response.parse()
            assert_matches_type(object, budget, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_delete(self, client: Hanzo) -> None:
        budget = client.budget.delete(
            id="id",
        )
        assert_matches_type(object, budget, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_delete(self, client: Hanzo) -> None:
        response = client.budget.with_raw_response.delete(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        budget = response.parse()
        assert_matches_type(object, budget, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_delete(self, client: Hanzo) -> None:
        with client.budget.with_streaming_response.delete(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            budget = response.parse()
            assert_matches_type(object, budget, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_info(self, client: Hanzo) -> None:
        budget = client.budget.info(
            budgets=["string"],
        )
        assert_matches_type(object, budget, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_info(self, client: Hanzo) -> None:
        response = client.budget.with_raw_response.info(
            budgets=["string"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        budget = response.parse()
        assert_matches_type(object, budget, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_info(self, client: Hanzo) -> None:
        with client.budget.with_streaming_response.info(
            budgets=["string"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            budget = response.parse()
            assert_matches_type(object, budget, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_settings(self, client: Hanzo) -> None:
        budget = client.budget.settings(
            budget_id="budget_id",
        )
        assert_matches_type(object, budget, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_settings(self, client: Hanzo) -> None:
        response = client.budget.with_raw_response.settings(
            budget_id="budget_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        budget = response.parse()
        assert_matches_type(object, budget, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_settings(self, client: Hanzo) -> None:
        with client.budget.with_streaming_response.settings(
            budget_id="budget_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            budget = response.parse()
            assert_matches_type(object, budget, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncBudget:
    parametrize = pytest.mark.parametrize("async_client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_create(self, async_client: AsyncHanzo) -> None:
        budget = await async_client.budget.create()
        assert_matches_type(object, budget, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncHanzo) -> None:
        budget = await async_client.budget.create(
            budget_duration="budget_duration",
            budget_id="budget_id",
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
        assert_matches_type(object, budget, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncHanzo) -> None:
        response = await async_client.budget.with_raw_response.create()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        budget = await response.parse()
        assert_matches_type(object, budget, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncHanzo) -> None:
        async with async_client.budget.with_streaming_response.create() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            budget = await response.parse()
            assert_matches_type(object, budget, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_update(self, async_client: AsyncHanzo) -> None:
        budget = await async_client.budget.update()
        assert_matches_type(object, budget, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncHanzo) -> None:
        budget = await async_client.budget.update(
            budget_duration="budget_duration",
            budget_id="budget_id",
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
        assert_matches_type(object, budget, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_update(self, async_client: AsyncHanzo) -> None:
        response = await async_client.budget.with_raw_response.update()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        budget = await response.parse()
        assert_matches_type(object, budget, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncHanzo) -> None:
        async with async_client.budget.with_streaming_response.update() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            budget = await response.parse()
            assert_matches_type(object, budget, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_list(self, async_client: AsyncHanzo) -> None:
        budget = await async_client.budget.list()
        assert_matches_type(object, budget, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncHanzo) -> None:
        response = await async_client.budget.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        budget = await response.parse()
        assert_matches_type(object, budget, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncHanzo) -> None:
        async with async_client.budget.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            budget = await response.parse()
            assert_matches_type(object, budget, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_delete(self, async_client: AsyncHanzo) -> None:
        budget = await async_client.budget.delete(
            id="id",
        )
        assert_matches_type(object, budget, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncHanzo) -> None:
        response = await async_client.budget.with_raw_response.delete(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        budget = await response.parse()
        assert_matches_type(object, budget, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncHanzo) -> None:
        async with async_client.budget.with_streaming_response.delete(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            budget = await response.parse()
            assert_matches_type(object, budget, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_info(self, async_client: AsyncHanzo) -> None:
        budget = await async_client.budget.info(
            budgets=["string"],
        )
        assert_matches_type(object, budget, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_info(self, async_client: AsyncHanzo) -> None:
        response = await async_client.budget.with_raw_response.info(
            budgets=["string"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        budget = await response.parse()
        assert_matches_type(object, budget, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_info(self, async_client: AsyncHanzo) -> None:
        async with async_client.budget.with_streaming_response.info(
            budgets=["string"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            budget = await response.parse()
            assert_matches_type(object, budget, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_settings(self, async_client: AsyncHanzo) -> None:
        budget = await async_client.budget.settings(
            budget_id="budget_id",
        )
        assert_matches_type(object, budget, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_settings(self, async_client: AsyncHanzo) -> None:
        response = await async_client.budget.with_raw_response.settings(
            budget_id="budget_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        budget = await response.parse()
        assert_matches_type(object, budget, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_settings(self, async_client: AsyncHanzo) -> None:
        async with async_client.budget.with_streaming_response.settings(
            budget_id="budget_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            budget = await response.parse()
            assert_matches_type(object, budget, path=["response"])

        assert cast(Any, response.is_closed) is True
