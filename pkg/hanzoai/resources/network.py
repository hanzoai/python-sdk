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

__all__ = ["NetworkResource", "AsyncNetworkResource"]


class NetworkResource(SyncAPIResource):
    """Blockchain network management."""

    @cached_property
    def with_raw_response(self) -> NetworkResourceWithRawResponse:
        return NetworkResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> NetworkResourceWithStreamingResponse:
        return NetworkResourceWithStreamingResponse(self)

    def list(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all networks."""
        return self._get(
            "/network/networks",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def get(
        self,
        network_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a specific network."""
        return self._get(
            f"/network/networks/{network_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def status(
        self,
        network_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get network status."""
        return self._get(
            f"/network/networks/{network_id}/status",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def stats(
        self,
        network_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get network statistics."""
        return self._get(
            f"/network/networks/{network_id}/stats",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def peers(
        self,
        network_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List network peers."""
        return self._get(
            f"/network/networks/{network_id}/peers",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class AsyncNetworkResource(AsyncAPIResource):
    """Blockchain network management (async)."""

    @cached_property
    def with_raw_response(self) -> AsyncNetworkResourceWithRawResponse:
        return AsyncNetworkResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncNetworkResourceWithStreamingResponse:
        return AsyncNetworkResourceWithStreamingResponse(self)

    async def list(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            "/network/networks",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def get(
        self,
        network_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/network/networks/{network_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def status(
        self,
        network_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/network/networks/{network_id}/status",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def stats(
        self,
        network_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/network/networks/{network_id}/stats",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def peers(
        self,
        network_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/network/networks/{network_id}/peers",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class NetworkResourceWithRawResponse:
    def __init__(self, network: NetworkResource) -> None:
        self._network = network
        self.list = to_raw_response_wrapper(network.list)
        self.get = to_raw_response_wrapper(network.get)
        self.status = to_raw_response_wrapper(network.status)
        self.stats = to_raw_response_wrapper(network.stats)
        self.peers = to_raw_response_wrapper(network.peers)


class AsyncNetworkResourceWithRawResponse:
    def __init__(self, network: AsyncNetworkResource) -> None:
        self._network = network
        self.list = async_to_raw_response_wrapper(network.list)
        self.get = async_to_raw_response_wrapper(network.get)
        self.status = async_to_raw_response_wrapper(network.status)
        self.stats = async_to_raw_response_wrapper(network.stats)
        self.peers = async_to_raw_response_wrapper(network.peers)


class NetworkResourceWithStreamingResponse:
    def __init__(self, network: NetworkResource) -> None:
        self._network = network
        self.list = to_streamed_response_wrapper(network.list)
        self.get = to_streamed_response_wrapper(network.get)
        self.status = to_streamed_response_wrapper(network.status)
        self.stats = to_streamed_response_wrapper(network.stats)
        self.peers = to_streamed_response_wrapper(network.peers)


class AsyncNetworkResourceWithStreamingResponse:
    def __init__(self, network: AsyncNetworkResource) -> None:
        self._network = network
        self.list = async_to_streamed_response_wrapper(network.list)
        self.get = async_to_streamed_response_wrapper(network.get)
        self.status = async_to_streamed_response_wrapper(network.status)
        self.stats = async_to_streamed_response_wrapper(network.stats)
        self.peers = async_to_streamed_response_wrapper(network.peers)
