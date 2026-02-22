# Hanzo AI SDK

from __future__ import annotations

from typing import Dict

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

__all__ = ["SecretsResource", "AsyncSecretsResource"]


class SecretsResource(SyncAPIResource):
    """Secret and credential management."""

    @cached_property
    def with_raw_response(self) -> SecretsResourceWithRawResponse:
        return SecretsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> SecretsResourceWithStreamingResponse:
        return SecretsResourceWithStreamingResponse(self)

    def list(
        self,
        *,
        namespace: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all secrets."""
        return self._get(
            "/infrastructure/secrets",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"namespace": namespace},
            ),
            cast_to=object,
        )

    def get(
        self,
        secret_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a specific secret (metadata only)."""
        return self._get(
            f"/infrastructure/secrets/{secret_id}",
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
        namespace: str,
        data: Dict[str, str],
        type: str = "Opaque",
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a new secret."""
        return self._post(
            "/infrastructure/secrets",
            body={"name": name, "namespace": namespace, "data": data, "type": type},
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
        secret_id: str,
        *,
        data: Dict[str, str],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update a secret."""
        return self._put(
            f"/infrastructure/secrets/{secret_id}",
            body={"data": data},
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
        secret_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a secret."""
        return self._delete(
            f"/infrastructure/secrets/{secret_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class AsyncSecretsResource(AsyncAPIResource):
    """Secret and credential management (async)."""

    @cached_property
    def with_raw_response(self) -> AsyncSecretsResourceWithRawResponse:
        return AsyncSecretsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncSecretsResourceWithStreamingResponse:
        return AsyncSecretsResourceWithStreamingResponse(self)

    async def list(
        self,
        *,
        namespace: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            "/infrastructure/secrets",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"namespace": namespace},
            ),
            cast_to=object,
        )

    async def get(
        self,
        secret_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/infrastructure/secrets/{secret_id}",
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
        namespace: str,
        data: Dict[str, str],
        type: str = "Opaque",
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            "/infrastructure/secrets",
            body={"name": name, "namespace": namespace, "data": data, "type": type},
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
        secret_id: str,
        *,
        data: Dict[str, str],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._put(
            f"/infrastructure/secrets/{secret_id}",
            body={"data": data},
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
        secret_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._delete(
            f"/infrastructure/secrets/{secret_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class SecretsResourceWithRawResponse:
    def __init__(self, secrets: SecretsResource) -> None:
        self._secrets = secrets
        self.list = to_raw_response_wrapper(secrets.list)
        self.get = to_raw_response_wrapper(secrets.get)
        self.create = to_raw_response_wrapper(secrets.create)
        self.update = to_raw_response_wrapper(secrets.update)
        self.delete = to_raw_response_wrapper(secrets.delete)


class AsyncSecretsResourceWithRawResponse:
    def __init__(self, secrets: AsyncSecretsResource) -> None:
        self._secrets = secrets
        self.list = async_to_raw_response_wrapper(secrets.list)
        self.get = async_to_raw_response_wrapper(secrets.get)
        self.create = async_to_raw_response_wrapper(secrets.create)
        self.update = async_to_raw_response_wrapper(secrets.update)
        self.delete = async_to_raw_response_wrapper(secrets.delete)


class SecretsResourceWithStreamingResponse:
    def __init__(self, secrets: SecretsResource) -> None:
        self._secrets = secrets
        self.list = to_streamed_response_wrapper(secrets.list)
        self.get = to_streamed_response_wrapper(secrets.get)
        self.create = to_streamed_response_wrapper(secrets.create)
        self.update = to_streamed_response_wrapper(secrets.update)
        self.delete = to_streamed_response_wrapper(secrets.delete)


class AsyncSecretsResourceWithStreamingResponse:
    def __init__(self, secrets: AsyncSecretsResource) -> None:
        self._secrets = secrets
        self.list = async_to_streamed_response_wrapper(secrets.list)
        self.get = async_to_streamed_response_wrapper(secrets.get)
        self.create = async_to_streamed_response_wrapper(secrets.create)
        self.update = async_to_streamed_response_wrapper(secrets.update)
        self.delete = async_to_streamed_response_wrapper(secrets.delete)
