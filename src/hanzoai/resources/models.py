# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional

import httpx

from ..types import model_list_params
from .._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from .._utils import maybe_transform, async_maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .._base_client import make_request_options

__all__ = ["ModelsResource", "AsyncModelsResource"]


class ModelsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> ModelsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return ModelsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ModelsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return ModelsResourceWithStreamingResponse(self)

    def list(
        self,
        *,
        fallback_type: Optional[str] | Omit = omit,
        include_metadata: Optional[bool] | Omit = omit,
        include_model_access_groups: Optional[bool] | Omit = omit,
        only_model_access_groups: Optional[bool] | Omit = omit,
        return_wildcard_routes: Optional[bool] | Omit = omit,
        team_id: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        Use `/model/info` - to get detailed model information, example - pricing, mode,
        etc.

        This is just for compatibility with openai projects like aider.

        Query Parameters:

        - include_metadata: Include additional metadata in the response with fallback
          information
        - fallback_type: Type of fallbacks to include ("general", "context_window",
          "content_policy") Defaults to "general" when include_metadata=true

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/v1/models",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "fallback_type": fallback_type,
                        "include_metadata": include_metadata,
                        "include_model_access_groups": include_model_access_groups,
                        "only_model_access_groups": only_model_access_groups,
                        "return_wildcard_routes": return_wildcard_routes,
                        "team_id": team_id,
                    },
                    model_list_params.ModelListParams,
                ),
            ),
            cast_to=object,
        )


class AsyncModelsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncModelsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncModelsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncModelsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return AsyncModelsResourceWithStreamingResponse(self)

    async def list(
        self,
        *,
        fallback_type: Optional[str] | Omit = omit,
        include_metadata: Optional[bool] | Omit = omit,
        include_model_access_groups: Optional[bool] | Omit = omit,
        only_model_access_groups: Optional[bool] | Omit = omit,
        return_wildcard_routes: Optional[bool] | Omit = omit,
        team_id: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        Use `/model/info` - to get detailed model information, example - pricing, mode,
        etc.

        This is just for compatibility with openai projects like aider.

        Query Parameters:

        - include_metadata: Include additional metadata in the response with fallback
          information
        - fallback_type: Type of fallbacks to include ("general", "context_window",
          "content_policy") Defaults to "general" when include_metadata=true

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/v1/models",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "fallback_type": fallback_type,
                        "include_metadata": include_metadata,
                        "include_model_access_groups": include_model_access_groups,
                        "only_model_access_groups": only_model_access_groups,
                        "return_wildcard_routes": return_wildcard_routes,
                        "team_id": team_id,
                    },
                    model_list_params.ModelListParams,
                ),
            ),
            cast_to=object,
        )


class ModelsResourceWithRawResponse:
    def __init__(self, models: ModelsResource) -> None:
        self._models = models

        self.list = to_raw_response_wrapper(
            models.list,
        )


class AsyncModelsResourceWithRawResponse:
    def __init__(self, models: AsyncModelsResource) -> None:
        self._models = models

        self.list = async_to_raw_response_wrapper(
            models.list,
        )


class ModelsResourceWithStreamingResponse:
    def __init__(self, models: ModelsResource) -> None:
        self._models = models

        self.list = to_streamed_response_wrapper(
            models.list,
        )


class AsyncModelsResourceWithStreamingResponse:
    def __init__(self, models: AsyncModelsResource) -> None:
        self._models = models

        self.list = async_to_streamed_response_wrapper(
            models.list,
        )
