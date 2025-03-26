# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from hanzoai import Hanzo, AsyncHanzo
from tests.utils import assert_matches_type
from hanzoai.types import (
    UserCreateResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestUser:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    def test_method_create(self, client: Hanzo) -> None:
        user = client.user.create()
        assert_matches_type(UserCreateResponse, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_create_with_all_params(self, client: Hanzo) -> None:
        user = client.user.create(
            aliases={},
            allowed_cache_controls=[{}],
            auto_create_key=True,
            blocked=True,
            budget_duration="budget_duration",
            config={},
            duration="duration",
            guardrails=["string"],
            key_alias="key_alias",
            max_budget=0,
            max_parallel_requests=0,
            metadata={},
            model_max_budget={},
            model_rpm_limit={},
            model_tpm_limit={},
            models=[{}],
            permissions={},
            rpm_limit=0,
            send_invite_email=True,
            spend=0,
            team_id="team_id",
            teams=[{}],
            tpm_limit=0,
            user_alias="user_alias",
            user_email="user_email",
            user_id="user_id",
            user_role="proxy_admin",
        )
        assert_matches_type(UserCreateResponse, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_create(self, client: Hanzo) -> None:
        response = client.user.with_raw_response.create()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        user = response.parse()
        assert_matches_type(UserCreateResponse, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_create(self, client: Hanzo) -> None:
        with client.user.with_streaming_response.create() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            user = response.parse()
            assert_matches_type(UserCreateResponse, user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_update(self, client: Hanzo) -> None:
        user = client.user.update()
        assert_matches_type(object, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_update_with_all_params(self, client: Hanzo) -> None:
        user = client.user.update(
            aliases={},
            allowed_cache_controls=[{}],
            blocked=True,
            budget_duration="budget_duration",
            config={},
            duration="duration",
            guardrails=["string"],
            key_alias="key_alias",
            max_budget=0,
            max_parallel_requests=0,
            metadata={},
            model_max_budget={},
            model_rpm_limit={},
            model_tpm_limit={},
            models=[{}],
            password="password",
            permissions={},
            rpm_limit=0,
            spend=0,
            team_id="team_id",
            tpm_limit=0,
            user_email="user_email",
            user_id="user_id",
            user_role="proxy_admin",
        )
        assert_matches_type(object, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_update(self, client: Hanzo) -> None:
        response = client.user.with_raw_response.update()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        user = response.parse()
        assert_matches_type(object, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_update(self, client: Hanzo) -> None:
        with client.user.with_streaming_response.update() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            user = response.parse()
            assert_matches_type(object, user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_list(self, client: Hanzo) -> None:
        user = client.user.list()
        assert_matches_type(object, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_list_with_all_params(self, client: Hanzo) -> None:
        user = client.user.list(
            page=1,
            page_size=1,
            role="role",
            user_ids="user_ids",
        )
        assert_matches_type(object, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_list(self, client: Hanzo) -> None:
        response = client.user.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        user = response.parse()
        assert_matches_type(object, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_list(self, client: Hanzo) -> None:
        with client.user.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            user = response.parse()
            assert_matches_type(object, user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_delete(self, client: Hanzo) -> None:
        user = client.user.delete(
            user_ids=["string"],
        )
        assert_matches_type(object, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_delete_with_all_params(self, client: Hanzo) -> None:
        user = client.user.delete(
            user_ids=["string"],
            llm_changed_by="llm-changed-by",
        )
        assert_matches_type(object, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_delete(self, client: Hanzo) -> None:
        response = client.user.with_raw_response.delete(
            user_ids=["string"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        user = response.parse()
        assert_matches_type(object, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_delete(self, client: Hanzo) -> None:
        with client.user.with_streaming_response.delete(
            user_ids=["string"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            user = response.parse()
            assert_matches_type(object, user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_retrieve_info(self, client: Hanzo) -> None:
        user = client.user.retrieve_info()
        assert_matches_type(object, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_retrieve_info_with_all_params(self, client: Hanzo) -> None:
        user = client.user.retrieve_info(
            user_id="user_id",
        )
        assert_matches_type(object, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_retrieve_info(self, client: Hanzo) -> None:
        response = client.user.with_raw_response.retrieve_info()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        user = response.parse()
        assert_matches_type(object, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_retrieve_info(self, client: Hanzo) -> None:
        with client.user.with_streaming_response.retrieve_info() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            user = response.parse()
            assert_matches_type(object, user, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncUser:
    parametrize = pytest.mark.parametrize("async_client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_create(self, async_client: AsyncHanzo) -> None:
        user = await async_client.user.create()
        assert_matches_type(UserCreateResponse, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncHanzo) -> None:
        user = await async_client.user.create(
            aliases={},
            allowed_cache_controls=[{}],
            auto_create_key=True,
            blocked=True,
            budget_duration="budget_duration",
            config={},
            duration="duration",
            guardrails=["string"],
            key_alias="key_alias",
            max_budget=0,
            max_parallel_requests=0,
            metadata={},
            model_max_budget={},
            model_rpm_limit={},
            model_tpm_limit={},
            models=[{}],
            permissions={},
            rpm_limit=0,
            send_invite_email=True,
            spend=0,
            team_id="team_id",
            teams=[{}],
            tpm_limit=0,
            user_alias="user_alias",
            user_email="user_email",
            user_id="user_id",
            user_role="proxy_admin",
        )
        assert_matches_type(UserCreateResponse, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncHanzo) -> None:
        response = await async_client.user.with_raw_response.create()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        user = await response.parse()
        assert_matches_type(UserCreateResponse, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncHanzo) -> None:
        async with async_client.user.with_streaming_response.create() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            user = await response.parse()
            assert_matches_type(UserCreateResponse, user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_update(self, async_client: AsyncHanzo) -> None:
        user = await async_client.user.update()
        assert_matches_type(object, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncHanzo) -> None:
        user = await async_client.user.update(
            aliases={},
            allowed_cache_controls=[{}],
            blocked=True,
            budget_duration="budget_duration",
            config={},
            duration="duration",
            guardrails=["string"],
            key_alias="key_alias",
            max_budget=0,
            max_parallel_requests=0,
            metadata={},
            model_max_budget={},
            model_rpm_limit={},
            model_tpm_limit={},
            models=[{}],
            password="password",
            permissions={},
            rpm_limit=0,
            spend=0,
            team_id="team_id",
            tpm_limit=0,
            user_email="user_email",
            user_id="user_id",
            user_role="proxy_admin",
        )
        assert_matches_type(object, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_update(self, async_client: AsyncHanzo) -> None:
        response = await async_client.user.with_raw_response.update()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        user = await response.parse()
        assert_matches_type(object, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncHanzo) -> None:
        async with async_client.user.with_streaming_response.update() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            user = await response.parse()
            assert_matches_type(object, user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_list(self, async_client: AsyncHanzo) -> None:
        user = await async_client.user.list()
        assert_matches_type(object, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncHanzo) -> None:
        user = await async_client.user.list(
            page=1,
            page_size=1,
            role="role",
            user_ids="user_ids",
        )
        assert_matches_type(object, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncHanzo) -> None:
        response = await async_client.user.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        user = await response.parse()
        assert_matches_type(object, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncHanzo) -> None:
        async with async_client.user.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            user = await response.parse()
            assert_matches_type(object, user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_delete(self, async_client: AsyncHanzo) -> None:
        user = await async_client.user.delete(
            user_ids=["string"],
        )
        assert_matches_type(object, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_delete_with_all_params(self, async_client: AsyncHanzo) -> None:
        user = await async_client.user.delete(
            user_ids=["string"],
            llm_changed_by="llm-changed-by",
        )
        assert_matches_type(object, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncHanzo) -> None:
        response = await async_client.user.with_raw_response.delete(
            user_ids=["string"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        user = await response.parse()
        assert_matches_type(object, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncHanzo) -> None:
        async with async_client.user.with_streaming_response.delete(
            user_ids=["string"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            user = await response.parse()
            assert_matches_type(object, user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_retrieve_info(self, async_client: AsyncHanzo) -> None:
        user = await async_client.user.retrieve_info()
        assert_matches_type(object, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_retrieve_info_with_all_params(self, async_client: AsyncHanzo) -> None:
        user = await async_client.user.retrieve_info(
            user_id="user_id",
        )
        assert_matches_type(object, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_retrieve_info(self, async_client: AsyncHanzo) -> None:
        response = await async_client.user.with_raw_response.retrieve_info()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        user = await response.parse()
        assert_matches_type(object, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_retrieve_info(self, async_client: AsyncHanzo) -> None:
        async with async_client.user.with_streaming_response.retrieve_info() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            user = await response.parse()
            assert_matches_type(object, user, path=["response"])

        assert cast(Any, response.is_closed) is True
