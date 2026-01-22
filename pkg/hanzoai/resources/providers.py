# Hanzo AI SDK

from __future__ import annotations

from typing import Optional, Dict, Any

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

__all__ = ["ProvidersResource", "AsyncProvidersResource"]


class ProvidersResource(SyncAPIResource):
    """LLM Provider management for AI/ML operations."""

    @cached_property
    def with_raw_response(self) -> ProvidersResourceWithRawResponse:
        return ProvidersResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ProvidersResourceWithStreamingResponse:
        return ProvidersResourceWithStreamingResponse(self)

    def list(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all configured LLM providers."""
        return self._get(
            "/providers",
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
        provider_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a specific provider configuration."""
        return self._get(
            f"/providers/{provider_id}",
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
        type: str,
        config: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a new LLM provider configuration."""
        return self._post(
            "/providers",
            body={"name": name, "type": type, "config": config},
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
        provider_id: str,
        *,
        name: str | NotGiven = NOT_GIVEN,
        config: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update a provider configuration."""
        return self._put(
            f"/providers/{provider_id}",
            body={"name": name, "config": config},
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
        provider_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a provider configuration."""
        return self._delete(
            f"/providers/{provider_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def refresh_mcp_tools(
        self,
        provider_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Refresh MCP tools for a provider."""
        return self._post(
            f"/providers/{provider_id}/mcp/refresh",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class AsyncProvidersResource(AsyncAPIResource):
    """LLM Provider management for AI/ML operations (async)."""

    @cached_property
    def with_raw_response(self) -> AsyncProvidersResourceWithRawResponse:
        return AsyncProvidersResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncProvidersResourceWithStreamingResponse:
        return AsyncProvidersResourceWithStreamingResponse(self)

    async def list(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all configured LLM providers."""
        return await self._get(
            "/providers",
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
        provider_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a specific provider configuration."""
        return await self._get(
            f"/providers/{provider_id}",
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
        type: str,
        config: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a new LLM provider configuration."""
        return await self._post(
            "/providers",
            body={"name": name, "type": type, "config": config},
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
        provider_id: str,
        *,
        name: str | NotGiven = NOT_GIVEN,
        config: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update a provider configuration."""
        return await self._put(
            f"/providers/{provider_id}",
            body={"name": name, "config": config},
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
        provider_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a provider configuration."""
        return await self._delete(
            f"/providers/{provider_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def refresh_mcp_tools(
        self,
        provider_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Refresh MCP tools for a provider."""
        return await self._post(
            f"/providers/{provider_id}/mcp/refresh",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class ProvidersResourceWithRawResponse:
    def __init__(self, providers: ProvidersResource) -> None:
        self._providers = providers
        self.list = to_raw_response_wrapper(providers.list)
        self.get = to_raw_response_wrapper(providers.get)
        self.create = to_raw_response_wrapper(providers.create)
        self.update = to_raw_response_wrapper(providers.update)
        self.delete = to_raw_response_wrapper(providers.delete)
        self.refresh_mcp_tools = to_raw_response_wrapper(providers.refresh_mcp_tools)


class AsyncProvidersResourceWithRawResponse:
    def __init__(self, providers: AsyncProvidersResource) -> None:
        self._providers = providers
        self.list = async_to_raw_response_wrapper(providers.list)
        self.get = async_to_raw_response_wrapper(providers.get)
        self.create = async_to_raw_response_wrapper(providers.create)
        self.update = async_to_raw_response_wrapper(providers.update)
        self.delete = async_to_raw_response_wrapper(providers.delete)
        self.refresh_mcp_tools = async_to_raw_response_wrapper(providers.refresh_mcp_tools)


class ProvidersResourceWithStreamingResponse:
    def __init__(self, providers: ProvidersResource) -> None:
        self._providers = providers
        self.list = to_streamed_response_wrapper(providers.list)
        self.get = to_streamed_response_wrapper(providers.get)
        self.create = to_streamed_response_wrapper(providers.create)
        self.update = to_streamed_response_wrapper(providers.update)
        self.delete = to_streamed_response_wrapper(providers.delete)
        self.refresh_mcp_tools = to_streamed_response_wrapper(providers.refresh_mcp_tools)


class AsyncProvidersResourceWithStreamingResponse:
    def __init__(self, providers: AsyncProvidersResource) -> None:
        self._providers = providers
        self.list = async_to_streamed_response_wrapper(providers.list)
        self.get = async_to_streamed_response_wrapper(providers.get)
        self.create = async_to_streamed_response_wrapper(providers.create)
        self.update = async_to_streamed_response_wrapper(providers.update)
        self.delete = async_to_streamed_response_wrapper(providers.delete)
        self.refresh_mcp_tools = async_to_streamed_response_wrapper(providers.refresh_mcp_tools)
