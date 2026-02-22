# Hanzo AI SDK

from __future__ import annotations

from typing import Any, Dict

import httpx

from .._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .._base_client import make_request_options

__all__ = ["TokensResource", "AsyncTokensResource"]


class TokensResource(SyncAPIResource):
    """Blockchain token management."""

    @cached_property
    def with_raw_response(self) -> TokensResourceWithRawResponse:
        return TokensResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> TokensResourceWithStreamingResponse:
        return TokensResourceWithStreamingResponse(self)

    def list(
        self,
        *,
        network_id: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all tokens."""
        return self._get(
            "/network/tokens",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"network_id": network_id},
            ),
            cast_to=object,
        )

    def get(
        self,
        token_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a specific token."""
        return self._get(
            f"/network/tokens/{token_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def create(
        self,
        *,
        name: str,
        symbol: str,
        network_id: str,
        total_supply: str,
        decimals: int = 18,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a new token."""
        return self._post(
            "/network/tokens",
            body={
                "name": name,
                "symbol": symbol,
                "network_id": network_id,
                "total_supply": total_supply,
                "decimals": decimals,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def mint(
        self,
        token_id: str,
        *,
        to_address: str,
        amount: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Mint new tokens."""
        return self._post(
            f"/network/tokens/{token_id}/mint",
            body={"to_address": to_address, "amount": amount},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def burn(
        self,
        token_id: str,
        *,
        amount: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Burn tokens."""
        return self._post(
            f"/network/tokens/{token_id}/burn",
            body={"amount": amount},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def holders(
        self,
        token_id: str,
        *,
        limit: int | NotGiven = NOT_GIVEN,
        offset: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get token holders."""
        return self._get(
            f"/network/tokens/{token_id}/holders",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"limit": limit, "offset": offset},
            ),
            cast_to=object,
        )


class AsyncTokensResource(AsyncAPIResource):
    """Blockchain token management (async)."""

    @cached_property
    def with_raw_response(self) -> AsyncTokensResourceWithRawResponse:
        return AsyncTokensResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncTokensResourceWithStreamingResponse:
        return AsyncTokensResourceWithStreamingResponse(self)

    async def list(
        self,
        *,
        network_id: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            "/network/tokens",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"network_id": network_id},
            ),
            cast_to=object,
        )

    async def get(
        self,
        token_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/network/tokens/{token_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def create(
        self,
        *,
        name: str,
        symbol: str,
        network_id: str,
        total_supply: str,
        decimals: int = 18,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            "/network/tokens",
            body={
                "name": name,
                "symbol": symbol,
                "network_id": network_id,
                "total_supply": total_supply,
                "decimals": decimals,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def mint(
        self,
        token_id: str,
        *,
        to_address: str,
        amount: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            f"/network/tokens/{token_id}/mint",
            body={"to_address": to_address, "amount": amount},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def burn(
        self,
        token_id: str,
        *,
        amount: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            f"/network/tokens/{token_id}/burn",
            body={"amount": amount},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def holders(
        self,
        token_id: str,
        *,
        limit: int | NotGiven = NOT_GIVEN,
        offset: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/network/tokens/{token_id}/holders",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"limit": limit, "offset": offset},
            ),
            cast_to=object,
        )


class TokensResourceWithRawResponse:
    def __init__(self, tokens: TokensResource) -> None:
        self._tokens = tokens
        self.list = to_raw_response_wrapper(tokens.list)
        self.get = to_raw_response_wrapper(tokens.get)
        self.create = to_raw_response_wrapper(tokens.create)
        self.mint = to_raw_response_wrapper(tokens.mint)
        self.burn = to_raw_response_wrapper(tokens.burn)
        self.holders = to_raw_response_wrapper(tokens.holders)


class AsyncTokensResourceWithRawResponse:
    def __init__(self, tokens: AsyncTokensResource) -> None:
        self._tokens = tokens
        self.list = async_to_raw_response_wrapper(tokens.list)
        self.get = async_to_raw_response_wrapper(tokens.get)
        self.create = async_to_raw_response_wrapper(tokens.create)
        self.mint = async_to_raw_response_wrapper(tokens.mint)
        self.burn = async_to_raw_response_wrapper(tokens.burn)
        self.holders = async_to_raw_response_wrapper(tokens.holders)


class TokensResourceWithStreamingResponse:
    def __init__(self, tokens: TokensResource) -> None:
        self._tokens = tokens
        self.list = to_streamed_response_wrapper(tokens.list)
        self.get = to_streamed_response_wrapper(tokens.get)
        self.create = to_streamed_response_wrapper(tokens.create)
        self.mint = to_streamed_response_wrapper(tokens.mint)
        self.burn = to_streamed_response_wrapper(tokens.burn)
        self.holders = to_streamed_response_wrapper(tokens.holders)


class AsyncTokensResourceWithStreamingResponse:
    def __init__(self, tokens: AsyncTokensResource) -> None:
        self._tokens = tokens
        self.list = async_to_streamed_response_wrapper(tokens.list)
        self.get = async_to_streamed_response_wrapper(tokens.get)
        self.create = async_to_streamed_response_wrapper(tokens.create)
        self.mint = async_to_streamed_response_wrapper(tokens.mint)
        self.burn = async_to_streamed_response_wrapper(tokens.burn)
        self.holders = async_to_streamed_response_wrapper(tokens.holders)
