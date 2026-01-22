# Hanzo AI SDK

from __future__ import annotations
from typing import Dict, Any, List
import httpx
from .._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import to_raw_response_wrapper, to_streamed_response_wrapper, async_to_raw_response_wrapper, async_to_streamed_response_wrapper
from .._base_client import make_request_options

__all__ = ["GraphsResource", "AsyncGraphsResource"]


class GraphsResource(SyncAPIResource):
    """Knowledge graph management."""

    @cached_property
    def with_raw_response(self) -> GraphsResourceWithRawResponse:
        return GraphsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> GraphsResourceWithStreamingResponse:
        return GraphsResourceWithStreamingResponse(self)

    def list(self, *, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        """List all graphs."""
        return self._get("/ai/graphs", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    def get(self, graph_id: str, *, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        """Get a specific graph."""
        return self._get(f"/ai/graphs/{graph_id}", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    def create(self, *, name: str, description: str | NotGiven = NOT_GIVEN, schema: Dict[str, Any] | NotGiven = NOT_GIVEN, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        """Create a new graph."""
        return self._post("/ai/graphs", body={"name": name, "description": description, "schema": schema}, options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    def delete(self, graph_id: str, *, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        """Delete a graph."""
        return self._delete(f"/ai/graphs/{graph_id}", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    def add_node(self, graph_id: str, *, type: str, properties: Dict[str, Any], extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        """Add a node to the graph."""
        return self._post(f"/ai/graphs/{graph_id}/nodes", body={"type": type, "properties": properties}, options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    def add_edge(self, graph_id: str, *, source_id: str, target_id: str, type: str, properties: Dict[str, Any] | NotGiven = NOT_GIVEN, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        """Add an edge to the graph."""
        return self._post(f"/ai/graphs/{graph_id}/edges", body={"source_id": source_id, "target_id": target_id, "type": type, "properties": properties}, options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    def query(self, graph_id: str, *, query: str, params: Dict[str, Any] | NotGiven = NOT_GIVEN, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        """Query the graph."""
        return self._post(f"/ai/graphs/{graph_id}/query", body={"query": query, "params": params}, options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    def search(self, graph_id: str, *, text: str, node_types: List[str] | NotGiven = NOT_GIVEN, limit: int | NotGiven = NOT_GIVEN, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        """Search the graph."""
        return self._post(f"/ai/graphs/{graph_id}/search", body={"text": text, "node_types": node_types, "limit": limit}, options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    def stats(self, graph_id: str, *, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        """Get graph statistics."""
        return self._get(f"/ai/graphs/{graph_id}/stats", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)


class AsyncGraphsResource(AsyncAPIResource):
    """Knowledge graph management (async)."""

    @cached_property
    def with_raw_response(self) -> AsyncGraphsResourceWithRawResponse:
        return AsyncGraphsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncGraphsResourceWithStreamingResponse:
        return AsyncGraphsResourceWithStreamingResponse(self)

    async def list(self, *, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        return await self._get("/ai/graphs", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    async def get(self, graph_id: str, *, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        return await self._get(f"/ai/graphs/{graph_id}", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    async def create(self, *, name: str, description: str | NotGiven = NOT_GIVEN, schema: Dict[str, Any] | NotGiven = NOT_GIVEN, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        return await self._post("/ai/graphs", body={"name": name, "description": description, "schema": schema}, options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    async def delete(self, graph_id: str, *, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        return await self._delete(f"/ai/graphs/{graph_id}", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    async def add_node(self, graph_id: str, *, type: str, properties: Dict[str, Any], extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        return await self._post(f"/ai/graphs/{graph_id}/nodes", body={"type": type, "properties": properties}, options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    async def add_edge(self, graph_id: str, *, source_id: str, target_id: str, type: str, properties: Dict[str, Any] | NotGiven = NOT_GIVEN, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        return await self._post(f"/ai/graphs/{graph_id}/edges", body={"source_id": source_id, "target_id": target_id, "type": type, "properties": properties}, options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    async def query(self, graph_id: str, *, query: str, params: Dict[str, Any] | NotGiven = NOT_GIVEN, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        return await self._post(f"/ai/graphs/{graph_id}/query", body={"query": query, "params": params}, options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    async def search(self, graph_id: str, *, text: str, node_types: List[str] | NotGiven = NOT_GIVEN, limit: int | NotGiven = NOT_GIVEN, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        return await self._post(f"/ai/graphs/{graph_id}/search", body={"text": text, "node_types": node_types, "limit": limit}, options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    async def stats(self, graph_id: str, *, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        return await self._get(f"/ai/graphs/{graph_id}/stats", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)


class GraphsResourceWithRawResponse:
    def __init__(self, graphs: GraphsResource) -> None:
        self._graphs = graphs
        self.list = to_raw_response_wrapper(graphs.list)
        self.get = to_raw_response_wrapper(graphs.get)
        self.create = to_raw_response_wrapper(graphs.create)
        self.delete = to_raw_response_wrapper(graphs.delete)
        self.add_node = to_raw_response_wrapper(graphs.add_node)
        self.add_edge = to_raw_response_wrapper(graphs.add_edge)
        self.query = to_raw_response_wrapper(graphs.query)
        self.search = to_raw_response_wrapper(graphs.search)
        self.stats = to_raw_response_wrapper(graphs.stats)


class AsyncGraphsResourceWithRawResponse:
    def __init__(self, graphs: AsyncGraphsResource) -> None:
        self._graphs = graphs
        self.list = async_to_raw_response_wrapper(graphs.list)
        self.get = async_to_raw_response_wrapper(graphs.get)
        self.create = async_to_raw_response_wrapper(graphs.create)
        self.delete = async_to_raw_response_wrapper(graphs.delete)
        self.add_node = async_to_raw_response_wrapper(graphs.add_node)
        self.add_edge = async_to_raw_response_wrapper(graphs.add_edge)
        self.query = async_to_raw_response_wrapper(graphs.query)
        self.search = async_to_raw_response_wrapper(graphs.search)
        self.stats = async_to_raw_response_wrapper(graphs.stats)


class GraphsResourceWithStreamingResponse:
    def __init__(self, graphs: GraphsResource) -> None:
        self._graphs = graphs
        self.list = to_streamed_response_wrapper(graphs.list)
        self.get = to_streamed_response_wrapper(graphs.get)
        self.create = to_streamed_response_wrapper(graphs.create)
        self.delete = to_streamed_response_wrapper(graphs.delete)
        self.add_node = to_streamed_response_wrapper(graphs.add_node)
        self.add_edge = to_streamed_response_wrapper(graphs.add_edge)
        self.query = to_streamed_response_wrapper(graphs.query)
        self.search = to_streamed_response_wrapper(graphs.search)
        self.stats = to_streamed_response_wrapper(graphs.stats)


class AsyncGraphsResourceWithStreamingResponse:
    def __init__(self, graphs: AsyncGraphsResource) -> None:
        self._graphs = graphs
        self.list = async_to_streamed_response_wrapper(graphs.list)
        self.get = async_to_streamed_response_wrapper(graphs.get)
        self.create = async_to_streamed_response_wrapper(graphs.create)
        self.delete = async_to_streamed_response_wrapper(graphs.delete)
        self.add_node = async_to_streamed_response_wrapper(graphs.add_node)
        self.add_edge = async_to_streamed_response_wrapper(graphs.add_edge)
        self.query = async_to_streamed_response_wrapper(graphs.query)
        self.search = async_to_streamed_response_wrapper(graphs.search)
        self.stats = async_to_streamed_response_wrapper(graphs.stats)
