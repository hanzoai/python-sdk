# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from Hanzo_AI import HanzoAI, AsyncHanzoAI
from tests.utils import assert_matches_type

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestCredentials:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    def test_method_create(self, client: HanzoAI) -> None:
        credential = client.credentials.create(
            credential_info={},
            credential_name="credential_name",
            credential_values={},
        )
        assert_matches_type(object, credential, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_create(self, client: HanzoAI) -> None:
        response = client.credentials.with_raw_response.create(
            credential_info={},
            credential_name="credential_name",
            credential_values={},
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        credential = response.parse()
        assert_matches_type(object, credential, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_create(self, client: HanzoAI) -> None:
        with client.credentials.with_streaming_response.create(
            credential_info={},
            credential_name="credential_name",
            credential_values={},
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            credential = response.parse()
            assert_matches_type(object, credential, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_retrieve(self, client: HanzoAI) -> None:
        credential = client.credentials.retrieve(
            "credential_name",
        )
        assert_matches_type(object, credential, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_retrieve(self, client: HanzoAI) -> None:
        response = client.credentials.with_raw_response.retrieve(
            "credential_name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        credential = response.parse()
        assert_matches_type(object, credential, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_retrieve(self, client: HanzoAI) -> None:
        with client.credentials.with_streaming_response.retrieve(
            "credential_name",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            credential = response.parse()
            assert_matches_type(object, credential, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_path_params_retrieve(self, client: HanzoAI) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `credential_name` but received ''"):
            client.credentials.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip()
    @parametrize
    def test_method_update(self, client: HanzoAI) -> None:
        credential = client.credentials.update(
            path_credential_name="credential_name",
            credential_info={},
            body_credential_name="credential_name",
            credential_values={},
        )
        assert_matches_type(object, credential, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_update(self, client: HanzoAI) -> None:
        response = client.credentials.with_raw_response.update(
            path_credential_name="credential_name",
            credential_info={},
            body_credential_name="credential_name",
            credential_values={},
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        credential = response.parse()
        assert_matches_type(object, credential, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_update(self, client: HanzoAI) -> None:
        with client.credentials.with_streaming_response.update(
            path_credential_name="credential_name",
            credential_info={},
            body_credential_name="credential_name",
            credential_values={},
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            credential = response.parse()
            assert_matches_type(object, credential, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_path_params_update(self, client: HanzoAI) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `path_credential_name` but received ''"):
            client.credentials.with_raw_response.update(
                path_credential_name="",
                credential_info={},
                body_credential_name="",
                credential_values={},
            )

    @pytest.mark.skip()
    @parametrize
    def test_method_list(self, client: HanzoAI) -> None:
        credential = client.credentials.list()
        assert_matches_type(object, credential, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_list(self, client: HanzoAI) -> None:
        response = client.credentials.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        credential = response.parse()
        assert_matches_type(object, credential, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_list(self, client: HanzoAI) -> None:
        with client.credentials.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            credential = response.parse()
            assert_matches_type(object, credential, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_delete(self, client: HanzoAI) -> None:
        credential = client.credentials.delete(
            "credential_name",
        )
        assert_matches_type(object, credential, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_delete(self, client: HanzoAI) -> None:
        response = client.credentials.with_raw_response.delete(
            "credential_name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        credential = response.parse()
        assert_matches_type(object, credential, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_delete(self, client: HanzoAI) -> None:
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
    def test_path_params_delete(self, client: HanzoAI) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `credential_name` but received ''"):
            client.credentials.with_raw_response.delete(
                "",
            )


class TestAsyncCredentials:
    parametrize = pytest.mark.parametrize("async_client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_create(self, async_client: AsyncHanzoAI) -> None:
        credential = await async_client.credentials.create(
            credential_info={},
            credential_name="credential_name",
            credential_values={},
        )
        assert_matches_type(object, credential, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncHanzoAI) -> None:
        response = await async_client.credentials.with_raw_response.create(
            credential_info={},
            credential_name="credential_name",
            credential_values={},
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        credential = await response.parse()
        assert_matches_type(object, credential, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncHanzoAI) -> None:
        async with async_client.credentials.with_streaming_response.create(
            credential_info={},
            credential_name="credential_name",
            credential_values={},
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            credential = await response.parse()
            assert_matches_type(object, credential, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncHanzoAI) -> None:
        credential = await async_client.credentials.retrieve(
            "credential_name",
        )
        assert_matches_type(object, credential, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncHanzoAI) -> None:
        response = await async_client.credentials.with_raw_response.retrieve(
            "credential_name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        credential = await response.parse()
        assert_matches_type(object, credential, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncHanzoAI) -> None:
        async with async_client.credentials.with_streaming_response.retrieve(
            "credential_name",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            credential = await response.parse()
            assert_matches_type(object, credential, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncHanzoAI) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `credential_name` but received ''"):
            await async_client.credentials.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip()
    @parametrize
    async def test_method_update(self, async_client: AsyncHanzoAI) -> None:
        credential = await async_client.credentials.update(
            path_credential_name="credential_name",
            credential_info={},
            body_credential_name="credential_name",
            credential_values={},
        )
        assert_matches_type(object, credential, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_update(self, async_client: AsyncHanzoAI) -> None:
        response = await async_client.credentials.with_raw_response.update(
            path_credential_name="credential_name",
            credential_info={},
            body_credential_name="credential_name",
            credential_values={},
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        credential = await response.parse()
        assert_matches_type(object, credential, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncHanzoAI) -> None:
        async with async_client.credentials.with_streaming_response.update(
            path_credential_name="credential_name",
            credential_info={},
            body_credential_name="credential_name",
            credential_values={},
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            credential = await response.parse()
            assert_matches_type(object, credential, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_path_params_update(self, async_client: AsyncHanzoAI) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `path_credential_name` but received ''"):
            await async_client.credentials.with_raw_response.update(
                path_credential_name="",
                credential_info={},
                body_credential_name="",
                credential_values={},
            )

    @pytest.mark.skip()
    @parametrize
    async def test_method_list(self, async_client: AsyncHanzoAI) -> None:
        credential = await async_client.credentials.list()
        assert_matches_type(object, credential, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncHanzoAI) -> None:
        response = await async_client.credentials.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        credential = await response.parse()
        assert_matches_type(object, credential, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncHanzoAI) -> None:
        async with async_client.credentials.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            credential = await response.parse()
            assert_matches_type(object, credential, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_delete(self, async_client: AsyncHanzoAI) -> None:
        credential = await async_client.credentials.delete(
            "credential_name",
        )
        assert_matches_type(object, credential, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncHanzoAI) -> None:
        response = await async_client.credentials.with_raw_response.delete(
            "credential_name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        credential = await response.parse()
        assert_matches_type(object, credential, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncHanzoAI) -> None:
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
    async def test_path_params_delete(self, async_client: AsyncHanzoAI) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `credential_name` but received ''"):
            await async_client.credentials.with_raw_response.delete(
                "",
            )
