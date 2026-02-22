# Hanzo AI SDK

from __future__ import annotations

from typing import Any, Dict, List

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

__all__ = ["MCPServersResource", "AsyncMCPServersResource"]


class MCPServersResource(SyncAPIResource):
    """Model Context Protocol server management."""

    @cached_property
    def with_raw_response(self) -> MCPServersResourceWithRawResponse:
        return MCPServersResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> MCPServersResourceWithStreamingResponse:
        return MCPServersResourceWithStreamingResponse(self)

    def list(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all MCP servers."""
        return self._get(
            "/mcp/servers",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def get(
        self,
        server_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a specific MCP server."""
        return self._get(
            f"/mcp/servers/{server_id}",
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
        url: str,
        api_key: str | NotGiven = NOT_GIVEN,
        tools: List[str] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Register a new MCP server."""
        return self._post(
            "/mcp/servers",
            body={"name": name, "url": url, "api_key": api_key, "tools": tools},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def update(
        self,
        server_id: str,
        *,
        url: str | NotGiven = NOT_GIVEN,
        api_key: str | NotGiven = NOT_GIVEN,
        enabled: bool | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update an MCP server."""
        return self._put(
            f"/mcp/servers/{server_id}",
            body={"url": url, "api_key": api_key, "enabled": enabled},
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
        server_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Remove an MCP server."""
        return self._delete(
            f"/mcp/servers/{server_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def list_tools(
        self,
        server_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List tools from an MCP server."""
        return self._get(
            f"/mcp/servers/{server_id}/tools",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def call_tool(
        self,
        server_id: str,
        tool_name: str,
        *,
        arguments: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Call a tool on an MCP server."""
        return self._post(
            f"/mcp/servers/{server_id}/tools/{tool_name}",
            body={"arguments": arguments},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def refresh(
        self,
        server_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Refresh MCP server tools."""
        return self._post(
            f"/mcp/servers/{server_id}/refresh",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class AsyncMCPServersResource(AsyncAPIResource):
    """Model Context Protocol server management (async)."""

    @cached_property
    def with_raw_response(self) -> AsyncMCPServersResourceWithRawResponse:
        return AsyncMCPServersResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncMCPServersResourceWithStreamingResponse:
        return AsyncMCPServersResourceWithStreamingResponse(self)

    async def list(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            "/mcp/servers",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def get(
        self,
        server_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/mcp/servers/{server_id}",
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
        url: str,
        api_key: str | NotGiven = NOT_GIVEN,
        tools: List[str] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            "/mcp/servers",
            body={"name": name, "url": url, "api_key": api_key, "tools": tools},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def update(
        self,
        server_id: str,
        *,
        url: str | NotGiven = NOT_GIVEN,
        api_key: str | NotGiven = NOT_GIVEN,
        enabled: bool | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._put(
            f"/mcp/servers/{server_id}",
            body={"url": url, "api_key": api_key, "enabled": enabled},
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
        server_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._delete(
            f"/mcp/servers/{server_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def list_tools(
        self,
        server_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/mcp/servers/{server_id}/tools",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def call_tool(
        self,
        server_id: str,
        tool_name: str,
        *,
        arguments: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            f"/mcp/servers/{server_id}/tools/{tool_name}",
            body={"arguments": arguments},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def refresh(
        self,
        server_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            f"/mcp/servers/{server_id}/refresh",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class MCPServersResourceWithRawResponse:
    def __init__(self, mcp_servers: MCPServersResource) -> None:
        self._mcp_servers = mcp_servers
        self.list = to_raw_response_wrapper(mcp_servers.list)
        self.get = to_raw_response_wrapper(mcp_servers.get)
        self.create = to_raw_response_wrapper(mcp_servers.create)
        self.update = to_raw_response_wrapper(mcp_servers.update)
        self.delete = to_raw_response_wrapper(mcp_servers.delete)
        self.list_tools = to_raw_response_wrapper(mcp_servers.list_tools)
        self.call_tool = to_raw_response_wrapper(mcp_servers.call_tool)
        self.refresh = to_raw_response_wrapper(mcp_servers.refresh)


class AsyncMCPServersResourceWithRawResponse:
    def __init__(self, mcp_servers: AsyncMCPServersResource) -> None:
        self._mcp_servers = mcp_servers
        self.list = async_to_raw_response_wrapper(mcp_servers.list)
        self.get = async_to_raw_response_wrapper(mcp_servers.get)
        self.create = async_to_raw_response_wrapper(mcp_servers.create)
        self.update = async_to_raw_response_wrapper(mcp_servers.update)
        self.delete = async_to_raw_response_wrapper(mcp_servers.delete)
        self.list_tools = async_to_raw_response_wrapper(mcp_servers.list_tools)
        self.call_tool = async_to_raw_response_wrapper(mcp_servers.call_tool)
        self.refresh = async_to_raw_response_wrapper(mcp_servers.refresh)


class MCPServersResourceWithStreamingResponse:
    def __init__(self, mcp_servers: MCPServersResource) -> None:
        self._mcp_servers = mcp_servers
        self.list = to_streamed_response_wrapper(mcp_servers.list)
        self.get = to_streamed_response_wrapper(mcp_servers.get)
        self.create = to_streamed_response_wrapper(mcp_servers.create)
        self.update = to_streamed_response_wrapper(mcp_servers.update)
        self.delete = to_streamed_response_wrapper(mcp_servers.delete)
        self.list_tools = to_streamed_response_wrapper(mcp_servers.list_tools)
        self.call_tool = to_streamed_response_wrapper(mcp_servers.call_tool)
        self.refresh = to_streamed_response_wrapper(mcp_servers.refresh)


class AsyncMCPServersResourceWithStreamingResponse:
    def __init__(self, mcp_servers: AsyncMCPServersResource) -> None:
        self._mcp_servers = mcp_servers
        self.list = async_to_streamed_response_wrapper(mcp_servers.list)
        self.get = async_to_streamed_response_wrapper(mcp_servers.get)
        self.create = async_to_streamed_response_wrapper(mcp_servers.create)
        self.update = async_to_streamed_response_wrapper(mcp_servers.update)
        self.delete = async_to_streamed_response_wrapper(mcp_servers.delete)
        self.list_tools = async_to_streamed_response_wrapper(mcp_servers.list_tools)
        self.call_tool = async_to_streamed_response_wrapper(mcp_servers.call_tool)
        self.refresh = async_to_streamed_response_wrapper(mcp_servers.refresh)
