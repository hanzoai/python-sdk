# Hanzo AI SDK

from __future__ import annotations

from typing import Any, Dict, List

import httpx

from .._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._base_client import make_request_options


class ChainResource(SyncAPIResource):
    """Blockchain chain operations and status."""

    @cached_property
    def with_raw_response(self) -> ChainResourceWithRawResponse:
        return ChainResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ChainResourceWithStreamingResponse:
        return ChainResourceWithStreamingResponse(self)

    def status(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get chain status."""
        return self._get(
            "/chain/status",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def rpc(
        self,
        *,
        method: str,
        params: List[Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Execute RPC call."""
        return self._post(
            "/chain/rpc",
            body={"method": method, "params": params},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def validators(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List validators."""
        return self._get(
            "/chain/validators",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def params(
        self,
        param_name: str | NotGiven = NOT_GIVEN,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get chain parameters."""
        return self._get(
            "/chain/params",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"param_name": param_name},
            ),
            cast_to=object,
        )

    def block(
        self,
        block_number: int | str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get block by number."""
        return self._get(
            f"/chain/blocks/{block_number}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def transaction(
        self,
        tx_hash: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get transaction by hash."""
        return self._get(
            f"/chain/tx/{tx_hash}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class AsyncChainResource(AsyncAPIResource):
    """Blockchain chain operations and status."""

    @cached_property
    def with_raw_response(self) -> AsyncChainResourceWithRawResponse:
        return AsyncChainResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncChainResourceWithStreamingResponse:
        return AsyncChainResourceWithStreamingResponse(self)

    async def status(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get chain status."""
        return await self._get(
            "/chain/status",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def rpc(
        self,
        *,
        method: str,
        params: List[Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Execute RPC call."""
        return await self._post(
            "/chain/rpc",
            body={"method": method, "params": params},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def validators(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List validators."""
        return await self._get(
            "/chain/validators",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def params(
        self,
        param_name: str | NotGiven = NOT_GIVEN,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get chain parameters."""
        return await self._get(
            "/chain/params",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"param_name": param_name},
            ),
            cast_to=object,
        )

    async def block(
        self,
        block_number: int | str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get block by number."""
        return await self._get(
            f"/chain/blocks/{block_number}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def transaction(
        self,
        tx_hash: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get transaction by hash."""
        return await self._get(
            f"/chain/tx/{tx_hash}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class ChainResourceWithRawResponse:
    def __init__(self, chain: ChainResource) -> None:
        self._chain = chain


class AsyncChainResourceWithRawResponse:
    def __init__(self, chain: AsyncChainResource) -> None:
        self._chain = chain


class ChainResourceWithStreamingResponse:
    def __init__(self, chain: ChainResource) -> None:
        self._chain = chain


class AsyncChainResourceWithStreamingResponse:
    def __init__(self, chain: AsyncChainResource) -> None:
        self._chain = chain
