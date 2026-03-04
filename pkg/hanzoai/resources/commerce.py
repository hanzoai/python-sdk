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

__all__ = ["CommerceResource", "AsyncCommerceResource"]


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------


class OrdersResource(SyncAPIResource):
    """Order management and payment operations."""

    def list(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List orders."""
        return self._get(
            "/commerce/order",
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
        body: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create an order."""
        return self._post(
            "/commerce/order",
            body=body,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
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
        """Get an order by ID."""
        return self._get(
            f"/commerce/order/{order_id}",
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
        order_id: str,
        *,
        body: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update an order."""
        return self._patch(
            f"/commerce/order/{order_id}",
            body=body,
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
        order_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete an order."""
        return self._delete(
            f"/commerce/order/{order_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def authorize(
        self,
        order_id: str,
        *,
        body: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Authorize payment for an order."""
        return self._post(
            f"/commerce/order/{order_id}/authorize",
            body=body if not isinstance(body, NotGiven) else None,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def capture(
        self,
        order_id: str,
        *,
        body: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Capture payment for an order."""
        return self._post(
            f"/commerce/order/{order_id}/capture",
            body=body if not isinstance(body, NotGiven) else None,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def charge(
        self,
        order_id: str,
        *,
        body: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Charge an order."""
        return self._post(
            f"/commerce/order/{order_id}/charge",
            body=body if not isinstance(body, NotGiven) else None,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def refund(
        self,
        order_id: str,
        *,
        body: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Refund an order."""
        return self._post(
            f"/commerce/order/{order_id}/refund",
            body=body if not isinstance(body, NotGiven) else None,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def payments(
        self,
        order_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List payments for an order."""
        return self._get(
            f"/commerce/order/{order_id}/payments",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def returns(
        self,
        order_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List returns for an order."""
        return self._get(
            f"/commerce/order/{order_id}/returns",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def status(
        self,
        order_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get order status."""
        return self._get(
            f"/commerce/order/{order_id}/status",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class AsyncOrdersResource(AsyncAPIResource):
    """Order management and payment operations (async)."""

    async def list(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            "/commerce/order",
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
        body: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            "/commerce/order",
            body=body,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
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
            f"/commerce/order/{order_id}",
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
        order_id: str,
        *,
        body: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._patch(
            f"/commerce/order/{order_id}",
            body=body,
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
        order_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._delete(
            f"/commerce/order/{order_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def authorize(
        self,
        order_id: str,
        *,
        body: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            f"/commerce/order/{order_id}/authorize",
            body=body if not isinstance(body, NotGiven) else None,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def capture(
        self,
        order_id: str,
        *,
        body: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            f"/commerce/order/{order_id}/capture",
            body=body if not isinstance(body, NotGiven) else None,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def charge(
        self,
        order_id: str,
        *,
        body: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            f"/commerce/order/{order_id}/charge",
            body=body if not isinstance(body, NotGiven) else None,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def refund(
        self,
        order_id: str,
        *,
        body: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            f"/commerce/order/{order_id}/refund",
            body=body if not isinstance(body, NotGiven) else None,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def payments(
        self,
        order_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/commerce/order/{order_id}/payments",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def returns(
        self,
        order_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/commerce/order/{order_id}/returns",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def status(
        self,
        order_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/commerce/order/{order_id}/status",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------


class ProductsResource(SyncAPIResource):
    """Product catalog management."""

    def list(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List products."""
        return self._get(
            "/commerce/product",
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
        body: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a product."""
        return self._post(
            "/commerce/product",
            body=body,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def get(
        self,
        product_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a product by ID."""
        return self._get(
            f"/commerce/product/{product_id}",
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
        product_id: str,
        *,
        body: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update a product."""
        return self._patch(
            f"/commerce/product/{product_id}",
            body=body,
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
        product_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a product."""
        return self._delete(
            f"/commerce/product/{product_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class AsyncProductsResource(AsyncAPIResource):
    """Product catalog management (async)."""

    async def list(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            "/commerce/product",
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
        body: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            "/commerce/product",
            body=body,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def get(
        self,
        product_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/commerce/product/{product_id}",
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
        product_id: str,
        *,
        body: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._patch(
            f"/commerce/product/{product_id}",
            body=body,
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
        product_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._delete(
            f"/commerce/product/{product_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


# ---------------------------------------------------------------------------
# Variants
# ---------------------------------------------------------------------------


class VariantsResource(SyncAPIResource):
    """Product variant management."""

    def list(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List variants."""
        return self._get(
            "/commerce/variant",
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
        body: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a variant."""
        return self._post(
            "/commerce/variant",
            body=body,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def get(
        self,
        variant_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a variant by ID."""
        return self._get(
            f"/commerce/variant/{variant_id}",
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
        variant_id: str,
        *,
        body: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update a variant."""
        return self._patch(
            f"/commerce/variant/{variant_id}",
            body=body,
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
        variant_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a variant."""
        return self._delete(
            f"/commerce/variant/{variant_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class AsyncVariantsResource(AsyncAPIResource):
    """Product variant management (async)."""

    async def list(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            "/commerce/variant",
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
        body: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            "/commerce/variant",
            body=body,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def get(
        self,
        variant_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/commerce/variant/{variant_id}",
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
        variant_id: str,
        *,
        body: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._patch(
            f"/commerce/variant/{variant_id}",
            body=body,
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
        variant_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._delete(
            f"/commerce/variant/{variant_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


# ---------------------------------------------------------------------------
# Collections
# ---------------------------------------------------------------------------


class CollectionsResource(SyncAPIResource):
    """Product collection management."""

    def list(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List collections."""
        return self._get(
            "/commerce/collection",
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
        body: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a collection."""
        return self._post(
            "/commerce/collection",
            body=body,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def get(
        self,
        collection_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a collection by ID."""
        return self._get(
            f"/commerce/collection/{collection_id}",
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
        collection_id: str,
        *,
        body: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update a collection."""
        return self._patch(
            f"/commerce/collection/{collection_id}",
            body=body,
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
        collection_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a collection."""
        return self._delete(
            f"/commerce/collection/{collection_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class AsyncCollectionsResource(AsyncAPIResource):
    """Product collection management (async)."""

    async def list(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            "/commerce/collection",
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
        body: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            "/commerce/collection",
            body=body,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def get(
        self,
        collection_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/commerce/collection/{collection_id}",
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
        collection_id: str,
        *,
        body: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._patch(
            f"/commerce/collection/{collection_id}",
            body=body,
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
        collection_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._delete(
            f"/commerce/collection/{collection_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------


class TransactionsResource(SyncAPIResource):
    """Transaction management."""

    def list(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List transactions."""
        return self._get(
            "/commerce/transaction",
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
        body: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a transaction."""
        return self._post(
            "/commerce/transaction",
            body=body,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def get_by_kind(
        self,
        kind: str,
        transaction_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get transactions by kind and ID."""
        return self._get(
            f"/commerce/transaction/{kind}/{transaction_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class AsyncTransactionsResource(AsyncAPIResource):
    """Transaction management (async)."""

    async def list(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            "/commerce/transaction",
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
        body: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            "/commerce/transaction",
            body=body,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def get_by_kind(
        self,
        kind: str,
        transaction_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/commerce/transaction/{kind}/{transaction_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


# ---------------------------------------------------------------------------
# Accounts
# ---------------------------------------------------------------------------


class AccountsResource(SyncAPIResource):
    """Account authentication and management."""

    def login(
        self,
        *,
        email: str,
        password: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Login to an account."""
        return self._post(
            "/commerce/account/login",
            body={"email": email, "password": password},
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
        body: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a new account."""
        return self._post(
            "/commerce/account/create",
            body=body,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def get(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get current account."""
        return self._get(
            "/commerce/account",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def exists(
        self,
        email: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Check if account exists by email."""
        return self._get(
            f"/commerce/account/exists/{email}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class AsyncAccountsResource(AsyncAPIResource):
    """Account authentication and management (async)."""

    async def login(
        self,
        *,
        email: str,
        password: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            "/commerce/account/login",
            body={"email": email, "password": password},
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
        body: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            "/commerce/account/create",
            body=body,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def get(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            "/commerce/account",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def exists(
        self,
        email: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/commerce/account/exists/{email}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


# ---------------------------------------------------------------------------
# Users (admin)
# ---------------------------------------------------------------------------


class UsersResource(SyncAPIResource):
    """Admin user management."""

    def list(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List users."""
        return self._get(
            "/commerce/user",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def get(
        self,
        user_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a user by ID."""
        return self._get(
            f"/commerce/user/{user_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def orders(
        self,
        user_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get orders for a user."""
        return self._get(
            f"/commerce/user/{user_id}/orders",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def transactions(
        self,
        user_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get transactions for a user."""
        return self._get(
            f"/commerce/user/{user_id}/transactions",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def wallet(
        self,
        user_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get wallet for a user."""
        return self._get(
            f"/commerce/user/{user_id}/wallet",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class AsyncUsersResource(AsyncAPIResource):
    """Admin user management (async)."""

    async def list(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            "/commerce/user",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def get(
        self,
        user_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/commerce/user/{user_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def orders(
        self,
        user_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/commerce/user/{user_id}/orders",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def transactions(
        self,
        user_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/commerce/user/{user_id}/transactions",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def wallet(
        self,
        user_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/commerce/user/{user_id}/wallet",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


class SearchResource(SyncAPIResource):
    """Commerce search operations."""

    def users(
        self,
        *,
        q: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Search users."""
        return self._get(
            "/commerce/search/user",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"q": q},
            ),
            cast_to=object,
        )

    def orders(
        self,
        *,
        q: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Search orders."""
        return self._get(
            "/commerce/search/order",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"q": q},
            ),
            cast_to=object,
        )


class AsyncSearchResource(AsyncAPIResource):
    """Commerce search operations (async)."""

    async def users(
        self,
        *,
        q: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            "/commerce/search/user",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"q": q},
            ),
            cast_to=object,
        )

    async def orders(
        self,
        *,
        q: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            "/commerce/search/order",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"q": q},
            ),
            cast_to=object,
        )


# ---------------------------------------------------------------------------
# Subscriptions
# ---------------------------------------------------------------------------


class SubscriptionsResource(SyncAPIResource):
    """Subscription management (legacy)."""

    def create(
        self,
        *,
        body: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a subscription."""
        return self._post(
            "/commerce/subscribe",
            body=body,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
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
        """Get a subscription by ID."""
        return self._get(
            f"/commerce/subscribe/{subscription_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class AsyncSubscriptionsResource(AsyncAPIResource):
    """Subscription management (legacy, async)."""

    async def create(
        self,
        *,
        body: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            "/commerce/subscribe",
            body=body,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
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
            f"/commerce/subscribe/{subscription_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


# ---------------------------------------------------------------------------
# Webhooks
# ---------------------------------------------------------------------------


class WebhooksResource(SyncAPIResource):
    """Webhook management."""

    def list(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List webhooks."""
        return self._get(
            "/commerce/webhook",
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
        body: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a webhook."""
        return self._post(
            "/commerce/webhook",
            body=body,
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
        webhook_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a webhook."""
        return self._delete(
            f"/commerce/webhook/{webhook_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class AsyncWebhooksResource(AsyncAPIResource):
    """Webhook management (async)."""

    async def list(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            "/commerce/webhook",
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
        body: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            "/commerce/webhook",
            body=body,
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
        webhook_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._delete(
            f"/commerce/webhook/{webhook_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


# ---------------------------------------------------------------------------
# Stores
# ---------------------------------------------------------------------------


class StoresResource(SyncAPIResource):
    """Store and storefront management."""

    def list(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List stores."""
        return self._get(
            "/commerce/store",
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
        body: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a store."""
        return self._post(
            "/commerce/store",
            body=body,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def get(
        self,
        store_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a store by ID."""
        return self._get(
            f"/commerce/store/{store_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def product(
        self,
        store_id: str,
        product_key: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a product in a store by key."""
        return self._get(
            f"/commerce/store/{store_id}/product/{product_key}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def listings(
        self,
        store_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get store listings."""
        return self._get(
            f"/commerce/store/{store_id}/listing",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class AsyncStoresResource(AsyncAPIResource):
    """Store and storefront management (async)."""

    async def list(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            "/commerce/store",
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
        body: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            "/commerce/store",
            body=body,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def get(
        self,
        store_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/commerce/store/{store_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def product(
        self,
        store_id: str,
        product_key: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/commerce/store/{store_id}/product/{product_key}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def listings(
        self,
        store_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/commerce/store/{store_id}/listing",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


# ---------------------------------------------------------------------------
# Discounts
# ---------------------------------------------------------------------------


class DiscountsResource(SyncAPIResource):
    """Discount management."""

    def list(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List discounts."""
        return self._get(
            "/commerce/discount",
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
        body: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a discount."""
        return self._post(
            "/commerce/discount",
            body=body,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def get(
        self,
        discount_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a discount by ID."""
        return self._get(
            f"/commerce/discount/{discount_id}",
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
        discount_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a discount."""
        return self._delete(
            f"/commerce/discount/{discount_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class AsyncDiscountsResource(AsyncAPIResource):
    """Discount management (async)."""

    async def list(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            "/commerce/discount",
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
        body: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            "/commerce/discount",
            body=body,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def get(
        self,
        discount_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/commerce/discount/{discount_id}",
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
        discount_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._delete(
            f"/commerce/discount/{discount_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


# ---------------------------------------------------------------------------
# Payments
# ---------------------------------------------------------------------------


class PaymentsResource(SyncAPIResource):
    """Payment management."""

    def list(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List payments."""
        return self._get(
            "/commerce/payment",
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
        body: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a payment."""
        return self._post(
            "/commerce/payment",
            body=body,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def refund(
        self,
        payment_id: str,
        *,
        body: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Refund a payment."""
        return self._post(
            f"/commerce/payment/{payment_id}/refund",
            body=body if not isinstance(body, NotGiven) else None,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class AsyncPaymentsResource(AsyncAPIResource):
    """Payment management (async)."""

    async def list(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            "/commerce/payment",
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
        body: Dict[str, Any],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            "/commerce/payment",
            body=body,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def refund(
        self,
        payment_id: str,
        *,
        body: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            f"/commerce/payment/{payment_id}/refund",
            body=body if not isinstance(body, NotGiven) else None,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


# ---------------------------------------------------------------------------
# Top-level Commerce Resource
# ---------------------------------------------------------------------------


class CommerceResource(SyncAPIResource):
    """Hanzo Commerce API: orders, products, variants, collections,
    transactions, accounts, users, search, subscriptions, webhooks,
    stores, discounts, and payments."""

    @cached_property
    def orders(self) -> OrdersResource:
        return OrdersResource(self._client)

    @cached_property
    def products(self) -> ProductsResource:
        return ProductsResource(self._client)

    @cached_property
    def variants(self) -> VariantsResource:
        return VariantsResource(self._client)

    @cached_property
    def collections(self) -> CollectionsResource:
        return CollectionsResource(self._client)

    @cached_property
    def transactions(self) -> TransactionsResource:
        return TransactionsResource(self._client)

    @cached_property
    def accounts(self) -> AccountsResource:
        return AccountsResource(self._client)

    @cached_property
    def users(self) -> UsersResource:
        return UsersResource(self._client)

    @cached_property
    def search(self) -> SearchResource:
        return SearchResource(self._client)

    @cached_property
    def subscriptions(self) -> SubscriptionsResource:
        return SubscriptionsResource(self._client)

    @cached_property
    def webhooks(self) -> WebhooksResource:
        return WebhooksResource(self._client)

    @cached_property
    def stores(self) -> StoresResource:
        return StoresResource(self._client)

    @cached_property
    def discounts(self) -> DiscountsResource:
        return DiscountsResource(self._client)

    @cached_property
    def payments(self) -> PaymentsResource:
        return PaymentsResource(self._client)

    @cached_property
    def with_raw_response(self) -> CommerceResourceWithRawResponse:
        return CommerceResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> CommerceResourceWithStreamingResponse:
        return CommerceResourceWithStreamingResponse(self)

    def ping(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Health check."""
        return self._get(
            "/commerce/ping",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class AsyncCommerceResource(AsyncAPIResource):
    """Hanzo Commerce API (async): orders, products, variants, collections,
    transactions, accounts, users, search, subscriptions, webhooks,
    stores, discounts, and payments."""

    @cached_property
    def orders(self) -> AsyncOrdersResource:
        return AsyncOrdersResource(self._client)

    @cached_property
    def products(self) -> AsyncProductsResource:
        return AsyncProductsResource(self._client)

    @cached_property
    def variants(self) -> AsyncVariantsResource:
        return AsyncVariantsResource(self._client)

    @cached_property
    def collections(self) -> AsyncCollectionsResource:
        return AsyncCollectionsResource(self._client)

    @cached_property
    def transactions(self) -> AsyncTransactionsResource:
        return AsyncTransactionsResource(self._client)

    @cached_property
    def accounts(self) -> AsyncAccountsResource:
        return AsyncAccountsResource(self._client)

    @cached_property
    def users(self) -> AsyncUsersResource:
        return AsyncUsersResource(self._client)

    @cached_property
    def search(self) -> AsyncSearchResource:
        return AsyncSearchResource(self._client)

    @cached_property
    def subscriptions(self) -> AsyncSubscriptionsResource:
        return AsyncSubscriptionsResource(self._client)

    @cached_property
    def webhooks(self) -> AsyncWebhooksResource:
        return AsyncWebhooksResource(self._client)

    @cached_property
    def stores(self) -> AsyncStoresResource:
        return AsyncStoresResource(self._client)

    @cached_property
    def discounts(self) -> AsyncDiscountsResource:
        return AsyncDiscountsResource(self._client)

    @cached_property
    def payments(self) -> AsyncPaymentsResource:
        return AsyncPaymentsResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncCommerceResourceWithRawResponse:
        return AsyncCommerceResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncCommerceResourceWithStreamingResponse:
        return AsyncCommerceResourceWithStreamingResponse(self)

    async def ping(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            "/commerce/ping",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


# ---------------------------------------------------------------------------
# Raw response wrappers
# ---------------------------------------------------------------------------


class CommerceResourceWithRawResponse:
    def __init__(self, commerce: CommerceResource) -> None:
        self._commerce = commerce
        self.ping = to_raw_response_wrapper(commerce.ping)

    @cached_property
    def orders(self) -> OrdersResourceWithRawResponse:
        return OrdersResourceWithRawResponse(self._commerce.orders)

    @cached_property
    def products(self) -> ProductsResourceWithRawResponse:
        return ProductsResourceWithRawResponse(self._commerce.products)

    @cached_property
    def variants(self) -> VariantsResourceWithRawResponse:
        return VariantsResourceWithRawResponse(self._commerce.variants)

    @cached_property
    def collections(self) -> CollectionsResourceWithRawResponse:
        return CollectionsResourceWithRawResponse(self._commerce.collections)

    @cached_property
    def transactions(self) -> TransactionsResourceWithRawResponse:
        return TransactionsResourceWithRawResponse(self._commerce.transactions)

    @cached_property
    def accounts(self) -> AccountsResourceWithRawResponse:
        return AccountsResourceWithRawResponse(self._commerce.accounts)

    @cached_property
    def users(self) -> UsersResourceWithRawResponse:
        return UsersResourceWithRawResponse(self._commerce.users)

    @cached_property
    def search(self) -> SearchResourceWithRawResponse:
        return SearchResourceWithRawResponse(self._commerce.search)

    @cached_property
    def subscriptions(self) -> SubscriptionsResourceWithRawResponse:
        return SubscriptionsResourceWithRawResponse(self._commerce.subscriptions)

    @cached_property
    def webhooks(self) -> WebhooksResourceWithRawResponse:
        return WebhooksResourceWithRawResponse(self._commerce.webhooks)

    @cached_property
    def stores(self) -> StoresResourceWithRawResponse:
        return StoresResourceWithRawResponse(self._commerce.stores)

    @cached_property
    def discounts(self) -> DiscountsResourceWithRawResponse:
        return DiscountsResourceWithRawResponse(self._commerce.discounts)

    @cached_property
    def payments(self) -> PaymentsResourceWithRawResponse:
        return PaymentsResourceWithRawResponse(self._commerce.payments)


class AsyncCommerceResourceWithRawResponse:
    def __init__(self, commerce: AsyncCommerceResource) -> None:
        self._commerce = commerce
        self.ping = async_to_raw_response_wrapper(commerce.ping)

    @cached_property
    def orders(self) -> AsyncOrdersResourceWithRawResponse:
        return AsyncOrdersResourceWithRawResponse(self._commerce.orders)

    @cached_property
    def products(self) -> AsyncProductsResourceWithRawResponse:
        return AsyncProductsResourceWithRawResponse(self._commerce.products)

    @cached_property
    def variants(self) -> AsyncVariantsResourceWithRawResponse:
        return AsyncVariantsResourceWithRawResponse(self._commerce.variants)

    @cached_property
    def collections(self) -> AsyncCollectionsResourceWithRawResponse:
        return AsyncCollectionsResourceWithRawResponse(self._commerce.collections)

    @cached_property
    def transactions(self) -> AsyncTransactionsResourceWithRawResponse:
        return AsyncTransactionsResourceWithRawResponse(self._commerce.transactions)

    @cached_property
    def accounts(self) -> AsyncAccountsResourceWithRawResponse:
        return AsyncAccountsResourceWithRawResponse(self._commerce.accounts)

    @cached_property
    def users(self) -> AsyncUsersResourceWithRawResponse:
        return AsyncUsersResourceWithRawResponse(self._commerce.users)

    @cached_property
    def search(self) -> AsyncSearchResourceWithRawResponse:
        return AsyncSearchResourceWithRawResponse(self._commerce.search)

    @cached_property
    def subscriptions(self) -> AsyncSubscriptionsResourceWithRawResponse:
        return AsyncSubscriptionsResourceWithRawResponse(self._commerce.subscriptions)

    @cached_property
    def webhooks(self) -> AsyncWebhooksResourceWithRawResponse:
        return AsyncWebhooksResourceWithRawResponse(self._commerce.webhooks)

    @cached_property
    def stores(self) -> AsyncStoresResourceWithRawResponse:
        return AsyncStoresResourceWithRawResponse(self._commerce.stores)

    @cached_property
    def discounts(self) -> AsyncDiscountsResourceWithRawResponse:
        return AsyncDiscountsResourceWithRawResponse(self._commerce.discounts)

    @cached_property
    def payments(self) -> AsyncPaymentsResourceWithRawResponse:
        return AsyncPaymentsResourceWithRawResponse(self._commerce.payments)


# ---------------------------------------------------------------------------
# Streaming response wrappers
# ---------------------------------------------------------------------------


class CommerceResourceWithStreamingResponse:
    def __init__(self, commerce: CommerceResource) -> None:
        self._commerce = commerce
        self.ping = to_streamed_response_wrapper(commerce.ping)

    @cached_property
    def orders(self) -> OrdersResourceWithStreamingResponse:
        return OrdersResourceWithStreamingResponse(self._commerce.orders)

    @cached_property
    def products(self) -> ProductsResourceWithStreamingResponse:
        return ProductsResourceWithStreamingResponse(self._commerce.products)

    @cached_property
    def variants(self) -> VariantsResourceWithStreamingResponse:
        return VariantsResourceWithStreamingResponse(self._commerce.variants)

    @cached_property
    def collections(self) -> CollectionsResourceWithStreamingResponse:
        return CollectionsResourceWithStreamingResponse(self._commerce.collections)

    @cached_property
    def transactions(self) -> TransactionsResourceWithStreamingResponse:
        return TransactionsResourceWithStreamingResponse(self._commerce.transactions)

    @cached_property
    def accounts(self) -> AccountsResourceWithStreamingResponse:
        return AccountsResourceWithStreamingResponse(self._commerce.accounts)

    @cached_property
    def users(self) -> UsersResourceWithStreamingResponse:
        return UsersResourceWithStreamingResponse(self._commerce.users)

    @cached_property
    def search(self) -> SearchResourceWithStreamingResponse:
        return SearchResourceWithStreamingResponse(self._commerce.search)

    @cached_property
    def subscriptions(self) -> SubscriptionsResourceWithStreamingResponse:
        return SubscriptionsResourceWithStreamingResponse(self._commerce.subscriptions)

    @cached_property
    def webhooks(self) -> WebhooksResourceWithStreamingResponse:
        return WebhooksResourceWithStreamingResponse(self._commerce.webhooks)

    @cached_property
    def stores(self) -> StoresResourceWithStreamingResponse:
        return StoresResourceWithStreamingResponse(self._commerce.stores)

    @cached_property
    def discounts(self) -> DiscountsResourceWithStreamingResponse:
        return DiscountsResourceWithStreamingResponse(self._commerce.discounts)

    @cached_property
    def payments(self) -> PaymentsResourceWithStreamingResponse:
        return PaymentsResourceWithStreamingResponse(self._commerce.payments)


class AsyncCommerceResourceWithStreamingResponse:
    def __init__(self, commerce: AsyncCommerceResource) -> None:
        self._commerce = commerce
        self.ping = async_to_streamed_response_wrapper(commerce.ping)

    @cached_property
    def orders(self) -> AsyncOrdersResourceWithStreamingResponse:
        return AsyncOrdersResourceWithStreamingResponse(self._commerce.orders)

    @cached_property
    def products(self) -> AsyncProductsResourceWithStreamingResponse:
        return AsyncProductsResourceWithStreamingResponse(self._commerce.products)

    @cached_property
    def variants(self) -> AsyncVariantsResourceWithStreamingResponse:
        return AsyncVariantsResourceWithStreamingResponse(self._commerce.variants)

    @cached_property
    def collections(self) -> AsyncCollectionsResourceWithStreamingResponse:
        return AsyncCollectionsResourceWithStreamingResponse(self._commerce.collections)

    @cached_property
    def transactions(self) -> AsyncTransactionsResourceWithStreamingResponse:
        return AsyncTransactionsResourceWithStreamingResponse(self._commerce.transactions)

    @cached_property
    def accounts(self) -> AsyncAccountsResourceWithStreamingResponse:
        return AsyncAccountsResourceWithStreamingResponse(self._commerce.accounts)

    @cached_property
    def users(self) -> AsyncUsersResourceWithStreamingResponse:
        return AsyncUsersResourceWithStreamingResponse(self._commerce.users)

    @cached_property
    def search(self) -> AsyncSearchResourceWithStreamingResponse:
        return AsyncSearchResourceWithStreamingResponse(self._commerce.search)

    @cached_property
    def subscriptions(self) -> AsyncSubscriptionsResourceWithStreamingResponse:
        return AsyncSubscriptionsResourceWithStreamingResponse(self._commerce.subscriptions)

    @cached_property
    def webhooks(self) -> AsyncWebhooksResourceWithStreamingResponse:
        return AsyncWebhooksResourceWithStreamingResponse(self._commerce.webhooks)

    @cached_property
    def stores(self) -> AsyncStoresResourceWithStreamingResponse:
        return AsyncStoresResourceWithStreamingResponse(self._commerce.stores)

    @cached_property
    def discounts(self) -> AsyncDiscountsResourceWithStreamingResponse:
        return AsyncDiscountsResourceWithStreamingResponse(self._commerce.discounts)

    @cached_property
    def payments(self) -> AsyncPaymentsResourceWithStreamingResponse:
        return AsyncPaymentsResourceWithStreamingResponse(self._commerce.payments)


# ---------------------------------------------------------------------------
# Sub-resource raw response wrappers
# ---------------------------------------------------------------------------


class OrdersResourceWithRawResponse:
    def __init__(self, orders: OrdersResource) -> None:
        self._orders = orders
        self.list = to_raw_response_wrapper(orders.list)
        self.create = to_raw_response_wrapper(orders.create)
        self.get = to_raw_response_wrapper(orders.get)
        self.update = to_raw_response_wrapper(orders.update)
        self.delete = to_raw_response_wrapper(orders.delete)
        self.authorize = to_raw_response_wrapper(orders.authorize)
        self.capture = to_raw_response_wrapper(orders.capture)
        self.charge = to_raw_response_wrapper(orders.charge)
        self.refund = to_raw_response_wrapper(orders.refund)
        self.payments = to_raw_response_wrapper(orders.payments)
        self.returns = to_raw_response_wrapper(orders.returns)
        self.status = to_raw_response_wrapper(orders.status)


class AsyncOrdersResourceWithRawResponse:
    def __init__(self, orders: AsyncOrdersResource) -> None:
        self._orders = orders
        self.list = async_to_raw_response_wrapper(orders.list)
        self.create = async_to_raw_response_wrapper(orders.create)
        self.get = async_to_raw_response_wrapper(orders.get)
        self.update = async_to_raw_response_wrapper(orders.update)
        self.delete = async_to_raw_response_wrapper(orders.delete)
        self.authorize = async_to_raw_response_wrapper(orders.authorize)
        self.capture = async_to_raw_response_wrapper(orders.capture)
        self.charge = async_to_raw_response_wrapper(orders.charge)
        self.refund = async_to_raw_response_wrapper(orders.refund)
        self.payments = async_to_raw_response_wrapper(orders.payments)
        self.returns = async_to_raw_response_wrapper(orders.returns)
        self.status = async_to_raw_response_wrapper(orders.status)


class ProductsResourceWithRawResponse:
    def __init__(self, products: ProductsResource) -> None:
        self._products = products
        self.list = to_raw_response_wrapper(products.list)
        self.create = to_raw_response_wrapper(products.create)
        self.get = to_raw_response_wrapper(products.get)
        self.update = to_raw_response_wrapper(products.update)
        self.delete = to_raw_response_wrapper(products.delete)


class AsyncProductsResourceWithRawResponse:
    def __init__(self, products: AsyncProductsResource) -> None:
        self._products = products
        self.list = async_to_raw_response_wrapper(products.list)
        self.create = async_to_raw_response_wrapper(products.create)
        self.get = async_to_raw_response_wrapper(products.get)
        self.update = async_to_raw_response_wrapper(products.update)
        self.delete = async_to_raw_response_wrapper(products.delete)


class VariantsResourceWithRawResponse:
    def __init__(self, variants: VariantsResource) -> None:
        self._variants = variants
        self.list = to_raw_response_wrapper(variants.list)
        self.create = to_raw_response_wrapper(variants.create)
        self.get = to_raw_response_wrapper(variants.get)
        self.update = to_raw_response_wrapper(variants.update)
        self.delete = to_raw_response_wrapper(variants.delete)


class AsyncVariantsResourceWithRawResponse:
    def __init__(self, variants: AsyncVariantsResource) -> None:
        self._variants = variants
        self.list = async_to_raw_response_wrapper(variants.list)
        self.create = async_to_raw_response_wrapper(variants.create)
        self.get = async_to_raw_response_wrapper(variants.get)
        self.update = async_to_raw_response_wrapper(variants.update)
        self.delete = async_to_raw_response_wrapper(variants.delete)


class CollectionsResourceWithRawResponse:
    def __init__(self, collections: CollectionsResource) -> None:
        self._collections = collections
        self.list = to_raw_response_wrapper(collections.list)
        self.create = to_raw_response_wrapper(collections.create)
        self.get = to_raw_response_wrapper(collections.get)
        self.update = to_raw_response_wrapper(collections.update)
        self.delete = to_raw_response_wrapper(collections.delete)


class AsyncCollectionsResourceWithRawResponse:
    def __init__(self, collections: AsyncCollectionsResource) -> None:
        self._collections = collections
        self.list = async_to_raw_response_wrapper(collections.list)
        self.create = async_to_raw_response_wrapper(collections.create)
        self.get = async_to_raw_response_wrapper(collections.get)
        self.update = async_to_raw_response_wrapper(collections.update)
        self.delete = async_to_raw_response_wrapper(collections.delete)


class TransactionsResourceWithRawResponse:
    def __init__(self, transactions: TransactionsResource) -> None:
        self._transactions = transactions
        self.list = to_raw_response_wrapper(transactions.list)
        self.create = to_raw_response_wrapper(transactions.create)
        self.get_by_kind = to_raw_response_wrapper(transactions.get_by_kind)


class AsyncTransactionsResourceWithRawResponse:
    def __init__(self, transactions: AsyncTransactionsResource) -> None:
        self._transactions = transactions
        self.list = async_to_raw_response_wrapper(transactions.list)
        self.create = async_to_raw_response_wrapper(transactions.create)
        self.get_by_kind = async_to_raw_response_wrapper(transactions.get_by_kind)


class AccountsResourceWithRawResponse:
    def __init__(self, accounts: AccountsResource) -> None:
        self._accounts = accounts
        self.login = to_raw_response_wrapper(accounts.login)
        self.create = to_raw_response_wrapper(accounts.create)
        self.get = to_raw_response_wrapper(accounts.get)
        self.exists = to_raw_response_wrapper(accounts.exists)


class AsyncAccountsResourceWithRawResponse:
    def __init__(self, accounts: AsyncAccountsResource) -> None:
        self._accounts = accounts
        self.login = async_to_raw_response_wrapper(accounts.login)
        self.create = async_to_raw_response_wrapper(accounts.create)
        self.get = async_to_raw_response_wrapper(accounts.get)
        self.exists = async_to_raw_response_wrapper(accounts.exists)


class UsersResourceWithRawResponse:
    def __init__(self, users: UsersResource) -> None:
        self._users = users
        self.list = to_raw_response_wrapper(users.list)
        self.get = to_raw_response_wrapper(users.get)
        self.orders = to_raw_response_wrapper(users.orders)
        self.transactions = to_raw_response_wrapper(users.transactions)
        self.wallet = to_raw_response_wrapper(users.wallet)


class AsyncUsersResourceWithRawResponse:
    def __init__(self, users: AsyncUsersResource) -> None:
        self._users = users
        self.list = async_to_raw_response_wrapper(users.list)
        self.get = async_to_raw_response_wrapper(users.get)
        self.orders = async_to_raw_response_wrapper(users.orders)
        self.transactions = async_to_raw_response_wrapper(users.transactions)
        self.wallet = async_to_raw_response_wrapper(users.wallet)


class SearchResourceWithRawResponse:
    def __init__(self, search: SearchResource) -> None:
        self._search = search
        self.users = to_raw_response_wrapper(search.users)
        self.orders = to_raw_response_wrapper(search.orders)


class AsyncSearchResourceWithRawResponse:
    def __init__(self, search: AsyncSearchResource) -> None:
        self._search = search
        self.users = async_to_raw_response_wrapper(search.users)
        self.orders = async_to_raw_response_wrapper(search.orders)


class SubscriptionsResourceWithRawResponse:
    def __init__(self, subscriptions: SubscriptionsResource) -> None:
        self._subscriptions = subscriptions
        self.create = to_raw_response_wrapper(subscriptions.create)
        self.get = to_raw_response_wrapper(subscriptions.get)


class AsyncSubscriptionsResourceWithRawResponse:
    def __init__(self, subscriptions: AsyncSubscriptionsResource) -> None:
        self._subscriptions = subscriptions
        self.create = async_to_raw_response_wrapper(subscriptions.create)
        self.get = async_to_raw_response_wrapper(subscriptions.get)


class WebhooksResourceWithRawResponse:
    def __init__(self, webhooks: WebhooksResource) -> None:
        self._webhooks = webhooks
        self.list = to_raw_response_wrapper(webhooks.list)
        self.create = to_raw_response_wrapper(webhooks.create)
        self.delete = to_raw_response_wrapper(webhooks.delete)


class AsyncWebhooksResourceWithRawResponse:
    def __init__(self, webhooks: AsyncWebhooksResource) -> None:
        self._webhooks = webhooks
        self.list = async_to_raw_response_wrapper(webhooks.list)
        self.create = async_to_raw_response_wrapper(webhooks.create)
        self.delete = async_to_raw_response_wrapper(webhooks.delete)


class StoresResourceWithRawResponse:
    def __init__(self, stores: StoresResource) -> None:
        self._stores = stores
        self.list = to_raw_response_wrapper(stores.list)
        self.create = to_raw_response_wrapper(stores.create)
        self.get = to_raw_response_wrapper(stores.get)
        self.product = to_raw_response_wrapper(stores.product)
        self.listings = to_raw_response_wrapper(stores.listings)


class AsyncStoresResourceWithRawResponse:
    def __init__(self, stores: AsyncStoresResource) -> None:
        self._stores = stores
        self.list = async_to_raw_response_wrapper(stores.list)
        self.create = async_to_raw_response_wrapper(stores.create)
        self.get = async_to_raw_response_wrapper(stores.get)
        self.product = async_to_raw_response_wrapper(stores.product)
        self.listings = async_to_raw_response_wrapper(stores.listings)


class DiscountsResourceWithRawResponse:
    def __init__(self, discounts: DiscountsResource) -> None:
        self._discounts = discounts
        self.list = to_raw_response_wrapper(discounts.list)
        self.create = to_raw_response_wrapper(discounts.create)
        self.get = to_raw_response_wrapper(discounts.get)
        self.delete = to_raw_response_wrapper(discounts.delete)


class AsyncDiscountsResourceWithRawResponse:
    def __init__(self, discounts: AsyncDiscountsResource) -> None:
        self._discounts = discounts
        self.list = async_to_raw_response_wrapper(discounts.list)
        self.create = async_to_raw_response_wrapper(discounts.create)
        self.get = async_to_raw_response_wrapper(discounts.get)
        self.delete = async_to_raw_response_wrapper(discounts.delete)


class PaymentsResourceWithRawResponse:
    def __init__(self, payments: PaymentsResource) -> None:
        self._payments = payments
        self.list = to_raw_response_wrapper(payments.list)
        self.create = to_raw_response_wrapper(payments.create)
        self.refund = to_raw_response_wrapper(payments.refund)


class AsyncPaymentsResourceWithRawResponse:
    def __init__(self, payments: AsyncPaymentsResource) -> None:
        self._payments = payments
        self.list = async_to_raw_response_wrapper(payments.list)
        self.create = async_to_raw_response_wrapper(payments.create)
        self.refund = async_to_raw_response_wrapper(payments.refund)


# ---------------------------------------------------------------------------
# Sub-resource streaming response wrappers
# ---------------------------------------------------------------------------


class OrdersResourceWithStreamingResponse:
    def __init__(self, orders: OrdersResource) -> None:
        self._orders = orders
        self.list = to_streamed_response_wrapper(orders.list)
        self.create = to_streamed_response_wrapper(orders.create)
        self.get = to_streamed_response_wrapper(orders.get)
        self.update = to_streamed_response_wrapper(orders.update)
        self.delete = to_streamed_response_wrapper(orders.delete)
        self.authorize = to_streamed_response_wrapper(orders.authorize)
        self.capture = to_streamed_response_wrapper(orders.capture)
        self.charge = to_streamed_response_wrapper(orders.charge)
        self.refund = to_streamed_response_wrapper(orders.refund)
        self.payments = to_streamed_response_wrapper(orders.payments)
        self.returns = to_streamed_response_wrapper(orders.returns)
        self.status = to_streamed_response_wrapper(orders.status)


class AsyncOrdersResourceWithStreamingResponse:
    def __init__(self, orders: AsyncOrdersResource) -> None:
        self._orders = orders
        self.list = async_to_streamed_response_wrapper(orders.list)
        self.create = async_to_streamed_response_wrapper(orders.create)
        self.get = async_to_streamed_response_wrapper(orders.get)
        self.update = async_to_streamed_response_wrapper(orders.update)
        self.delete = async_to_streamed_response_wrapper(orders.delete)
        self.authorize = async_to_streamed_response_wrapper(orders.authorize)
        self.capture = async_to_streamed_response_wrapper(orders.capture)
        self.charge = async_to_streamed_response_wrapper(orders.charge)
        self.refund = async_to_streamed_response_wrapper(orders.refund)
        self.payments = async_to_streamed_response_wrapper(orders.payments)
        self.returns = async_to_streamed_response_wrapper(orders.returns)
        self.status = async_to_streamed_response_wrapper(orders.status)


class ProductsResourceWithStreamingResponse:
    def __init__(self, products: ProductsResource) -> None:
        self._products = products
        self.list = to_streamed_response_wrapper(products.list)
        self.create = to_streamed_response_wrapper(products.create)
        self.get = to_streamed_response_wrapper(products.get)
        self.update = to_streamed_response_wrapper(products.update)
        self.delete = to_streamed_response_wrapper(products.delete)


class AsyncProductsResourceWithStreamingResponse:
    def __init__(self, products: AsyncProductsResource) -> None:
        self._products = products
        self.list = async_to_streamed_response_wrapper(products.list)
        self.create = async_to_streamed_response_wrapper(products.create)
        self.get = async_to_streamed_response_wrapper(products.get)
        self.update = async_to_streamed_response_wrapper(products.update)
        self.delete = async_to_streamed_response_wrapper(products.delete)


class VariantsResourceWithStreamingResponse:
    def __init__(self, variants: VariantsResource) -> None:
        self._variants = variants
        self.list = to_streamed_response_wrapper(variants.list)
        self.create = to_streamed_response_wrapper(variants.create)
        self.get = to_streamed_response_wrapper(variants.get)
        self.update = to_streamed_response_wrapper(variants.update)
        self.delete = to_streamed_response_wrapper(variants.delete)


class AsyncVariantsResourceWithStreamingResponse:
    def __init__(self, variants: AsyncVariantsResource) -> None:
        self._variants = variants
        self.list = async_to_streamed_response_wrapper(variants.list)
        self.create = async_to_streamed_response_wrapper(variants.create)
        self.get = async_to_streamed_response_wrapper(variants.get)
        self.update = async_to_streamed_response_wrapper(variants.update)
        self.delete = async_to_streamed_response_wrapper(variants.delete)


class CollectionsResourceWithStreamingResponse:
    def __init__(self, collections: CollectionsResource) -> None:
        self._collections = collections
        self.list = to_streamed_response_wrapper(collections.list)
        self.create = to_streamed_response_wrapper(collections.create)
        self.get = to_streamed_response_wrapper(collections.get)
        self.update = to_streamed_response_wrapper(collections.update)
        self.delete = to_streamed_response_wrapper(collections.delete)


class AsyncCollectionsResourceWithStreamingResponse:
    def __init__(self, collections: AsyncCollectionsResource) -> None:
        self._collections = collections
        self.list = async_to_streamed_response_wrapper(collections.list)
        self.create = async_to_streamed_response_wrapper(collections.create)
        self.get = async_to_streamed_response_wrapper(collections.get)
        self.update = async_to_streamed_response_wrapper(collections.update)
        self.delete = async_to_streamed_response_wrapper(collections.delete)


class TransactionsResourceWithStreamingResponse:
    def __init__(self, transactions: TransactionsResource) -> None:
        self._transactions = transactions
        self.list = to_streamed_response_wrapper(transactions.list)
        self.create = to_streamed_response_wrapper(transactions.create)
        self.get_by_kind = to_streamed_response_wrapper(transactions.get_by_kind)


class AsyncTransactionsResourceWithStreamingResponse:
    def __init__(self, transactions: AsyncTransactionsResource) -> None:
        self._transactions = transactions
        self.list = async_to_streamed_response_wrapper(transactions.list)
        self.create = async_to_streamed_response_wrapper(transactions.create)
        self.get_by_kind = async_to_streamed_response_wrapper(transactions.get_by_kind)


class AccountsResourceWithStreamingResponse:
    def __init__(self, accounts: AccountsResource) -> None:
        self._accounts = accounts
        self.login = to_streamed_response_wrapper(accounts.login)
        self.create = to_streamed_response_wrapper(accounts.create)
        self.get = to_streamed_response_wrapper(accounts.get)
        self.exists = to_streamed_response_wrapper(accounts.exists)


class AsyncAccountsResourceWithStreamingResponse:
    def __init__(self, accounts: AsyncAccountsResource) -> None:
        self._accounts = accounts
        self.login = async_to_streamed_response_wrapper(accounts.login)
        self.create = async_to_streamed_response_wrapper(accounts.create)
        self.get = async_to_streamed_response_wrapper(accounts.get)
        self.exists = async_to_streamed_response_wrapper(accounts.exists)


class UsersResourceWithStreamingResponse:
    def __init__(self, users: UsersResource) -> None:
        self._users = users
        self.list = to_streamed_response_wrapper(users.list)
        self.get = to_streamed_response_wrapper(users.get)
        self.orders = to_streamed_response_wrapper(users.orders)
        self.transactions = to_streamed_response_wrapper(users.transactions)
        self.wallet = to_streamed_response_wrapper(users.wallet)


class AsyncUsersResourceWithStreamingResponse:
    def __init__(self, users: AsyncUsersResource) -> None:
        self._users = users
        self.list = async_to_streamed_response_wrapper(users.list)
        self.get = async_to_streamed_response_wrapper(users.get)
        self.orders = async_to_streamed_response_wrapper(users.orders)
        self.transactions = async_to_streamed_response_wrapper(users.transactions)
        self.wallet = async_to_streamed_response_wrapper(users.wallet)


class SearchResourceWithStreamingResponse:
    def __init__(self, search: SearchResource) -> None:
        self._search = search
        self.users = to_streamed_response_wrapper(search.users)
        self.orders = to_streamed_response_wrapper(search.orders)


class AsyncSearchResourceWithStreamingResponse:
    def __init__(self, search: AsyncSearchResource) -> None:
        self._search = search
        self.users = async_to_streamed_response_wrapper(search.users)
        self.orders = async_to_streamed_response_wrapper(search.orders)


class SubscriptionsResourceWithStreamingResponse:
    def __init__(self, subscriptions: SubscriptionsResource) -> None:
        self._subscriptions = subscriptions
        self.create = to_streamed_response_wrapper(subscriptions.create)
        self.get = to_streamed_response_wrapper(subscriptions.get)


class AsyncSubscriptionsResourceWithStreamingResponse:
    def __init__(self, subscriptions: AsyncSubscriptionsResource) -> None:
        self._subscriptions = subscriptions
        self.create = async_to_streamed_response_wrapper(subscriptions.create)
        self.get = async_to_streamed_response_wrapper(subscriptions.get)


class WebhooksResourceWithStreamingResponse:
    def __init__(self, webhooks: WebhooksResource) -> None:
        self._webhooks = webhooks
        self.list = to_streamed_response_wrapper(webhooks.list)
        self.create = to_streamed_response_wrapper(webhooks.create)
        self.delete = to_streamed_response_wrapper(webhooks.delete)


class AsyncWebhooksResourceWithStreamingResponse:
    def __init__(self, webhooks: AsyncWebhooksResource) -> None:
        self._webhooks = webhooks
        self.list = async_to_streamed_response_wrapper(webhooks.list)
        self.create = async_to_streamed_response_wrapper(webhooks.create)
        self.delete = async_to_streamed_response_wrapper(webhooks.delete)


class StoresResourceWithStreamingResponse:
    def __init__(self, stores: StoresResource) -> None:
        self._stores = stores
        self.list = to_streamed_response_wrapper(stores.list)
        self.create = to_streamed_response_wrapper(stores.create)
        self.get = to_streamed_response_wrapper(stores.get)
        self.product = to_streamed_response_wrapper(stores.product)
        self.listings = to_streamed_response_wrapper(stores.listings)


class AsyncStoresResourceWithStreamingResponse:
    def __init__(self, stores: AsyncStoresResource) -> None:
        self._stores = stores
        self.list = async_to_streamed_response_wrapper(stores.list)
        self.create = async_to_streamed_response_wrapper(stores.create)
        self.get = async_to_streamed_response_wrapper(stores.get)
        self.product = async_to_streamed_response_wrapper(stores.product)
        self.listings = async_to_streamed_response_wrapper(stores.listings)


class DiscountsResourceWithStreamingResponse:
    def __init__(self, discounts: DiscountsResource) -> None:
        self._discounts = discounts
        self.list = to_streamed_response_wrapper(discounts.list)
        self.create = to_streamed_response_wrapper(discounts.create)
        self.get = to_streamed_response_wrapper(discounts.get)
        self.delete = to_streamed_response_wrapper(discounts.delete)


class AsyncDiscountsResourceWithStreamingResponse:
    def __init__(self, discounts: AsyncDiscountsResource) -> None:
        self._discounts = discounts
        self.list = async_to_streamed_response_wrapper(discounts.list)
        self.create = async_to_streamed_response_wrapper(discounts.create)
        self.get = async_to_streamed_response_wrapper(discounts.get)
        self.delete = async_to_streamed_response_wrapper(discounts.delete)


class PaymentsResourceWithStreamingResponse:
    def __init__(self, payments: PaymentsResource) -> None:
        self._payments = payments
        self.list = to_streamed_response_wrapper(payments.list)
        self.create = to_streamed_response_wrapper(payments.create)
        self.refund = to_streamed_response_wrapper(payments.refund)


class AsyncPaymentsResourceWithStreamingResponse:
    def __init__(self, payments: AsyncPaymentsResource) -> None:
        self._payments = payments
        self.list = async_to_streamed_response_wrapper(payments.list)
        self.create = async_to_streamed_response_wrapper(payments.create)
        self.refund = async_to_streamed_response_wrapper(payments.refund)
