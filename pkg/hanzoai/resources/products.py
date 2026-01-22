# Hanzo AI SDK

from __future__ import annotations
from typing import Dict, Any, List
import httpx
from .._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import to_raw_response_wrapper, to_streamed_response_wrapper, async_to_raw_response_wrapper, async_to_streamed_response_wrapper
from .._base_client import make_request_options

__all__ = ["ProductsResource", "AsyncProductsResource"]


class ProductsResource(SyncAPIResource):
    """Product catalog management."""

    @cached_property
    def with_raw_response(self) -> ProductsResourceWithRawResponse:
        return ProductsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ProductsResourceWithStreamingResponse:
        return ProductsResourceWithStreamingResponse(self)

    def list(self, *, collection_id: str | NotGiven = NOT_GIVEN, limit: int | NotGiven = NOT_GIVEN, offset: int | NotGiven = NOT_GIVEN, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        """List all products."""
        return self._get("/commerce/products", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout, query={"collection_id": collection_id, "limit": limit, "offset": offset}), cast_to=object)

    def get(self, product_id: str, *, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        """Get a specific product."""
        return self._get(f"/commerce/products/{product_id}", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    def create(self, *, name: str, price: float, description: str | NotGiven = NOT_GIVEN, images: List[str] | NotGiven = NOT_GIVEN, metadata: Dict[str, Any] | NotGiven = NOT_GIVEN, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        """Create a new product."""
        return self._post("/commerce/products", body={"name": name, "price": price, "description": description, "images": images, "metadata": metadata}, options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    def update(self, product_id: str, *, name: str | NotGiven = NOT_GIVEN, price: float | NotGiven = NOT_GIVEN, description: str | NotGiven = NOT_GIVEN, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        """Update a product."""
        return self._put(f"/commerce/products/{product_id}", body={"name": name, "price": price, "description": description}, options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    def delete(self, product_id: str, *, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        """Delete a product."""
        return self._delete(f"/commerce/products/{product_id}", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    def list_variants(self, product_id: str, *, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        """List product variants."""
        return self._get(f"/commerce/products/{product_id}/variants", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)


class AsyncProductsResource(AsyncAPIResource):
    """Product catalog management (async)."""

    @cached_property
    def with_raw_response(self) -> AsyncProductsResourceWithRawResponse:
        return AsyncProductsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncProductsResourceWithStreamingResponse:
        return AsyncProductsResourceWithStreamingResponse(self)

    async def list(self, *, collection_id: str | NotGiven = NOT_GIVEN, limit: int | NotGiven = NOT_GIVEN, offset: int | NotGiven = NOT_GIVEN, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        return await self._get("/commerce/products", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout, query={"collection_id": collection_id, "limit": limit, "offset": offset}), cast_to=object)

    async def get(self, product_id: str, *, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        return await self._get(f"/commerce/products/{product_id}", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    async def create(self, *, name: str, price: float, description: str | NotGiven = NOT_GIVEN, images: List[str] | NotGiven = NOT_GIVEN, metadata: Dict[str, Any] | NotGiven = NOT_GIVEN, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        return await self._post("/commerce/products", body={"name": name, "price": price, "description": description, "images": images, "metadata": metadata}, options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    async def update(self, product_id: str, *, name: str | NotGiven = NOT_GIVEN, price: float | NotGiven = NOT_GIVEN, description: str | NotGiven = NOT_GIVEN, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        return await self._put(f"/commerce/products/{product_id}", body={"name": name, "price": price, "description": description}, options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    async def delete(self, product_id: str, *, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        return await self._delete(f"/commerce/products/{product_id}", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)

    async def list_variants(self, product_id: str, *, extra_headers: Headers | None = None, extra_query: Query | None = None, extra_body: Body | None = None, timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN) -> object:
        return await self._get(f"/commerce/products/{product_id}/variants", options=make_request_options(extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout), cast_to=object)


class ProductsResourceWithRawResponse:
    def __init__(self, products: ProductsResource) -> None:
        self._products = products
        self.list = to_raw_response_wrapper(products.list)
        self.get = to_raw_response_wrapper(products.get)
        self.create = to_raw_response_wrapper(products.create)
        self.update = to_raw_response_wrapper(products.update)
        self.delete = to_raw_response_wrapper(products.delete)
        self.list_variants = to_raw_response_wrapper(products.list_variants)


class AsyncProductsResourceWithRawResponse:
    def __init__(self, products: AsyncProductsResource) -> None:
        self._products = products
        self.list = async_to_raw_response_wrapper(products.list)
        self.get = async_to_raw_response_wrapper(products.get)
        self.create = async_to_raw_response_wrapper(products.create)
        self.update = async_to_raw_response_wrapper(products.update)
        self.delete = async_to_raw_response_wrapper(products.delete)
        self.list_variants = async_to_raw_response_wrapper(products.list_variants)


class ProductsResourceWithStreamingResponse:
    def __init__(self, products: ProductsResource) -> None:
        self._products = products
        self.list = to_streamed_response_wrapper(products.list)
        self.get = to_streamed_response_wrapper(products.get)
        self.create = to_streamed_response_wrapper(products.create)
        self.update = to_streamed_response_wrapper(products.update)
        self.delete = to_streamed_response_wrapper(products.delete)
        self.list_variants = to_streamed_response_wrapper(products.list_variants)


class AsyncProductsResourceWithStreamingResponse:
    def __init__(self, products: AsyncProductsResource) -> None:
        self._products = products
        self.list = async_to_streamed_response_wrapper(products.list)
        self.get = async_to_streamed_response_wrapper(products.get)
        self.create = async_to_streamed_response_wrapper(products.create)
        self.update = async_to_streamed_response_wrapper(products.update)
        self.delete = async_to_streamed_response_wrapper(products.delete)
        self.list_variants = async_to_streamed_response_wrapper(products.list_variants)
