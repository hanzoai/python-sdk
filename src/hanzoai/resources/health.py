# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union, Optional
from typing_extensions import Literal

import httpx

from ..types import health_check_all_params, health_check_services_params
from .._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from .._utils import (
    maybe_transform,
    async_maybe_transform,
)
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .._base_client import make_request_options

__all__ = ["HealthResource", "AsyncHealthResource"]


class HealthResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> HealthResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return HealthResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> HealthResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return HealthResourceWithStreamingResponse(self)

    def check_all(
        self,
        *,
        model: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        🚨 USE `/health/liveliness` to health check the proxy 🚨

        See more 👉 https://docs.hanzo.ai/docs/proxy/health

        Check the health of all the endpoints in config.yaml

        To run health checks in the background, add this to config.yaml:

        ```
        general_settings:
            # ... other settings
            background_health_checks: True
        ```

        else, the health checks will be run on models when /health is called.

        Args:
          model: Specify the model name (optional)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/health",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform({"model": model}, health_check_all_params.HealthCheckAllParams),
            ),
            cast_to=object,
        )

    def check_liveliness(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Unprotected endpoint for checking if worker is alive"""
        return self._get(
            "/health/liveliness",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def check_liveness(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Unprotected endpoint for checking if worker is alive"""
        return self._get(
            "/health/liveness",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def check_readiness(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Unprotected endpoint for checking if worker can receive requests"""
        return self._get(
            "/health/readiness",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def check_services(
        self,
        *,
        service: Union[
            Literal[
                "slack_budget_alerts", "langfuse", "slack", "openmeter", "webhook", "email", "braintrust", "datadog"
            ],
            str,
        ],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Use this admin-only endpoint to check if the service is healthy.

        Example:

        ```
        curl -L -X GET 'http://0.0.0.0:4000/health/services?service=datadog'     -H 'Authorization: Bearer sk-1234'
        ```

        Args:
          service: Specify the service being hit.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/health/services",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform({"service": service}, health_check_services_params.HealthCheckServicesParams),
            ),
            cast_to=object,
        )


class AsyncHealthResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncHealthResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncHealthResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncHealthResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return AsyncHealthResourceWithStreamingResponse(self)

    async def check_all(
        self,
        *,
        model: Optional[str] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        🚨 USE `/health/liveliness` to health check the proxy 🚨

        See more 👉 https://docs.hanzo.ai/docs/proxy/health

        Check the health of all the endpoints in config.yaml

        To run health checks in the background, add this to config.yaml:

        ```
        general_settings:
            # ... other settings
            background_health_checks: True
        ```

        else, the health checks will be run on models when /health is called.

        Args:
          model: Specify the model name (optional)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/health",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform({"model": model}, health_check_all_params.HealthCheckAllParams),
            ),
            cast_to=object,
        )

    async def check_liveliness(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Unprotected endpoint for checking if worker is alive"""
        return await self._get(
            "/health/liveliness",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def check_liveness(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Unprotected endpoint for checking if worker is alive"""
        return await self._get(
            "/health/liveness",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def check_readiness(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Unprotected endpoint for checking if worker can receive requests"""
        return await self._get(
            "/health/readiness",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def check_services(
        self,
        *,
        service: Union[
            Literal[
                "slack_budget_alerts", "langfuse", "slack", "openmeter", "webhook", "email", "braintrust", "datadog"
            ],
            str,
        ],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Use this admin-only endpoint to check if the service is healthy.

        Example:

        ```
        curl -L -X GET 'http://0.0.0.0:4000/health/services?service=datadog'     -H 'Authorization: Bearer sk-1234'
        ```

        Args:
          service: Specify the service being hit.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/health/services",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {"service": service}, health_check_services_params.HealthCheckServicesParams
                ),
            ),
            cast_to=object,
        )


class HealthResourceWithRawResponse:
    def __init__(self, health: HealthResource) -> None:
        self._health = health

        self.check_all = to_raw_response_wrapper(
            health.check_all,
        )
        self.check_liveliness = to_raw_response_wrapper(
            health.check_liveliness,
        )
        self.check_liveness = to_raw_response_wrapper(
            health.check_liveness,
        )
        self.check_readiness = to_raw_response_wrapper(
            health.check_readiness,
        )
        self.check_services = to_raw_response_wrapper(
            health.check_services,
        )


class AsyncHealthResourceWithRawResponse:
    def __init__(self, health: AsyncHealthResource) -> None:
        self._health = health

        self.check_all = async_to_raw_response_wrapper(
            health.check_all,
        )
        self.check_liveliness = async_to_raw_response_wrapper(
            health.check_liveliness,
        )
        self.check_liveness = async_to_raw_response_wrapper(
            health.check_liveness,
        )
        self.check_readiness = async_to_raw_response_wrapper(
            health.check_readiness,
        )
        self.check_services = async_to_raw_response_wrapper(
            health.check_services,
        )


class HealthResourceWithStreamingResponse:
    def __init__(self, health: HealthResource) -> None:
        self._health = health

        self.check_all = to_streamed_response_wrapper(
            health.check_all,
        )
        self.check_liveliness = to_streamed_response_wrapper(
            health.check_liveliness,
        )
        self.check_liveness = to_streamed_response_wrapper(
            health.check_liveness,
        )
        self.check_readiness = to_streamed_response_wrapper(
            health.check_readiness,
        )
        self.check_services = to_streamed_response_wrapper(
            health.check_services,
        )


class AsyncHealthResourceWithStreamingResponse:
    def __init__(self, health: AsyncHealthResource) -> None:
        self._health = health

        self.check_all = async_to_streamed_response_wrapper(
            health.check_all,
        )
        self.check_liveliness = async_to_streamed_response_wrapper(
            health.check_liveliness,
        )
        self.check_liveness = async_to_streamed_response_wrapper(
            health.check_liveness,
        )
        self.check_readiness = async_to_streamed_response_wrapper(
            health.check_readiness,
        )
        self.check_services = async_to_streamed_response_wrapper(
            health.check_services,
        )
