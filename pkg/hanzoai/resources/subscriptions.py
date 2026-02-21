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

__all__ = ["SubscriptionsResource", "AsyncSubscriptionsResource"]


class SubscriptionsResource(SyncAPIResource):
    """Subscription management."""

    @cached_property
    def with_raw_response(self) -> SubscriptionsResourceWithRawResponse:
        return SubscriptionsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> SubscriptionsResourceWithStreamingResponse:
        return SubscriptionsResourceWithStreamingResponse(self)

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
        """List all subscriptions."""
        return self._get(
            "/commerce/subscriptions",
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
        subscription_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a specific subscription."""
        return self._get(
            f"/commerce/subscriptions/{subscription_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def create(
        self,
        *,
        plan_id: str,
        customer_id: str,
        payment_method_id: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a new subscription."""
        return self._post(
            "/commerce/subscriptions",
            body={"plan_id": plan_id, "customer_id": customer_id, "payment_method_id": payment_method_id},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def update(
        self,
        subscription_id: str,
        *,
        plan_id: str | NotGiven = NOT_GIVEN,
        quantity: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update a subscription."""
        return self._put(
            f"/commerce/subscriptions/{subscription_id}",
            body={"plan_id": plan_id, "quantity": quantity},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def cancel(
        self,
        subscription_id: str,
        *,
        at_period_end: bool = True,
        reason: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Cancel a subscription."""
        return self._post(
            f"/commerce/subscriptions/{subscription_id}/cancel",
            body={"at_period_end": at_period_end, "reason": reason},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def pause(
        self,
        subscription_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Pause a subscription."""
        return self._post(
            f"/commerce/subscriptions/{subscription_id}/pause",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def resume(
        self,
        subscription_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Resume a paused subscription."""
        return self._post(
            f"/commerce/subscriptions/{subscription_id}/resume",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def list_invoices(
        self,
        subscription_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List subscription invoices."""
        return self._get(
            f"/commerce/subscriptions/{subscription_id}/invoices",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class AsyncSubscriptionsResource(AsyncAPIResource):
    """Subscription management (async)."""

    @cached_property
    def with_raw_response(self) -> AsyncSubscriptionsResourceWithRawResponse:
        return AsyncSubscriptionsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncSubscriptionsResourceWithStreamingResponse:
        return AsyncSubscriptionsResourceWithStreamingResponse(self)

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
            "/commerce/subscriptions",
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
        subscription_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/commerce/subscriptions/{subscription_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def create(
        self,
        *,
        plan_id: str,
        customer_id: str,
        payment_method_id: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            "/commerce/subscriptions",
            body={"plan_id": plan_id, "customer_id": customer_id, "payment_method_id": payment_method_id},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def update(
        self,
        subscription_id: str,
        *,
        plan_id: str | NotGiven = NOT_GIVEN,
        quantity: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._put(
            f"/commerce/subscriptions/{subscription_id}",
            body={"plan_id": plan_id, "quantity": quantity},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def cancel(
        self,
        subscription_id: str,
        *,
        at_period_end: bool = True,
        reason: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            f"/commerce/subscriptions/{subscription_id}/cancel",
            body={"at_period_end": at_period_end, "reason": reason},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def pause(
        self,
        subscription_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            f"/commerce/subscriptions/{subscription_id}/pause",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def resume(
        self,
        subscription_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            f"/commerce/subscriptions/{subscription_id}/resume",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def list_invoices(
        self,
        subscription_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/commerce/subscriptions/{subscription_id}/invoices",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class SubscriptionsResourceWithRawResponse:
    def __init__(self, subscriptions: SubscriptionsResource) -> None:
        self._subscriptions = subscriptions
        self.list = to_raw_response_wrapper(subscriptions.list)
        self.get = to_raw_response_wrapper(subscriptions.get)
        self.create = to_raw_response_wrapper(subscriptions.create)
        self.update = to_raw_response_wrapper(subscriptions.update)
        self.cancel = to_raw_response_wrapper(subscriptions.cancel)
        self.pause = to_raw_response_wrapper(subscriptions.pause)
        self.resume = to_raw_response_wrapper(subscriptions.resume)
        self.list_invoices = to_raw_response_wrapper(subscriptions.list_invoices)


class AsyncSubscriptionsResourceWithRawResponse:
    def __init__(self, subscriptions: AsyncSubscriptionsResource) -> None:
        self._subscriptions = subscriptions
        self.list = async_to_raw_response_wrapper(subscriptions.list)
        self.get = async_to_raw_response_wrapper(subscriptions.get)
        self.create = async_to_raw_response_wrapper(subscriptions.create)
        self.update = async_to_raw_response_wrapper(subscriptions.update)
        self.cancel = async_to_raw_response_wrapper(subscriptions.cancel)
        self.pause = async_to_raw_response_wrapper(subscriptions.pause)
        self.resume = async_to_raw_response_wrapper(subscriptions.resume)
        self.list_invoices = async_to_raw_response_wrapper(subscriptions.list_invoices)


class SubscriptionsResourceWithStreamingResponse:
    def __init__(self, subscriptions: SubscriptionsResource) -> None:
        self._subscriptions = subscriptions
        self.list = to_streamed_response_wrapper(subscriptions.list)
        self.get = to_streamed_response_wrapper(subscriptions.get)
        self.create = to_streamed_response_wrapper(subscriptions.create)
        self.update = to_streamed_response_wrapper(subscriptions.update)
        self.cancel = to_streamed_response_wrapper(subscriptions.cancel)
        self.pause = to_streamed_response_wrapper(subscriptions.pause)
        self.resume = to_streamed_response_wrapper(subscriptions.resume)
        self.list_invoices = to_streamed_response_wrapper(subscriptions.list_invoices)


class AsyncSubscriptionsResourceWithStreamingResponse:
    def __init__(self, subscriptions: AsyncSubscriptionsResource) -> None:
        self._subscriptions = subscriptions
        self.list = async_to_streamed_response_wrapper(subscriptions.list)
        self.get = async_to_streamed_response_wrapper(subscriptions.get)
        self.create = async_to_streamed_response_wrapper(subscriptions.create)
        self.update = async_to_streamed_response_wrapper(subscriptions.update)
        self.cancel = async_to_streamed_response_wrapper(subscriptions.cancel)
        self.pause = async_to_streamed_response_wrapper(subscriptions.pause)
        self.resume = async_to_streamed_response_wrapper(subscriptions.resume)
        self.list_invoices = async_to_streamed_response_wrapper(subscriptions.list_invoices)
