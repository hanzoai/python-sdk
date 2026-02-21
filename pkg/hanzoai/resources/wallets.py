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

__all__ = ["WalletsResource", "AsyncWalletsResource"]


class WalletsResource(SyncAPIResource):
    """Blockchain wallet management."""

    @cached_property
    def with_raw_response(self) -> WalletsResourceWithRawResponse:
        return WalletsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> WalletsResourceWithStreamingResponse:
        return WalletsResourceWithStreamingResponse(self)

    def list(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all wallets."""
        return self._get(
            "/network/wallets",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def get(
        self,
        wallet_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a specific wallet."""
        return self._get(
            f"/network/wallets/{wallet_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def create(
        self,
        *,
        name: str,
        network_id: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a new wallet."""
        return self._post(
            "/network/wallets",
            body={"name": name, "network_id": network_id},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def delete(
        self,
        wallet_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a wallet."""
        return self._delete(
            f"/network/wallets/{wallet_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def balance(
        self,
        wallet_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get wallet balance."""
        return self._get(
            f"/network/wallets/{wallet_id}/balance",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def transactions(
        self,
        wallet_id: str,
        *,
        limit: int | NotGiven = NOT_GIVEN,
        offset: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get wallet transactions."""
        return self._get(
            f"/network/wallets/{wallet_id}/transactions",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"limit": limit, "offset": offset},
            ),
            cast_to=object,
        )

    def transfer(
        self,
        wallet_id: str,
        *,
        to_address: str,
        amount: str,
        token_id: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Transfer from wallet."""
        return self._post(
            f"/network/wallets/{wallet_id}/transfer",
            body={"to_address": to_address, "amount": amount, "token_id": token_id},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def sign(
        self,
        wallet_id: str,
        *,
        message: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Sign a message with wallet."""
        return self._post(
            f"/network/wallets/{wallet_id}/sign",
            body={"message": message},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class AsyncWalletsResource(AsyncAPIResource):
    """Blockchain wallet management (async)."""

    @cached_property
    def with_raw_response(self) -> AsyncWalletsResourceWithRawResponse:
        return AsyncWalletsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncWalletsResourceWithStreamingResponse:
        return AsyncWalletsResourceWithStreamingResponse(self)

    async def list(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            "/network/wallets",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def get(
        self,
        wallet_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/network/wallets/{wallet_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def create(
        self,
        *,
        name: str,
        network_id: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            "/network/wallets",
            body={"name": name, "network_id": network_id},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def delete(
        self,
        wallet_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._delete(
            f"/network/wallets/{wallet_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def balance(
        self,
        wallet_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/network/wallets/{wallet_id}/balance",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def transactions(
        self,
        wallet_id: str,
        *,
        limit: int | NotGiven = NOT_GIVEN,
        offset: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/network/wallets/{wallet_id}/transactions",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"limit": limit, "offset": offset},
            ),
            cast_to=object,
        )

    async def transfer(
        self,
        wallet_id: str,
        *,
        to_address: str,
        amount: str,
        token_id: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            f"/network/wallets/{wallet_id}/transfer",
            body={"to_address": to_address, "amount": amount, "token_id": token_id},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def sign(
        self,
        wallet_id: str,
        *,
        message: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            f"/network/wallets/{wallet_id}/sign",
            body={"message": message},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class WalletsResourceWithRawResponse:
    def __init__(self, wallets: WalletsResource) -> None:
        self._wallets = wallets
        self.list = to_raw_response_wrapper(wallets.list)
        self.get = to_raw_response_wrapper(wallets.get)
        self.create = to_raw_response_wrapper(wallets.create)
        self.delete = to_raw_response_wrapper(wallets.delete)
        self.balance = to_raw_response_wrapper(wallets.balance)
        self.transactions = to_raw_response_wrapper(wallets.transactions)
        self.transfer = to_raw_response_wrapper(wallets.transfer)
        self.sign = to_raw_response_wrapper(wallets.sign)


class AsyncWalletsResourceWithRawResponse:
    def __init__(self, wallets: AsyncWalletsResource) -> None:
        self._wallets = wallets
        self.list = async_to_raw_response_wrapper(wallets.list)
        self.get = async_to_raw_response_wrapper(wallets.get)
        self.create = async_to_raw_response_wrapper(wallets.create)
        self.delete = async_to_raw_response_wrapper(wallets.delete)
        self.balance = async_to_raw_response_wrapper(wallets.balance)
        self.transactions = async_to_raw_response_wrapper(wallets.transactions)
        self.transfer = async_to_raw_response_wrapper(wallets.transfer)
        self.sign = async_to_raw_response_wrapper(wallets.sign)


class WalletsResourceWithStreamingResponse:
    def __init__(self, wallets: WalletsResource) -> None:
        self._wallets = wallets
        self.list = to_streamed_response_wrapper(wallets.list)
        self.get = to_streamed_response_wrapper(wallets.get)
        self.create = to_streamed_response_wrapper(wallets.create)
        self.delete = to_streamed_response_wrapper(wallets.delete)
        self.balance = to_streamed_response_wrapper(wallets.balance)
        self.transactions = to_streamed_response_wrapper(wallets.transactions)
        self.transfer = to_streamed_response_wrapper(wallets.transfer)
        self.sign = to_streamed_response_wrapper(wallets.sign)


class AsyncWalletsResourceWithStreamingResponse:
    def __init__(self, wallets: AsyncWalletsResource) -> None:
        self._wallets = wallets
        self.list = async_to_streamed_response_wrapper(wallets.list)
        self.get = async_to_streamed_response_wrapper(wallets.get)
        self.create = async_to_streamed_response_wrapper(wallets.create)
        self.delete = async_to_streamed_response_wrapper(wallets.delete)
        self.balance = async_to_streamed_response_wrapper(wallets.balance)
        self.transactions = async_to_streamed_response_wrapper(wallets.transactions)
        self.transfer = async_to_streamed_response_wrapper(wallets.transfer)
        self.sign = async_to_streamed_response_wrapper(wallets.sign)
