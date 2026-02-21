# Hanzo AI SDK

from __future__ import annotations

from typing import Any, Dict, Optional

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

__all__ = ["StorageResource", "AsyncStorageResource"]


class StorageResource(SyncAPIResource):
    """Object storage service."""

    @cached_property
    def with_raw_response(self) -> StorageResourceWithRawResponse:
        return StorageResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> StorageResourceWithStreamingResponse:
        return StorageResourceWithStreamingResponse(self)

    def list_buckets(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all storage buckets."""
        return self._get(
            "/storage/buckets",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def create_bucket(
        self,
        *,
        name: str,
        region: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a new storage bucket."""
        return self._post(
            "/storage/buckets",
            body={"name": name, "region": region},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def delete_bucket(
        self,
        bucket_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a storage bucket."""
        return self._delete(
            f"/storage/buckets/{bucket_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def list_objects(
        self,
        bucket_id: str,
        *,
        prefix: str | NotGiven = NOT_GIVEN,
        limit: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List objects in a bucket."""
        return self._get(
            f"/storage/buckets/{bucket_id}/objects",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"prefix": prefix, "limit": limit},
            ),
            cast_to=object,
        )

    def get_object(
        self,
        bucket_id: str,
        key: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get an object from a bucket."""
        return self._get(
            f"/storage/buckets/{bucket_id}/objects/{key}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def put_object(
        self,
        bucket_id: str,
        key: str,
        *,
        data: bytes,
        content_type: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Put an object into a bucket."""
        return self._put(
            f"/storage/buckets/{bucket_id}/objects/{key}",
            body=data,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def delete_object(
        self,
        bucket_id: str,
        key: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete an object from a bucket."""
        return self._delete(
            f"/storage/buckets/{bucket_id}/objects/{key}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def get_presigned_url(
        self,
        bucket_id: str,
        key: str,
        *,
        expires_in: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a presigned URL for an object."""
        return self._post(
            f"/storage/buckets/{bucket_id}/presign",
            body={"key": key, "expires_in": expires_in},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class AsyncStorageResource(AsyncAPIResource):
    """Object storage service (async)."""

    @cached_property
    def with_raw_response(self) -> AsyncStorageResourceWithRawResponse:
        return AsyncStorageResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncStorageResourceWithStreamingResponse:
        return AsyncStorageResourceWithStreamingResponse(self)

    async def list_buckets(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all storage buckets."""
        return await self._get(
            "/storage/buckets",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def create_bucket(
        self,
        *,
        name: str,
        region: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a new storage bucket."""
        return await self._post(
            "/storage/buckets",
            body={"name": name, "region": region},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def delete_bucket(
        self,
        bucket_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a storage bucket."""
        return await self._delete(
            f"/storage/buckets/{bucket_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def list_objects(
        self,
        bucket_id: str,
        *,
        prefix: str | NotGiven = NOT_GIVEN,
        limit: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List objects in a bucket."""
        return await self._get(
            f"/storage/buckets/{bucket_id}/objects",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"prefix": prefix, "limit": limit},
            ),
            cast_to=object,
        )

    async def get_object(
        self,
        bucket_id: str,
        key: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get an object from a bucket."""
        return await self._get(
            f"/storage/buckets/{bucket_id}/objects/{key}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def put_object(
        self,
        bucket_id: str,
        key: str,
        *,
        data: bytes,
        content_type: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Put an object into a bucket."""
        return await self._put(
            f"/storage/buckets/{bucket_id}/objects/{key}",
            body=data,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def delete_object(
        self,
        bucket_id: str,
        key: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete an object from a bucket."""
        return await self._delete(
            f"/storage/buckets/{bucket_id}/objects/{key}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def get_presigned_url(
        self,
        bucket_id: str,
        key: str,
        *,
        expires_in: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a presigned URL for an object."""
        return await self._post(
            f"/storage/buckets/{bucket_id}/presign",
            body={"key": key, "expires_in": expires_in},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class StorageResourceWithRawResponse:
    def __init__(self, storage: StorageResource) -> None:
        self._storage = storage
        self.list_buckets = to_raw_response_wrapper(storage.list_buckets)
        self.create_bucket = to_raw_response_wrapper(storage.create_bucket)
        self.delete_bucket = to_raw_response_wrapper(storage.delete_bucket)
        self.list_objects = to_raw_response_wrapper(storage.list_objects)
        self.get_object = to_raw_response_wrapper(storage.get_object)
        self.put_object = to_raw_response_wrapper(storage.put_object)
        self.delete_object = to_raw_response_wrapper(storage.delete_object)
        self.get_presigned_url = to_raw_response_wrapper(storage.get_presigned_url)


class AsyncStorageResourceWithRawResponse:
    def __init__(self, storage: AsyncStorageResource) -> None:
        self._storage = storage
        self.list_buckets = async_to_raw_response_wrapper(storage.list_buckets)
        self.create_bucket = async_to_raw_response_wrapper(storage.create_bucket)
        self.delete_bucket = async_to_raw_response_wrapper(storage.delete_bucket)
        self.list_objects = async_to_raw_response_wrapper(storage.list_objects)
        self.get_object = async_to_raw_response_wrapper(storage.get_object)
        self.put_object = async_to_raw_response_wrapper(storage.put_object)
        self.delete_object = async_to_raw_response_wrapper(storage.delete_object)
        self.get_presigned_url = async_to_raw_response_wrapper(storage.get_presigned_url)


class StorageResourceWithStreamingResponse:
    def __init__(self, storage: StorageResource) -> None:
        self._storage = storage
        self.list_buckets = to_streamed_response_wrapper(storage.list_buckets)
        self.create_bucket = to_streamed_response_wrapper(storage.create_bucket)
        self.delete_bucket = to_streamed_response_wrapper(storage.delete_bucket)
        self.list_objects = to_streamed_response_wrapper(storage.list_objects)
        self.get_object = to_streamed_response_wrapper(storage.get_object)
        self.put_object = to_streamed_response_wrapper(storage.put_object)
        self.delete_object = to_streamed_response_wrapper(storage.delete_object)
        self.get_presigned_url = to_streamed_response_wrapper(storage.get_presigned_url)


class AsyncStorageResourceWithStreamingResponse:
    def __init__(self, storage: AsyncStorageResource) -> None:
        self._storage = storage
        self.list_buckets = async_to_streamed_response_wrapper(storage.list_buckets)
        self.create_bucket = async_to_streamed_response_wrapper(storage.create_bucket)
        self.delete_bucket = async_to_streamed_response_wrapper(storage.delete_bucket)
        self.list_objects = async_to_streamed_response_wrapper(storage.list_objects)
        self.get_object = async_to_streamed_response_wrapper(storage.get_object)
        self.put_object = async_to_streamed_response_wrapper(storage.put_object)
        self.delete_object = async_to_streamed_response_wrapper(storage.delete_object)
        self.get_presigned_url = async_to_streamed_response_wrapper(storage.get_presigned_url)
