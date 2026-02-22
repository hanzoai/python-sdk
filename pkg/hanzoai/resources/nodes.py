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

__all__ = ["NodesResource", "AsyncNodesResource"]


class NodesResource(SyncAPIResource):
    """Blockchain node management."""

    @cached_property
    def with_raw_response(self) -> NodesResourceWithRawResponse:
        return NodesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> NodesResourceWithStreamingResponse:
        return NodesResourceWithStreamingResponse(self)

    def list(
        self,
        *,
        network_id: str | NotGiven = NOT_GIVEN,
        status: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all nodes."""
        return self._get(
            "/network/nodes",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"network_id": network_id, "status": status},
            ),
            cast_to=object,
        )

    def get(
        self,
        node_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a specific node."""
        return self._get(
            f"/network/nodes/{node_id}",
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
        network_id: str,
        type: str,
        config: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a new node."""
        return self._post(
            "/network/nodes",
            body={"network_id": network_id, "type": type, "config": config},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def delete(
        self,
        node_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a node."""
        return self._delete(
            f"/network/nodes/{node_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def start(
        self,
        node_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Start a node."""
        return self._post(
            f"/network/nodes/{node_id}/start",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def stop(
        self,
        node_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Stop a node."""
        return self._post(
            f"/network/nodes/{node_id}/stop",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def logs(
        self,
        node_id: str,
        *,
        lines: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get node logs."""
        return self._get(
            f"/network/nodes/{node_id}/logs",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"lines": lines},
            ),
            cast_to=object,
        )

    def stats(
        self,
        node_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get node statistics."""
        return self._get(
            f"/network/nodes/{node_id}/stats",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class AsyncNodesResource(AsyncAPIResource):
    """Blockchain node management (async)."""

    @cached_property
    def with_raw_response(self) -> AsyncNodesResourceWithRawResponse:
        return AsyncNodesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncNodesResourceWithStreamingResponse:
        return AsyncNodesResourceWithStreamingResponse(self)

    async def list(
        self,
        *,
        network_id: str | NotGiven = NOT_GIVEN,
        status: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            "/network/nodes",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"network_id": network_id, "status": status},
            ),
            cast_to=object,
        )

    async def get(
        self,
        node_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/network/nodes/{node_id}",
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
        network_id: str,
        type: str,
        config: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            "/network/nodes",
            body={"network_id": network_id, "type": type, "config": config},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def delete(
        self,
        node_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._delete(
            f"/network/nodes/{node_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def start(
        self,
        node_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            f"/network/nodes/{node_id}/start",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def stop(
        self,
        node_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            f"/network/nodes/{node_id}/stop",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def logs(
        self,
        node_id: str,
        *,
        lines: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/network/nodes/{node_id}/logs",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"lines": lines},
            ),
            cast_to=object,
        )

    async def stats(
        self,
        node_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/network/nodes/{node_id}/stats",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class NodesResourceWithRawResponse:
    def __init__(self, nodes: NodesResource) -> None:
        self._nodes = nodes
        self.list = to_raw_response_wrapper(nodes.list)
        self.get = to_raw_response_wrapper(nodes.get)
        self.create = to_raw_response_wrapper(nodes.create)
        self.delete = to_raw_response_wrapper(nodes.delete)
        self.start = to_raw_response_wrapper(nodes.start)
        self.stop = to_raw_response_wrapper(nodes.stop)
        self.logs = to_raw_response_wrapper(nodes.logs)
        self.stats = to_raw_response_wrapper(nodes.stats)


class AsyncNodesResourceWithRawResponse:
    def __init__(self, nodes: AsyncNodesResource) -> None:
        self._nodes = nodes
        self.list = async_to_raw_response_wrapper(nodes.list)
        self.get = async_to_raw_response_wrapper(nodes.get)
        self.create = async_to_raw_response_wrapper(nodes.create)
        self.delete = async_to_raw_response_wrapper(nodes.delete)
        self.start = async_to_raw_response_wrapper(nodes.start)
        self.stop = async_to_raw_response_wrapper(nodes.stop)
        self.logs = async_to_raw_response_wrapper(nodes.logs)
        self.stats = async_to_raw_response_wrapper(nodes.stats)


class NodesResourceWithStreamingResponse:
    def __init__(self, nodes: NodesResource) -> None:
        self._nodes = nodes
        self.list = to_streamed_response_wrapper(nodes.list)
        self.get = to_streamed_response_wrapper(nodes.get)
        self.create = to_streamed_response_wrapper(nodes.create)
        self.delete = to_streamed_response_wrapper(nodes.delete)
        self.start = to_streamed_response_wrapper(nodes.start)
        self.stop = to_streamed_response_wrapper(nodes.stop)
        self.logs = to_streamed_response_wrapper(nodes.logs)
        self.stats = to_streamed_response_wrapper(nodes.stats)


class AsyncNodesResourceWithStreamingResponse:
    def __init__(self, nodes: AsyncNodesResource) -> None:
        self._nodes = nodes
        self.list = async_to_streamed_response_wrapper(nodes.list)
        self.get = async_to_streamed_response_wrapper(nodes.get)
        self.create = async_to_streamed_response_wrapper(nodes.create)
        self.delete = async_to_streamed_response_wrapper(nodes.delete)
        self.start = async_to_streamed_response_wrapper(nodes.start)
        self.stop = async_to_streamed_response_wrapper(nodes.stop)
        self.logs = async_to_streamed_response_wrapper(nodes.logs)
        self.stats = async_to_streamed_response_wrapper(nodes.stats)
