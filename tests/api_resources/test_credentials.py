# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from hanzoai import Hanzo, AsyncHanzo
from tests.utils import assert_matches_type

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestCredentials:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    def test_method_create(self, client: Hanzo) -> None:
        credential = client.credentials.create(
            credential_info={},
            credential_name="credential_name",
        )
        assert_matches_type(object, credential, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_create_with_all_params(self, client: Hanzo) -> None:
        credential = client.credentials.create(
            credential_info={},
            credential_name="credential_name",
            credential_values={},
            model_id="model_id",
        )
        assert_matches_type(object, credential, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_create(self, client: Hanzo) -> None:
        response = client.credentials.with_raw_response.create(
            credential_info={},
            credential_name="credential_name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        credential = response.parse()
        assert_matches_type(object, credential, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_create(self, client: Hanzo) -> None:
        with client.credentials.with_streaming_response.create(
            credential_info={},
            credential_name="credential_name",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            credential = response.parse()
            assert_matches_type(object, credential, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_list(self, client: Hanzo) -> None:
        credential = client.credentials.list()
        assert_matches_type(object, credential, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_list(self, client: Hanzo) -> None:
        response = client.credentials.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        credential = response.parse()
        assert_matches_type(object, credential, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_list(self, client: Hanzo) -> None:
        with client.credentials.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            credential = response.parse()
            assert_matches_type(object, credential, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_delete(self, client: Hanzo) -> None:
        credential = client.credentials.delete(
            "credential_name",
        )
        assert_matches_type(object, credential, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_delete(self, client: Hanzo) -> None:
        response = client.credentials.with_raw_response.delete(
            "credential_name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        credential = response.parse()
        assert_matches_type(object, credential, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_delete(self, client: Hanzo) -> None:
        with client.credentials.with_streaming_response.delete(
            "credential_name",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            credential = response.parse()
            assert_matches_type(object, credential, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_path_params_delete(self, client: Hanzo) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `credential_name` but received ''"):
            client.credentials.with_raw_response.delete(
                "",
            )


class TestAsyncCredentials:
    parametrize = pytest.mark.parametrize("async_client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_create(self, async_client: AsyncHanzo) -> None:
        credential = await async_client.credentials.create(
            credential_info={},
            credential_name="credential_name",
        )
        assert_matches_type(object, credential, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncHanzo) -> None:
        credential = await async_client.credentials.create(
            credential_info={},
            credential_name="credential_name",
            credential_values={},
            model_id="model_id",
        )
        assert_matches_type(object, credential, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncHanzo) -> None:
        response = await async_client.credentials.with_raw_response.create(
            credential_info={},
            credential_name="credential_name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        credential = await response.parse()
        assert_matches_type(object, credential, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncHanzo) -> None:
        async with async_client.credentials.with_streaming_response.create(
            credential_info={},
            credential_name="credential_name",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            credential = await response.parse()
            assert_matches_type(object, credential, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_list(self, async_client: AsyncHanzo) -> None:
        credential = await async_client.credentials.list()
        assert_matches_type(object, credential, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncHanzo) -> None:
        response = await async_client.credentials.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        credential = await response.parse()
        assert_matches_type(object, credential, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncHanzo) -> None:
        async with async_client.credentials.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            credential = await response.parse()
            assert_matches_type(object, credential, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_delete(self, async_client: AsyncHanzo) -> None:
        credential = await async_client.credentials.delete(
            "credential_name",
        )
        assert_matches_type(object, credential, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncHanzo) -> None:
        response = await async_client.credentials.with_raw_response.delete(
            "credential_name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        credential = await response.parse()
        assert_matches_type(object, credential, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncHanzo) -> None:
        async with async_client.credentials.with_streaming_response.delete(
            "credential_name",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            credential = await response.parse()
            assert_matches_type(object, credential, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncHanzo) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `credential_name` but received ''"):
            await async_client.credentials.with_raw_response.delete(
                "",
            )
