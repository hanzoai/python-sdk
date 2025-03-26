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
from ...types.model import info_list_params
from ..._base_client import make_request_options

__all__ = ["InfoResource", "AsyncInfoResource"]


class InfoResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> InfoResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return InfoResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> InfoResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return InfoResourceWithStreamingResponse(self)

    def list(
        self,
        *,
        llm_model_id: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Provides more info about each model in /models, including config.yaml
        descriptions (except api key and api base)

        Parameters: llm_model_id: Optional[str] = None (this is the value of
        `x-llm-model-id` returned in response headers)

            - When llm_model_id is passed, it will return the info for that specific model
            - When llm_model_id is not passed, it will return the info for all models

        Returns: Returns a dictionary containing information about each model.

        Example Response:

        ```json
        {
          "data": [
            {
              "model_name": "fake-openai-endpoint",
              "llm_params": {
                "api_base": "https://exampleopenaiendpoint-production.up.railway.app/",
                "model": "openai/fake"
              },
              "model_info": {
                "id": "112f74fab24a7a5245d2ced3536dd8f5f9192c57ee6e332af0f0512e08bed5af",
                "db_model": false
              }
            }
          ]
        }
        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/model/info",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform({"llm_model_id": llm_model_id}, info_list_params.InfoListParams),
            ),
            cast_to=object,
        )


class AsyncInfoResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncInfoResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncInfoResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncInfoResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return AsyncInfoResourceWithStreamingResponse(self)

    async def list(
        self,
        *,
        llm_model_id: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Provides more info about each model in /models, including config.yaml
        descriptions (except api key and api base)

        Parameters: llm_model_id: Optional[str] = None (this is the value of
        `x-llm-model-id` returned in response headers)

            - When llm_model_id is passed, it will return the info for that specific model
            - When llm_model_id is not passed, it will return the info for all models

        Returns: Returns a dictionary containing information about each model.

        Example Response:

        ```json
        {
          "data": [
            {
              "model_name": "fake-openai-endpoint",
              "llm_params": {
                "api_base": "https://exampleopenaiendpoint-production.up.railway.app/",
                "model": "openai/fake"
              },
              "model_info": {
                "id": "112f74fab24a7a5245d2ced3536dd8f5f9192c57ee6e332af0f0512e08bed5af",
                "db_model": false
              }
            }
          ]
        }
        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/model/info",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform({"llm_model_id": llm_model_id}, info_list_params.InfoListParams),
            ),
            cast_to=object,
        )


class InfoResourceWithRawResponse:
    def __init__(self, info: InfoResource) -> None:
        self._info = info

        self.list = to_raw_response_wrapper(
            info.list,
        )


class AsyncInfoResourceWithRawResponse:
    def __init__(self, info: AsyncInfoResource) -> None:
        self._info = info

        self.list = async_to_raw_response_wrapper(
            info.list,
        )


class InfoResourceWithStreamingResponse:
    def __init__(self, info: InfoResource) -> None:
        self._info = info

        self.list = to_streamed_response_wrapper(
            info.list,
        )


class AsyncInfoResourceWithStreamingResponse:
    def __init__(self, info: AsyncInfoResource) -> None:
        self._info = info

        self.list = async_to_streamed_response_wrapper(
            info.list,
        )
