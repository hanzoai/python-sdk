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

__all__ = ["CouponsResource", "AsyncCouponsResource"]


class CouponsResource(SyncAPIResource):
    """Coupon and discount management."""

    @cached_property
    def with_raw_response(self) -> CouponsResourceWithRawResponse:
        return CouponsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> CouponsResourceWithStreamingResponse:
        return CouponsResourceWithStreamingResponse(self)

    def list(
        self,
        *,
        active: bool | NotGiven = NOT_GIVEN,
        limit: int | NotGiven = NOT_GIVEN,
        offset: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all coupons."""
        return self._get(
            "/marketing/coupons",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"active": active, "limit": limit, "offset": offset},
            ),
            cast_to=object,
        )

    def get(
        self,
        coupon_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a specific coupon."""
        return self._get(
            f"/marketing/coupons/{coupon_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def create(
        self,
        *,
        code: str,
        discount_type: str,
        discount_value: float,
        valid_from: str | NotGiven = NOT_GIVEN,
        valid_until: str | NotGiven = NOT_GIVEN,
        max_uses: int | NotGiven = NOT_GIVEN,
        min_purchase: float | NotGiven = NOT_GIVEN,
        applicable_products: List[str] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a new coupon."""
        return self._post(
            "/marketing/coupons",
            body={
                "code": code,
                "discount_type": discount_type,
                "discount_value": discount_value,
                "valid_from": valid_from,
                "valid_until": valid_until,
                "max_uses": max_uses,
                "min_purchase": min_purchase,
                "applicable_products": applicable_products,
            },
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def update(
        self,
        coupon_id: str,
        *,
        discount_value: float | NotGiven = NOT_GIVEN,
        valid_until: str | NotGiven = NOT_GIVEN,
        max_uses: int | NotGiven = NOT_GIVEN,
        active: bool | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update a coupon."""
        return self._put(
            f"/marketing/coupons/{coupon_id}",
            body={"discount_value": discount_value, "valid_until": valid_until, "max_uses": max_uses, "active": active},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def delete(
        self,
        coupon_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a coupon."""
        return self._delete(
            f"/marketing/coupons/{coupon_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def validate(
        self,
        code: str,
        *,
        cart_total: float | NotGiven = NOT_GIVEN,
        product_ids: List[str] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Validate a coupon code."""
        return self._post(
            f"/marketing/coupons/{code}/validate",
            body={"cart_total": cart_total, "product_ids": product_ids},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def stats(
        self,
        coupon_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get coupon usage statistics."""
        return self._get(
            f"/marketing/coupons/{coupon_id}/stats",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class AsyncCouponsResource(AsyncAPIResource):
    """Coupon and discount management (async)."""

    @cached_property
    def with_raw_response(self) -> AsyncCouponsResourceWithRawResponse:
        return AsyncCouponsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncCouponsResourceWithStreamingResponse:
        return AsyncCouponsResourceWithStreamingResponse(self)

    async def list(
        self,
        *,
        active: bool | NotGiven = NOT_GIVEN,
        limit: int | NotGiven = NOT_GIVEN,
        offset: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            "/marketing/coupons",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"active": active, "limit": limit, "offset": offset},
            ),
            cast_to=object,
        )

    async def get(
        self,
        coupon_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/marketing/coupons/{coupon_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def create(
        self,
        *,
        code: str,
        discount_type: str,
        discount_value: float,
        valid_from: str | NotGiven = NOT_GIVEN,
        valid_until: str | NotGiven = NOT_GIVEN,
        max_uses: int | NotGiven = NOT_GIVEN,
        min_purchase: float | NotGiven = NOT_GIVEN,
        applicable_products: List[str] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            "/marketing/coupons",
            body={
                "code": code,
                "discount_type": discount_type,
                "discount_value": discount_value,
                "valid_from": valid_from,
                "valid_until": valid_until,
                "max_uses": max_uses,
                "min_purchase": min_purchase,
                "applicable_products": applicable_products,
            },
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def update(
        self,
        coupon_id: str,
        *,
        discount_value: float | NotGiven = NOT_GIVEN,
        valid_until: str | NotGiven = NOT_GIVEN,
        max_uses: int | NotGiven = NOT_GIVEN,
        active: bool | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._put(
            f"/marketing/coupons/{coupon_id}",
            body={"discount_value": discount_value, "valid_until": valid_until, "max_uses": max_uses, "active": active},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def delete(
        self,
        coupon_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._delete(
            f"/marketing/coupons/{coupon_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def validate(
        self,
        code: str,
        *,
        cart_total: float | NotGiven = NOT_GIVEN,
        product_ids: List[str] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            f"/marketing/coupons/{code}/validate",
            body={"cart_total": cart_total, "product_ids": product_ids},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def stats(
        self,
        coupon_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/marketing/coupons/{coupon_id}/stats",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class CouponsResourceWithRawResponse:
    def __init__(self, coupons: CouponsResource) -> None:
        self._coupons = coupons
        self.list = to_raw_response_wrapper(coupons.list)
        self.get = to_raw_response_wrapper(coupons.get)
        self.create = to_raw_response_wrapper(coupons.create)
        self.update = to_raw_response_wrapper(coupons.update)
        self.delete = to_raw_response_wrapper(coupons.delete)
        self.validate = to_raw_response_wrapper(coupons.validate)
        self.stats = to_raw_response_wrapper(coupons.stats)


class AsyncCouponsResourceWithRawResponse:
    def __init__(self, coupons: AsyncCouponsResource) -> None:
        self._coupons = coupons
        self.list = async_to_raw_response_wrapper(coupons.list)
        self.get = async_to_raw_response_wrapper(coupons.get)
        self.create = async_to_raw_response_wrapper(coupons.create)
        self.update = async_to_raw_response_wrapper(coupons.update)
        self.delete = async_to_raw_response_wrapper(coupons.delete)
        self.validate = async_to_raw_response_wrapper(coupons.validate)
        self.stats = async_to_raw_response_wrapper(coupons.stats)


class CouponsResourceWithStreamingResponse:
    def __init__(self, coupons: CouponsResource) -> None:
        self._coupons = coupons
        self.list = to_streamed_response_wrapper(coupons.list)
        self.get = to_streamed_response_wrapper(coupons.get)
        self.create = to_streamed_response_wrapper(coupons.create)
        self.update = to_streamed_response_wrapper(coupons.update)
        self.delete = to_streamed_response_wrapper(coupons.delete)
        self.validate = to_streamed_response_wrapper(coupons.validate)
        self.stats = to_streamed_response_wrapper(coupons.stats)


class AsyncCouponsResourceWithStreamingResponse:
    def __init__(self, coupons: AsyncCouponsResource) -> None:
        self._coupons = coupons
        self.list = async_to_streamed_response_wrapper(coupons.list)
        self.get = async_to_streamed_response_wrapper(coupons.get)
        self.create = async_to_streamed_response_wrapper(coupons.create)
        self.update = async_to_streamed_response_wrapper(coupons.update)
        self.delete = async_to_streamed_response_wrapper(coupons.delete)
        self.validate = async_to_streamed_response_wrapper(coupons.validate)
        self.stats = async_to_streamed_response_wrapper(coupons.stats)
