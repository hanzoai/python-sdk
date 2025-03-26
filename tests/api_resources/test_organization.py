# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from hanzoai import Hanzo, AsyncHanzo
from tests.utils import assert_matches_type
from hanzoai.types import (
    OrganizationListResponse,
    OrganizationCreateResponse,
    OrganizationDeleteResponse,
    OrganizationUpdateResponse,
    OrganizationAddMemberResponse,
    OrganizationUpdateMemberResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestOrganization:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    def test_method_create(self, client: Hanzo) -> None:
        organization = client.organization.create(
            organization_alias="organization_alias",
        )
        assert_matches_type(OrganizationCreateResponse, organization, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_create_with_all_params(self, client: Hanzo) -> None:
        organization = client.organization.create(
            organization_alias="organization_alias",
            budget_duration="budget_duration",
            budget_id="budget_id",
            max_budget=0,
            max_parallel_requests=0,
            metadata={},
            model_max_budget={},
            models=[{}],
            organization_id="organization_id",
            rpm_limit=0,
            soft_budget=0,
            tpm_limit=0,
        )
        assert_matches_type(OrganizationCreateResponse, organization, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_create(self, client: Hanzo) -> None:
        response = client.organization.with_raw_response.create(
            organization_alias="organization_alias",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        organization = response.parse()
        assert_matches_type(OrganizationCreateResponse, organization, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_create(self, client: Hanzo) -> None:
        with client.organization.with_streaming_response.create(
            organization_alias="organization_alias",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            organization = response.parse()
            assert_matches_type(OrganizationCreateResponse, organization, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_update(self, client: Hanzo) -> None:
        organization = client.organization.update()
        assert_matches_type(OrganizationUpdateResponse, organization, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_update_with_all_params(self, client: Hanzo) -> None:
        organization = client.organization.update(
            budget_id="budget_id",
            metadata={},
            models=["string"],
            organization_alias="organization_alias",
            organization_id="organization_id",
            spend=0,
            updated_by="updated_by",
        )
        assert_matches_type(OrganizationUpdateResponse, organization, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_update(self, client: Hanzo) -> None:
        response = client.organization.with_raw_response.update()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        organization = response.parse()
        assert_matches_type(OrganizationUpdateResponse, organization, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_update(self, client: Hanzo) -> None:
        with client.organization.with_streaming_response.update() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            organization = response.parse()
            assert_matches_type(OrganizationUpdateResponse, organization, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_list(self, client: Hanzo) -> None:
        organization = client.organization.list()
        assert_matches_type(OrganizationListResponse, organization, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_list(self, client: Hanzo) -> None:
        response = client.organization.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        organization = response.parse()
        assert_matches_type(OrganizationListResponse, organization, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_list(self, client: Hanzo) -> None:
        with client.organization.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            organization = response.parse()
            assert_matches_type(OrganizationListResponse, organization, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_delete(self, client: Hanzo) -> None:
        organization = client.organization.delete(
            organization_ids=["string"],
        )
        assert_matches_type(OrganizationDeleteResponse, organization, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_delete(self, client: Hanzo) -> None:
        response = client.organization.with_raw_response.delete(
            organization_ids=["string"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        organization = response.parse()
        assert_matches_type(OrganizationDeleteResponse, organization, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_delete(self, client: Hanzo) -> None:
        with client.organization.with_streaming_response.delete(
            organization_ids=["string"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            organization = response.parse()
            assert_matches_type(OrganizationDeleteResponse, organization, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_add_member(self, client: Hanzo) -> None:
        organization = client.organization.add_member(
            member=[{"role": "org_admin"}],
            organization_id="organization_id",
        )
        assert_matches_type(OrganizationAddMemberResponse, organization, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_add_member_with_all_params(self, client: Hanzo) -> None:
        organization = client.organization.add_member(
            member=[
                {
                    "role": "org_admin",
                    "user_email": "user_email",
                    "user_id": "user_id",
                }
            ],
            organization_id="organization_id",
            max_budget_in_organization=0,
        )
        assert_matches_type(OrganizationAddMemberResponse, organization, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_add_member(self, client: Hanzo) -> None:
        response = client.organization.with_raw_response.add_member(
            member=[{"role": "org_admin"}],
            organization_id="organization_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        organization = response.parse()
        assert_matches_type(OrganizationAddMemberResponse, organization, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_add_member(self, client: Hanzo) -> None:
        with client.organization.with_streaming_response.add_member(
            member=[{"role": "org_admin"}],
            organization_id="organization_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            organization = response.parse()
            assert_matches_type(OrganizationAddMemberResponse, organization, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_delete_member(self, client: Hanzo) -> None:
        organization = client.organization.delete_member(
            organization_id="organization_id",
        )
        assert_matches_type(object, organization, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_delete_member_with_all_params(self, client: Hanzo) -> None:
        organization = client.organization.delete_member(
            organization_id="organization_id",
            user_email="user_email",
            user_id="user_id",
        )
        assert_matches_type(object, organization, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_delete_member(self, client: Hanzo) -> None:
        response = client.organization.with_raw_response.delete_member(
            organization_id="organization_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        organization = response.parse()
        assert_matches_type(object, organization, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_delete_member(self, client: Hanzo) -> None:
        with client.organization.with_streaming_response.delete_member(
            organization_id="organization_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            organization = response.parse()
            assert_matches_type(object, organization, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_update_member(self, client: Hanzo) -> None:
        organization = client.organization.update_member(
            organization_id="organization_id",
        )
        assert_matches_type(OrganizationUpdateMemberResponse, organization, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_update_member_with_all_params(self, client: Hanzo) -> None:
        organization = client.organization.update_member(
            organization_id="organization_id",
            max_budget_in_organization=0,
            role="proxy_admin",
            user_email="user_email",
            user_id="user_id",
        )
        assert_matches_type(OrganizationUpdateMemberResponse, organization, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_update_member(self, client: Hanzo) -> None:
        response = client.organization.with_raw_response.update_member(
            organization_id="organization_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        organization = response.parse()
        assert_matches_type(OrganizationUpdateMemberResponse, organization, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_update_member(self, client: Hanzo) -> None:
        with client.organization.with_streaming_response.update_member(
            organization_id="organization_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            organization = response.parse()
            assert_matches_type(OrganizationUpdateMemberResponse, organization, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncOrganization:
    parametrize = pytest.mark.parametrize("async_client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_create(self, async_client: AsyncHanzo) -> None:
        organization = await async_client.organization.create(
            organization_alias="organization_alias",
        )
        assert_matches_type(OrganizationCreateResponse, organization, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncHanzo) -> None:
        organization = await async_client.organization.create(
            organization_alias="organization_alias",
            budget_duration="budget_duration",
            budget_id="budget_id",
            max_budget=0,
            max_parallel_requests=0,
            metadata={},
            model_max_budget={},
            models=[{}],
            organization_id="organization_id",
            rpm_limit=0,
            soft_budget=0,
            tpm_limit=0,
        )
        assert_matches_type(OrganizationCreateResponse, organization, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncHanzo) -> None:
        response = await async_client.organization.with_raw_response.create(
            organization_alias="organization_alias",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        organization = await response.parse()
        assert_matches_type(OrganizationCreateResponse, organization, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncHanzo) -> None:
        async with async_client.organization.with_streaming_response.create(
            organization_alias="organization_alias",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            organization = await response.parse()
            assert_matches_type(OrganizationCreateResponse, organization, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_update(self, async_client: AsyncHanzo) -> None:
        organization = await async_client.organization.update()
        assert_matches_type(OrganizationUpdateResponse, organization, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncHanzo) -> None:
        organization = await async_client.organization.update(
            budget_id="budget_id",
            metadata={},
            models=["string"],
            organization_alias="organization_alias",
            organization_id="organization_id",
            spend=0,
            updated_by="updated_by",
        )
        assert_matches_type(OrganizationUpdateResponse, organization, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_update(self, async_client: AsyncHanzo) -> None:
        response = await async_client.organization.with_raw_response.update()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        organization = await response.parse()
        assert_matches_type(OrganizationUpdateResponse, organization, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncHanzo) -> None:
        async with async_client.organization.with_streaming_response.update() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            organization = await response.parse()
            assert_matches_type(OrganizationUpdateResponse, organization, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_list(self, async_client: AsyncHanzo) -> None:
        organization = await async_client.organization.list()
        assert_matches_type(OrganizationListResponse, organization, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncHanzo) -> None:
        response = await async_client.organization.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        organization = await response.parse()
        assert_matches_type(OrganizationListResponse, organization, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncHanzo) -> None:
        async with async_client.organization.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            organization = await response.parse()
            assert_matches_type(OrganizationListResponse, organization, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_delete(self, async_client: AsyncHanzo) -> None:
        organization = await async_client.organization.delete(
            organization_ids=["string"],
        )
        assert_matches_type(OrganizationDeleteResponse, organization, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncHanzo) -> None:
        response = await async_client.organization.with_raw_response.delete(
            organization_ids=["string"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        organization = await response.parse()
        assert_matches_type(OrganizationDeleteResponse, organization, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncHanzo) -> None:
        async with async_client.organization.with_streaming_response.delete(
            organization_ids=["string"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            organization = await response.parse()
            assert_matches_type(OrganizationDeleteResponse, organization, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_add_member(self, async_client: AsyncHanzo) -> None:
        organization = await async_client.organization.add_member(
            member=[{"role": "org_admin"}],
            organization_id="organization_id",
        )
        assert_matches_type(OrganizationAddMemberResponse, organization, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_add_member_with_all_params(self, async_client: AsyncHanzo) -> None:
        organization = await async_client.organization.add_member(
            member=[
                {
                    "role": "org_admin",
                    "user_email": "user_email",
                    "user_id": "user_id",
                }
            ],
            organization_id="organization_id",
            max_budget_in_organization=0,
        )
        assert_matches_type(OrganizationAddMemberResponse, organization, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_add_member(self, async_client: AsyncHanzo) -> None:
        response = await async_client.organization.with_raw_response.add_member(
            member=[{"role": "org_admin"}],
            organization_id="organization_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        organization = await response.parse()
        assert_matches_type(OrganizationAddMemberResponse, organization, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_add_member(self, async_client: AsyncHanzo) -> None:
        async with async_client.organization.with_streaming_response.add_member(
            member=[{"role": "org_admin"}],
            organization_id="organization_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            organization = await response.parse()
            assert_matches_type(OrganizationAddMemberResponse, organization, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_delete_member(self, async_client: AsyncHanzo) -> None:
        organization = await async_client.organization.delete_member(
            organization_id="organization_id",
        )
        assert_matches_type(object, organization, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_delete_member_with_all_params(self, async_client: AsyncHanzo) -> None:
        organization = await async_client.organization.delete_member(
            organization_id="organization_id",
            user_email="user_email",
            user_id="user_id",
        )
        assert_matches_type(object, organization, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_delete_member(self, async_client: AsyncHanzo) -> None:
        response = await async_client.organization.with_raw_response.delete_member(
            organization_id="organization_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        organization = await response.parse()
        assert_matches_type(object, organization, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_delete_member(self, async_client: AsyncHanzo) -> None:
        async with async_client.organization.with_streaming_response.delete_member(
            organization_id="organization_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            organization = await response.parse()
            assert_matches_type(object, organization, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_update_member(self, async_client: AsyncHanzo) -> None:
        organization = await async_client.organization.update_member(
            organization_id="organization_id",
        )
        assert_matches_type(OrganizationUpdateMemberResponse, organization, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_update_member_with_all_params(self, async_client: AsyncHanzo) -> None:
        organization = await async_client.organization.update_member(
            organization_id="organization_id",
            max_budget_in_organization=0,
            role="proxy_admin",
            user_email="user_email",
            user_id="user_id",
        )
        assert_matches_type(OrganizationUpdateMemberResponse, organization, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_update_member(self, async_client: AsyncHanzo) -> None:
        response = await async_client.organization.with_raw_response.update_member(
            organization_id="organization_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        organization = await response.parse()
        assert_matches_type(OrganizationUpdateMemberResponse, organization, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_update_member(self, async_client: AsyncHanzo) -> None:
        async with async_client.organization.with_streaming_response.update_member(
            organization_id="organization_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            organization = await response.parse()
            assert_matches_type(OrganizationUpdateMemberResponse, organization, path=["response"])

        assert cast(Any, response.is_closed) is True
