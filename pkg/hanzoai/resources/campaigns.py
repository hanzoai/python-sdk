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

__all__ = ["CampaignsResource", "AsyncCampaignsResource"]


class CampaignsResource(SyncAPIResource):
    """Marketing campaign management."""

    @cached_property
    def with_raw_response(self) -> CampaignsResourceWithRawResponse:
        return CampaignsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> CampaignsResourceWithStreamingResponse:
        return CampaignsResourceWithStreamingResponse(self)

    def list(
        self,
        *,
        status: str | NotGiven = NOT_GIVEN,
        type: str | NotGiven = NOT_GIVEN,
        limit: int | NotGiven = NOT_GIVEN,
        offset: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all campaigns."""
        return self._get(
            "/marketing/campaigns",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"status": status, "type": type, "limit": limit, "offset": offset},
            ),
            cast_to=object,
        )

    def get(
        self,
        campaign_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a specific campaign."""
        return self._get(
            f"/marketing/campaigns/{campaign_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def create(
        self,
        *,
        name: str,
        type: str,
        start_date: str,
        end_date: str | NotGiven = NOT_GIVEN,
        budget: float | NotGiven = NOT_GIVEN,
        targeting: Dict[str, Any] | NotGiven = NOT_GIVEN,
        content: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a new campaign."""
        return self._post(
            "/marketing/campaigns",
            body={
                "name": name,
                "type": type,
                "start_date": start_date,
                "end_date": end_date,
                "budget": budget,
                "targeting": targeting,
                "content": content,
            },
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def update(
        self,
        campaign_id: str,
        *,
        name: str | NotGiven = NOT_GIVEN,
        status: str | NotGiven = NOT_GIVEN,
        budget: float | NotGiven = NOT_GIVEN,
        targeting: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update a campaign."""
        return self._put(
            f"/marketing/campaigns/{campaign_id}",
            body={"name": name, "status": status, "budget": budget, "targeting": targeting},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def delete(
        self,
        campaign_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a campaign."""
        return self._delete(
            f"/marketing/campaigns/{campaign_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def start(
        self,
        campaign_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Start a campaign."""
        return self._post(
            f"/marketing/campaigns/{campaign_id}/start",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def pause(
        self,
        campaign_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Pause a campaign."""
        return self._post(
            f"/marketing/campaigns/{campaign_id}/pause",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def stats(
        self,
        campaign_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get campaign statistics."""
        return self._get(
            f"/marketing/campaigns/{campaign_id}/stats",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class AsyncCampaignsResource(AsyncAPIResource):
    """Marketing campaign management (async)."""

    @cached_property
    def with_raw_response(self) -> AsyncCampaignsResourceWithRawResponse:
        return AsyncCampaignsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncCampaignsResourceWithStreamingResponse:
        return AsyncCampaignsResourceWithStreamingResponse(self)

    async def list(
        self,
        *,
        status: str | NotGiven = NOT_GIVEN,
        type: str | NotGiven = NOT_GIVEN,
        limit: int | NotGiven = NOT_GIVEN,
        offset: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            "/marketing/campaigns",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"status": status, "type": type, "limit": limit, "offset": offset},
            ),
            cast_to=object,
        )

    async def get(
        self,
        campaign_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/marketing/campaigns/{campaign_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def create(
        self,
        *,
        name: str,
        type: str,
        start_date: str,
        end_date: str | NotGiven = NOT_GIVEN,
        budget: float | NotGiven = NOT_GIVEN,
        targeting: Dict[str, Any] | NotGiven = NOT_GIVEN,
        content: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            "/marketing/campaigns",
            body={
                "name": name,
                "type": type,
                "start_date": start_date,
                "end_date": end_date,
                "budget": budget,
                "targeting": targeting,
                "content": content,
            },
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def update(
        self,
        campaign_id: str,
        *,
        name: str | NotGiven = NOT_GIVEN,
        status: str | NotGiven = NOT_GIVEN,
        budget: float | NotGiven = NOT_GIVEN,
        targeting: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._put(
            f"/marketing/campaigns/{campaign_id}",
            body={"name": name, "status": status, "budget": budget, "targeting": targeting},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def delete(
        self,
        campaign_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._delete(
            f"/marketing/campaigns/{campaign_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def start(
        self,
        campaign_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            f"/marketing/campaigns/{campaign_id}/start",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def pause(
        self,
        campaign_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            f"/marketing/campaigns/{campaign_id}/pause",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def stats(
        self,
        campaign_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/marketing/campaigns/{campaign_id}/stats",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class CampaignsResourceWithRawResponse:
    def __init__(self, campaigns: CampaignsResource) -> None:
        self._campaigns = campaigns
        self.list = to_raw_response_wrapper(campaigns.list)
        self.get = to_raw_response_wrapper(campaigns.get)
        self.create = to_raw_response_wrapper(campaigns.create)
        self.update = to_raw_response_wrapper(campaigns.update)
        self.delete = to_raw_response_wrapper(campaigns.delete)
        self.start = to_raw_response_wrapper(campaigns.start)
        self.pause = to_raw_response_wrapper(campaigns.pause)
        self.stats = to_raw_response_wrapper(campaigns.stats)


class AsyncCampaignsResourceWithRawResponse:
    def __init__(self, campaigns: AsyncCampaignsResource) -> None:
        self._campaigns = campaigns
        self.list = async_to_raw_response_wrapper(campaigns.list)
        self.get = async_to_raw_response_wrapper(campaigns.get)
        self.create = async_to_raw_response_wrapper(campaigns.create)
        self.update = async_to_raw_response_wrapper(campaigns.update)
        self.delete = async_to_raw_response_wrapper(campaigns.delete)
        self.start = async_to_raw_response_wrapper(campaigns.start)
        self.pause = async_to_raw_response_wrapper(campaigns.pause)
        self.stats = async_to_raw_response_wrapper(campaigns.stats)


class CampaignsResourceWithStreamingResponse:
    def __init__(self, campaigns: CampaignsResource) -> None:
        self._campaigns = campaigns
        self.list = to_streamed_response_wrapper(campaigns.list)
        self.get = to_streamed_response_wrapper(campaigns.get)
        self.create = to_streamed_response_wrapper(campaigns.create)
        self.update = to_streamed_response_wrapper(campaigns.update)
        self.delete = to_streamed_response_wrapper(campaigns.delete)
        self.start = to_streamed_response_wrapper(campaigns.start)
        self.pause = to_streamed_response_wrapper(campaigns.pause)
        self.stats = to_streamed_response_wrapper(campaigns.stats)


class AsyncCampaignsResourceWithStreamingResponse:
    def __init__(self, campaigns: AsyncCampaignsResource) -> None:
        self._campaigns = campaigns
        self.list = async_to_streamed_response_wrapper(campaigns.list)
        self.get = async_to_streamed_response_wrapper(campaigns.get)
        self.create = async_to_streamed_response_wrapper(campaigns.create)
        self.update = async_to_streamed_response_wrapper(campaigns.update)
        self.delete = async_to_streamed_response_wrapper(campaigns.delete)
        self.start = async_to_streamed_response_wrapper(campaigns.start)
        self.pause = async_to_streamed_response_wrapper(campaigns.pause)
        self.stats = async_to_streamed_response_wrapper(campaigns.stats)
