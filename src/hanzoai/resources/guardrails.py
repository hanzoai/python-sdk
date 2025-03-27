# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

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
from ..types.guardrail_list_response import GuardrailListResponse

__all__ = ["GuardrailsResource", "AsyncGuardrailsResource"]


class GuardrailsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> GuardrailsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return GuardrailsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> GuardrailsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return GuardrailsResourceWithStreamingResponse(self)

    def list(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> GuardrailListResponse:
        """
        List the guardrails that are available on the proxy server

        👉 [Guardrail docs](https://docs.hanzo.ai/docs/proxy/guardrails/quick_start)

        Example Request:

        ```bash
        curl -X GET "http://localhost:4000/guardrails/list" -H "Authorization: Bearer <your_api_key>"
        ```

        Example Response:

        ```json
        {
          "guardrails": [
            {
              "guardrail_name": "bedrock-pre-guard",
              "guardrail_info": {
                "params": [
                  {
                    "name": "toxicity_score",
                    "type": "float",
                    "description": "Score between 0-1 indicating content toxicity level"
                  },
                  {
                    "name": "pii_detection",
                    "type": "boolean"
                  }
                ]
              }
            }
          ]
        }
        ```
        """
        return self._get(
            "/guardrails/list",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=GuardrailListResponse,
        )


class AsyncGuardrailsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncGuardrailsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncGuardrailsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncGuardrailsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return AsyncGuardrailsResourceWithStreamingResponse(self)

    async def list(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> GuardrailListResponse:
        """
        List the guardrails that are available on the proxy server

        👉 [Guardrail docs](https://docs.hanzo.ai/docs/proxy/guardrails/quick_start)

        Example Request:

        ```bash
        curl -X GET "http://localhost:4000/guardrails/list" -H "Authorization: Bearer <your_api_key>"
        ```

        Example Response:

        ```json
        {
          "guardrails": [
            {
              "guardrail_name": "bedrock-pre-guard",
              "guardrail_info": {
                "params": [
                  {
                    "name": "toxicity_score",
                    "type": "float",
                    "description": "Score between 0-1 indicating content toxicity level"
                  },
                  {
                    "name": "pii_detection",
                    "type": "boolean"
                  }
                ]
              }
            }
          ]
        }
        ```
        """
        return await self._get(
            "/guardrails/list",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=GuardrailListResponse,
        )


class GuardrailsResourceWithRawResponse:
    def __init__(self, guardrails: GuardrailsResource) -> None:
        self._guardrails = guardrails

        self.list = to_raw_response_wrapper(
            guardrails.list,
        )


class AsyncGuardrailsResourceWithRawResponse:
    def __init__(self, guardrails: AsyncGuardrailsResource) -> None:
        self._guardrails = guardrails

        self.list = async_to_raw_response_wrapper(
            guardrails.list,
        )


class GuardrailsResourceWithStreamingResponse:
    def __init__(self, guardrails: GuardrailsResource) -> None:
        self._guardrails = guardrails

        self.list = to_streamed_response_wrapper(
            guardrails.list,
        )


class AsyncGuardrailsResourceWithStreamingResponse:
    def __init__(self, guardrails: AsyncGuardrailsResource) -> None:
        self._guardrails = guardrails

        self.list = async_to_streamed_response_wrapper(
            guardrails.list,
        )
