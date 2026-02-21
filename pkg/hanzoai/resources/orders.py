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

__all__ = ["OrdersResource", "AsyncOrdersResource"]


class OrdersResource(SyncAPIResource):
    """Order management."""

    @cached_property
    def with_raw_response(self) -> OrdersResourceWithRawResponse:
        return OrdersResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> OrdersResourceWithStreamingResponse:
        return OrdersResourceWithStreamingResponse(self)

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
        """List all orders."""
        return self._get(
            "/commerce/orders",
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
        order_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a specific order."""
        return self._get(
            f"/commerce/orders/{order_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def create(
        self,
        *,
        cart_id: str,
        shipping_address: Dict[str, Any],
        billing_address: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a new order."""
        return self._post(
            "/commerce/orders",
            body={"cart_id": cart_id, "shipping_address": shipping_address, "billing_address": billing_address},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def update(
        self,
        order_id: str,
        *,
        status: str | NotGiven = NOT_GIVEN,
        tracking_number: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update an order."""
        return self._put(
            f"/commerce/orders/{order_id}",
            body={"status": status, "tracking_number": tracking_number},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def cancel(
        self,
        order_id: str,
        *,
        reason: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Cancel an order."""
        return self._post(
            f"/commerce/orders/{order_id}/cancel",
            body={"reason": reason},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def refund(
        self,
        order_id: str,
        *,
        amount: float | NotGiven = NOT_GIVEN,
        reason: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Refund an order."""
        return self._post(
            f"/commerce/orders/{order_id}/refund",
            body={"amount": amount, "reason": reason},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def list_items(
        self,
        order_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List order items."""
        return self._get(
            f"/commerce/orders/{order_id}/items",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class AsyncOrdersResource(AsyncAPIResource):
    """Order management (async)."""

    @cached_property
    def with_raw_response(self) -> AsyncOrdersResourceWithRawResponse:
        return AsyncOrdersResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncOrdersResourceWithStreamingResponse:
        return AsyncOrdersResourceWithStreamingResponse(self)

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
            "/commerce/orders",
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
        order_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/commerce/orders/{order_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def create(
        self,
        *,
        cart_id: str,
        shipping_address: Dict[str, Any],
        billing_address: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            "/commerce/orders",
            body={"cart_id": cart_id, "shipping_address": shipping_address, "billing_address": billing_address},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def update(
        self,
        order_id: str,
        *,
        status: str | NotGiven = NOT_GIVEN,
        tracking_number: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._put(
            f"/commerce/orders/{order_id}",
            body={"status": status, "tracking_number": tracking_number},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def cancel(
        self,
        order_id: str,
        *,
        reason: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            f"/commerce/orders/{order_id}/cancel",
            body={"reason": reason},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def refund(
        self,
        order_id: str,
        *,
        amount: float | NotGiven = NOT_GIVEN,
        reason: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            f"/commerce/orders/{order_id}/refund",
            body={"amount": amount, "reason": reason},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def list_items(
        self,
        order_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/commerce/orders/{order_id}/items",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class OrdersResourceWithRawResponse:
    def __init__(self, orders: OrdersResource) -> None:
        self._orders = orders
        self.list = to_raw_response_wrapper(orders.list)
        self.get = to_raw_response_wrapper(orders.get)
        self.create = to_raw_response_wrapper(orders.create)
        self.update = to_raw_response_wrapper(orders.update)
        self.cancel = to_raw_response_wrapper(orders.cancel)
        self.refund = to_raw_response_wrapper(orders.refund)
        self.list_items = to_raw_response_wrapper(orders.list_items)


class AsyncOrdersResourceWithRawResponse:
    def __init__(self, orders: AsyncOrdersResource) -> None:
        self._orders = orders
        self.list = async_to_raw_response_wrapper(orders.list)
        self.get = async_to_raw_response_wrapper(orders.get)
        self.create = async_to_raw_response_wrapper(orders.create)
        self.update = async_to_raw_response_wrapper(orders.update)
        self.cancel = async_to_raw_response_wrapper(orders.cancel)
        self.refund = async_to_raw_response_wrapper(orders.refund)
        self.list_items = async_to_raw_response_wrapper(orders.list_items)


class OrdersResourceWithStreamingResponse:
    def __init__(self, orders: OrdersResource) -> None:
        self._orders = orders
        self.list = to_streamed_response_wrapper(orders.list)
        self.get = to_streamed_response_wrapper(orders.get)
        self.create = to_streamed_response_wrapper(orders.create)
        self.update = to_streamed_response_wrapper(orders.update)
        self.cancel = to_streamed_response_wrapper(orders.cancel)
        self.refund = to_streamed_response_wrapper(orders.refund)
        self.list_items = to_streamed_response_wrapper(orders.list_items)


class AsyncOrdersResourceWithStreamingResponse:
    def __init__(self, orders: AsyncOrdersResource) -> None:
        self._orders = orders
        self.list = async_to_streamed_response_wrapper(orders.list)
        self.get = async_to_streamed_response_wrapper(orders.get)
        self.create = async_to_streamed_response_wrapper(orders.create)
        self.update = async_to_streamed_response_wrapper(orders.update)
        self.cancel = async_to_streamed_response_wrapper(orders.cancel)
        self.refund = async_to_streamed_response_wrapper(orders.refund)
        self.list_items = async_to_streamed_response_wrapper(orders.list_items)
