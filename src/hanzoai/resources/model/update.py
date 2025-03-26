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
from ...types.model import update_full_params, update_partial_params
from ..._base_client import make_request_options
from ...types.model_info_param import ModelInfoParam

__all__ = ["UpdateResource", "AsyncUpdateResource"]


class UpdateResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> UpdateResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return UpdateResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> UpdateResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return UpdateResourceWithStreamingResponse(self)

    def full(
        self,
        *,
        llm_params: Optional[update_full_params.LlmParams] | NotGiven = NOT_GIVEN,
        model_info: Optional[ModelInfoParam] | NotGiven = NOT_GIVEN,
        model_name: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Edit existing model params

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/model/update",
            body=maybe_transform(
                {
                    "llm_params": llm_params,
                    "model_info": model_info,
                    "model_name": model_name,
                },
                update_full_params.UpdateFullParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def partial(
        self,
        model_id: str,
        *,
        llm_params: Optional[update_partial_params.LlmParams] | NotGiven = NOT_GIVEN,
        model_info: Optional[ModelInfoParam] | NotGiven = NOT_GIVEN,
        model_name: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        PATCH Endpoint for partial model updates.

        Only updates the fields specified in the request while preserving other existing
        values. Follows proper PATCH semantics by only modifying provided fields.

        Args: model_id: The ID of the model to update patch_data: The fields to update
        and their new values user_api_key_dict: User authentication information

        Returns: Updated model information

        Raises: ProxyException: For various error conditions including authentication
        and database errors

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not model_id:
            raise ValueError(f"Expected a non-empty value for `model_id` but received {model_id!r}")
        return self._patch(
            f"/model/{model_id}/update",
            body=maybe_transform(
                {
                    "llm_params": llm_params,
                    "model_info": model_info,
                    "model_name": model_name,
                },
                update_partial_params.UpdatePartialParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class AsyncUpdateResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncUpdateResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncUpdateResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncUpdateResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return AsyncUpdateResourceWithStreamingResponse(self)

    async def full(
        self,
        *,
        llm_params: Optional[update_full_params.LlmParams] | NotGiven = NOT_GIVEN,
        model_info: Optional[ModelInfoParam] | NotGiven = NOT_GIVEN,
        model_name: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Edit existing model params

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/model/update",
            body=await async_maybe_transform(
                {
                    "llm_params": llm_params,
                    "model_info": model_info,
                    "model_name": model_name,
                },
                update_full_params.UpdateFullParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def partial(
        self,
        model_id: str,
        *,
        llm_params: Optional[update_partial_params.LlmParams] | NotGiven = NOT_GIVEN,
        model_info: Optional[ModelInfoParam] | NotGiven = NOT_GIVEN,
        model_name: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        PATCH Endpoint for partial model updates.

        Only updates the fields specified in the request while preserving other existing
        values. Follows proper PATCH semantics by only modifying provided fields.

        Args: model_id: The ID of the model to update patch_data: The fields to update
        and their new values user_api_key_dict: User authentication information

        Returns: Updated model information

        Raises: ProxyException: For various error conditions including authentication
        and database errors

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not model_id:
            raise ValueError(f"Expected a non-empty value for `model_id` but received {model_id!r}")
        return await self._patch(
            f"/model/{model_id}/update",
            body=await async_maybe_transform(
                {
                    "llm_params": llm_params,
                    "model_info": model_info,
                    "model_name": model_name,
                },
                update_partial_params.UpdatePartialParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class UpdateResourceWithRawResponse:
    def __init__(self, update: UpdateResource) -> None:
        self._update = update

        self.full = to_raw_response_wrapper(
            update.full,
        )
        self.partial = to_raw_response_wrapper(
            update.partial,
        )


class AsyncUpdateResourceWithRawResponse:
    def __init__(self, update: AsyncUpdateResource) -> None:
        self._update = update

        self.full = async_to_raw_response_wrapper(
            update.full,
        )
        self.partial = async_to_raw_response_wrapper(
            update.partial,
        )


class UpdateResourceWithStreamingResponse:
    def __init__(self, update: UpdateResource) -> None:
        self._update = update

        self.full = to_streamed_response_wrapper(
            update.full,
        )
        self.partial = to_streamed_response_wrapper(
            update.partial,
        )


class AsyncUpdateResourceWithStreamingResponse:
    def __init__(self, update: AsyncUpdateResource) -> None:
        self._update = update

        self.full = async_to_streamed_response_wrapper(
            update.full,
        )
        self.partial = async_to_streamed_response_wrapper(
            update.partial,
        )
