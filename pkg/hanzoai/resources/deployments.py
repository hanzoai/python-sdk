# Hanzo AI SDK

from __future__ import annotations

from typing import Any, Dict

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

__all__ = ["DeploymentsResource", "AsyncDeploymentsResource"]


class DeploymentsResource(SyncAPIResource):
    """Kubernetes deployment management."""

    @cached_property
    def with_raw_response(self) -> DeploymentsResourceWithRawResponse:
        return DeploymentsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> DeploymentsResourceWithStreamingResponse:
        return DeploymentsResourceWithStreamingResponse(self)

    def list(
        self,
        *,
        namespace: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all deployments."""
        return self._get(
            "/infrastructure/deployments",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"namespace": namespace},
            ),
            cast_to=object,
        )

    def get(
        self,
        deployment_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a specific deployment."""
        return self._get(
            f"/infrastructure/deployments/{deployment_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def create(
        self,
        *,
        name: str,
        namespace: str,
        image: str,
        replicas: int = 1,
        env: Dict[str, str] | NotGiven = NOT_GIVEN,
        resources: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a new deployment."""
        return self._post(
            "/infrastructure/deployments",
            body={
                "name": name,
                "namespace": namespace,
                "image": image,
                "replicas": replicas,
                "env": env,
                "resources": resources,
            },
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def update(
        self,
        deployment_id: str,
        *,
        image: str | NotGiven = NOT_GIVEN,
        replicas: int | NotGiven = NOT_GIVEN,
        env: Dict[str, str] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update a deployment."""
        return self._put(
            f"/infrastructure/deployments/{deployment_id}",
            body={"image": image, "replicas": replicas, "env": env},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def delete(
        self,
        deployment_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a deployment."""
        return self._delete(
            f"/infrastructure/deployments/{deployment_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def scale(
        self,
        deployment_id: str,
        *,
        replicas: int,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Scale a deployment."""
        return self._post(
            f"/infrastructure/deployments/{deployment_id}/scale",
            body={"replicas": replicas},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def restart(
        self,
        deployment_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Restart a deployment."""
        return self._post(
            f"/infrastructure/deployments/{deployment_id}/restart",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def rollback(
        self,
        deployment_id: str,
        *,
        revision: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Rollback a deployment."""
        return self._post(
            f"/infrastructure/deployments/{deployment_id}/rollback",
            body={"revision": revision},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def status(
        self,
        deployment_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get deployment status."""
        return self._get(
            f"/infrastructure/deployments/{deployment_id}/status",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class AsyncDeploymentsResource(AsyncAPIResource):
    """Kubernetes deployment management (async)."""

    @cached_property
    def with_raw_response(self) -> AsyncDeploymentsResourceWithRawResponse:
        return AsyncDeploymentsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncDeploymentsResourceWithStreamingResponse:
        return AsyncDeploymentsResourceWithStreamingResponse(self)

    async def list(
        self,
        *,
        namespace: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            "/infrastructure/deployments",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"namespace": namespace},
            ),
            cast_to=object,
        )

    async def get(
        self,
        deployment_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/infrastructure/deployments/{deployment_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def create(
        self,
        *,
        name: str,
        namespace: str,
        image: str,
        replicas: int = 1,
        env: Dict[str, str] | NotGiven = NOT_GIVEN,
        resources: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            "/infrastructure/deployments",
            body={
                "name": name,
                "namespace": namespace,
                "image": image,
                "replicas": replicas,
                "env": env,
                "resources": resources,
            },
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def update(
        self,
        deployment_id: str,
        *,
        image: str | NotGiven = NOT_GIVEN,
        replicas: int | NotGiven = NOT_GIVEN,
        env: Dict[str, str] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._put(
            f"/infrastructure/deployments/{deployment_id}",
            body={"image": image, "replicas": replicas, "env": env},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def delete(
        self,
        deployment_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._delete(
            f"/infrastructure/deployments/{deployment_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def scale(
        self,
        deployment_id: str,
        *,
        replicas: int,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            f"/infrastructure/deployments/{deployment_id}/scale",
            body={"replicas": replicas},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def restart(
        self,
        deployment_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            f"/infrastructure/deployments/{deployment_id}/restart",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def rollback(
        self,
        deployment_id: str,
        *,
        revision: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            f"/infrastructure/deployments/{deployment_id}/rollback",
            body={"revision": revision},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def status(
        self,
        deployment_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/infrastructure/deployments/{deployment_id}/status",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class DeploymentsResourceWithRawResponse:
    def __init__(self, deployments: DeploymentsResource) -> None:
        self._deployments = deployments
        self.list = to_raw_response_wrapper(deployments.list)
        self.get = to_raw_response_wrapper(deployments.get)
        self.create = to_raw_response_wrapper(deployments.create)
        self.update = to_raw_response_wrapper(deployments.update)
        self.delete = to_raw_response_wrapper(deployments.delete)
        self.scale = to_raw_response_wrapper(deployments.scale)
        self.restart = to_raw_response_wrapper(deployments.restart)
        self.rollback = to_raw_response_wrapper(deployments.rollback)
        self.status = to_raw_response_wrapper(deployments.status)


class AsyncDeploymentsResourceWithRawResponse:
    def __init__(self, deployments: AsyncDeploymentsResource) -> None:
        self._deployments = deployments
        self.list = async_to_raw_response_wrapper(deployments.list)
        self.get = async_to_raw_response_wrapper(deployments.get)
        self.create = async_to_raw_response_wrapper(deployments.create)
        self.update = async_to_raw_response_wrapper(deployments.update)
        self.delete = async_to_raw_response_wrapper(deployments.delete)
        self.scale = async_to_raw_response_wrapper(deployments.scale)
        self.restart = async_to_raw_response_wrapper(deployments.restart)
        self.rollback = async_to_raw_response_wrapper(deployments.rollback)
        self.status = async_to_raw_response_wrapper(deployments.status)


class DeploymentsResourceWithStreamingResponse:
    def __init__(self, deployments: DeploymentsResource) -> None:
        self._deployments = deployments
        self.list = to_streamed_response_wrapper(deployments.list)
        self.get = to_streamed_response_wrapper(deployments.get)
        self.create = to_streamed_response_wrapper(deployments.create)
        self.update = to_streamed_response_wrapper(deployments.update)
        self.delete = to_streamed_response_wrapper(deployments.delete)
        self.scale = to_streamed_response_wrapper(deployments.scale)
        self.restart = to_streamed_response_wrapper(deployments.restart)
        self.rollback = to_streamed_response_wrapper(deployments.rollback)
        self.status = to_streamed_response_wrapper(deployments.status)


class AsyncDeploymentsResourceWithStreamingResponse:
    def __init__(self, deployments: AsyncDeploymentsResource) -> None:
        self._deployments = deployments
        self.list = async_to_streamed_response_wrapper(deployments.list)
        self.get = async_to_streamed_response_wrapper(deployments.get)
        self.create = async_to_streamed_response_wrapper(deployments.create)
        self.update = async_to_streamed_response_wrapper(deployments.update)
        self.delete = async_to_streamed_response_wrapper(deployments.delete)
        self.scale = async_to_streamed_response_wrapper(deployments.scale)
        self.restart = async_to_streamed_response_wrapper(deployments.restart)
        self.rollback = async_to_streamed_response_wrapper(deployments.rollback)
        self.status = async_to_streamed_response_wrapper(deployments.status)
