# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List

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
from ...types.team import model_add_params, model_remove_params
from ..._base_client import make_request_options

__all__ = ["ModelResource", "AsyncModelResource"]


class ModelResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> ModelResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return ModelResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ModelResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return ModelResourceWithStreamingResponse(self)

    def add(
        self,
        *,
        models: List[str],
        team_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Add models to a team's allowed model list.

        Only proxy admin or team admin can
        add models.

        Parameters:

        - team_id: str - Required. The team to add models to
        - models: List[str] - Required. List of models to add to the team

        Example Request:

        ```
        curl --location 'http://0.0.0.0:4000/team/model/add'     --header 'Authorization: Bearer sk-1234'     --header 'Content-Type: application/json'     --data '{
            "team_id": "team-1234",
            "models": ["gpt-4", "claude-2"]
        }'
        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/team/model/add",
            body=maybe_transform(
                {
                    "models": models,
                    "team_id": team_id,
                },
                model_add_params.ModelAddParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def remove(
        self,
        *,
        models: List[str],
        team_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Remove models from a team's allowed model list.

        Only proxy admin or team admin
        can remove models.

        Parameters:

        - team_id: str - Required. The team to remove models from
        - models: List[str] - Required. List of models to remove from the team

        Example Request:

        ```
        curl --location 'http://0.0.0.0:4000/team/model/delete'     --header 'Authorization: Bearer sk-1234'     --header 'Content-Type: application/json'     --data '{
            "team_id": "team-1234",
            "models": ["gpt-4"]
        }'
        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/team/model/delete",
            body=maybe_transform(
                {
                    "models": models,
                    "team_id": team_id,
                },
                model_remove_params.ModelRemoveParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class AsyncModelResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncModelResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncModelResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncModelResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return AsyncModelResourceWithStreamingResponse(self)

    async def add(
        self,
        *,
        models: List[str],
        team_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Add models to a team's allowed model list.

        Only proxy admin or team admin can
        add models.

        Parameters:

        - team_id: str - Required. The team to add models to
        - models: List[str] - Required. List of models to add to the team

        Example Request:

        ```
        curl --location 'http://0.0.0.0:4000/team/model/add'     --header 'Authorization: Bearer sk-1234'     --header 'Content-Type: application/json'     --data '{
            "team_id": "team-1234",
            "models": ["gpt-4", "claude-2"]
        }'
        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/team/model/add",
            body=await async_maybe_transform(
                {
                    "models": models,
                    "team_id": team_id,
                },
                model_add_params.ModelAddParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def remove(
        self,
        *,
        models: List[str],
        team_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Remove models from a team's allowed model list.

        Only proxy admin or team admin
        can remove models.

        Parameters:

        - team_id: str - Required. The team to remove models from
        - models: List[str] - Required. List of models to remove from the team

        Example Request:

        ```
        curl --location 'http://0.0.0.0:4000/team/model/delete'     --header 'Authorization: Bearer sk-1234'     --header 'Content-Type: application/json'     --data '{
            "team_id": "team-1234",
            "models": ["gpt-4"]
        }'
        ```

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/team/model/delete",
            body=await async_maybe_transform(
                {
                    "models": models,
                    "team_id": team_id,
                },
                model_remove_params.ModelRemoveParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class ModelResourceWithRawResponse:
    def __init__(self, model: ModelResource) -> None:
        self._model = model

        self.add = to_raw_response_wrapper(
            model.add,
        )
        self.remove = to_raw_response_wrapper(
            model.remove,
        )


class AsyncModelResourceWithRawResponse:
    def __init__(self, model: AsyncModelResource) -> None:
        self._model = model

        self.add = async_to_raw_response_wrapper(
            model.add,
        )
        self.remove = async_to_raw_response_wrapper(
            model.remove,
        )


class ModelResourceWithStreamingResponse:
    def __init__(self, model: ModelResource) -> None:
        self._model = model

        self.add = to_streamed_response_wrapper(
            model.add,
        )
        self.remove = to_streamed_response_wrapper(
            model.remove,
        )


class AsyncModelResourceWithStreamingResponse:
    def __init__(self, model: AsyncModelResource) -> None:
        self._model = model

        self.add = async_to_streamed_response_wrapper(
            model.add,
        )
        self.remove = async_to_streamed_response_wrapper(
            model.remove,
        )
