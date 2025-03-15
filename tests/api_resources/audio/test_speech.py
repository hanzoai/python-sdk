# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from Hanzo_AI import HanzoAI, AsyncHanzoAI
from tests.utils import assert_matches_type

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestSpeech:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    def test_method_create(self, client: HanzoAI) -> None:
        speech = client.audio.speech.create()
        assert_matches_type(object, speech, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_create(self, client: HanzoAI) -> None:
        response = client.audio.speech.with_raw_response.create()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        speech = response.parse()
        assert_matches_type(object, speech, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_create(self, client: HanzoAI) -> None:
        with client.audio.speech.with_streaming_response.create() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            speech = response.parse()
            assert_matches_type(object, speech, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncSpeech:
    parametrize = pytest.mark.parametrize("async_client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_create(self, async_client: AsyncHanzoAI) -> None:
        speech = await async_client.audio.speech.create()
        assert_matches_type(object, speech, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncHanzoAI) -> None:
        response = await async_client.audio.speech.with_raw_response.create()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        speech = await response.parse()
        assert_matches_type(object, speech, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncHanzoAI) -> None:
        async with async_client.audio.speech.with_streaming_response.create() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            speech = await response.parse()
            assert_matches_type(object, speech, path=["response"])

        assert cast(Any, response.is_closed) is True
