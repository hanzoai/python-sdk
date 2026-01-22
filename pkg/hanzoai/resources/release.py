# Hanzo AI SDK

from __future__ import annotations

from typing import Dict, Any, List

import httpx

from .._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._base_client import make_request_options


class ReleaseResource(SyncAPIResource):
    """Release management for environment promotion."""

    @cached_property
    def with_raw_response(self) -> ReleaseResourceWithRawResponse:
        return ReleaseResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ReleaseResourceWithStreamingResponse:
        return ReleaseResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        name: str,
        source: str,
        revision: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a release from a revision."""
        return self._post(
            "/release",
            body={"name": name, "source": source, "revision": revision},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
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
        """List releases."""
        return self._get(
            "/release",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def get(
        self,
        release_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get release details."""
        return self._get(
            f"/release/{release_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def promote(
        self,
        release_id: str,
        *,
        target_env: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Promote release to target environment."""
        return self._post(
            f"/release/{release_id}/promote",
            body={"target_env": target_env},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def rollback(
        self,
        release_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Rollback a release."""
        return self._post(
            f"/release/{release_id}/rollback",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class AsyncReleaseResource(AsyncAPIResource):
    """Release management for environment promotion."""

    @cached_property
    def with_raw_response(self) -> AsyncReleaseResourceWithRawResponse:
        return AsyncReleaseResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncReleaseResourceWithStreamingResponse:
        return AsyncReleaseResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        name: str,
        source: str,
        revision: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a release from a revision."""
        return await self._post(
            "/release",
            body={"name": name, "source": source, "revision": revision},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
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
        """List releases."""
        return await self._get(
            "/release",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def get(
        self,
        release_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get release details."""
        return await self._get(
            f"/release/{release_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def promote(
        self,
        release_id: str,
        *,
        target_env: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Promote release to target environment."""
        return await self._post(
            f"/release/{release_id}/promote",
            body={"target_env": target_env},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def rollback(
        self,
        release_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Rollback a release."""
        return await self._post(
            f"/release/{release_id}/rollback",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class ReleaseResourceWithRawResponse:
    def __init__(self, release: ReleaseResource) -> None:
        self._release = release

class AsyncReleaseResourceWithRawResponse:
    def __init__(self, release: AsyncReleaseResource) -> None:
        self._release = release

class ReleaseResourceWithStreamingResponse:
    def __init__(self, release: ReleaseResource) -> None:
        self._release = release

class AsyncReleaseResourceWithStreamingResponse:
    def __init__(self, release: AsyncReleaseResource) -> None:
        self._release = release
