# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, Optional, cast

import pytest

from hanzoai import Hanzo, AsyncHanzo
from tests.utils import assert_matches_type
from hanzoai.types import (
    KeyListResponse,
    KeyBlockResponse,
    GenerateKeyResponse,
    KeyCheckHealthResponse,
)
from hanzoai._utils import parse_datetime

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestKey:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    def test_method_update(self, client: Hanzo) -> None:
        key = client.key.update(
            key="key",
        )
        assert_matches_type(object, key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_update_with_all_params(self, client: Hanzo) -> None:
        key = client.key.update(
            key="key",
            aliases={},
            allowed_cache_controls=[{}],
            blocked=True,
            budget_duration="budget_duration",
            budget_id="budget_id",
            config={},
            duration="duration",
            enforced_params=["string"],
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
            spend=0,
            tags=["string"],
            team_id="team_id",
            temp_budget_expiry=parse_datetime("2019-12-27T18:11:19.117Z"),
            temp_budget_increase=0,
            tpm_limit=0,
            user_id="user_id",
            llm_changed_by="llm-changed-by",
        )
        assert_matches_type(object, key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_update(self, client: Hanzo) -> None:
        response = client.key.with_raw_response.update(
            key="key",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        key = response.parse()
        assert_matches_type(object, key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_update(self, client: Hanzo) -> None:
        with client.key.with_streaming_response.update(
            key="key",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            key = response.parse()
            assert_matches_type(object, key, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_list(self, client: Hanzo) -> None:
        key = client.key.list()
        assert_matches_type(KeyListResponse, key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_list_with_all_params(self, client: Hanzo) -> None:
        key = client.key.list(
            include_team_keys=True,
            key_alias="key_alias",
            organization_id="organization_id",
            page=1,
            return_full_object=True,
            size=1,
            team_id="team_id",
            user_id="user_id",
        )
        assert_matches_type(KeyListResponse, key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_list(self, client: Hanzo) -> None:
        response = client.key.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        key = response.parse()
        assert_matches_type(KeyListResponse, key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_list(self, client: Hanzo) -> None:
        with client.key.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            key = response.parse()
            assert_matches_type(KeyListResponse, key, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_delete(self, client: Hanzo) -> None:
        key = client.key.delete()
        assert_matches_type(object, key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_delete_with_all_params(self, client: Hanzo) -> None:
        key = client.key.delete(
            key_aliases=["string"],
            keys=["string"],
            llm_changed_by="llm-changed-by",
        )
        assert_matches_type(object, key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_delete(self, client: Hanzo) -> None:
        response = client.key.with_raw_response.delete()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        key = response.parse()
        assert_matches_type(object, key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_delete(self, client: Hanzo) -> None:
        with client.key.with_streaming_response.delete() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            key = response.parse()
            assert_matches_type(object, key, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_block(self, client: Hanzo) -> None:
        key = client.key.block(
            key="key",
        )
        assert_matches_type(Optional[KeyBlockResponse], key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_block_with_all_params(self, client: Hanzo) -> None:
        key = client.key.block(
            key="key",
            llm_changed_by="llm-changed-by",
        )
        assert_matches_type(Optional[KeyBlockResponse], key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_block(self, client: Hanzo) -> None:
        response = client.key.with_raw_response.block(
            key="key",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        key = response.parse()
        assert_matches_type(Optional[KeyBlockResponse], key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_block(self, client: Hanzo) -> None:
        with client.key.with_streaming_response.block(
            key="key",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            key = response.parse()
            assert_matches_type(Optional[KeyBlockResponse], key, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_check_health(self, client: Hanzo) -> None:
        key = client.key.check_health()
        assert_matches_type(KeyCheckHealthResponse, key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_check_health(self, client: Hanzo) -> None:
        response = client.key.with_raw_response.check_health()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        key = response.parse()
        assert_matches_type(KeyCheckHealthResponse, key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_check_health(self, client: Hanzo) -> None:
        with client.key.with_streaming_response.check_health() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            key = response.parse()
            assert_matches_type(KeyCheckHealthResponse, key, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_generate(self, client: Hanzo) -> None:
        key = client.key.generate()
        assert_matches_type(GenerateKeyResponse, key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_generate_with_all_params(self, client: Hanzo) -> None:
        key = client.key.generate(
            aliases={},
            allowed_cache_controls=[{}],
            blocked=True,
            budget_duration="budget_duration",
            budget_id="budget_id",
            config={},
            duration="duration",
            enforced_params=["string"],
            guardrails=["string"],
            key="key",
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
            soft_budget=0,
            spend=0,
            tags=["string"],
            team_id="team_id",
            tpm_limit=0,
            user_id="user_id",
            llm_changed_by="llm-changed-by",
        )
        assert_matches_type(GenerateKeyResponse, key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_generate(self, client: Hanzo) -> None:
        response = client.key.with_raw_response.generate()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        key = response.parse()
        assert_matches_type(GenerateKeyResponse, key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_generate(self, client: Hanzo) -> None:
        with client.key.with_streaming_response.generate() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            key = response.parse()
            assert_matches_type(GenerateKeyResponse, key, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_regenerate_by_key(self, client: Hanzo) -> None:
        key = client.key.regenerate_by_key(
            path_key="key",
        )
        assert_matches_type(Optional[GenerateKeyResponse], key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_regenerate_by_key_with_all_params(self, client: Hanzo) -> None:
        key = client.key.regenerate_by_key(
            path_key="key",
            aliases={},
            allowed_cache_controls=[{}],
            blocked=True,
            budget_duration="budget_duration",
            budget_id="budget_id",
            config={},
            duration="duration",
            enforced_params=["string"],
            guardrails=["string"],
            body_key="key",
            key_alias="key_alias",
            max_budget=0,
            max_parallel_requests=0,
            metadata={},
            model_max_budget={},
            model_rpm_limit={},
            model_tpm_limit={},
            models=[{}],
            new_master_key="new_master_key",
            permissions={},
            rpm_limit=0,
            send_invite_email=True,
            soft_budget=0,
            spend=0,
            tags=["string"],
            team_id="team_id",
            tpm_limit=0,
            user_id="user_id",
            llm_changed_by="llm-changed-by",
        )
        assert_matches_type(Optional[GenerateKeyResponse], key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_regenerate_by_key(self, client: Hanzo) -> None:
        response = client.key.with_raw_response.regenerate_by_key(
            path_key="key",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        key = response.parse()
        assert_matches_type(Optional[GenerateKeyResponse], key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_regenerate_by_key(self, client: Hanzo) -> None:
        with client.key.with_streaming_response.regenerate_by_key(
            path_key="key",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            key = response.parse()
            assert_matches_type(Optional[GenerateKeyResponse], key, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_path_params_regenerate_by_key(self, client: Hanzo) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `path_key` but received ''"):
            client.key.with_raw_response.regenerate_by_key(
                path_key="",
            )

    @pytest.mark.skip()
    @parametrize
    def test_method_retrieve_info(self, client: Hanzo) -> None:
        key = client.key.retrieve_info()
        assert_matches_type(object, key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_retrieve_info_with_all_params(self, client: Hanzo) -> None:
        key = client.key.retrieve_info(
            key="key",
        )
        assert_matches_type(object, key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_retrieve_info(self, client: Hanzo) -> None:
        response = client.key.with_raw_response.retrieve_info()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        key = response.parse()
        assert_matches_type(object, key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_retrieve_info(self, client: Hanzo) -> None:
        with client.key.with_streaming_response.retrieve_info() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            key = response.parse()
            assert_matches_type(object, key, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_unblock(self, client: Hanzo) -> None:
        key = client.key.unblock(
            key="key",
        )
        assert_matches_type(object, key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_unblock_with_all_params(self, client: Hanzo) -> None:
        key = client.key.unblock(
            key="key",
            llm_changed_by="llm-changed-by",
        )
        assert_matches_type(object, key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_unblock(self, client: Hanzo) -> None:
        response = client.key.with_raw_response.unblock(
            key="key",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        key = response.parse()
        assert_matches_type(object, key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_unblock(self, client: Hanzo) -> None:
        with client.key.with_streaming_response.unblock(
            key="key",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            key = response.parse()
            assert_matches_type(object, key, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncKey:
    parametrize = pytest.mark.parametrize("async_client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_update(self, async_client: AsyncHanzo) -> None:
        key = await async_client.key.update(
            key="key",
        )
        assert_matches_type(object, key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncHanzo) -> None:
        key = await async_client.key.update(
            key="key",
            aliases={},
            allowed_cache_controls=[{}],
            blocked=True,
            budget_duration="budget_duration",
            budget_id="budget_id",
            config={},
            duration="duration",
            enforced_params=["string"],
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
            spend=0,
            tags=["string"],
            team_id="team_id",
            temp_budget_expiry=parse_datetime("2019-12-27T18:11:19.117Z"),
            temp_budget_increase=0,
            tpm_limit=0,
            user_id="user_id",
            llm_changed_by="llm-changed-by",
        )
        assert_matches_type(object, key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_update(self, async_client: AsyncHanzo) -> None:
        response = await async_client.key.with_raw_response.update(
            key="key",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        key = await response.parse()
        assert_matches_type(object, key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncHanzo) -> None:
        async with async_client.key.with_streaming_response.update(
            key="key",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            key = await response.parse()
            assert_matches_type(object, key, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_list(self, async_client: AsyncHanzo) -> None:
        key = await async_client.key.list()
        assert_matches_type(KeyListResponse, key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncHanzo) -> None:
        key = await async_client.key.list(
            include_team_keys=True,
            key_alias="key_alias",
            organization_id="organization_id",
            page=1,
            return_full_object=True,
            size=1,
            team_id="team_id",
            user_id="user_id",
        )
        assert_matches_type(KeyListResponse, key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncHanzo) -> None:
        response = await async_client.key.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        key = await response.parse()
        assert_matches_type(KeyListResponse, key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncHanzo) -> None:
        async with async_client.key.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            key = await response.parse()
            assert_matches_type(KeyListResponse, key, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_delete(self, async_client: AsyncHanzo) -> None:
        key = await async_client.key.delete()
        assert_matches_type(object, key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_delete_with_all_params(self, async_client: AsyncHanzo) -> None:
        key = await async_client.key.delete(
            key_aliases=["string"],
            keys=["string"],
            llm_changed_by="llm-changed-by",
        )
        assert_matches_type(object, key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncHanzo) -> None:
        response = await async_client.key.with_raw_response.delete()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        key = await response.parse()
        assert_matches_type(object, key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncHanzo) -> None:
        async with async_client.key.with_streaming_response.delete() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            key = await response.parse()
            assert_matches_type(object, key, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_block(self, async_client: AsyncHanzo) -> None:
        key = await async_client.key.block(
            key="key",
        )
        assert_matches_type(Optional[KeyBlockResponse], key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_block_with_all_params(self, async_client: AsyncHanzo) -> None:
        key = await async_client.key.block(
            key="key",
            llm_changed_by="llm-changed-by",
        )
        assert_matches_type(Optional[KeyBlockResponse], key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_block(self, async_client: AsyncHanzo) -> None:
        response = await async_client.key.with_raw_response.block(
            key="key",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        key = await response.parse()
        assert_matches_type(Optional[KeyBlockResponse], key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_block(self, async_client: AsyncHanzo) -> None:
        async with async_client.key.with_streaming_response.block(
            key="key",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            key = await response.parse()
            assert_matches_type(Optional[KeyBlockResponse], key, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_check_health(self, async_client: AsyncHanzo) -> None:
        key = await async_client.key.check_health()
        assert_matches_type(KeyCheckHealthResponse, key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_check_health(self, async_client: AsyncHanzo) -> None:
        response = await async_client.key.with_raw_response.check_health()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        key = await response.parse()
        assert_matches_type(KeyCheckHealthResponse, key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_check_health(self, async_client: AsyncHanzo) -> None:
        async with async_client.key.with_streaming_response.check_health() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            key = await response.parse()
            assert_matches_type(KeyCheckHealthResponse, key, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_generate(self, async_client: AsyncHanzo) -> None:
        key = await async_client.key.generate()
        assert_matches_type(GenerateKeyResponse, key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_generate_with_all_params(self, async_client: AsyncHanzo) -> None:
        key = await async_client.key.generate(
            aliases={},
            allowed_cache_controls=[{}],
            blocked=True,
            budget_duration="budget_duration",
            budget_id="budget_id",
            config={},
            duration="duration",
            enforced_params=["string"],
            guardrails=["string"],
            key="key",
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
            soft_budget=0,
            spend=0,
            tags=["string"],
            team_id="team_id",
            tpm_limit=0,
            user_id="user_id",
            llm_changed_by="llm-changed-by",
        )
        assert_matches_type(GenerateKeyResponse, key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_generate(self, async_client: AsyncHanzo) -> None:
        response = await async_client.key.with_raw_response.generate()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        key = await response.parse()
        assert_matches_type(GenerateKeyResponse, key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_generate(self, async_client: AsyncHanzo) -> None:
        async with async_client.key.with_streaming_response.generate() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            key = await response.parse()
            assert_matches_type(GenerateKeyResponse, key, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_regenerate_by_key(self, async_client: AsyncHanzo) -> None:
        key = await async_client.key.regenerate_by_key(
            path_key="key",
        )
        assert_matches_type(Optional[GenerateKeyResponse], key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_regenerate_by_key_with_all_params(self, async_client: AsyncHanzo) -> None:
        key = await async_client.key.regenerate_by_key(
            path_key="key",
            aliases={},
            allowed_cache_controls=[{}],
            blocked=True,
            budget_duration="budget_duration",
            budget_id="budget_id",
            config={},
            duration="duration",
            enforced_params=["string"],
            guardrails=["string"],
            body_key="key",
            key_alias="key_alias",
            max_budget=0,
            max_parallel_requests=0,
            metadata={},
            model_max_budget={},
            model_rpm_limit={},
            model_tpm_limit={},
            models=[{}],
            new_master_key="new_master_key",
            permissions={},
            rpm_limit=0,
            send_invite_email=True,
            soft_budget=0,
            spend=0,
            tags=["string"],
            team_id="team_id",
            tpm_limit=0,
            user_id="user_id",
            llm_changed_by="llm-changed-by",
        )
        assert_matches_type(Optional[GenerateKeyResponse], key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_regenerate_by_key(self, async_client: AsyncHanzo) -> None:
        response = await async_client.key.with_raw_response.regenerate_by_key(
            path_key="key",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        key = await response.parse()
        assert_matches_type(Optional[GenerateKeyResponse], key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_regenerate_by_key(self, async_client: AsyncHanzo) -> None:
        async with async_client.key.with_streaming_response.regenerate_by_key(
            path_key="key",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            key = await response.parse()
            assert_matches_type(Optional[GenerateKeyResponse], key, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_path_params_regenerate_by_key(self, async_client: AsyncHanzo) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `path_key` but received ''"):
            await async_client.key.with_raw_response.regenerate_by_key(
                path_key="",
            )

    @pytest.mark.skip()
    @parametrize
    async def test_method_retrieve_info(self, async_client: AsyncHanzo) -> None:
        key = await async_client.key.retrieve_info()
        assert_matches_type(object, key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_retrieve_info_with_all_params(self, async_client: AsyncHanzo) -> None:
        key = await async_client.key.retrieve_info(
            key="key",
        )
        assert_matches_type(object, key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_retrieve_info(self, async_client: AsyncHanzo) -> None:
        response = await async_client.key.with_raw_response.retrieve_info()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        key = await response.parse()
        assert_matches_type(object, key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_retrieve_info(self, async_client: AsyncHanzo) -> None:
        async with async_client.key.with_streaming_response.retrieve_info() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            key = await response.parse()
            assert_matches_type(object, key, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_unblock(self, async_client: AsyncHanzo) -> None:
        key = await async_client.key.unblock(
            key="key",
        )
        assert_matches_type(object, key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_unblock_with_all_params(self, async_client: AsyncHanzo) -> None:
        key = await async_client.key.unblock(
            key="key",
            llm_changed_by="llm-changed-by",
        )
        assert_matches_type(object, key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_unblock(self, async_client: AsyncHanzo) -> None:
        response = await async_client.key.with_raw_response.unblock(
            key="key",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        key = await response.parse()
        assert_matches_type(object, key, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_unblock(self, async_client: AsyncHanzo) -> None:
        async with async_client.key.with_streaming_response.unblock(
            key="key",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            key = await response.parse()
            assert_matches_type(object, key, path=["response"])

        assert cast(Any, response.is_closed) is True
