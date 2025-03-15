# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from .pass_through_endpoint import (
    PassThroughEndpointResource,
    AsyncPassThroughEndpointResource,
    PassThroughEndpointResourceWithRawResponse,
    AsyncPassThroughEndpointResourceWithRawResponse,
    PassThroughEndpointResourceWithStreamingResponse,
    AsyncPassThroughEndpointResourceWithStreamingResponse,
)

__all__ = ["ConfigResource", "AsyncConfigResource"]


class ConfigResource(SyncAPIResource):
    @cached_property
    def pass_through_endpoint(self) -> PassThroughEndpointResource:
        return PassThroughEndpointResource(self._client)

    @cached_property
    def with_raw_response(self) -> ConfigResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return ConfigResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ConfigResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return ConfigResourceWithStreamingResponse(self)


class AsyncConfigResource(AsyncAPIResource):
    @cached_property
    def pass_through_endpoint(self) -> AsyncPassThroughEndpointResource:
        return AsyncPassThroughEndpointResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncConfigResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncConfigResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncConfigResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return AsyncConfigResourceWithStreamingResponse(self)


class ConfigResourceWithRawResponse:
    def __init__(self, config: ConfigResource) -> None:
        self._config = config

    @cached_property
    def pass_through_endpoint(self) -> PassThroughEndpointResourceWithRawResponse:
        return PassThroughEndpointResourceWithRawResponse(self._config.pass_through_endpoint)


class AsyncConfigResourceWithRawResponse:
    def __init__(self, config: AsyncConfigResource) -> None:
        self._config = config

    @cached_property
    def pass_through_endpoint(self) -> AsyncPassThroughEndpointResourceWithRawResponse:
        return AsyncPassThroughEndpointResourceWithRawResponse(self._config.pass_through_endpoint)


class ConfigResourceWithStreamingResponse:
    def __init__(self, config: ConfigResource) -> None:
        self._config = config

    @cached_property
    def pass_through_endpoint(self) -> PassThroughEndpointResourceWithStreamingResponse:
        return PassThroughEndpointResourceWithStreamingResponse(self._config.pass_through_endpoint)


class AsyncConfigResourceWithStreamingResponse:
    def __init__(self, config: AsyncConfigResource) -> None:
        self._config = config

    @cached_property
    def pass_through_endpoint(self) -> AsyncPassThroughEndpointResourceWithStreamingResponse:
        return AsyncPassThroughEndpointResourceWithStreamingResponse(self._config.pass_through_endpoint)
