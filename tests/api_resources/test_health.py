# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from hanzoai import Hanzo, AsyncHanzo
from tests.utils import assert_matches_type

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestHealth:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    def test_method_check_all(self, client: Hanzo) -> None:
        health = client.health.check_all()
        assert_matches_type(object, health, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_check_all_with_all_params(self, client: Hanzo) -> None:
        health = client.health.check_all(
            model="model",
        )
        assert_matches_type(object, health, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_check_all(self, client: Hanzo) -> None:
        response = client.health.with_raw_response.check_all()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        health = response.parse()
        assert_matches_type(object, health, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_check_all(self, client: Hanzo) -> None:
        with client.health.with_streaming_response.check_all() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            health = response.parse()
            assert_matches_type(object, health, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_check_liveliness(self, client: Hanzo) -> None:
        health = client.health.check_liveliness()
        assert_matches_type(object, health, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_check_liveliness(self, client: Hanzo) -> None:
        response = client.health.with_raw_response.check_liveliness()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        health = response.parse()
        assert_matches_type(object, health, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_check_liveliness(self, client: Hanzo) -> None:
        with client.health.with_streaming_response.check_liveliness() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            health = response.parse()
            assert_matches_type(object, health, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_check_liveness(self, client: Hanzo) -> None:
        health = client.health.check_liveness()
        assert_matches_type(object, health, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_check_liveness(self, client: Hanzo) -> None:
        response = client.health.with_raw_response.check_liveness()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        health = response.parse()
        assert_matches_type(object, health, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_check_liveness(self, client: Hanzo) -> None:
        with client.health.with_streaming_response.check_liveness() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            health = response.parse()
            assert_matches_type(object, health, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_check_readiness(self, client: Hanzo) -> None:
        health = client.health.check_readiness()
        assert_matches_type(object, health, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_check_readiness(self, client: Hanzo) -> None:
        response = client.health.with_raw_response.check_readiness()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        health = response.parse()
        assert_matches_type(object, health, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_check_readiness(self, client: Hanzo) -> None:
        with client.health.with_streaming_response.check_readiness() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            health = response.parse()
            assert_matches_type(object, health, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_check_services(self, client: Hanzo) -> None:
        health = client.health.check_services(
            service="slack_budget_alerts",
        )
        assert_matches_type(object, health, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_check_services(self, client: Hanzo) -> None:
        response = client.health.with_raw_response.check_services(
            service="slack_budget_alerts",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        health = response.parse()
        assert_matches_type(object, health, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_check_services(self, client: Hanzo) -> None:
        with client.health.with_streaming_response.check_services(
            service="slack_budget_alerts",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            health = response.parse()
            assert_matches_type(object, health, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncHealth:
    parametrize = pytest.mark.parametrize("async_client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_check_all(self, async_client: AsyncHanzo) -> None:
        health = await async_client.health.check_all()
        assert_matches_type(object, health, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_check_all_with_all_params(self, async_client: AsyncHanzo) -> None:
        health = await async_client.health.check_all(
            model="model",
        )
        assert_matches_type(object, health, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_check_all(self, async_client: AsyncHanzo) -> None:
        response = await async_client.health.with_raw_response.check_all()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        health = await response.parse()
        assert_matches_type(object, health, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_check_all(self, async_client: AsyncHanzo) -> None:
        async with async_client.health.with_streaming_response.check_all() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            health = await response.parse()
            assert_matches_type(object, health, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_check_liveliness(self, async_client: AsyncHanzo) -> None:
        health = await async_client.health.check_liveliness()
        assert_matches_type(object, health, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_check_liveliness(self, async_client: AsyncHanzo) -> None:
        response = await async_client.health.with_raw_response.check_liveliness()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        health = await response.parse()
        assert_matches_type(object, health, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_check_liveliness(self, async_client: AsyncHanzo) -> None:
        async with async_client.health.with_streaming_response.check_liveliness() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            health = await response.parse()
            assert_matches_type(object, health, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_check_liveness(self, async_client: AsyncHanzo) -> None:
        health = await async_client.health.check_liveness()
        assert_matches_type(object, health, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_check_liveness(self, async_client: AsyncHanzo) -> None:
        response = await async_client.health.with_raw_response.check_liveness()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        health = await response.parse()
        assert_matches_type(object, health, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_check_liveness(self, async_client: AsyncHanzo) -> None:
        async with async_client.health.with_streaming_response.check_liveness() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            health = await response.parse()
            assert_matches_type(object, health, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_check_readiness(self, async_client: AsyncHanzo) -> None:
        health = await async_client.health.check_readiness()
        assert_matches_type(object, health, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_check_readiness(self, async_client: AsyncHanzo) -> None:
        response = await async_client.health.with_raw_response.check_readiness()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        health = await response.parse()
        assert_matches_type(object, health, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_check_readiness(self, async_client: AsyncHanzo) -> None:
        async with async_client.health.with_streaming_response.check_readiness() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            health = await response.parse()
            assert_matches_type(object, health, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_check_services(self, async_client: AsyncHanzo) -> None:
        health = await async_client.health.check_services(
            service="slack_budget_alerts",
        )
        assert_matches_type(object, health, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_check_services(self, async_client: AsyncHanzo) -> None:
        response = await async_client.health.with_raw_response.check_services(
            service="slack_budget_alerts",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        health = await response.parse()
        assert_matches_type(object, health, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_check_services(self, async_client: AsyncHanzo) -> None:
        async with async_client.health.with_streaming_response.check_services(
            service="slack_budget_alerts",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            health = await response.parse()
            assert_matches_type(object, health, path=["response"])

        assert cast(Any, response.is_closed) is True
