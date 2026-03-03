# Hanzo AI SDK

from __future__ import annotations

from typing import Any, Dict, List

import httpx

from .._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._base_client import make_request_options


class GatewayResource(SyncAPIResource):
    """API gateway management service."""

    @cached_property
    def with_raw_response(self) -> GatewayResourceWithRawResponse:
        return GatewayResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> GatewayResourceWithStreamingResponse:
        return GatewayResourceWithStreamingResponse(self)

    # Status
    def status(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get gateway status."""
        return self._get(
            "/gateway/status",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # Rate limit management
    def list_rate_limits(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all rate limit rules."""
        return self._get(
            "/gateway/rate-limits",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def create_rate_limit(
        self,
        *,
        name: str,
        scope: str,
        requests_per_minute: int,
        burst_size: int,
        scope_id: str | NotGiven = NOT_GIVEN,
        enabled: bool | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a rate limit rule."""
        return self._post(
            "/gateway/rate-limits",
            body={
                "name": name,
                "scope": scope,
                "scopeId": scope_id,
                "requestsPerMinute": requests_per_minute,
                "burstSize": burst_size,
                "enabled": enabled,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def update_rate_limit(
        self,
        rule_id: str,
        *,
        name: str | NotGiven = NOT_GIVEN,
        requests_per_minute: int | NotGiven = NOT_GIVEN,
        burst_size: int | NotGiven = NOT_GIVEN,
        enabled: bool | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update a rate limit rule."""
        return self._put(
            f"/gateway/rate-limits/{rule_id}",
            body={
                "name": name,
                "requestsPerMinute": requests_per_minute,
                "burstSize": burst_size,
                "enabled": enabled,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def delete_rate_limit(
        self,
        rule_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a rate limit rule."""
        return self._delete(
            f"/gateway/rate-limits/{rule_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # Route management
    def list_routes(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all gateway routes."""
        return self._get(
            "/gateway/routes",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def create_route(
        self,
        *,
        name: str,
        host: str,
        backend: str,
        path_prefix: str | NotGiven = NOT_GIVEN,
        middlewares: List[str] | NotGiven = NOT_GIVEN,
        priority: int | NotGiven = NOT_GIVEN,
        enabled: bool | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a gateway route."""
        return self._post(
            "/gateway/routes",
            body={
                "name": name,
                "host": host,
                "backend": backend,
                "pathPrefix": path_prefix,
                "middlewares": middlewares,
                "priority": priority,
                "enabled": enabled,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def update_route(
        self,
        rule_id: str,
        *,
        name: str | NotGiven = NOT_GIVEN,
        host: str | NotGiven = NOT_GIVEN,
        backend: str | NotGiven = NOT_GIVEN,
        path_prefix: str | NotGiven = NOT_GIVEN,
        middlewares: List[str] | NotGiven = NOT_GIVEN,
        priority: int | NotGiven = NOT_GIVEN,
        enabled: bool | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update a gateway route."""
        return self._put(
            f"/gateway/routes/{rule_id}",
            body={
                "name": name,
                "host": host,
                "backend": backend,
                "pathPrefix": path_prefix,
                "middlewares": middlewares,
                "priority": priority,
                "enabled": enabled,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def delete_route(
        self,
        rule_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a gateway route."""
        return self._delete(
            f"/gateway/routes/{rule_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class AsyncGatewayResource(AsyncAPIResource):
    """API gateway management service."""

    @cached_property
    def with_raw_response(self) -> AsyncGatewayResourceWithRawResponse:
        return AsyncGatewayResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncGatewayResourceWithStreamingResponse:
        return AsyncGatewayResourceWithStreamingResponse(self)

    # Status
    async def status(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get gateway status."""
        return await self._get(
            "/gateway/status",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # Rate limit management
    async def list_rate_limits(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all rate limit rules."""
        return await self._get(
            "/gateway/rate-limits",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def create_rate_limit(
        self,
        *,
        name: str,
        scope: str,
        requests_per_minute: int,
        burst_size: int,
        scope_id: str | NotGiven = NOT_GIVEN,
        enabled: bool | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a rate limit rule."""
        return await self._post(
            "/gateway/rate-limits",
            body={
                "name": name,
                "scope": scope,
                "scopeId": scope_id,
                "requestsPerMinute": requests_per_minute,
                "burstSize": burst_size,
                "enabled": enabled,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def update_rate_limit(
        self,
        rule_id: str,
        *,
        name: str | NotGiven = NOT_GIVEN,
        requests_per_minute: int | NotGiven = NOT_GIVEN,
        burst_size: int | NotGiven = NOT_GIVEN,
        enabled: bool | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update a rate limit rule."""
        return await self._put(
            f"/gateway/rate-limits/{rule_id}",
            body={
                "name": name,
                "requestsPerMinute": requests_per_minute,
                "burstSize": burst_size,
                "enabled": enabled,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def delete_rate_limit(
        self,
        rule_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a rate limit rule."""
        return await self._delete(
            f"/gateway/rate-limits/{rule_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # Route management
    async def list_routes(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all gateway routes."""
        return await self._get(
            "/gateway/routes",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def create_route(
        self,
        *,
        name: str,
        host: str,
        backend: str,
        path_prefix: str | NotGiven = NOT_GIVEN,
        middlewares: List[str] | NotGiven = NOT_GIVEN,
        priority: int | NotGiven = NOT_GIVEN,
        enabled: bool | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a gateway route."""
        return await self._post(
            "/gateway/routes",
            body={
                "name": name,
                "host": host,
                "backend": backend,
                "pathPrefix": path_prefix,
                "middlewares": middlewares,
                "priority": priority,
                "enabled": enabled,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def update_route(
        self,
        rule_id: str,
        *,
        name: str | NotGiven = NOT_GIVEN,
        host: str | NotGiven = NOT_GIVEN,
        backend: str | NotGiven = NOT_GIVEN,
        path_prefix: str | NotGiven = NOT_GIVEN,
        middlewares: List[str] | NotGiven = NOT_GIVEN,
        priority: int | NotGiven = NOT_GIVEN,
        enabled: bool | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update a gateway route."""
        return await self._put(
            f"/gateway/routes/{rule_id}",
            body={
                "name": name,
                "host": host,
                "backend": backend,
                "pathPrefix": path_prefix,
                "middlewares": middlewares,
                "priority": priority,
                "enabled": enabled,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def delete_route(
        self,
        rule_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a gateway route."""
        return await self._delete(
            f"/gateway/routes/{rule_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class GatewayResourceWithRawResponse:
    def __init__(self, gateway: GatewayResource) -> None:
        self._gateway = gateway


class AsyncGatewayResourceWithRawResponse:
    def __init__(self, gateway: AsyncGatewayResource) -> None:
        self._gateway = gateway


class GatewayResourceWithStreamingResponse:
    def __init__(self, gateway: GatewayResource) -> None:
        self._gateway = gateway


class AsyncGatewayResourceWithStreamingResponse:
    def __init__(self, gateway: AsyncGatewayResource) -> None:
        self._gateway = gateway
