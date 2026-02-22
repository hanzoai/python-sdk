# Hanzo AI SDK

from __future__ import annotations

from typing import Any, Dict, List

import httpx

from .._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._base_client import make_request_options


class AccessResource(SyncAPIResource):
    """User-facing access grants and sharing."""

    @cached_property
    def with_raw_response(self) -> AccessResourceWithRawResponse:
        return AccessResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AccessResourceWithStreamingResponse:
        return AccessResourceWithStreamingResponse(self)

    def grant(
        self,
        *,
        principal: str,
        resource: str,
        ttl: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Grant access to a service or app."""
        return self._post(
            "/access/grant",
            body={"principal": principal, "resource": resource, "ttl": ttl},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def revoke(
        self,
        *,
        principal: str,
        resource: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Revoke access from a service or app."""
        return self._post(
            "/access/revoke",
            body={"principal": principal, "resource": resource},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def whoami(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get current access context."""
        return self._get(
            "/access/whoami",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def check(
        self,
        *,
        service: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Check access to a service."""
        return self._get(
            "/access/check",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"service": service},
            ),
            cast_to=object,
        )

    def share(
        self,
        *,
        service: str,
        ttl: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a shareable access link."""
        return self._post(
            "/access/share",
            body={"service": service, "ttl": ttl},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def list(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List current access grants."""
        return self._get(
            "/access",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class AsyncAccessResource(AsyncAPIResource):
    """User-facing access grants and sharing."""

    @cached_property
    def with_raw_response(self) -> AsyncAccessResourceWithRawResponse:
        return AsyncAccessResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncAccessResourceWithStreamingResponse:
        return AsyncAccessResourceWithStreamingResponse(self)

    async def grant(
        self,
        *,
        principal: str,
        resource: str,
        ttl: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Grant access to a service or app."""
        return await self._post(
            "/access/grant",
            body={"principal": principal, "resource": resource, "ttl": ttl},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def revoke(
        self,
        *,
        principal: str,
        resource: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Revoke access from a service or app."""
        return await self._post(
            "/access/revoke",
            body={"principal": principal, "resource": resource},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def whoami(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get current access context."""
        return await self._get(
            "/access/whoami",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def check(
        self,
        *,
        service: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Check access to a service."""
        return await self._get(
            "/access/check",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"service": service},
            ),
            cast_to=object,
        )

    async def share(
        self,
        *,
        service: str,
        ttl: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a shareable access link."""
        return await self._post(
            "/access/share",
            body={"service": service, "ttl": ttl},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def list(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List current access grants."""
        return await self._get(
            "/access",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class AccessResourceWithRawResponse:
    def __init__(self, access: AccessResource) -> None:
        self._access = access


class AsyncAccessResourceWithRawResponse:
    def __init__(self, access: AsyncAccessResource) -> None:
        self._access = access


class AccessResourceWithStreamingResponse:
    def __init__(self, access: AccessResource) -> None:
        self._access = access


class AsyncAccessResourceWithStreamingResponse:
    def __init__(self, access: AsyncAccessResource) -> None:
        self._access = access
