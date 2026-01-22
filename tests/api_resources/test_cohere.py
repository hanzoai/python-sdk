# # Hanzo AI SDK Tests

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from hanzoai import Hanzo, AsyncHanzo
from tests.utils import assert_matches_type

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestCohere:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_create(self, client: Hanzo) -> None:
        cohere = client.cohere.create(
            "endpoint",
        )
        assert_matches_type(object, cohere, path=["response"])

    @parametrize
    def test_raw_response_create(self, client: Hanzo) -> None:
        response = client.cohere.with_raw_response.create(
            "endpoint",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Hanzo-Lang") == "python"
        cohere = response.parse()
        assert_matches_type(object, cohere, path=["response"])

    @parametrize
    def test_streaming_response_create(self, client: Hanzo) -> None:
        with client.cohere.with_streaming_response.create(
            "endpoint",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Hanzo-Lang") == "python"

            cohere = response.parse()
            assert_matches_type(object, cohere, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_create(self, client: Hanzo) -> None:
        with pytest.raises(
            ValueError,
            match=r"Expected a non-empty value for `endpoint` but received ''",
        ):
            client.cohere.with_raw_response.create(
                "",
            )

    @parametrize
    def test_method_retrieve(self, client: Hanzo) -> None:
        cohere = client.cohere.retrieve(
            "endpoint",
        )
        assert_matches_type(object, cohere, path=["response"])

    @parametrize
    def test_raw_response_retrieve(self, client: Hanzo) -> None:
        response = client.cohere.with_raw_response.retrieve(
            "endpoint",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Hanzo-Lang") == "python"
        cohere = response.parse()
        assert_matches_type(object, cohere, path=["response"])

    @parametrize
    def test_streaming_response_retrieve(self, client: Hanzo) -> None:
        with client.cohere.with_streaming_response.retrieve(
            "endpoint",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Hanzo-Lang") == "python"

            cohere = response.parse()
            assert_matches_type(object, cohere, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_retrieve(self, client: Hanzo) -> None:
        with pytest.raises(
            ValueError,
            match=r"Expected a non-empty value for `endpoint` but received ''",
        ):
            client.cohere.with_raw_response.retrieve(
                "",
            )

    @parametrize
    def test_method_update(self, client: Hanzo) -> None:
        cohere = client.cohere.update(
            "endpoint",
        )
        assert_matches_type(object, cohere, path=["response"])

    @parametrize
    def test_raw_response_update(self, client: Hanzo) -> None:
        response = client.cohere.with_raw_response.update(
            "endpoint",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Hanzo-Lang") == "python"
        cohere = response.parse()
        assert_matches_type(object, cohere, path=["response"])

    @parametrize
    def test_streaming_response_update(self, client: Hanzo) -> None:
        with client.cohere.with_streaming_response.update(
            "endpoint",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Hanzo-Lang") == "python"

            cohere = response.parse()
            assert_matches_type(object, cohere, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_update(self, client: Hanzo) -> None:
        with pytest.raises(
            ValueError,
            match=r"Expected a non-empty value for `endpoint` but received ''",
        ):
            client.cohere.with_raw_response.update(
                "",
            )

    @parametrize
    def test_method_delete(self, client: Hanzo) -> None:
        cohere = client.cohere.delete(
            "endpoint",
        )
        assert_matches_type(object, cohere, path=["response"])

    @parametrize
    def test_raw_response_delete(self, client: Hanzo) -> None:
        response = client.cohere.with_raw_response.delete(
            "endpoint",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Hanzo-Lang") == "python"
        cohere = response.parse()
        assert_matches_type(object, cohere, path=["response"])

    @parametrize
    def test_streaming_response_delete(self, client: Hanzo) -> None:
        with client.cohere.with_streaming_response.delete(
            "endpoint",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Hanzo-Lang") == "python"

            cohere = response.parse()
            assert_matches_type(object, cohere, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_delete(self, client: Hanzo) -> None:
        with pytest.raises(
            ValueError,
            match=r"Expected a non-empty value for `endpoint` but received ''",
        ):
            client.cohere.with_raw_response.delete(
                "",
            )

    @parametrize
    def test_method_modify(self, client: Hanzo) -> None:
        cohere = client.cohere.modify(
            "endpoint",
        )
        assert_matches_type(object, cohere, path=["response"])

    @parametrize
    def test_raw_response_modify(self, client: Hanzo) -> None:
        response = client.cohere.with_raw_response.modify(
            "endpoint",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Hanzo-Lang") == "python"
        cohere = response.parse()
        assert_matches_type(object, cohere, path=["response"])

    @parametrize
    def test_streaming_response_modify(self, client: Hanzo) -> None:
        with client.cohere.with_streaming_response.modify(
            "endpoint",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Hanzo-Lang") == "python"

            cohere = response.parse()
            assert_matches_type(object, cohere, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_modify(self, client: Hanzo) -> None:
        with pytest.raises(
            ValueError,
            match=r"Expected a non-empty value for `endpoint` but received ''",
        ):
            client.cohere.with_raw_response.modify(
                "",
            )


class TestAsyncCohere:
    parametrize = pytest.mark.parametrize("async_client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    async def test_method_create(self, async_client: AsyncHanzo) -> None:
        cohere = await async_client.cohere.create(
            "endpoint",
        )
        assert_matches_type(object, cohere, path=["response"])

    @parametrize
    async def test_raw_response_create(self, async_client: AsyncHanzo) -> None:
        response = await async_client.cohere.with_raw_response.create(
            "endpoint",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Hanzo-Lang") == "python"
        cohere = await response.parse()
        assert_matches_type(object, cohere, path=["response"])

    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncHanzo) -> None:
        async with async_client.cohere.with_streaming_response.create(
            "endpoint",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Hanzo-Lang") == "python"

            cohere = await response.parse()
            assert_matches_type(object, cohere, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_create(self, async_client: AsyncHanzo) -> None:
        with pytest.raises(
            ValueError,
            match=r"Expected a non-empty value for `endpoint` but received ''",
        ):
            await async_client.cohere.with_raw_response.create(
                "",
            )

    @parametrize
    async def test_method_retrieve(self, async_client: AsyncHanzo) -> None:
        cohere = await async_client.cohere.retrieve(
            "endpoint",
        )
        assert_matches_type(object, cohere, path=["response"])

    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncHanzo) -> None:
        response = await async_client.cohere.with_raw_response.retrieve(
            "endpoint",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Hanzo-Lang") == "python"
        cohere = await response.parse()
        assert_matches_type(object, cohere, path=["response"])

    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncHanzo) -> None:
        async with async_client.cohere.with_streaming_response.retrieve(
            "endpoint",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Hanzo-Lang") == "python"

            cohere = await response.parse()
            assert_matches_type(object, cohere, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncHanzo) -> None:
        with pytest.raises(
            ValueError,
            match=r"Expected a non-empty value for `endpoint` but received ''",
        ):
            await async_client.cohere.with_raw_response.retrieve(
                "",
            )

    @parametrize
    async def test_method_update(self, async_client: AsyncHanzo) -> None:
        cohere = await async_client.cohere.update(
            "endpoint",
        )
        assert_matches_type(object, cohere, path=["response"])

    @parametrize
    async def test_raw_response_update(self, async_client: AsyncHanzo) -> None:
        response = await async_client.cohere.with_raw_response.update(
            "endpoint",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Hanzo-Lang") == "python"
        cohere = await response.parse()
        assert_matches_type(object, cohere, path=["response"])

    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncHanzo) -> None:
        async with async_client.cohere.with_streaming_response.update(
            "endpoint",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Hanzo-Lang") == "python"

            cohere = await response.parse()
            assert_matches_type(object, cohere, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_update(self, async_client: AsyncHanzo) -> None:
        with pytest.raises(
            ValueError,
            match=r"Expected a non-empty value for `endpoint` but received ''",
        ):
            await async_client.cohere.with_raw_response.update(
                "",
            )

    @parametrize
    async def test_method_delete(self, async_client: AsyncHanzo) -> None:
        cohere = await async_client.cohere.delete(
            "endpoint",
        )
        assert_matches_type(object, cohere, path=["response"])

    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncHanzo) -> None:
        response = await async_client.cohere.with_raw_response.delete(
            "endpoint",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Hanzo-Lang") == "python"
        cohere = await response.parse()
        assert_matches_type(object, cohere, path=["response"])

    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncHanzo) -> None:
        async with async_client.cohere.with_streaming_response.delete(
            "endpoint",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Hanzo-Lang") == "python"

            cohere = await response.parse()
            assert_matches_type(object, cohere, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_delete(self, async_client: AsyncHanzo) -> None:
        with pytest.raises(
            ValueError,
            match=r"Expected a non-empty value for `endpoint` but received ''",
        ):
            await async_client.cohere.with_raw_response.delete(
                "",
            )

    @parametrize
    async def test_method_modify(self, async_client: AsyncHanzo) -> None:
        cohere = await async_client.cohere.modify(
            "endpoint",
        )
        assert_matches_type(object, cohere, path=["response"])

    @parametrize
    async def test_raw_response_modify(self, async_client: AsyncHanzo) -> None:
        response = await async_client.cohere.with_raw_response.modify(
            "endpoint",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Hanzo-Lang") == "python"
        cohere = await response.parse()
        assert_matches_type(object, cohere, path=["response"])

    @parametrize
    async def test_streaming_response_modify(self, async_client: AsyncHanzo) -> None:
        async with async_client.cohere.with_streaming_response.modify(
            "endpoint",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Hanzo-Lang") == "python"

            cohere = await response.parse()
            assert_matches_type(object, cohere, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_modify(self, async_client: AsyncHanzo) -> None:
        with pytest.raises(
            ValueError,
            match=r"Expected a non-empty value for `endpoint` but received ''",
        ):
            await async_client.cohere.with_raw_response.modify(
                "",
            )
