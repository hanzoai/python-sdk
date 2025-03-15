# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional

import httpx

from ..._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from ..._utils import (
    maybe_transform,
    async_maybe_transform,
)
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..._base_client import make_request_options
from ...types.batches import cancel_cancel_params

__all__ = ["CancelResource", "AsyncCancelResource"]


class CancelResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> CancelResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return CancelResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> CancelResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return CancelResourceWithStreamingResponse(self)

    def cancel(
        self,
        batch_id: str,
        *,
        provider: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Cancel a batch.

        This is the equivalent of POST
        https://api.openai.com/v1/batches/{batch_id}/cancel

        Supports Identical Params as:
        https://platform.openai.com/docs/api-reference/batch/cancel

        Example Curl

        ```
        curl http://localhost:4000/v1/batches/batch_abc123/cancel         -H "Authorization: Bearer sk-1234"         -H "Content-Type: application/json"         -X POST

        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not batch_id:
            raise ValueError(f"Expected a non-empty value for `batch_id` but received {batch_id!r}")
        return self._post(
            f"/batches/{batch_id}/cancel",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform({"provider": provider}, cancel_cancel_params.CancelCancelParams),
            ),
            cast_to=object,
        )


class AsyncCancelResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncCancelResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncCancelResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncCancelResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return AsyncCancelResourceWithStreamingResponse(self)

    async def cancel(
        self,
        batch_id: str,
        *,
        provider: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Cancel a batch.

        This is the equivalent of POST
        https://api.openai.com/v1/batches/{batch_id}/cancel

        Supports Identical Params as:
        https://platform.openai.com/docs/api-reference/batch/cancel

        Example Curl

        ```
        curl http://localhost:4000/v1/batches/batch_abc123/cancel         -H "Authorization: Bearer sk-1234"         -H "Content-Type: application/json"         -X POST

        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not batch_id:
            raise ValueError(f"Expected a non-empty value for `batch_id` but received {batch_id!r}")
        return await self._post(
            f"/batches/{batch_id}/cancel",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform({"provider": provider}, cancel_cancel_params.CancelCancelParams),
            ),
            cast_to=object,
        )


class CancelResourceWithRawResponse:
    def __init__(self, cancel: CancelResource) -> None:
        self._cancel = cancel

        self.cancel = to_raw_response_wrapper(
            cancel.cancel,
        )


class AsyncCancelResourceWithRawResponse:
    def __init__(self, cancel: AsyncCancelResource) -> None:
        self._cancel = cancel

        self.cancel = async_to_raw_response_wrapper(
            cancel.cancel,
        )


class CancelResourceWithStreamingResponse:
    def __init__(self, cancel: CancelResource) -> None:
        self._cancel = cancel

        self.cancel = to_streamed_response_wrapper(
            cancel.cancel,
        )


class AsyncCancelResourceWithStreamingResponse:
    def __init__(self, cancel: AsyncCancelResource) -> None:
        self._cancel = cancel

        self.cancel = async_to_streamed_response_wrapper(
            cancel.cancel,
        )
