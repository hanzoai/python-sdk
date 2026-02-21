# Hanzo AI SDK

from __future__ import annotations

from typing import List, Optional

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

__all__ = ["ContainersResource", "AsyncContainersResource"]


class ContainersResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> ContainersResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return ContainersResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ContainersResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return ContainersResourceWithStreamingResponse(self)

    def list(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all containers in the infrastructure."""
        return self._get(
            "/infrastructure/containers",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def get(
        self,
        container_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Get details of a specific container.

        Args:
          container_id: The unique identifier of the container.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not container_id:
            raise ValueError(f"Expected a non-empty value for `container_id` but received {container_id!r}")
        return self._get(
            f"/infrastructure/containers/{container_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def create(
        self,
        *,
        name: Optional[str] | NotGiven = NOT_GIVEN,
        image: Optional[str] | NotGiven = NOT_GIVEN,
        command: Optional[List[str]] | NotGiven = NOT_GIVEN,
        env: Optional[dict] | NotGiven = NOT_GIVEN,
        ports: Optional[List[dict]] | NotGiven = NOT_GIVEN,
        volumes: Optional[List[dict]] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Create a new container.

        Args:
          name: The name of the container.

          image: The Docker image to use.

          command: The command to run in the container.

          env: Environment variables for the container.

          ports: Port mappings for the container.

          volumes: Volume mounts for the container.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/infrastructure/containers",
            body={
                "name": name,
                "image": image,
                "command": command,
                "env": env,
                "ports": ports,
                "volumes": volumes,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def update(
        self,
        container_id: str,
        *,
        name: Optional[str] | NotGiven = NOT_GIVEN,
        image: Optional[str] | NotGiven = NOT_GIVEN,
        env: Optional[dict] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Update an existing container.

        Args:
          container_id: The unique identifier of the container.

          name: The new name of the container.

          image: The new Docker image.

          env: Updated environment variables.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not container_id:
            raise ValueError(f"Expected a non-empty value for `container_id` but received {container_id!r}")
        return self._put(
            f"/infrastructure/containers/{container_id}",
            body={
                "name": name,
                "image": image,
                "env": env,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def delete(
        self,
        container_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Delete a container.

        Args:
          container_id: The unique identifier of the container.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not container_id:
            raise ValueError(f"Expected a non-empty value for `container_id` but received {container_id!r}")
        return self._delete(
            f"/infrastructure/containers/{container_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def start(
        self,
        container_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Start a stopped container.

        Args:
          container_id: The unique identifier of the container.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not container_id:
            raise ValueError(f"Expected a non-empty value for `container_id` but received {container_id!r}")
        return self._post(
            f"/infrastructure/containers/{container_id}/start",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def stop(
        self,
        container_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Stop a running container.

        Args:
          container_id: The unique identifier of the container.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not container_id:
            raise ValueError(f"Expected a non-empty value for `container_id` but received {container_id!r}")
        return self._post(
            f"/infrastructure/containers/{container_id}/stop",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def logs(
        self,
        container_id: str,
        *,
        tail: Optional[int] | NotGiven = NOT_GIVEN,
        follow: Optional[bool] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Get logs from a container.

        Args:
          container_id: The unique identifier of the container.

          tail: Number of lines to return from the end of the logs.

          follow: Whether to stream logs in real-time.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not container_id:
            raise ValueError(f"Expected a non-empty value for `container_id` but received {container_id!r}")
        return self._get(
            f"/infrastructure/containers/{container_id}/logs",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={
                    "tail": tail,
                    "follow": follow,
                },
            ),
            cast_to=object,
        )

    def exec(
        self,
        container_id: str,
        *,
        command: List[str],
        workdir: Optional[str] | NotGiven = NOT_GIVEN,
        env: Optional[dict] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Execute a command in a running container.

        Args:
          container_id: The unique identifier of the container.

          command: The command to execute.

          workdir: Working directory for the command.

          env: Environment variables for the command.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not container_id:
            raise ValueError(f"Expected a non-empty value for `container_id` but received {container_id!r}")
        return self._post(
            f"/infrastructure/containers/{container_id}/exec",
            body={
                "command": command,
                "workdir": workdir,
                "env": env,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class AsyncContainersResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncContainersResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/hanzoai/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncContainersResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncContainersResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/hanzoai/python-sdk#with_streaming_response
        """
        return AsyncContainersResourceWithStreamingResponse(self)

    async def list(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all containers in the infrastructure."""
        return await self._get(
            "/infrastructure/containers",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def get(
        self,
        container_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Get details of a specific container.

        Args:
          container_id: The unique identifier of the container.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not container_id:
            raise ValueError(f"Expected a non-empty value for `container_id` but received {container_id!r}")
        return await self._get(
            f"/infrastructure/containers/{container_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def create(
        self,
        *,
        name: Optional[str] | NotGiven = NOT_GIVEN,
        image: Optional[str] | NotGiven = NOT_GIVEN,
        command: Optional[List[str]] | NotGiven = NOT_GIVEN,
        env: Optional[dict] | NotGiven = NOT_GIVEN,
        ports: Optional[List[dict]] | NotGiven = NOT_GIVEN,
        volumes: Optional[List[dict]] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Create a new container.

        Args:
          name: The name of the container.

          image: The Docker image to use.

          command: The command to run in the container.

          env: Environment variables for the container.

          ports: Port mappings for the container.

          volumes: Volume mounts for the container.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/infrastructure/containers",
            body={
                "name": name,
                "image": image,
                "command": command,
                "env": env,
                "ports": ports,
                "volumes": volumes,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def update(
        self,
        container_id: str,
        *,
        name: Optional[str] | NotGiven = NOT_GIVEN,
        image: Optional[str] | NotGiven = NOT_GIVEN,
        env: Optional[dict] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Update an existing container.

        Args:
          container_id: The unique identifier of the container.

          name: The new name of the container.

          image: The new Docker image.

          env: Updated environment variables.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not container_id:
            raise ValueError(f"Expected a non-empty value for `container_id` but received {container_id!r}")
        return await self._put(
            f"/infrastructure/containers/{container_id}",
            body={
                "name": name,
                "image": image,
                "env": env,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def delete(
        self,
        container_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Delete a container.

        Args:
          container_id: The unique identifier of the container.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not container_id:
            raise ValueError(f"Expected a non-empty value for `container_id` but received {container_id!r}")
        return await self._delete(
            f"/infrastructure/containers/{container_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def start(
        self,
        container_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Start a stopped container.

        Args:
          container_id: The unique identifier of the container.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not container_id:
            raise ValueError(f"Expected a non-empty value for `container_id` but received {container_id!r}")
        return await self._post(
            f"/infrastructure/containers/{container_id}/start",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def stop(
        self,
        container_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Stop a running container.

        Args:
          container_id: The unique identifier of the container.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not container_id:
            raise ValueError(f"Expected a non-empty value for `container_id` but received {container_id!r}")
        return await self._post(
            f"/infrastructure/containers/{container_id}/stop",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def logs(
        self,
        container_id: str,
        *,
        tail: Optional[int] | NotGiven = NOT_GIVEN,
        follow: Optional[bool] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Get logs from a container.

        Args:
          container_id: The unique identifier of the container.

          tail: Number of lines to return from the end of the logs.

          follow: Whether to stream logs in real-time.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not container_id:
            raise ValueError(f"Expected a non-empty value for `container_id` but received {container_id!r}")
        return await self._get(
            f"/infrastructure/containers/{container_id}/logs",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={
                    "tail": tail,
                    "follow": follow,
                },
            ),
            cast_to=object,
        )

    async def exec(
        self,
        container_id: str,
        *,
        command: List[str],
        workdir: Optional[str] | NotGiven = NOT_GIVEN,
        env: Optional[dict] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """
        Execute a command in a running container.

        Args:
          container_id: The unique identifier of the container.

          command: The command to execute.

          workdir: Working directory for the command.

          env: Environment variables for the command.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not container_id:
            raise ValueError(f"Expected a non-empty value for `container_id` but received {container_id!r}")
        return await self._post(
            f"/infrastructure/containers/{container_id}/exec",
            body={
                "command": command,
                "workdir": workdir,
                "env": env,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class ContainersResourceWithRawResponse:
    def __init__(self, containers: ContainersResource) -> None:
        self._containers = containers

        self.list = to_raw_response_wrapper(
            containers.list,
        )
        self.get = to_raw_response_wrapper(
            containers.get,
        )
        self.create = to_raw_response_wrapper(
            containers.create,
        )
        self.update = to_raw_response_wrapper(
            containers.update,
        )
        self.delete = to_raw_response_wrapper(
            containers.delete,
        )
        self.start = to_raw_response_wrapper(
            containers.start,
        )
        self.stop = to_raw_response_wrapper(
            containers.stop,
        )
        self.logs = to_raw_response_wrapper(
            containers.logs,
        )
        self.exec = to_raw_response_wrapper(
            containers.exec,
        )


class AsyncContainersResourceWithRawResponse:
    def __init__(self, containers: AsyncContainersResource) -> None:
        self._containers = containers

        self.list = async_to_raw_response_wrapper(
            containers.list,
        )
        self.get = async_to_raw_response_wrapper(
            containers.get,
        )
        self.create = async_to_raw_response_wrapper(
            containers.create,
        )
        self.update = async_to_raw_response_wrapper(
            containers.update,
        )
        self.delete = async_to_raw_response_wrapper(
            containers.delete,
        )
        self.start = async_to_raw_response_wrapper(
            containers.start,
        )
        self.stop = async_to_raw_response_wrapper(
            containers.stop,
        )
        self.logs = async_to_raw_response_wrapper(
            containers.logs,
        )
        self.exec = async_to_raw_response_wrapper(
            containers.exec,
        )


class ContainersResourceWithStreamingResponse:
    def __init__(self, containers: ContainersResource) -> None:
        self._containers = containers

        self.list = to_streamed_response_wrapper(
            containers.list,
        )
        self.get = to_streamed_response_wrapper(
            containers.get,
        )
        self.create = to_streamed_response_wrapper(
            containers.create,
        )
        self.update = to_streamed_response_wrapper(
            containers.update,
        )
        self.delete = to_streamed_response_wrapper(
            containers.delete,
        )
        self.start = to_streamed_response_wrapper(
            containers.start,
        )
        self.stop = to_streamed_response_wrapper(
            containers.stop,
        )
        self.logs = to_streamed_response_wrapper(
            containers.logs,
        )
        self.exec = to_streamed_response_wrapper(
            containers.exec,
        )


class AsyncContainersResourceWithStreamingResponse:
    def __init__(self, containers: AsyncContainersResource) -> None:
        self._containers = containers

        self.list = async_to_streamed_response_wrapper(
            containers.list,
        )
        self.get = async_to_streamed_response_wrapper(
            containers.get,
        )
        self.create = async_to_streamed_response_wrapper(
            containers.create,
        )
        self.update = async_to_streamed_response_wrapper(
            containers.update,
        )
        self.delete = async_to_streamed_response_wrapper(
            containers.delete,
        )
        self.start = async_to_streamed_response_wrapper(
            containers.start,
        )
        self.stop = async_to_streamed_response_wrapper(
            containers.stop,
        )
        self.logs = async_to_streamed_response_wrapper(
            containers.logs,
        )
        self.exec = async_to_streamed_response_wrapper(
            containers.exec,
        )
