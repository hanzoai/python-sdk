# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from hanzoai import Hanzo, AsyncHanzo
from tests.utils import assert_matches_type
from hanzoai.types import (
    TeamCreateResponse,
    TeamAddMemberResponse,
    TeamUpdateMemberResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestTeam:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: Hanzo) -> None:
        team = client.team.create()
        assert_matches_type(TeamCreateResponse, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: Hanzo) -> None:
        team = client.team.create(
            admins=[{}],
            allowed_passthrough_routes=[{}],
            allowed_vector_store_indexes=[
                {
                    "index_name": "index_name",
                    "index_permissions": ["read"],
                }
            ],
            blocked=True,
            budget_duration="budget_duration",
            guardrails=["string"],
            max_budget=0,
            members=[{}],
            members_with_roles=[
                {
                    "role": "admin",
                    "user_email": "user_email",
                    "user_id": "user_id",
                }
            ],
            metadata={"foo": "bar"},
            model_aliases={"foo": "bar"},
            model_rpm_limit={"foo": 0},
            model_tpm_limit={"foo": 0},
            models=[{}],
            object_permission={
                "agent_access_groups": ["string"],
                "agents": ["string"],
                "mcp_access_groups": ["string"],
                "mcp_servers": ["string"],
                "mcp_tool_permissions": {"foo": ["string"]},
                "vector_stores": ["string"],
            },
            organization_id="organization_id",
            prompts=["string"],
            router_settings={"foo": "bar"},
            rpm_limit=0,
            rpm_limit_type="guaranteed_throughput",
            secret_manager_settings={"foo": "bar"},
            tags=[{}],
            team_alias="team_alias",
            team_id="team_id",
            team_member_budget=0,
            team_member_key_duration="team_member_key_duration",
            team_member_permissions=["string"],
            team_member_rpm_limit=0,
            team_member_tpm_limit=0,
            tpm_limit=0,
            tpm_limit_type="guaranteed_throughput",
            litellm_changed_by="litellm-changed-by",
        )
        assert_matches_type(TeamCreateResponse, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: Hanzo) -> None:
        response = client.team.with_raw_response.create()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        team = response.parse()
        assert_matches_type(TeamCreateResponse, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: Hanzo) -> None:
        with client.team.with_streaming_response.create() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            team = response.parse()
            assert_matches_type(TeamCreateResponse, team, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update(self, client: Hanzo) -> None:
        team = client.team.update(
            team_id="team_id",
        )
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_with_all_params(self, client: Hanzo) -> None:
        team = client.team.update(
            team_id="team_id",
            allowed_passthrough_routes=[{}],
            allowed_vector_store_indexes=[
                {
                    "index_name": "index_name",
                    "index_permissions": ["read"],
                }
            ],
            blocked=True,
            budget_duration="budget_duration",
            guardrails=["string"],
            max_budget=0,
            metadata={"foo": "bar"},
            model_aliases={"foo": "bar"},
            model_rpm_limit={"foo": 0},
            model_tpm_limit={"foo": 0},
            models=[{}],
            object_permission={
                "agent_access_groups": ["string"],
                "agents": ["string"],
                "mcp_access_groups": ["string"],
                "mcp_servers": ["string"],
                "mcp_tool_permissions": {"foo": ["string"]},
                "vector_stores": ["string"],
            },
            organization_id="organization_id",
            prompts=["string"],
            router_settings={"foo": "bar"},
            rpm_limit=0,
            secret_manager_settings={"foo": "bar"},
            tags=[{}],
            team_alias="team_alias",
            team_member_budget=0,
            team_member_budget_duration="team_member_budget_duration",
            team_member_key_duration="team_member_key_duration",
            team_member_rpm_limit=0,
            team_member_tpm_limit=0,
            tpm_limit=0,
            litellm_changed_by="litellm-changed-by",
        )
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update(self, client: Hanzo) -> None:
        response = client.team.with_raw_response.update(
            team_id="team_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        team = response.parse()
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update(self, client: Hanzo) -> None:
        with client.team.with_streaming_response.update(
            team_id="team_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            team = response.parse()
            assert_matches_type(object, team, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Hanzo) -> None:
        team = client.team.list()
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: Hanzo) -> None:
        team = client.team.list(
            organization_id="organization_id",
            user_id="user_id",
        )
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Hanzo) -> None:
        response = client.team.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        team = response.parse()
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Hanzo) -> None:
        with client.team.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            team = response.parse()
            assert_matches_type(object, team, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: Hanzo) -> None:
        team = client.team.delete(
            team_ids=["string"],
        )
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete_with_all_params(self, client: Hanzo) -> None:
        team = client.team.delete(
            team_ids=["string"],
            litellm_changed_by="litellm-changed-by",
        )
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: Hanzo) -> None:
        response = client.team.with_raw_response.delete(
            team_ids=["string"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        team = response.parse()
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: Hanzo) -> None:
        with client.team.with_streaming_response.delete(
            team_ids=["string"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            team = response.parse()
            assert_matches_type(object, team, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_add_member(self, client: Hanzo) -> None:
        team = client.team.add_member(
            member=[{"role": "admin"}],
            team_id="team_id",
        )
        assert_matches_type(TeamAddMemberResponse, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_add_member_with_all_params(self, client: Hanzo) -> None:
        team = client.team.add_member(
            member=[
                {
                    "role": "admin",
                    "user_email": "user_email",
                    "user_id": "user_id",
                }
            ],
            team_id="team_id",
            max_budget_in_team=0,
        )
        assert_matches_type(TeamAddMemberResponse, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_add_member(self, client: Hanzo) -> None:
        response = client.team.with_raw_response.add_member(
            member=[{"role": "admin"}],
            team_id="team_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        team = response.parse()
        assert_matches_type(TeamAddMemberResponse, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_add_member(self, client: Hanzo) -> None:
        with client.team.with_streaming_response.add_member(
            member=[{"role": "admin"}],
            team_id="team_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            team = response.parse()
            assert_matches_type(TeamAddMemberResponse, team, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_block(self, client: Hanzo) -> None:
        team = client.team.block(
            team_id="team_id",
        )
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_block(self, client: Hanzo) -> None:
        response = client.team.with_raw_response.block(
            team_id="team_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        team = response.parse()
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_block(self, client: Hanzo) -> None:
        with client.team.with_streaming_response.block(
            team_id="team_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            team = response.parse()
            assert_matches_type(object, team, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_disable_logging(self, client: Hanzo) -> None:
        team = client.team.disable_logging(
            "team_id",
        )
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_disable_logging(self, client: Hanzo) -> None:
        response = client.team.with_raw_response.disable_logging(
            "team_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        team = response.parse()
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_disable_logging(self, client: Hanzo) -> None:
        with client.team.with_streaming_response.disable_logging(
            "team_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            team = response.parse()
            assert_matches_type(object, team, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_disable_logging(self, client: Hanzo) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `team_id` but received ''"):
            client.team.with_raw_response.disable_logging(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_available(self, client: Hanzo) -> None:
        team = client.team.list_available()
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_available_with_all_params(self, client: Hanzo) -> None:
        team = client.team.list_available(
            response_model={},
        )
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list_available(self, client: Hanzo) -> None:
        response = client.team.with_raw_response.list_available()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        team = response.parse()
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list_available(self, client: Hanzo) -> None:
        with client.team.with_streaming_response.list_available() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            team = response.parse()
            assert_matches_type(object, team, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_remove_member(self, client: Hanzo) -> None:
        team = client.team.remove_member(
            team_id="team_id",
        )
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_remove_member_with_all_params(self, client: Hanzo) -> None:
        team = client.team.remove_member(
            team_id="team_id",
            user_email="user_email",
            user_id="user_id",
        )
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_remove_member(self, client: Hanzo) -> None:
        response = client.team.with_raw_response.remove_member(
            team_id="team_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        team = response.parse()
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_remove_member(self, client: Hanzo) -> None:
        with client.team.with_streaming_response.remove_member(
            team_id="team_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            team = response.parse()
            assert_matches_type(object, team, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_info(self, client: Hanzo) -> None:
        team = client.team.retrieve_info()
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_info_with_all_params(self, client: Hanzo) -> None:
        team = client.team.retrieve_info(
            team_id="team_id",
        )
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve_info(self, client: Hanzo) -> None:
        response = client.team.with_raw_response.retrieve_info()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        team = response.parse()
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve_info(self, client: Hanzo) -> None:
        with client.team.with_streaming_response.retrieve_info() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            team = response.parse()
            assert_matches_type(object, team, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_unblock(self, client: Hanzo) -> None:
        team = client.team.unblock(
            team_id="team_id",
        )
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_unblock(self, client: Hanzo) -> None:
        response = client.team.with_raw_response.unblock(
            team_id="team_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        team = response.parse()
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_unblock(self, client: Hanzo) -> None:
        with client.team.with_streaming_response.unblock(
            team_id="team_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            team = response.parse()
            assert_matches_type(object, team, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_member(self, client: Hanzo) -> None:
        team = client.team.update_member(
            team_id="team_id",
        )
        assert_matches_type(TeamUpdateMemberResponse, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_member_with_all_params(self, client: Hanzo) -> None:
        team = client.team.update_member(
            team_id="team_id",
            max_budget_in_team=0,
            role="admin",
            rpm_limit=0,
            tpm_limit=0,
            user_email="user_email",
            user_id="user_id",
        )
        assert_matches_type(TeamUpdateMemberResponse, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update_member(self, client: Hanzo) -> None:
        response = client.team.with_raw_response.update_member(
            team_id="team_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        team = response.parse()
        assert_matches_type(TeamUpdateMemberResponse, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update_member(self, client: Hanzo) -> None:
        with client.team.with_streaming_response.update_member(
            team_id="team_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            team = response.parse()
            assert_matches_type(TeamUpdateMemberResponse, team, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncTeam:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncHanzo) -> None:
        team = await async_client.team.create()
        assert_matches_type(TeamCreateResponse, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncHanzo) -> None:
        team = await async_client.team.create(
            admins=[{}],
            allowed_passthrough_routes=[{}],
            allowed_vector_store_indexes=[
                {
                    "index_name": "index_name",
                    "index_permissions": ["read"],
                }
            ],
            blocked=True,
            budget_duration="budget_duration",
            guardrails=["string"],
            max_budget=0,
            members=[{}],
            members_with_roles=[
                {
                    "role": "admin",
                    "user_email": "user_email",
                    "user_id": "user_id",
                }
            ],
            metadata={"foo": "bar"},
            model_aliases={"foo": "bar"},
            model_rpm_limit={"foo": 0},
            model_tpm_limit={"foo": 0},
            models=[{}],
            object_permission={
                "agent_access_groups": ["string"],
                "agents": ["string"],
                "mcp_access_groups": ["string"],
                "mcp_servers": ["string"],
                "mcp_tool_permissions": {"foo": ["string"]},
                "vector_stores": ["string"],
            },
            organization_id="organization_id",
            prompts=["string"],
            router_settings={"foo": "bar"},
            rpm_limit=0,
            rpm_limit_type="guaranteed_throughput",
            secret_manager_settings={"foo": "bar"},
            tags=[{}],
            team_alias="team_alias",
            team_id="team_id",
            team_member_budget=0,
            team_member_key_duration="team_member_key_duration",
            team_member_permissions=["string"],
            team_member_rpm_limit=0,
            team_member_tpm_limit=0,
            tpm_limit=0,
            tpm_limit_type="guaranteed_throughput",
            litellm_changed_by="litellm-changed-by",
        )
        assert_matches_type(TeamCreateResponse, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncHanzo) -> None:
        response = await async_client.team.with_raw_response.create()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        team = await response.parse()
        assert_matches_type(TeamCreateResponse, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncHanzo) -> None:
        async with async_client.team.with_streaming_response.create() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            team = await response.parse()
            assert_matches_type(TeamCreateResponse, team, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update(self, async_client: AsyncHanzo) -> None:
        team = await async_client.team.update(
            team_id="team_id",
        )
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncHanzo) -> None:
        team = await async_client.team.update(
            team_id="team_id",
            allowed_passthrough_routes=[{}],
            allowed_vector_store_indexes=[
                {
                    "index_name": "index_name",
                    "index_permissions": ["read"],
                }
            ],
            blocked=True,
            budget_duration="budget_duration",
            guardrails=["string"],
            max_budget=0,
            metadata={"foo": "bar"},
            model_aliases={"foo": "bar"},
            model_rpm_limit={"foo": 0},
            model_tpm_limit={"foo": 0},
            models=[{}],
            object_permission={
                "agent_access_groups": ["string"],
                "agents": ["string"],
                "mcp_access_groups": ["string"],
                "mcp_servers": ["string"],
                "mcp_tool_permissions": {"foo": ["string"]},
                "vector_stores": ["string"],
            },
            organization_id="organization_id",
            prompts=["string"],
            router_settings={"foo": "bar"},
            rpm_limit=0,
            secret_manager_settings={"foo": "bar"},
            tags=[{}],
            team_alias="team_alias",
            team_member_budget=0,
            team_member_budget_duration="team_member_budget_duration",
            team_member_key_duration="team_member_key_duration",
            team_member_rpm_limit=0,
            team_member_tpm_limit=0,
            tpm_limit=0,
            litellm_changed_by="litellm-changed-by",
        )
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update(self, async_client: AsyncHanzo) -> None:
        response = await async_client.team.with_raw_response.update(
            team_id="team_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        team = await response.parse()
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncHanzo) -> None:
        async with async_client.team.with_streaming_response.update(
            team_id="team_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            team = await response.parse()
            assert_matches_type(object, team, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncHanzo) -> None:
        team = await async_client.team.list()
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncHanzo) -> None:
        team = await async_client.team.list(
            organization_id="organization_id",
            user_id="user_id",
        )
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncHanzo) -> None:
        response = await async_client.team.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        team = await response.parse()
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncHanzo) -> None:
        async with async_client.team.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            team = await response.parse()
            assert_matches_type(object, team, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncHanzo) -> None:
        team = await async_client.team.delete(
            team_ids=["string"],
        )
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete_with_all_params(self, async_client: AsyncHanzo) -> None:
        team = await async_client.team.delete(
            team_ids=["string"],
            litellm_changed_by="litellm-changed-by",
        )
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncHanzo) -> None:
        response = await async_client.team.with_raw_response.delete(
            team_ids=["string"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        team = await response.parse()
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncHanzo) -> None:
        async with async_client.team.with_streaming_response.delete(
            team_ids=["string"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            team = await response.parse()
            assert_matches_type(object, team, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_add_member(self, async_client: AsyncHanzo) -> None:
        team = await async_client.team.add_member(
            member=[{"role": "admin"}],
            team_id="team_id",
        )
        assert_matches_type(TeamAddMemberResponse, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_add_member_with_all_params(self, async_client: AsyncHanzo) -> None:
        team = await async_client.team.add_member(
            member=[
                {
                    "role": "admin",
                    "user_email": "user_email",
                    "user_id": "user_id",
                }
            ],
            team_id="team_id",
            max_budget_in_team=0,
        )
        assert_matches_type(TeamAddMemberResponse, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_add_member(self, async_client: AsyncHanzo) -> None:
        response = await async_client.team.with_raw_response.add_member(
            member=[{"role": "admin"}],
            team_id="team_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        team = await response.parse()
        assert_matches_type(TeamAddMemberResponse, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_add_member(self, async_client: AsyncHanzo) -> None:
        async with async_client.team.with_streaming_response.add_member(
            member=[{"role": "admin"}],
            team_id="team_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            team = await response.parse()
            assert_matches_type(TeamAddMemberResponse, team, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_block(self, async_client: AsyncHanzo) -> None:
        team = await async_client.team.block(
            team_id="team_id",
        )
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_block(self, async_client: AsyncHanzo) -> None:
        response = await async_client.team.with_raw_response.block(
            team_id="team_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        team = await response.parse()
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_block(self, async_client: AsyncHanzo) -> None:
        async with async_client.team.with_streaming_response.block(
            team_id="team_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            team = await response.parse()
            assert_matches_type(object, team, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_disable_logging(self, async_client: AsyncHanzo) -> None:
        team = await async_client.team.disable_logging(
            "team_id",
        )
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_disable_logging(self, async_client: AsyncHanzo) -> None:
        response = await async_client.team.with_raw_response.disable_logging(
            "team_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        team = await response.parse()
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_disable_logging(self, async_client: AsyncHanzo) -> None:
        async with async_client.team.with_streaming_response.disable_logging(
            "team_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            team = await response.parse()
            assert_matches_type(object, team, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_disable_logging(self, async_client: AsyncHanzo) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `team_id` but received ''"):
            await async_client.team.with_raw_response.disable_logging(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_available(self, async_client: AsyncHanzo) -> None:
        team = await async_client.team.list_available()
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_available_with_all_params(self, async_client: AsyncHanzo) -> None:
        team = await async_client.team.list_available(
            response_model={},
        )
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list_available(self, async_client: AsyncHanzo) -> None:
        response = await async_client.team.with_raw_response.list_available()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        team = await response.parse()
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list_available(self, async_client: AsyncHanzo) -> None:
        async with async_client.team.with_streaming_response.list_available() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            team = await response.parse()
            assert_matches_type(object, team, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_remove_member(self, async_client: AsyncHanzo) -> None:
        team = await async_client.team.remove_member(
            team_id="team_id",
        )
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_remove_member_with_all_params(self, async_client: AsyncHanzo) -> None:
        team = await async_client.team.remove_member(
            team_id="team_id",
            user_email="user_email",
            user_id="user_id",
        )
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_remove_member(self, async_client: AsyncHanzo) -> None:
        response = await async_client.team.with_raw_response.remove_member(
            team_id="team_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        team = await response.parse()
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_remove_member(self, async_client: AsyncHanzo) -> None:
        async with async_client.team.with_streaming_response.remove_member(
            team_id="team_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            team = await response.parse()
            assert_matches_type(object, team, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_info(self, async_client: AsyncHanzo) -> None:
        team = await async_client.team.retrieve_info()
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_info_with_all_params(self, async_client: AsyncHanzo) -> None:
        team = await async_client.team.retrieve_info(
            team_id="team_id",
        )
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve_info(self, async_client: AsyncHanzo) -> None:
        response = await async_client.team.with_raw_response.retrieve_info()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        team = await response.parse()
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve_info(self, async_client: AsyncHanzo) -> None:
        async with async_client.team.with_streaming_response.retrieve_info() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            team = await response.parse()
            assert_matches_type(object, team, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_unblock(self, async_client: AsyncHanzo) -> None:
        team = await async_client.team.unblock(
            team_id="team_id",
        )
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_unblock(self, async_client: AsyncHanzo) -> None:
        response = await async_client.team.with_raw_response.unblock(
            team_id="team_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        team = await response.parse()
        assert_matches_type(object, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_unblock(self, async_client: AsyncHanzo) -> None:
        async with async_client.team.with_streaming_response.unblock(
            team_id="team_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            team = await response.parse()
            assert_matches_type(object, team, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_member(self, async_client: AsyncHanzo) -> None:
        team = await async_client.team.update_member(
            team_id="team_id",
        )
        assert_matches_type(TeamUpdateMemberResponse, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_member_with_all_params(self, async_client: AsyncHanzo) -> None:
        team = await async_client.team.update_member(
            team_id="team_id",
            max_budget_in_team=0,
            role="admin",
            rpm_limit=0,
            tpm_limit=0,
            user_email="user_email",
            user_id="user_id",
        )
        assert_matches_type(TeamUpdateMemberResponse, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update_member(self, async_client: AsyncHanzo) -> None:
        response = await async_client.team.with_raw_response.update_member(
            team_id="team_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        team = await response.parse()
        assert_matches_type(TeamUpdateMemberResponse, team, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update_member(self, async_client: AsyncHanzo) -> None:
        async with async_client.team.with_streaming_response.update_member(
            team_id="team_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            team = await response.parse()
            assert_matches_type(TeamUpdateMemberResponse, team, path=["response"])

        assert cast(Any, response.is_closed) is True
