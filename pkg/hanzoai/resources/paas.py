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

__all__ = ["PaaSResource", "AsyncPaaSResource"]


class PaaSResource(SyncAPIResource):
    """Platform-as-a-Service: projects, environments, containers, repos, builds."""

    @cached_property
    def with_raw_response(self) -> PaaSResourceWithRawResponse:
        return PaaSResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> PaaSResourceWithStreamingResponse:
        return PaaSResourceWithStreamingResponse(self)

    # Projects
    def list_projects(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List projects."""
        return self._get(
            "/paas/projects",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def create_project(
        self,
        *,
        name: str,
        description: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a project."""
        return self._post(
            "/paas/projects",
            body={"name": name, "description": description},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def retrieve_project(
        self,
        project_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a project."""
        return self._get(
            f"/paas/projects/{project_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def delete_project(
        self,
        project_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a project."""
        return self._delete(
            f"/paas/projects/{project_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # Environments
    def list_environments(
        self,
        project_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List environments for a project."""
        return self._get(
            f"/paas/projects/{project_id}/environments",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # Containers
    def list_containers(
        self,
        project_id: str,
        *,
        environment: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List containers for a project."""
        return self._get(
            f"/paas/projects/{project_id}/containers",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"environment": environment},
            ),
            cast_to=object,
        )

    # Builds
    def list_builds(
        self,
        project_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List builds for a project."""
        return self._get(
            f"/paas/projects/{project_id}/builds",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def trigger_build(
        self,
        project_id: str,
        *,
        ref: str | NotGiven = NOT_GIVEN,
        environment: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Trigger a build for a project."""
        return self._post(
            f"/paas/projects/{project_id}/builds",
            body={"ref": ref, "environment": environment},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # Deploy
    def deploy(
        self,
        project_id: str,
        *,
        environment: str,
        image: str | NotGiven = NOT_GIVEN,
        build_id: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Deploy a project to an environment."""
        return self._post(
            f"/paas/projects/{project_id}/deploy",
            body={"environment": environment, "image": image, "build_id": build_id},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class AsyncPaaSResource(AsyncAPIResource):
    """Platform-as-a-Service: projects, environments, containers, repos, builds (async)."""

    @cached_property
    def with_raw_response(self) -> AsyncPaaSResourceWithRawResponse:
        return AsyncPaaSResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncPaaSResourceWithStreamingResponse:
        return AsyncPaaSResourceWithStreamingResponse(self)

    async def list_projects(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List projects."""
        return await self._get(
            "/paas/projects",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def create_project(
        self,
        *,
        name: str,
        description: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a project."""
        return await self._post(
            "/paas/projects",
            body={"name": name, "description": description},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def retrieve_project(
        self,
        project_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a project."""
        return await self._get(
            f"/paas/projects/{project_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def delete_project(
        self,
        project_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a project."""
        return await self._delete(
            f"/paas/projects/{project_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def list_environments(
        self,
        project_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List environments for a project."""
        return await self._get(
            f"/paas/projects/{project_id}/environments",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def list_containers(
        self,
        project_id: str,
        *,
        environment: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List containers for a project."""
        return await self._get(
            f"/paas/projects/{project_id}/containers",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"environment": environment},
            ),
            cast_to=object,
        )

    async def list_builds(
        self,
        project_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List builds for a project."""
        return await self._get(
            f"/paas/projects/{project_id}/builds",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def trigger_build(
        self,
        project_id: str,
        *,
        ref: str | NotGiven = NOT_GIVEN,
        environment: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Trigger a build for a project."""
        return await self._post(
            f"/paas/projects/{project_id}/builds",
            body={"ref": ref, "environment": environment},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def deploy(
        self,
        project_id: str,
        *,
        environment: str,
        image: str | NotGiven = NOT_GIVEN,
        build_id: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Deploy a project to an environment."""
        return await self._post(
            f"/paas/projects/{project_id}/deploy",
            body={"environment": environment, "image": image, "build_id": build_id},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class PaaSResourceWithRawResponse:
    def __init__(self, paas: PaaSResource) -> None:
        self._paas = paas
        self.list_projects = to_raw_response_wrapper(paas.list_projects)
        self.create_project = to_raw_response_wrapper(paas.create_project)
        self.retrieve_project = to_raw_response_wrapper(paas.retrieve_project)
        self.delete_project = to_raw_response_wrapper(paas.delete_project)
        self.list_environments = to_raw_response_wrapper(paas.list_environments)
        self.list_containers = to_raw_response_wrapper(paas.list_containers)
        self.list_builds = to_raw_response_wrapper(paas.list_builds)
        self.trigger_build = to_raw_response_wrapper(paas.trigger_build)
        self.deploy = to_raw_response_wrapper(paas.deploy)


class AsyncPaaSResourceWithRawResponse:
    def __init__(self, paas: AsyncPaaSResource) -> None:
        self._paas = paas
        self.list_projects = async_to_raw_response_wrapper(paas.list_projects)
        self.create_project = async_to_raw_response_wrapper(paas.create_project)
        self.retrieve_project = async_to_raw_response_wrapper(paas.retrieve_project)
        self.delete_project = async_to_raw_response_wrapper(paas.delete_project)
        self.list_environments = async_to_raw_response_wrapper(paas.list_environments)
        self.list_containers = async_to_raw_response_wrapper(paas.list_containers)
        self.list_builds = async_to_raw_response_wrapper(paas.list_builds)
        self.trigger_build = async_to_raw_response_wrapper(paas.trigger_build)
        self.deploy = async_to_raw_response_wrapper(paas.deploy)


class PaaSResourceWithStreamingResponse:
    def __init__(self, paas: PaaSResource) -> None:
        self._paas = paas
        self.list_projects = to_streamed_response_wrapper(paas.list_projects)
        self.create_project = to_streamed_response_wrapper(paas.create_project)
        self.retrieve_project = to_streamed_response_wrapper(paas.retrieve_project)
        self.delete_project = to_streamed_response_wrapper(paas.delete_project)
        self.list_environments = to_streamed_response_wrapper(paas.list_environments)
        self.list_containers = to_streamed_response_wrapper(paas.list_containers)
        self.list_builds = to_streamed_response_wrapper(paas.list_builds)
        self.trigger_build = to_streamed_response_wrapper(paas.trigger_build)
        self.deploy = to_streamed_response_wrapper(paas.deploy)


class AsyncPaaSResourceWithStreamingResponse:
    def __init__(self, paas: AsyncPaaSResource) -> None:
        self._paas = paas
        self.list_projects = async_to_streamed_response_wrapper(paas.list_projects)
        self.create_project = async_to_streamed_response_wrapper(paas.create_project)
        self.retrieve_project = async_to_streamed_response_wrapper(paas.retrieve_project)
        self.delete_project = async_to_streamed_response_wrapper(paas.delete_project)
        self.list_environments = async_to_streamed_response_wrapper(paas.list_environments)
        self.list_containers = async_to_streamed_response_wrapper(paas.list_containers)
        self.list_builds = async_to_streamed_response_wrapper(paas.list_builds)
        self.trigger_build = async_to_streamed_response_wrapper(paas.trigger_build)
        self.deploy = async_to_streamed_response_wrapper(paas.deploy)
