# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Optional

import httpx

from ..._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ..._utils import maybe_transform, async_maybe_transform
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..._base_client import make_request_options
from ...types.config import (
    pass_through_endpoint_list_params,
    pass_through_endpoint_create_params,
    pass_through_endpoint_delete_params,
    pass_through_endpoint_update_params,
)
from ...types.config.pass_through_endpoint_response import PassThroughEndpointResponse

__all__ = ["PassThroughEndpointResource", "AsyncPassThroughEndpointResource"]


class PassThroughEndpointResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> PassThroughEndpointResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return PassThroughEndpointResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> PassThroughEndpointResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return PassThroughEndpointResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        path: str,
        target: str,
        id: Optional[str] | Omit = omit,
        auth: bool | Omit = omit,
        cost_per_request: float | Omit = omit,
        guardrails: Optional[Dict[str, Optional[pass_through_endpoint_create_params.Guardrails]]] | Omit = omit,
        headers: Dict[str, object] | Omit = omit,
        include_subpath: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        Create new pass-through endpoint

        Args:
          path: The route to be added to the LiteLLM Proxy Server.

          target: The URL to which requests for this path should be forwarded.

          id: Optional unique identifier for the pass-through endpoint. If not provided,
              endpoints will be identified by path for backwards compatibility.

          auth: Whether authentication is required for the pass-through endpoint. If True,
              requests to the endpoint will require a valid LiteLLM API key.

          cost_per_request: The USD cost per request to the target endpoint. This is used to calculate the
              cost of the request to the target endpoint.

          guardrails: Guardrails configuration for this passthrough endpoint. Dict keys are guardrail
              names, values are optional settings for field targeting. When set, all
              org/team/key level guardrails will also execute. Defaults to None (no guardrails
              execute).

          headers: Key-value pairs of headers to be forwarded with the request. You can set any key
              value pair here and it will be forwarded to your target endpoint

          include_subpath: If True, requests to subpaths of the path will be forwarded to the target
              endpoint. For example, if the path is /bria and include_subpath is True,
              requests to /bria/v1/text-to-image/base/2.3 will be forwarded to the target
              endpoint.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/config/pass_through_endpoint",
            body=maybe_transform(
                {
                    "path": path,
                    "target": target,
                    "id": id,
                    "auth": auth,
                    "cost_per_request": cost_per_request,
                    "guardrails": guardrails,
                    "headers": headers,
                    "include_subpath": include_subpath,
                },
                pass_through_endpoint_create_params.PassThroughEndpointCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def update(
        self,
        endpoint_id: str,
        *,
        path: str,
        target: str,
        id: Optional[str] | Omit = omit,
        auth: bool | Omit = omit,
        cost_per_request: float | Omit = omit,
        guardrails: Optional[Dict[str, Optional[pass_through_endpoint_update_params.Guardrails]]] | Omit = omit,
        headers: Dict[str, object] | Omit = omit,
        include_subpath: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        Update a pass-through endpoint by ID.

        Args:
          path: The route to be added to the LiteLLM Proxy Server.

          target: The URL to which requests for this path should be forwarded.

          id: Optional unique identifier for the pass-through endpoint. If not provided,
              endpoints will be identified by path for backwards compatibility.

          auth: Whether authentication is required for the pass-through endpoint. If True,
              requests to the endpoint will require a valid LiteLLM API key.

          cost_per_request: The USD cost per request to the target endpoint. This is used to calculate the
              cost of the request to the target endpoint.

          guardrails: Guardrails configuration for this passthrough endpoint. Dict keys are guardrail
              names, values are optional settings for field targeting. When set, all
              org/team/key level guardrails will also execute. Defaults to None (no guardrails
              execute).

          headers: Key-value pairs of headers to be forwarded with the request. You can set any key
              value pair here and it will be forwarded to your target endpoint

          include_subpath: If True, requests to subpaths of the path will be forwarded to the target
              endpoint. For example, if the path is /bria and include_subpath is True,
              requests to /bria/v1/text-to-image/base/2.3 will be forwarded to the target
              endpoint.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not endpoint_id:
            raise ValueError(f"Expected a non-empty value for `endpoint_id` but received {endpoint_id!r}")
        return self._post(
            f"/config/pass_through_endpoint/{endpoint_id}",
            body=maybe_transform(
                {
                    "path": path,
                    "target": target,
                    "id": id,
                    "auth": auth,
                    "cost_per_request": cost_per_request,
                    "guardrails": guardrails,
                    "headers": headers,
                    "include_subpath": include_subpath,
                },
                pass_through_endpoint_update_params.PassThroughEndpointUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def list(
        self,
        *,
        endpoint_id: Optional[str] | Omit = omit,
        team_id: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PassThroughEndpointResponse:
        """
        GET configured pass through endpoint.

        If no endpoint_id given, return all configured endpoints.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/config/pass_through_endpoint",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "endpoint_id": endpoint_id,
                        "team_id": team_id,
                    },
                    pass_through_endpoint_list_params.PassThroughEndpointListParams,
                ),
            ),
            cast_to=PassThroughEndpointResponse,
        )

    def delete(
        self,
        *,
        endpoint_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PassThroughEndpointResponse:
        """
        Delete a pass-through endpoint by ID.

        Returns - the deleted endpoint

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._delete(
            "/config/pass_through_endpoint",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {"endpoint_id": endpoint_id}, pass_through_endpoint_delete_params.PassThroughEndpointDeleteParams
                ),
            ),
            cast_to=PassThroughEndpointResponse,
        )


class AsyncPassThroughEndpointResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncPassThroughEndpointResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncPassThroughEndpointResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncPassThroughEndpointResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return AsyncPassThroughEndpointResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        path: str,
        target: str,
        id: Optional[str] | Omit = omit,
        auth: bool | Omit = omit,
        cost_per_request: float | Omit = omit,
        guardrails: Optional[Dict[str, Optional[pass_through_endpoint_create_params.Guardrails]]] | Omit = omit,
        headers: Dict[str, object] | Omit = omit,
        include_subpath: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        Create new pass-through endpoint

        Args:
          path: The route to be added to the LiteLLM Proxy Server.

          target: The URL to which requests for this path should be forwarded.

          id: Optional unique identifier for the pass-through endpoint. If not provided,
              endpoints will be identified by path for backwards compatibility.

          auth: Whether authentication is required for the pass-through endpoint. If True,
              requests to the endpoint will require a valid LiteLLM API key.

          cost_per_request: The USD cost per request to the target endpoint. This is used to calculate the
              cost of the request to the target endpoint.

          guardrails: Guardrails configuration for this passthrough endpoint. Dict keys are guardrail
              names, values are optional settings for field targeting. When set, all
              org/team/key level guardrails will also execute. Defaults to None (no guardrails
              execute).

          headers: Key-value pairs of headers to be forwarded with the request. You can set any key
              value pair here and it will be forwarded to your target endpoint

          include_subpath: If True, requests to subpaths of the path will be forwarded to the target
              endpoint. For example, if the path is /bria and include_subpath is True,
              requests to /bria/v1/text-to-image/base/2.3 will be forwarded to the target
              endpoint.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/config/pass_through_endpoint",
            body=await async_maybe_transform(
                {
                    "path": path,
                    "target": target,
                    "id": id,
                    "auth": auth,
                    "cost_per_request": cost_per_request,
                    "guardrails": guardrails,
                    "headers": headers,
                    "include_subpath": include_subpath,
                },
                pass_through_endpoint_create_params.PassThroughEndpointCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def update(
        self,
        endpoint_id: str,
        *,
        path: str,
        target: str,
        id: Optional[str] | Omit = omit,
        auth: bool | Omit = omit,
        cost_per_request: float | Omit = omit,
        guardrails: Optional[Dict[str, Optional[pass_through_endpoint_update_params.Guardrails]]] | Omit = omit,
        headers: Dict[str, object] | Omit = omit,
        include_subpath: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        Update a pass-through endpoint by ID.

        Args:
          path: The route to be added to the LiteLLM Proxy Server.

          target: The URL to which requests for this path should be forwarded.

          id: Optional unique identifier for the pass-through endpoint. If not provided,
              endpoints will be identified by path for backwards compatibility.

          auth: Whether authentication is required for the pass-through endpoint. If True,
              requests to the endpoint will require a valid LiteLLM API key.

          cost_per_request: The USD cost per request to the target endpoint. This is used to calculate the
              cost of the request to the target endpoint.

          guardrails: Guardrails configuration for this passthrough endpoint. Dict keys are guardrail
              names, values are optional settings for field targeting. When set, all
              org/team/key level guardrails will also execute. Defaults to None (no guardrails
              execute).

          headers: Key-value pairs of headers to be forwarded with the request. You can set any key
              value pair here and it will be forwarded to your target endpoint

          include_subpath: If True, requests to subpaths of the path will be forwarded to the target
              endpoint. For example, if the path is /bria and include_subpath is True,
              requests to /bria/v1/text-to-image/base/2.3 will be forwarded to the target
              endpoint.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not endpoint_id:
            raise ValueError(f"Expected a non-empty value for `endpoint_id` but received {endpoint_id!r}")
        return await self._post(
            f"/config/pass_through_endpoint/{endpoint_id}",
            body=await async_maybe_transform(
                {
                    "path": path,
                    "target": target,
                    "id": id,
                    "auth": auth,
                    "cost_per_request": cost_per_request,
                    "guardrails": guardrails,
                    "headers": headers,
                    "include_subpath": include_subpath,
                },
                pass_through_endpoint_update_params.PassThroughEndpointUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def list(
        self,
        *,
        endpoint_id: Optional[str] | Omit = omit,
        team_id: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PassThroughEndpointResponse:
        """
        GET configured pass through endpoint.

        If no endpoint_id given, return all configured endpoints.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/config/pass_through_endpoint",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "endpoint_id": endpoint_id,
                        "team_id": team_id,
                    },
                    pass_through_endpoint_list_params.PassThroughEndpointListParams,
                ),
            ),
            cast_to=PassThroughEndpointResponse,
        )

    async def delete(
        self,
        *,
        endpoint_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PassThroughEndpointResponse:
        """
        Delete a pass-through endpoint by ID.

        Returns - the deleted endpoint

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._delete(
            "/config/pass_through_endpoint",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {"endpoint_id": endpoint_id}, pass_through_endpoint_delete_params.PassThroughEndpointDeleteParams
                ),
            ),
            cast_to=PassThroughEndpointResponse,
        )


class PassThroughEndpointResourceWithRawResponse:
    def __init__(self, pass_through_endpoint: PassThroughEndpointResource) -> None:
        self._pass_through_endpoint = pass_through_endpoint

        self.create = to_raw_response_wrapper(
            pass_through_endpoint.create,
        )
        self.update = to_raw_response_wrapper(
            pass_through_endpoint.update,
        )
        self.list = to_raw_response_wrapper(
            pass_through_endpoint.list,
        )
        self.delete = to_raw_response_wrapper(
            pass_through_endpoint.delete,
        )


class AsyncPassThroughEndpointResourceWithRawResponse:
    def __init__(self, pass_through_endpoint: AsyncPassThroughEndpointResource) -> None:
        self._pass_through_endpoint = pass_through_endpoint

        self.create = async_to_raw_response_wrapper(
            pass_through_endpoint.create,
        )
        self.update = async_to_raw_response_wrapper(
            pass_through_endpoint.update,
        )
        self.list = async_to_raw_response_wrapper(
            pass_through_endpoint.list,
        )
        self.delete = async_to_raw_response_wrapper(
            pass_through_endpoint.delete,
        )


class PassThroughEndpointResourceWithStreamingResponse:
    def __init__(self, pass_through_endpoint: PassThroughEndpointResource) -> None:
        self._pass_through_endpoint = pass_through_endpoint

        self.create = to_streamed_response_wrapper(
            pass_through_endpoint.create,
        )
        self.update = to_streamed_response_wrapper(
            pass_through_endpoint.update,
        )
        self.list = to_streamed_response_wrapper(
            pass_through_endpoint.list,
        )
        self.delete = to_streamed_response_wrapper(
            pass_through_endpoint.delete,
        )


class AsyncPassThroughEndpointResourceWithStreamingResponse:
    def __init__(self, pass_through_endpoint: AsyncPassThroughEndpointResource) -> None:
        self._pass_through_endpoint = pass_through_endpoint

        self.create = async_to_streamed_response_wrapper(
            pass_through_endpoint.create,
        )
        self.update = async_to_streamed_response_wrapper(
            pass_through_endpoint.update,
        )
        self.list = async_to_streamed_response_wrapper(
            pass_through_endpoint.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            pass_through_endpoint.delete,
        )
