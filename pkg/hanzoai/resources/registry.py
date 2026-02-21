# Hanzo AI SDK

from __future__ import annotations

from typing import Any, Dict, List

import httpx

from .._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._base_client import make_request_options


class RegistryResource(SyncAPIResource):
    """Container registry management."""

    @cached_property
    def with_raw_response(self) -> RegistryResourceWithRawResponse:
        return RegistryResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> RegistryResourceWithStreamingResponse:
        return RegistryResourceWithStreamingResponse(self)

    def list_repos(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List repositories."""
        return self._get(
            "/registry/repos",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def create_repo(
        self,
        *,
        name: str,
        visibility: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a repository."""
        return self._post(
            "/registry/repos",
            body={"name": name, "visibility": visibility},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def delete_repo(
        self,
        repo_name: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a repository."""
        return self._delete(
            f"/registry/repos/{repo_name}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def list_images(
        self,
        repo_name: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List images in a repository."""
        return self._get(
            f"/registry/repos/{repo_name}/images",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def tag_image(
        self,
        repo_name: str,
        *,
        source_tag: str,
        target_tag: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Tag an image."""
        return self._post(
            f"/registry/repos/{repo_name}/tag",
            body={"source_tag": source_tag, "target_tag": target_tag},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def delete_image(
        self,
        repo_name: str,
        tag: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete an image."""
        return self._delete(
            f"/registry/repos/{repo_name}/images/{tag}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def login(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get registry login credentials."""
        return self._post(
            "/registry/login",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class AsyncRegistryResource(AsyncAPIResource):
    """Container registry management."""

    @cached_property
    def with_raw_response(self) -> AsyncRegistryResourceWithRawResponse:
        return AsyncRegistryResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncRegistryResourceWithStreamingResponse:
        return AsyncRegistryResourceWithStreamingResponse(self)

    async def list_repos(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List repositories."""
        return await self._get(
            "/registry/repos",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def create_repo(
        self,
        *,
        name: str,
        visibility: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a repository."""
        return await self._post(
            "/registry/repos",
            body={"name": name, "visibility": visibility},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def delete_repo(
        self,
        repo_name: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a repository."""
        return await self._delete(
            f"/registry/repos/{repo_name}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def list_images(
        self,
        repo_name: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List images in a repository."""
        return await self._get(
            f"/registry/repos/{repo_name}/images",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def tag_image(
        self,
        repo_name: str,
        *,
        source_tag: str,
        target_tag: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Tag an image."""
        return await self._post(
            f"/registry/repos/{repo_name}/tag",
            body={"source_tag": source_tag, "target_tag": target_tag},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def delete_image(
        self,
        repo_name: str,
        tag: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete an image."""
        return await self._delete(
            f"/registry/repos/{repo_name}/images/{tag}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def login(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get registry login credentials."""
        return await self._post(
            "/registry/login",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class RegistryResourceWithRawResponse:
    def __init__(self, registry: RegistryResource) -> None:
        self._registry = registry


class AsyncRegistryResourceWithRawResponse:
    def __init__(self, registry: AsyncRegistryResource) -> None:
        self._registry = registry


class RegistryResourceWithStreamingResponse:
    def __init__(self, registry: RegistryResource) -> None:
        self._registry = registry


class AsyncRegistryResourceWithStreamingResponse:
    def __init__(self, registry: AsyncRegistryResource) -> None:
        self._registry = registry
