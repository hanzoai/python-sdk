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

__all__ = ["CheckoutResource", "AsyncCheckoutResource"]


class CheckoutResource(SyncAPIResource):
    """Checkout and payment processing."""

    @cached_property
    def with_raw_response(self) -> CheckoutResourceWithRawResponse:
        return CheckoutResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> CheckoutResourceWithStreamingResponse:
        return CheckoutResourceWithStreamingResponse(self)

    def create_session(
        self,
        *,
        cart_id: str,
        success_url: str,
        cancel_url: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a checkout session."""
        return self._post(
            "/commerce/checkout/sessions",
            body={"cart_id": cart_id, "success_url": success_url, "cancel_url": cancel_url},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def get_session(
        self,
        session_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get checkout session details."""
        return self._get(
            f"/commerce/checkout/sessions/{session_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def complete(
        self,
        session_id: str,
        *,
        payment_method: str,
        payment_details: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Complete a checkout session."""
        return self._post(
            f"/commerce/checkout/sessions/{session_id}/complete",
            body={"payment_method": payment_method, "payment_details": payment_details},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def expire(
        self,
        session_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Expire a checkout session."""
        return self._post(
            f"/commerce/checkout/sessions/{session_id}/expire",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def list_payment_methods(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List available payment methods."""
        return self._get(
            "/commerce/checkout/payment-methods",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class AsyncCheckoutResource(AsyncAPIResource):
    """Checkout and payment processing (async)."""

    @cached_property
    def with_raw_response(self) -> AsyncCheckoutResourceWithRawResponse:
        return AsyncCheckoutResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncCheckoutResourceWithStreamingResponse:
        return AsyncCheckoutResourceWithStreamingResponse(self)

    async def create_session(
        self,
        *,
        cart_id: str,
        success_url: str,
        cancel_url: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            "/commerce/checkout/sessions",
            body={"cart_id": cart_id, "success_url": success_url, "cancel_url": cancel_url},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def get_session(
        self,
        session_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/commerce/checkout/sessions/{session_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def complete(
        self,
        session_id: str,
        *,
        payment_method: str,
        payment_details: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            f"/commerce/checkout/sessions/{session_id}/complete",
            body={"payment_method": payment_method, "payment_details": payment_details},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def expire(
        self,
        session_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            f"/commerce/checkout/sessions/{session_id}/expire",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def list_payment_methods(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            "/commerce/checkout/payment-methods",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class CheckoutResourceWithRawResponse:
    def __init__(self, checkout: CheckoutResource) -> None:
        self._checkout = checkout
        self.create_session = to_raw_response_wrapper(checkout.create_session)
        self.get_session = to_raw_response_wrapper(checkout.get_session)
        self.complete = to_raw_response_wrapper(checkout.complete)
        self.expire = to_raw_response_wrapper(checkout.expire)
        self.list_payment_methods = to_raw_response_wrapper(checkout.list_payment_methods)


class AsyncCheckoutResourceWithRawResponse:
    def __init__(self, checkout: AsyncCheckoutResource) -> None:
        self._checkout = checkout
        self.create_session = async_to_raw_response_wrapper(checkout.create_session)
        self.get_session = async_to_raw_response_wrapper(checkout.get_session)
        self.complete = async_to_raw_response_wrapper(checkout.complete)
        self.expire = async_to_raw_response_wrapper(checkout.expire)
        self.list_payment_methods = async_to_raw_response_wrapper(checkout.list_payment_methods)


class CheckoutResourceWithStreamingResponse:
    def __init__(self, checkout: CheckoutResource) -> None:
        self._checkout = checkout
        self.create_session = to_streamed_response_wrapper(checkout.create_session)
        self.get_session = to_streamed_response_wrapper(checkout.get_session)
        self.complete = to_streamed_response_wrapper(checkout.complete)
        self.expire = to_streamed_response_wrapper(checkout.expire)
        self.list_payment_methods = to_streamed_response_wrapper(checkout.list_payment_methods)


class AsyncCheckoutResourceWithStreamingResponse:
    def __init__(self, checkout: AsyncCheckoutResource) -> None:
        self._checkout = checkout
        self.create_session = async_to_streamed_response_wrapper(checkout.create_session)
        self.get_session = async_to_streamed_response_wrapper(checkout.get_session)
        self.complete = async_to_streamed_response_wrapper(checkout.complete)
        self.expire = async_to_streamed_response_wrapper(checkout.expire)
        self.list_payment_methods = async_to_streamed_response_wrapper(checkout.list_payment_methods)
