# Hanzo AI SDK

from __future__ import annotations

from typing import Any, Dict

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

__all__ = ["ReferralsResource", "AsyncReferralsResource"]


class ReferralsResource(SyncAPIResource):
    """Referral program management."""

    @cached_property
    def with_raw_response(self) -> ReferralsResourceWithRawResponse:
        return ReferralsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ReferralsResourceWithStreamingResponse:
        return ReferralsResourceWithStreamingResponse(self)

    def list(
        self,
        *,
        status: str | NotGiven = NOT_GIVEN,
        limit: int | NotGiven = NOT_GIVEN,
        offset: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all referrals."""
        return self._get(
            "/marketing/referrals",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"status": status, "limit": limit, "offset": offset},
            ),
            cast_to=object,
        )

    def get(
        self,
        referral_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a specific referral."""
        return self._get(
            f"/marketing/referrals/{referral_id}",
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
        referrer_id: str,
        referred_email: str,
        metadata: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a new referral."""
        return self._post(
            "/marketing/referrals",
            body={
                "referrer_id": referrer_id,
                "referred_email": referred_email,
                "metadata": metadata,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def track(
        self,
        referral_code: str,
        *,
        event: str,
        metadata: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Track a referral event."""
        return self._post(
            f"/marketing/referrals/{referral_code}/track",
            body={"event": event, "metadata": metadata},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def validate(
        self,
        referral_code: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Validate a referral code."""
        return self._get(
            f"/marketing/referrals/{referral_code}/validate",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def complete(
        self,
        referral_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Mark a referral as completed."""
        return self._post(
            f"/marketing/referrals/{referral_id}/complete",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def stats(
        self,
        user_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get referral stats for a user."""
        return self._get(
            f"/marketing/referrals/stats/{user_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class AsyncReferralsResource(AsyncAPIResource):
    """Referral program management (async)."""

    @cached_property
    def with_raw_response(self) -> AsyncReferralsResourceWithRawResponse:
        return AsyncReferralsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncReferralsResourceWithStreamingResponse:
        return AsyncReferralsResourceWithStreamingResponse(self)

    async def list(
        self,
        *,
        status: str | NotGiven = NOT_GIVEN,
        limit: int | NotGiven = NOT_GIVEN,
        offset: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            "/marketing/referrals",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"status": status, "limit": limit, "offset": offset},
            ),
            cast_to=object,
        )

    async def get(
        self,
        referral_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/marketing/referrals/{referral_id}",
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
        referrer_id: str,
        referred_email: str,
        metadata: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            "/marketing/referrals",
            body={
                "referrer_id": referrer_id,
                "referred_email": referred_email,
                "metadata": metadata,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def track(
        self,
        referral_code: str,
        *,
        event: str,
        metadata: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            f"/marketing/referrals/{referral_code}/track",
            body={"event": event, "metadata": metadata},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def validate(
        self,
        referral_code: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/marketing/referrals/{referral_code}/validate",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def complete(
        self,
        referral_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            f"/marketing/referrals/{referral_id}/complete",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def stats(
        self,
        user_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/marketing/referrals/stats/{user_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class ReferralsResourceWithRawResponse:
    def __init__(self, referrals: ReferralsResource) -> None:
        self._referrals = referrals
        self.list = to_raw_response_wrapper(referrals.list)
        self.get = to_raw_response_wrapper(referrals.get)
        self.create = to_raw_response_wrapper(referrals.create)
        self.track = to_raw_response_wrapper(referrals.track)
        self.validate = to_raw_response_wrapper(referrals.validate)
        self.complete = to_raw_response_wrapper(referrals.complete)
        self.stats = to_raw_response_wrapper(referrals.stats)


class AsyncReferralsResourceWithRawResponse:
    def __init__(self, referrals: AsyncReferralsResource) -> None:
        self._referrals = referrals
        self.list = async_to_raw_response_wrapper(referrals.list)
        self.get = async_to_raw_response_wrapper(referrals.get)
        self.create = async_to_raw_response_wrapper(referrals.create)
        self.track = async_to_raw_response_wrapper(referrals.track)
        self.validate = async_to_raw_response_wrapper(referrals.validate)
        self.complete = async_to_raw_response_wrapper(referrals.complete)
        self.stats = async_to_raw_response_wrapper(referrals.stats)


class ReferralsResourceWithStreamingResponse:
    def __init__(self, referrals: ReferralsResource) -> None:
        self._referrals = referrals
        self.list = to_streamed_response_wrapper(referrals.list)
        self.get = to_streamed_response_wrapper(referrals.get)
        self.create = to_streamed_response_wrapper(referrals.create)
        self.track = to_streamed_response_wrapper(referrals.track)
        self.validate = to_streamed_response_wrapper(referrals.validate)
        self.complete = to_streamed_response_wrapper(referrals.complete)
        self.stats = to_streamed_response_wrapper(referrals.stats)


class AsyncReferralsResourceWithStreamingResponse:
    def __init__(self, referrals: AsyncReferralsResource) -> None:
        self._referrals = referrals
        self.list = async_to_streamed_response_wrapper(referrals.list)
        self.get = async_to_streamed_response_wrapper(referrals.get)
        self.create = async_to_streamed_response_wrapper(referrals.create)
        self.track = async_to_streamed_response_wrapper(referrals.track)
        self.validate = async_to_streamed_response_wrapper(referrals.validate)
        self.complete = async_to_streamed_response_wrapper(referrals.complete)
        self.stats = async_to_streamed_response_wrapper(referrals.stats)
