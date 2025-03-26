# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from hanzoai import Hanzo, AsyncHanzo
from tests.utils import assert_matches_type
from hanzoai._utils import parse_datetime

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestModel:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    def test_method_create(self, client: Hanzo) -> None:
        model = client.model.create(
            llm_params={"model": "model"},
            model_info={"id": "id"},
            model_name="model_name",
        )
        assert_matches_type(object, model, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_create_with_all_params(self, client: Hanzo) -> None:
        model = client.model.create(
            llm_params={
                "model": "model",
                "api_base": "api_base",
                "api_key": "api_key",
                "api_version": "api_version",
                "aws_access_key_id": "aws_access_key_id",
                "aws_region_name": "aws_region_name",
                "aws_secret_access_key": "aws_secret_access_key",
                "budget_duration": "budget_duration",
                "configurable_clientside_auth_params": ["string"],
                "custom_llm_provider": "custom_llm_provider",
                "input_cost_per_second": 0,
                "input_cost_per_token": 0,
                "llm_trace_id": "llm_trace_id",
                "max_budget": 0,
                "max_file_size_mb": 0,
                "max_retries": 0,
                "merge_reasoning_content_in_choices": True,
                "model_info": {},
                "organization": "organization",
                "output_cost_per_second": 0,
                "output_cost_per_token": 0,
                "region_name": "region_name",
                "rpm": 0,
                "stream_timeout": 0,
                "timeout": 0,
                "tpm": 0,
                "use_in_pass_through": True,
                "vertex_credentials": "string",
                "vertex_location": "vertex_location",
                "vertex_project": "vertex_project",
                "watsonx_region_name": "watsonx_region_name",
            },
            model_info={
                "id": "id",
                "base_model": "base_model",
                "created_at": parse_datetime("2019-12-27T18:11:19.117Z"),
                "created_by": "created_by",
                "db_model": True,
                "team_id": "team_id",
                "team_public_model_name": "team_public_model_name",
                "tier": "free",
                "updated_at": parse_datetime("2019-12-27T18:11:19.117Z"),
                "updated_by": "updated_by",
            },
            model_name="model_name",
        )
        assert_matches_type(object, model, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_create(self, client: Hanzo) -> None:
        response = client.model.with_raw_response.create(
            llm_params={"model": "model"},
            model_info={"id": "id"},
            model_name="model_name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        model = response.parse()
        assert_matches_type(object, model, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_create(self, client: Hanzo) -> None:
        with client.model.with_streaming_response.create(
            llm_params={"model": "model"},
            model_info={"id": "id"},
            model_name="model_name",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            model = response.parse()
            assert_matches_type(object, model, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_delete(self, client: Hanzo) -> None:
        model = client.model.delete(
            id="id",
        )
        assert_matches_type(object, model, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_delete(self, client: Hanzo) -> None:
        response = client.model.with_raw_response.delete(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        model = response.parse()
        assert_matches_type(object, model, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_delete(self, client: Hanzo) -> None:
        with client.model.with_streaming_response.delete(
            id="id",
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
    async def test_method_create(self, async_client: AsyncHanzo) -> None:
        model = await async_client.model.create(
            llm_params={"model": "model"},
            model_info={"id": "id"},
            model_name="model_name",
        )
        assert_matches_type(object, model, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncHanzo) -> None:
        model = await async_client.model.create(
            llm_params={
                "model": "model",
                "api_base": "api_base",
                "api_key": "api_key",
                "api_version": "api_version",
                "aws_access_key_id": "aws_access_key_id",
                "aws_region_name": "aws_region_name",
                "aws_secret_access_key": "aws_secret_access_key",
                "budget_duration": "budget_duration",
                "configurable_clientside_auth_params": ["string"],
                "custom_llm_provider": "custom_llm_provider",
                "input_cost_per_second": 0,
                "input_cost_per_token": 0,
                "llm_trace_id": "llm_trace_id",
                "max_budget": 0,
                "max_file_size_mb": 0,
                "max_retries": 0,
                "merge_reasoning_content_in_choices": True,
                "model_info": {},
                "organization": "organization",
                "output_cost_per_second": 0,
                "output_cost_per_token": 0,
                "region_name": "region_name",
                "rpm": 0,
                "stream_timeout": 0,
                "timeout": 0,
                "tpm": 0,
                "use_in_pass_through": True,
                "vertex_credentials": "string",
                "vertex_location": "vertex_location",
                "vertex_project": "vertex_project",
                "watsonx_region_name": "watsonx_region_name",
            },
            model_info={
                "id": "id",
                "base_model": "base_model",
                "created_at": parse_datetime("2019-12-27T18:11:19.117Z"),
                "created_by": "created_by",
                "db_model": True,
                "team_id": "team_id",
                "team_public_model_name": "team_public_model_name",
                "tier": "free",
                "updated_at": parse_datetime("2019-12-27T18:11:19.117Z"),
                "updated_by": "updated_by",
            },
            model_name="model_name",
        )
        assert_matches_type(object, model, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncHanzo) -> None:
        response = await async_client.model.with_raw_response.create(
            llm_params={"model": "model"},
            model_info={"id": "id"},
            model_name="model_name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        model = await response.parse()
        assert_matches_type(object, model, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncHanzo) -> None:
        async with async_client.model.with_streaming_response.create(
            llm_params={"model": "model"},
            model_info={"id": "id"},
            model_name="model_name",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            model = await response.parse()
            assert_matches_type(object, model, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_delete(self, async_client: AsyncHanzo) -> None:
        model = await async_client.model.delete(
            id="id",
        )
        assert_matches_type(object, model, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncHanzo) -> None:
        response = await async_client.model.with_raw_response.delete(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        model = await response.parse()
        assert_matches_type(object, model, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncHanzo) -> None:
        async with async_client.model.with_streaming_response.delete(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            model = await response.parse()
            assert_matches_type(object, model, path=["response"])

        assert cast(Any, response.is_closed) is True
