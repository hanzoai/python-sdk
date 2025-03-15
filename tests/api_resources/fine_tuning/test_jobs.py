# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from hanzoai import Hanzo, AsyncHanzo
from tests.utils import assert_matches_type

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestJobs:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    def test_method_create(self, client: Hanzo) -> None:
        job = client.fine_tuning.jobs.create(
            custom_llm_provider="openai",
            model="model",
            training_file="training_file",
        )
        assert_matches_type(object, job, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_create_with_all_params(self, client: Hanzo) -> None:
        job = client.fine_tuning.jobs.create(
            custom_llm_provider="openai",
            model="model",
            training_file="training_file",
            hyperparameters={
                "batch_size": "string",
                "learning_rate_multiplier": "string",
                "n_epochs": "string",
            },
            integrations=["string"],
            seed=0,
            suffix="suffix",
            validation_file="validation_file",
        )
        assert_matches_type(object, job, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_create(self, client: Hanzo) -> None:
        response = client.fine_tuning.jobs.with_raw_response.create(
            custom_llm_provider="openai",
            model="model",
            training_file="training_file",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        job = response.parse()
        assert_matches_type(object, job, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_create(self, client: Hanzo) -> None:
        with client.fine_tuning.jobs.with_streaming_response.create(
            custom_llm_provider="openai",
            model="model",
            training_file="training_file",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            job = response.parse()
            assert_matches_type(object, job, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_retrieve(self, client: Hanzo) -> None:
        job = client.fine_tuning.jobs.retrieve(
            fine_tuning_job_id="fine_tuning_job_id",
            custom_llm_provider="openai",
        )
        assert_matches_type(object, job, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_retrieve(self, client: Hanzo) -> None:
        response = client.fine_tuning.jobs.with_raw_response.retrieve(
            fine_tuning_job_id="fine_tuning_job_id",
            custom_llm_provider="openai",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        job = response.parse()
        assert_matches_type(object, job, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_retrieve(self, client: Hanzo) -> None:
        with client.fine_tuning.jobs.with_streaming_response.retrieve(
            fine_tuning_job_id="fine_tuning_job_id",
            custom_llm_provider="openai",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            job = response.parse()
            assert_matches_type(object, job, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_path_params_retrieve(self, client: Hanzo) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `fine_tuning_job_id` but received ''"):
            client.fine_tuning.jobs.with_raw_response.retrieve(
                fine_tuning_job_id="",
                custom_llm_provider="openai",
            )

    @pytest.mark.skip()
    @parametrize
    def test_method_list(self, client: Hanzo) -> None:
        job = client.fine_tuning.jobs.list(
            custom_llm_provider="openai",
        )
        assert_matches_type(object, job, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_list_with_all_params(self, client: Hanzo) -> None:
        job = client.fine_tuning.jobs.list(
            custom_llm_provider="openai",
            after="after",
            limit=0,
        )
        assert_matches_type(object, job, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_list(self, client: Hanzo) -> None:
        response = client.fine_tuning.jobs.with_raw_response.list(
            custom_llm_provider="openai",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        job = response.parse()
        assert_matches_type(object, job, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_list(self, client: Hanzo) -> None:
        with client.fine_tuning.jobs.with_streaming_response.list(
            custom_llm_provider="openai",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            job = response.parse()
            assert_matches_type(object, job, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncJobs:
    parametrize = pytest.mark.parametrize("async_client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_create(self, async_client: AsyncHanzo) -> None:
        job = await async_client.fine_tuning.jobs.create(
            custom_llm_provider="openai",
            model="model",
            training_file="training_file",
        )
        assert_matches_type(object, job, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncHanzo) -> None:
        job = await async_client.fine_tuning.jobs.create(
            custom_llm_provider="openai",
            model="model",
            training_file="training_file",
            hyperparameters={
                "batch_size": "string",
                "learning_rate_multiplier": "string",
                "n_epochs": "string",
            },
            integrations=["string"],
            seed=0,
            suffix="suffix",
            validation_file="validation_file",
        )
        assert_matches_type(object, job, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncHanzo) -> None:
        response = await async_client.fine_tuning.jobs.with_raw_response.create(
            custom_llm_provider="openai",
            model="model",
            training_file="training_file",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        job = await response.parse()
        assert_matches_type(object, job, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncHanzo) -> None:
        async with async_client.fine_tuning.jobs.with_streaming_response.create(
            custom_llm_provider="openai",
            model="model",
            training_file="training_file",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            job = await response.parse()
            assert_matches_type(object, job, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncHanzo) -> None:
        job = await async_client.fine_tuning.jobs.retrieve(
            fine_tuning_job_id="fine_tuning_job_id",
            custom_llm_provider="openai",
        )
        assert_matches_type(object, job, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncHanzo) -> None:
        response = await async_client.fine_tuning.jobs.with_raw_response.retrieve(
            fine_tuning_job_id="fine_tuning_job_id",
            custom_llm_provider="openai",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        job = await response.parse()
        assert_matches_type(object, job, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncHanzo) -> None:
        async with async_client.fine_tuning.jobs.with_streaming_response.retrieve(
            fine_tuning_job_id="fine_tuning_job_id",
            custom_llm_provider="openai",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            job = await response.parse()
            assert_matches_type(object, job, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncHanzo) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `fine_tuning_job_id` but received ''"):
            await async_client.fine_tuning.jobs.with_raw_response.retrieve(
                fine_tuning_job_id="",
                custom_llm_provider="openai",
            )

    @pytest.mark.skip()
    @parametrize
    async def test_method_list(self, async_client: AsyncHanzo) -> None:
        job = await async_client.fine_tuning.jobs.list(
            custom_llm_provider="openai",
        )
        assert_matches_type(object, job, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncHanzo) -> None:
        job = await async_client.fine_tuning.jobs.list(
            custom_llm_provider="openai",
            after="after",
            limit=0,
        )
        assert_matches_type(object, job, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncHanzo) -> None:
        response = await async_client.fine_tuning.jobs.with_raw_response.list(
            custom_llm_provider="openai",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        job = await response.parse()
        assert_matches_type(object, job, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncHanzo) -> None:
        async with async_client.fine_tuning.jobs.with_streaming_response.list(
            custom_llm_provider="openai",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            job = await response.parse()
            assert_matches_type(object, job, path=["response"])

        assert cast(Any, response.is_closed) is True
