# Hanzo AI SDK

from __future__ import annotations

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

__all__ = ["CartResource", "AsyncCartResource"]


class CartResource(SyncAPIResource):
    """Shopping cart management."""

    @cached_property
    def with_raw_response(self) -> CartResourceWithRawResponse:
        return CartResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> CartResourceWithStreamingResponse:
        return CartResourceWithStreamingResponse(self)

    def get(
        self,
        cart_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get cart contents."""
        return self._get(
            f"/commerce/cart/{cart_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def create(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a new cart."""
        return self._post(
            "/commerce/cart",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def add_item(
        self,
        cart_id: str,
        *,
        product_id: str,
        quantity: int = 1,
        variant_id: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Add item to cart."""
        return self._post(
            f"/commerce/cart/{cart_id}/items",
            body={"product_id": product_id, "quantity": quantity, "variant_id": variant_id},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def update_item(
        self,
        cart_id: str,
        item_id: str,
        *,
        quantity: int,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update cart item quantity."""
        return self._put(
            f"/commerce/cart/{cart_id}/items/{item_id}",
            body={"quantity": quantity},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def remove_item(
        self,
        cart_id: str,
        item_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Remove item from cart."""
        return self._delete(
            f"/commerce/cart/{cart_id}/items/{item_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def clear(
        self,
        cart_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Clear all items from cart."""
        return self._delete(
            f"/commerce/cart/{cart_id}/items",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def apply_coupon(
        self,
        cart_id: str,
        *,
        code: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Apply coupon to cart."""
        return self._post(
            f"/commerce/cart/{cart_id}/coupon",
            body={"code": code},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class AsyncCartResource(AsyncAPIResource):
    """Shopping cart management (async)."""

    @cached_property
    def with_raw_response(self) -> AsyncCartResourceWithRawResponse:
        return AsyncCartResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncCartResourceWithStreamingResponse:
        return AsyncCartResourceWithStreamingResponse(self)

    async def get(
        self,
        cart_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/commerce/cart/{cart_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def create(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            "/commerce/cart",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def add_item(
        self,
        cart_id: str,
        *,
        product_id: str,
        quantity: int = 1,
        variant_id: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            f"/commerce/cart/{cart_id}/items",
            body={"product_id": product_id, "quantity": quantity, "variant_id": variant_id},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def update_item(
        self,
        cart_id: str,
        item_id: str,
        *,
        quantity: int,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._put(
            f"/commerce/cart/{cart_id}/items/{item_id}",
            body={"quantity": quantity},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def remove_item(
        self,
        cart_id: str,
        item_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._delete(
            f"/commerce/cart/{cart_id}/items/{item_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def clear(
        self,
        cart_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._delete(
            f"/commerce/cart/{cart_id}/items",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def apply_coupon(
        self,
        cart_id: str,
        *,
        code: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            f"/commerce/cart/{cart_id}/coupon",
            body={"code": code},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class CartResourceWithRawResponse:
    def __init__(self, cart: CartResource) -> None:
        self._cart = cart
        self.get = to_raw_response_wrapper(cart.get)
        self.create = to_raw_response_wrapper(cart.create)
        self.add_item = to_raw_response_wrapper(cart.add_item)
        self.update_item = to_raw_response_wrapper(cart.update_item)
        self.remove_item = to_raw_response_wrapper(cart.remove_item)
        self.clear = to_raw_response_wrapper(cart.clear)
        self.apply_coupon = to_raw_response_wrapper(cart.apply_coupon)


class AsyncCartResourceWithRawResponse:
    def __init__(self, cart: AsyncCartResource) -> None:
        self._cart = cart
        self.get = async_to_raw_response_wrapper(cart.get)
        self.create = async_to_raw_response_wrapper(cart.create)
        self.add_item = async_to_raw_response_wrapper(cart.add_item)
        self.update_item = async_to_raw_response_wrapper(cart.update_item)
        self.remove_item = async_to_raw_response_wrapper(cart.remove_item)
        self.clear = async_to_raw_response_wrapper(cart.clear)
        self.apply_coupon = async_to_raw_response_wrapper(cart.apply_coupon)


class CartResourceWithStreamingResponse:
    def __init__(self, cart: CartResource) -> None:
        self._cart = cart
        self.get = to_streamed_response_wrapper(cart.get)
        self.create = to_streamed_response_wrapper(cart.create)
        self.add_item = to_streamed_response_wrapper(cart.add_item)
        self.update_item = to_streamed_response_wrapper(cart.update_item)
        self.remove_item = to_streamed_response_wrapper(cart.remove_item)
        self.clear = to_streamed_response_wrapper(cart.clear)
        self.apply_coupon = to_streamed_response_wrapper(cart.apply_coupon)


class AsyncCartResourceWithStreamingResponse:
    def __init__(self, cart: AsyncCartResource) -> None:
        self._cart = cart
        self.get = async_to_streamed_response_wrapper(cart.get)
        self.create = async_to_streamed_response_wrapper(cart.create)
        self.add_item = async_to_streamed_response_wrapper(cart.add_item)
        self.update_item = async_to_streamed_response_wrapper(cart.update_item)
        self.remove_item = async_to_streamed_response_wrapper(cart.remove_item)
        self.clear = async_to_streamed_response_wrapper(cart.clear)
        self.apply_coupon = async_to_streamed_response_wrapper(cart.apply_coupon)
