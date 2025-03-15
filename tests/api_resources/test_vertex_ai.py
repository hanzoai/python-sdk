# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from hanzoai import Hanzo, AsyncHanzo
from tests.utils import assert_matches_type

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestVertexAI:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    def test_method_create(self, client: Hanzo) -> None:
        vertex_ai = client.vertex_ai.create(
            "endpoint",
        )
        assert_matches_type(object, vertex_ai, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_create(self, client: Hanzo) -> None:
        response = client.vertex_ai.with_raw_response.create(
            "endpoint",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        vertex_ai = response.parse()
        assert_matches_type(object, vertex_ai, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_create(self, client: Hanzo) -> None:
        with client.vertex_ai.with_streaming_response.create(
            "endpoint",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            vertex_ai = response.parse()
            assert_matches_type(object, vertex_ai, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_path_params_create(self, client: Hanzo) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `endpoint` but received ''"):
            client.vertex_ai.with_raw_response.create(
                "",
            )

    @pytest.mark.skip()
    @parametrize
    def test_method_retrieve(self, client: Hanzo) -> None:
        vertex_ai = client.vertex_ai.retrieve(
            "endpoint",
        )
        assert_matches_type(object, vertex_ai, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_retrieve(self, client: Hanzo) -> None:
        response = client.vertex_ai.with_raw_response.retrieve(
            "endpoint",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        vertex_ai = response.parse()
        assert_matches_type(object, vertex_ai, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_retrieve(self, client: Hanzo) -> None:
        with client.vertex_ai.with_streaming_response.retrieve(
            "endpoint",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            vertex_ai = response.parse()
            assert_matches_type(object, vertex_ai, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_path_params_retrieve(self, client: Hanzo) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `endpoint` but received ''"):
            client.vertex_ai.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip()
    @parametrize
    def test_method_update(self, client: Hanzo) -> None:
        vertex_ai = client.vertex_ai.update(
            "endpoint",
        )
        assert_matches_type(object, vertex_ai, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_update(self, client: Hanzo) -> None:
        response = client.vertex_ai.with_raw_response.update(
            "endpoint",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        vertex_ai = response.parse()
        assert_matches_type(object, vertex_ai, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_update(self, client: Hanzo) -> None:
        with client.vertex_ai.with_streaming_response.update(
            "endpoint",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            vertex_ai = response.parse()
            assert_matches_type(object, vertex_ai, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_path_params_update(self, client: Hanzo) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `endpoint` but received ''"):
            client.vertex_ai.with_raw_response.update(
                "",
            )

    @pytest.mark.skip()
    @parametrize
    def test_method_delete(self, client: Hanzo) -> None:
        vertex_ai = client.vertex_ai.delete(
            "endpoint",
        )
        assert_matches_type(object, vertex_ai, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_delete(self, client: Hanzo) -> None:
        response = client.vertex_ai.with_raw_response.delete(
            "endpoint",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        vertex_ai = response.parse()
        assert_matches_type(object, vertex_ai, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_delete(self, client: Hanzo) -> None:
        with client.vertex_ai.with_streaming_response.delete(
            "endpoint",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            vertex_ai = response.parse()
            assert_matches_type(object, vertex_ai, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_path_params_delete(self, client: Hanzo) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `endpoint` but received ''"):
            client.vertex_ai.with_raw_response.delete(
                "",
            )

    @pytest.mark.skip()
    @parametrize
    def test_method_patch(self, client: Hanzo) -> None:
        vertex_ai = client.vertex_ai.patch(
            "endpoint",
        )
        assert_matches_type(object, vertex_ai, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_patch(self, client: Hanzo) -> None:
        response = client.vertex_ai.with_raw_response.patch(
            "endpoint",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        vertex_ai = response.parse()
        assert_matches_type(object, vertex_ai, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_patch(self, client: Hanzo) -> None:
        with client.vertex_ai.with_streaming_response.patch(
            "endpoint",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            vertex_ai = response.parse()
            assert_matches_type(object, vertex_ai, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_path_params_patch(self, client: Hanzo) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `endpoint` but received ''"):
            client.vertex_ai.with_raw_response.patch(
                "",
            )


class TestAsyncVertexAI:
    parametrize = pytest.mark.parametrize("async_client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_create(self, async_client: AsyncHanzo) -> None:
        vertex_ai = await async_client.vertex_ai.create(
            "endpoint",
        )
        assert_matches_type(object, vertex_ai, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncHanzo) -> None:
        response = await async_client.vertex_ai.with_raw_response.create(
            "endpoint",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        vertex_ai = await response.parse()
        assert_matches_type(object, vertex_ai, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncHanzo) -> None:
        async with async_client.vertex_ai.with_streaming_response.create(
            "endpoint",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            vertex_ai = await response.parse()
            assert_matches_type(object, vertex_ai, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_path_params_create(self, async_client: AsyncHanzo) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `endpoint` but received ''"):
            await async_client.vertex_ai.with_raw_response.create(
                "",
            )

    @pytest.mark.skip()
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncHanzo) -> None:
        vertex_ai = await async_client.vertex_ai.retrieve(
            "endpoint",
        )
        assert_matches_type(object, vertex_ai, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncHanzo) -> None:
        response = await async_client.vertex_ai.with_raw_response.retrieve(
            "endpoint",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        vertex_ai = await response.parse()
        assert_matches_type(object, vertex_ai, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncHanzo) -> None:
        async with async_client.vertex_ai.with_streaming_response.retrieve(
            "endpoint",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            vertex_ai = await response.parse()
            assert_matches_type(object, vertex_ai, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncHanzo) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `endpoint` but received ''"):
            await async_client.vertex_ai.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip()
    @parametrize
    async def test_method_update(self, async_client: AsyncHanzo) -> None:
        vertex_ai = await async_client.vertex_ai.update(
            "endpoint",
        )
        assert_matches_type(object, vertex_ai, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_update(self, async_client: AsyncHanzo) -> None:
        response = await async_client.vertex_ai.with_raw_response.update(
            "endpoint",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        vertex_ai = await response.parse()
        assert_matches_type(object, vertex_ai, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncHanzo) -> None:
        async with async_client.vertex_ai.with_streaming_response.update(
            "endpoint",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            vertex_ai = await response.parse()
            assert_matches_type(object, vertex_ai, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_path_params_update(self, async_client: AsyncHanzo) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `endpoint` but received ''"):
            await async_client.vertex_ai.with_raw_response.update(
                "",
            )

    @pytest.mark.skip()
    @parametrize
    async def test_method_delete(self, async_client: AsyncHanzo) -> None:
        vertex_ai = await async_client.vertex_ai.delete(
            "endpoint",
        )
        assert_matches_type(object, vertex_ai, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncHanzo) -> None:
        response = await async_client.vertex_ai.with_raw_response.delete(
            "endpoint",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        vertex_ai = await response.parse()
        assert_matches_type(object, vertex_ai, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncHanzo) -> None:
        async with async_client.vertex_ai.with_streaming_response.delete(
            "endpoint",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            vertex_ai = await response.parse()
            assert_matches_type(object, vertex_ai, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncHanzo) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `endpoint` but received ''"):
            await async_client.vertex_ai.with_raw_response.delete(
                "",
            )

    @pytest.mark.skip()
    @parametrize
    async def test_method_patch(self, async_client: AsyncHanzo) -> None:
        vertex_ai = await async_client.vertex_ai.patch(
            "endpoint",
        )
        assert_matches_type(object, vertex_ai, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_patch(self, async_client: AsyncHanzo) -> None:
        response = await async_client.vertex_ai.with_raw_response.patch(
            "endpoint",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        vertex_ai = await response.parse()
        assert_matches_type(object, vertex_ai, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_patch(self, async_client: AsyncHanzo) -> None:
        async with async_client.vertex_ai.with_streaming_response.patch(
            "endpoint",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            vertex_ai = await response.parse()
            assert_matches_type(object, vertex_ai, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_path_params_patch(self, async_client: AsyncHanzo) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `endpoint` but received ''"):
            await async_client.vertex_ai.with_raw_response.patch(
                "",
            )
