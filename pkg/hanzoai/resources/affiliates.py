# Hanzo AI SDK

from __future__ import annotations
from typing import Dict, Any
import httpx
from .._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import to_raw_response_wrapper, to_streamed_response_wrapper, async_to_raw_response_wrapper, async_to_streamed_response_wrapper
from .._base_client import make_request_options

__all__ = ["AffiliatesResource", "AsyncAffiliatesResource"]


class AffiliatesResource(SyncAPIResource):
    """Affiliate program management."""

    @cached_property
    def with_raw_response(self) -> AffiliatesResourceWithRawResponse:
        return AffiliatesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AffiliatesResourceWithStreamingResponse:
        return AffiliatesResourceWithStreamingResponse(self)

    def list(self, *, status: str | NotGiven = NOT_GIVEN, limit: int | NotGiven = NOT_GIVEN, offset: int | NotGiven = NOT_GIVEN, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        """List all affiliates."""
        return self._get("/marketing/affiliates", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout, query={"status": status, "limit": limit, "offset": offset}), cast_to=object)

    def get(self, affiliate_id: str, *, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        """Get a specific affiliate."""
        return self._get(f"/marketing/affiliates/{affiliate_id}", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    def create(self, *, user_id: str, commission_rate: float | NotGiven = NOT_GIVEN, metadata: Dict[str, Any] | NotGiven = NOT_GIVEN, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        """Create a new affiliate."""
        return self._post("/marketing/affiliates", body={"user_id": user_id, "commission_rate": commission_rate, "metadata": metadata}, options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    def update(self, affiliate_id: str, *, commission_rate: float | NotGiven = NOT_GIVEN, status: str | NotGiven = NOT_GIVEN, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        """Update an affiliate."""
        return self._put(f"/marketing/affiliates/{affiliate_id}", body={"commission_rate": commission_rate, "status": status}, options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    def delete(self, affiliate_id: str, *, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        """Delete an affiliate."""
        return self._delete(f"/marketing/affiliates/{affiliate_id}", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    def stats(self, affiliate_id: str, *, start_date: str | NotGiven = NOT_GIVEN, end_date: str | NotGiven = NOT_GIVEN, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        """Get affiliate statistics."""
        return self._get(f"/marketing/affiliates/{affiliate_id}/stats", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout, query={"start_date": start_date, "end_date": end_date}), cast_to=object)

    def payouts(self, affiliate_id: str, *, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        """Get affiliate payouts."""
        return self._get(f"/marketing/affiliates/{affiliate_id}/payouts", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)


class AsyncAffiliatesResource(AsyncAPIResource):
    """Affiliate program management (async)."""

    @cached_property
    def with_raw_response(self) -> AsyncAffiliatesResourceWithRawResponse:
        return AsyncAffiliatesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncAffiliatesResourceWithStreamingResponse:
        return AsyncAffiliatesResourceWithStreamingResponse(self)

    async def list(self, *, status: str | NotGiven = NOT_GIVEN, limit: int | NotGiven = NOT_GIVEN, offset: int | NotGiven = NOT_GIVEN, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        return await self._get("/marketing/affiliates", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout, query={"status": status, "limit": limit, "offset": offset}), cast_to=object)

    async def get(self, affiliate_id: str, *, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        return await self._get(f"/marketing/affiliates/{affiliate_id}", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    async def create(self, *, user_id: str, commission_rate: float | NotGiven = NOT_GIVEN, metadata: Dict[str, Any] | NotGiven = NOT_GIVEN, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        return await self._post("/marketing/affiliates", body={"user_id": user_id, "commission_rate": commission_rate, "metadata": metadata}, options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    async def update(self, affiliate_id: str, *, commission_rate: float | NotGiven = NOT_GIVEN, status: str | NotGiven = NOT_GIVEN, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        return await self._put(f"/marketing/affiliates/{affiliate_id}", body={"commission_rate": commission_rate, "status": status}, options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    async def delete(self, affiliate_id: str, *, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        return await self._delete(f"/marketing/affiliates/{affiliate_id}", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    async def stats(self, affiliate_id: str, *, start_date: str | NotGiven = NOT_GIVEN, end_date: str | NotGiven = NOT_GIVEN, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        return await self._get(f"/marketing/affiliates/{affiliate_id}/stats", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout, query={"start_date": start_date, "end_date": end_date}), cast_to=object)

    async def payouts(self, affiliate_id: str, *, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        return await self._get(f"/marketing/affiliates/{affiliate_id}/payouts", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)


class AffiliatesResourceWithRawResponse:
    def __init__(self, affiliates: AffiliatesResource) -> None:
        self._affiliates = affiliates
        self.list = to_raw_response_wrapper(affiliates.list)
        self.get = to_raw_response_wrapper(affiliates.get)
        self.create = to_raw_response_wrapper(affiliates.create)
        self.update = to_raw_response_wrapper(affiliates.update)
        self.delete = to_raw_response_wrapper(affiliates.delete)
        self.stats = to_raw_response_wrapper(affiliates.stats)
        self.payouts = to_raw_response_wrapper(affiliates.payouts)


class AsyncAffiliatesResourceWithRawResponse:
    def __init__(self, affiliates: AsyncAffiliatesResource) -> None:
        self._affiliates = affiliates
        self.list = async_to_raw_response_wrapper(affiliates.list)
        self.get = async_to_raw_response_wrapper(affiliates.get)
        self.create = async_to_raw_response_wrapper(affiliates.create)
        self.update = async_to_raw_response_wrapper(affiliates.update)
        self.delete = async_to_raw_response_wrapper(affiliates.delete)
        self.stats = async_to_raw_response_wrapper(affiliates.stats)
        self.payouts = async_to_raw_response_wrapper(affiliates.payouts)


class AffiliatesResourceWithStreamingResponse:
    def __init__(self, affiliates: AffiliatesResource) -> None:
        self._affiliates = affiliates
        self.list = to_streamed_response_wrapper(affiliates.list)
        self.get = to_streamed_response_wrapper(affiliates.get)
        self.create = to_streamed_response_wrapper(affiliates.create)
        self.update = to_streamed_response_wrapper(affiliates.update)
        self.delete = to_streamed_response_wrapper(affiliates.delete)
        self.stats = to_streamed_response_wrapper(affiliates.stats)
        self.payouts = to_streamed_response_wrapper(affiliates.payouts)


class AsyncAffiliatesResourceWithStreamingResponse:
    def __init__(self, affiliates: AsyncAffiliatesResource) -> None:
        self._affiliates = affiliates
        self.list = async_to_streamed_response_wrapper(affiliates.list)
        self.get = async_to_streamed_response_wrapper(affiliates.get)
        self.create = async_to_streamed_response_wrapper(affiliates.create)
        self.update = async_to_streamed_response_wrapper(affiliates.update)
        self.delete = async_to_streamed_response_wrapper(affiliates.delete)
        self.stats = async_to_streamed_response_wrapper(affiliates.stats)
        self.payouts = async_to_streamed_response_wrapper(affiliates.payouts)
