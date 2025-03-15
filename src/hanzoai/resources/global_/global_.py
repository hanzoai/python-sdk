# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from .spend import (
    SpendResource,
    AsyncSpendResource,
    SpendResourceWithRawResponse,
    AsyncSpendResourceWithRawResponse,
    SpendResourceWithStreamingResponse,
    AsyncSpendResourceWithStreamingResponse,
)
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource

__all__ = ["GlobalResource", "AsyncGlobalResource"]


class GlobalResource(SyncAPIResource):
    @cached_property
    def spend(self) -> SpendResource:
        return SpendResource(self._client)

    @cached_property
    def with_raw_response(self) -> GlobalResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return GlobalResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> GlobalResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return GlobalResourceWithStreamingResponse(self)


class AsyncGlobalResource(AsyncAPIResource):
    @cached_property
    def spend(self) -> AsyncSpendResource:
        return AsyncSpendResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncGlobalResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncGlobalResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncGlobalResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return AsyncGlobalResourceWithStreamingResponse(self)


class GlobalResourceWithRawResponse:
    def __init__(self, global_: GlobalResource) -> None:
        self._global_ = global_

    @cached_property
    def spend(self) -> SpendResourceWithRawResponse:
        return SpendResourceWithRawResponse(self._global_.spend)


class AsyncGlobalResourceWithRawResponse:
    def __init__(self, global_: AsyncGlobalResource) -> None:
        self._global_ = global_

    @cached_property
    def spend(self) -> AsyncSpendResourceWithRawResponse:
        return AsyncSpendResourceWithRawResponse(self._global_.spend)


class GlobalResourceWithStreamingResponse:
    def __init__(self, global_: GlobalResource) -> None:
        self._global_ = global_

    @cached_property
    def spend(self) -> SpendResourceWithStreamingResponse:
        return SpendResourceWithStreamingResponse(self._global_.spend)


class AsyncGlobalResourceWithStreamingResponse:
    def __init__(self, global_: AsyncGlobalResource) -> None:
        self._global_ = global_

    @cached_property
    def spend(self) -> AsyncSpendResourceWithStreamingResponse:
        return AsyncSpendResourceWithStreamingResponse(self._global_.spend)
