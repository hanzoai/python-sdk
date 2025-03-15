# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from hanzoai import Hanzo, AsyncHanzo
from tests.utils import assert_matches_type

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestModel:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    def test_method_add(self, client: Hanzo) -> None:
        model = client.team.model.add(
            models=["string"],
            team_id="team_id",
        )
        assert_matches_type(object, model, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_add(self, client: Hanzo) -> None:
        response = client.team.model.with_raw_response.add(
            models=["string"],
            team_id="team_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        model = response.parse()
        assert_matches_type(object, model, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_add(self, client: Hanzo) -> None:
        with client.team.model.with_streaming_response.add(
            models=["string"],
            team_id="team_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            model = response.parse()
            assert_matches_type(object, model, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_remove(self, client: Hanzo) -> None:
        model = client.team.model.remove(
            models=["string"],
            team_id="team_id",
        )
        assert_matches_type(object, model, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_remove(self, client: Hanzo) -> None:
        response = client.team.model.with_raw_response.remove(
            models=["string"],
            team_id="team_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        model = response.parse()
        assert_matches_type(object, model, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_remove(self, client: Hanzo) -> None:
        with client.team.model.with_streaming_response.remove(
            models=["string"],
            team_id="team_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            model = response.parse()
            assert_matches_type(object, model, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncModel:
    parametrize = pytest.mark.parametrize("async_client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_add(self, async_client: AsyncHanzo) -> None:
        model = await async_client.team.model.add(
            models=["string"],
            team_id="team_id",
        )
        assert_matches_type(object, model, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_add(self, async_client: AsyncHanzo) -> None:
        response = await async_client.team.model.with_raw_response.add(
            models=["string"],
            team_id="team_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        model = await response.parse()
        assert_matches_type(object, model, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_add(self, async_client: AsyncHanzo) -> None:
        async with async_client.team.model.with_streaming_response.add(
            models=["string"],
            team_id="team_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            model = await response.parse()
            assert_matches_type(object, model, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_remove(self, async_client: AsyncHanzo) -> None:
        model = await async_client.team.model.remove(
            models=["string"],
            team_id="team_id",
        )
        assert_matches_type(object, model, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_remove(self, async_client: AsyncHanzo) -> None:
        response = await async_client.team.model.with_raw_response.remove(
            models=["string"],
            team_id="team_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        model = await response.parse()
        assert_matches_type(object, model, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_remove(self, async_client: AsyncHanzo) -> None:
        async with async_client.team.model.with_streaming_response.remove(
            models=["string"],
            team_id="team_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            model = await response.parse()
            assert_matches_type(object, model, path=["response"])

        assert cast(Any, response.is_closed) is True
