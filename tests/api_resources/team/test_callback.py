# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from hanzoai import Hanzo, AsyncHanzo
from tests.utils import assert_matches_type

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestCallback:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    def test_method_retrieve(self, client: Hanzo) -> None:
        callback = client.team.callback.retrieve(
            "team_id",
        )
        assert_matches_type(object, callback, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_retrieve(self, client: Hanzo) -> None:
        response = client.team.callback.with_raw_response.retrieve(
            "team_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        callback = response.parse()
        assert_matches_type(object, callback, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_retrieve(self, client: Hanzo) -> None:
        with client.team.callback.with_streaming_response.retrieve(
            "team_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            callback = response.parse()
            assert_matches_type(object, callback, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_path_params_retrieve(self, client: Hanzo) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `team_id` but received ''"):
            client.team.callback.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip()
    @parametrize
    def test_method_add(self, client: Hanzo) -> None:
        callback = client.team.callback.add(
            team_id="team_id",
            callback_name="callback_name",
            callback_vars={"foo": "string"},
        )
        assert_matches_type(object, callback, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_add_with_all_params(self, client: Hanzo) -> None:
        callback = client.team.callback.add(
            team_id="team_id",
            callback_name="callback_name",
            callback_vars={"foo": "string"},
            callback_type="success",
            llm_changed_by="llm-changed-by",
        )
        assert_matches_type(object, callback, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_add(self, client: Hanzo) -> None:
        response = client.team.callback.with_raw_response.add(
            team_id="team_id",
            callback_name="callback_name",
            callback_vars={"foo": "string"},
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        callback = response.parse()
        assert_matches_type(object, callback, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_add(self, client: Hanzo) -> None:
        with client.team.callback.with_streaming_response.add(
            team_id="team_id",
            callback_name="callback_name",
            callback_vars={"foo": "string"},
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            callback = response.parse()
            assert_matches_type(object, callback, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_path_params_add(self, client: Hanzo) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `team_id` but received ''"):
            client.team.callback.with_raw_response.add(
                team_id="",
                callback_name="callback_name",
                callback_vars={"foo": "string"},
            )


class TestAsyncCallback:
    parametrize = pytest.mark.parametrize("async_client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncHanzo) -> None:
        callback = await async_client.team.callback.retrieve(
            "team_id",
        )
        assert_matches_type(object, callback, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncHanzo) -> None:
        response = await async_client.team.callback.with_raw_response.retrieve(
            "team_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        callback = await response.parse()
        assert_matches_type(object, callback, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncHanzo) -> None:
        async with async_client.team.callback.with_streaming_response.retrieve(
            "team_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            callback = await response.parse()
            assert_matches_type(object, callback, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncHanzo) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `team_id` but received ''"):
            await async_client.team.callback.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip()
    @parametrize
    async def test_method_add(self, async_client: AsyncHanzo) -> None:
        callback = await async_client.team.callback.add(
            team_id="team_id",
            callback_name="callback_name",
            callback_vars={"foo": "string"},
        )
        assert_matches_type(object, callback, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_add_with_all_params(self, async_client: AsyncHanzo) -> None:
        callback = await async_client.team.callback.add(
            team_id="team_id",
            callback_name="callback_name",
            callback_vars={"foo": "string"},
            callback_type="success",
            llm_changed_by="llm-changed-by",
        )
        assert_matches_type(object, callback, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_add(self, async_client: AsyncHanzo) -> None:
        response = await async_client.team.callback.with_raw_response.add(
            team_id="team_id",
            callback_name="callback_name",
            callback_vars={"foo": "string"},
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        callback = await response.parse()
        assert_matches_type(object, callback, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_add(self, async_client: AsyncHanzo) -> None:
        async with async_client.team.callback.with_streaming_response.add(
            team_id="team_id",
            callback_name="callback_name",
            callback_vars={"foo": "string"},
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            callback = await response.parse()
            assert_matches_type(object, callback, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_path_params_add(self, async_client: AsyncHanzo) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `team_id` but received ''"):
            await async_client.team.callback.with_raw_response.add(
                team_id="",
                callback_name="callback_name",
                callback_vars={"foo": "string"},
            )
