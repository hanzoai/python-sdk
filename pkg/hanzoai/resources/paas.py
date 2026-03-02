# Hanzo AI SDK — PaaS Resource (platform.hanzo.ai tRPC backend)

from __future__ import annotations

from typing import Any, Dict, List, Optional

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
    """Platform-as-a-Service: orgs, projects, environments, containers, clusters,
    builds, domains, repos, VMs, team, audit. Maps to tRPC routers at
    platform.hanzo.ai/api/trpc."""

    @cached_property
    def with_raw_response(self) -> PaaSResourceWithRawResponse:
        return PaaSResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> PaaSResourceWithStreamingResponse:
        return PaaSResourceWithStreamingResponse(self)

    # ── System ────────────────────────────────────────────────────────

    def health(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Health check."""
        return self._get(
            "/paas/system.health",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    def stats(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Platform statistics."""
        return self._get(
            "/paas/system.stats",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    # ── User ──────────────────────────────────────────────────────────

    def me(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get current user info."""
        return self._get(
            "/paas/user.me",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Organizations ─────────────────────────────────────────────────

    def list_organizations(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List organizations for the current user."""
        return self._get(
            "/paas/organization.list",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    def create_organization(
        self,
        *,
        name: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create an organization."""
        return self._post(
            "/paas/organization.create",
            body={"name": name},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    def retrieve_organization(
        self,
        org_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get an organization by ID."""
        return self._get(
            "/paas/organization.get",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
                query={"orgId": org_id},
            ),
            cast_to=object,
        )

    def update_organization(
        self,
        org_id: str,
        *,
        name: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update an organization."""
        return self._post(
            "/paas/organization.update",
            body={"orgId": org_id, "name": name},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    def delete_organization(
        self,
        org_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete an organization."""
        return self._post(
            "/paas/organization.delete",
            body={"orgId": org_id},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Projects ──────────────────────────────────────────────────────

    def list_projects(
        self,
        org_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List projects in an organization."""
        return self._get(
            "/paas/project.list",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
                query={"orgId": org_id},
            ),
            cast_to=object,
        )

    def create_project(
        self,
        *,
        org_id: str,
        name: str,
        description: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a project."""
        return self._post(
            "/paas/project.create",
            body={"orgId": org_id, "name": name, "description": description},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    def retrieve_project(
        self,
        org_id: str,
        project_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a project."""
        return self._get(
            "/paas/project.get",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
                query={"orgId": org_id, "projectId": project_id},
            ),
            cast_to=object,
        )

    def update_project(
        self,
        org_id: str,
        project_id: str,
        *,
        name: str | NotGiven = NOT_GIVEN,
        description: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update a project."""
        return self._post(
            "/paas/project.update",
            body={
                "orgId": org_id, "projectId": project_id,
                "name": name, "description": description,
            },
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    def delete_project(
        self,
        org_id: str,
        project_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a project."""
        return self._post(
            "/paas/project.delete",
            body={"orgId": org_id, "projectId": project_id},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Environments ──────────────────────────────────────────────────

    def list_environments(
        self,
        org_id: str,
        project_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List environments for a project."""
        return self._get(
            "/paas/environment.list",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
                query={"orgId": org_id, "projectId": project_id},
            ),
            cast_to=object,
        )

    def create_environment(
        self,
        *,
        org_id: str,
        project_id: str,
        name: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create an environment."""
        return self._post(
            "/paas/environment.create",
            body={"orgId": org_id, "projectId": project_id, "name": name},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Containers ────────────────────────────────────────────────────

    def list_containers(
        self,
        org_id: str,
        project_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List containers for a project."""
        return self._get(
            "/paas/container.list",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
                query={"orgId": org_id, "projectId": project_id},
            ),
            cast_to=object,
        )

    def create_container(
        self,
        *,
        org_id: str,
        project_id: str,
        name: str,
        image: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a container."""
        return self._post(
            "/paas/container.create",
            body={
                "orgId": org_id, "projectId": project_id,
                "name": name, "image": image,
            },
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    def retrieve_container(
        self,
        org_id: str,
        project_id: str,
        container_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a container."""
        return self._get(
            "/paas/container.get",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
                query={
                    "orgId": org_id, "projectId": project_id,
                    "containerId": container_id,
                },
            ),
            cast_to=object,
        )

    def update_container(
        self,
        org_id: str,
        project_id: str,
        container_id: str,
        *,
        image: str | NotGiven = NOT_GIVEN,
        name: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update a container."""
        return self._post(
            "/paas/container.update",
            body={
                "orgId": org_id, "projectId": project_id,
                "containerId": container_id,
                "image": image, "name": name,
            },
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    def delete_container(
        self,
        org_id: str,
        project_id: str,
        container_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a container."""
        return self._post(
            "/paas/container.delete",
            body={
                "orgId": org_id, "projectId": project_id,
                "containerId": container_id,
            },
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    def redeploy_container(
        self,
        org_id: str,
        project_id: str,
        container_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Redeploy a container."""
        return self._post(
            "/paas/container.redeploy",
            body={
                "orgId": org_id, "projectId": project_id,
                "containerId": container_id,
            },
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    def container_logs(
        self,
        org_id: str,
        project_id: str,
        container_id: str,
        *,
        lines: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get container logs."""
        return self._get(
            "/paas/container.logs",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
                query={
                    "orgId": org_id, "projectId": project_id,
                    "containerId": container_id, "lines": lines,
                },
            ),
            cast_to=object,
        )

    # ── Clusters ──────────────────────────────────────────────────────

    def list_clusters(
        self,
        org_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List clusters for an organization."""
        return self._get(
            "/paas/cluster.list",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
                query={"orgId": org_id},
            ),
            cast_to=object,
        )

    def create_cluster(
        self,
        *,
        org_id: str,
        name: str,
        provider: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a cluster."""
        return self._post(
            "/paas/cluster.create",
            body={"orgId": org_id, "name": name, "provider": provider},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    def retrieve_cluster(
        self,
        org_id: str,
        cluster_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a cluster."""
        return self._get(
            "/paas/cluster.get",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
                query={"orgId": org_id, "clusterId": cluster_id},
            ),
            cast_to=object,
        )

    # ── Builds ────────────────────────────────────────────────────────

    def list_builds(
        self,
        org_id: str,
        project_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List builds for a project."""
        return self._get(
            "/paas/build.list",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
                query={"orgId": org_id, "projectId": project_id},
            ),
            cast_to=object,
        )

    def trigger_build(
        self,
        *,
        org_id: str,
        project_id: str,
        container_id: str,
        ref: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Trigger a build."""
        return self._post(
            "/paas/build.trigger",
            body={
                "orgId": org_id, "projectId": project_id,
                "containerId": container_id, "ref": ref,
            },
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    def retrieve_build(
        self,
        org_id: str,
        project_id: str,
        build_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get build status."""
        return self._get(
            "/paas/build.get",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
                query={
                    "orgId": org_id, "projectId": project_id,
                    "buildId": build_id,
                },
            ),
            cast_to=object,
        )

    def build_logs(
        self,
        org_id: str,
        project_id: str,
        build_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get build logs."""
        return self._get(
            "/paas/build.logs",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
                query={
                    "orgId": org_id, "projectId": project_id,
                    "buildId": build_id,
                },
            ),
            cast_to=object,
        )

    def cancel_build(
        self,
        org_id: str,
        project_id: str,
        build_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Cancel a build."""
        return self._post(
            "/paas/build.cancel",
            body={
                "orgId": org_id, "projectId": project_id,
                "buildId": build_id,
            },
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Domains ───────────────────────────────────────────────────────

    def list_domains(
        self,
        org_id: str,
        project_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List domains for a project."""
        return self._get(
            "/paas/domain.list",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
                query={"orgId": org_id, "projectId": project_id},
            ),
            cast_to=object,
        )

    def add_domain(
        self,
        *,
        org_id: str,
        project_id: str,
        domain: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Add a domain to a project."""
        return self._post(
            "/paas/domain.add",
            body={"orgId": org_id, "projectId": project_id, "domain": domain},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    def remove_domain(
        self,
        *,
        org_id: str,
        project_id: str,
        domain: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Remove a domain from a project."""
        return self._post(
            "/paas/domain.remove",
            body={"orgId": org_id, "projectId": project_id, "domain": domain},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    def verify_domain(
        self,
        *,
        org_id: str,
        project_id: str,
        domain: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Verify a domain."""
        return self._post(
            "/paas/domain.verify",
            body={"orgId": org_id, "projectId": project_id, "domain": domain},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Repositories ──────────────────────────────────────────────────

    def list_repositories(
        self,
        org_id: str,
        *,
        search: str | NotGiven = NOT_GIVEN,
        limit: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List repositories."""
        return self._get(
            "/paas/repository.list",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
                query={"orgId": org_id, "search": search, "limit": limit},
            ),
            cast_to=object,
        )

    # ── Team ──────────────────────────────────────────────────────────

    def list_team(
        self,
        org_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List team members for an organization."""
        return self._get(
            "/paas/orgTeam.list",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
                query={"orgId": org_id},
            ),
            cast_to=object,
        )

    def invite_member(
        self,
        *,
        org_id: str,
        email: str,
        role: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Invite a team member."""
        return self._post(
            "/paas/orgTeam.invite",
            body={"orgId": org_id, "email": email, "role": role},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    def remove_member(
        self,
        *,
        org_id: str,
        user_id: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Remove a team member."""
        return self._post(
            "/paas/orgTeam.remove",
            body={"orgId": org_id, "userId": user_id},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Audit ─────────────────────────────────────────────────────────

    def list_audit_events(
        self,
        org_id: str,
        *,
        limit: int | NotGiven = NOT_GIVEN,
        offset: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List audit events for an organization."""
        return self._get(
            "/paas/audit.list",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
                query={"orgId": org_id, "limit": limit, "offset": offset},
            ),
            cast_to=object,
        )

    # ── VMs ───────────────────────────────────────────────────────────

    def list_vms(
        self,
        org_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List VMs for an organization."""
        return self._get(
            "/paas/vm.list",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
                query={"orgId": org_id},
            ),
            cast_to=object,
        )

    def create_vm(
        self,
        *,
        org_id: str,
        name: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a VM."""
        return self._post(
            "/paas/vm.create",
            body={"orgId": org_id, "name": name},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    def retrieve_vm(
        self,
        org_id: str,
        vm_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a VM."""
        return self._get(
            "/paas/vm.get",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
                query={"orgId": org_id, "vmId": vm_id},
            ),
            cast_to=object,
        )

    def delete_vm(
        self,
        org_id: str,
        vm_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a VM."""
        return self._post(
            "/paas/vm.delete",
            body={"orgId": org_id, "vmId": vm_id},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )


# ══════════════════════════════════════════════════════════════════════
#  Async mirror
# ══════════════════════════════════════════════════════════════════════


class AsyncPaaSResource(AsyncAPIResource):
    """Platform-as-a-Service (async). Maps to tRPC routers at
    platform.hanzo.ai/api/trpc."""

    @cached_property
    def with_raw_response(self) -> AsyncPaaSResourceWithRawResponse:
        return AsyncPaaSResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncPaaSResourceWithStreamingResponse:
        return AsyncPaaSResourceWithStreamingResponse(self)

    # ── System ────────────────────────────────────────────────────────

    async def health(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Health check."""
        return await self._get(
            "/paas/system.health",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    async def stats(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Platform statistics."""
        return await self._get(
            "/paas/system.stats",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    # ── User ──────────────────────────────────────────────────────────

    async def me(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get current user info."""
        return await self._get(
            "/paas/user.me",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Organizations ─────────────────────────────────────────────────

    async def list_organizations(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List organizations for the current user."""
        return await self._get(
            "/paas/organization.list",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    async def create_organization(
        self,
        *,
        name: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create an organization."""
        return await self._post(
            "/paas/organization.create",
            body={"name": name},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    async def retrieve_organization(
        self,
        org_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get an organization by ID."""
        return await self._get(
            "/paas/organization.get",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
                query={"orgId": org_id},
            ),
            cast_to=object,
        )

    async def update_organization(
        self,
        org_id: str,
        *,
        name: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update an organization."""
        return await self._post(
            "/paas/organization.update",
            body={"orgId": org_id, "name": name},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    async def delete_organization(
        self,
        org_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete an organization."""
        return await self._post(
            "/paas/organization.delete",
            body={"orgId": org_id},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Projects ──────────────────────────────────────────────────────

    async def list_projects(
        self,
        org_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List projects in an organization."""
        return await self._get(
            "/paas/project.list",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
                query={"orgId": org_id},
            ),
            cast_to=object,
        )

    async def create_project(
        self,
        *,
        org_id: str,
        name: str,
        description: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a project."""
        return await self._post(
            "/paas/project.create",
            body={"orgId": org_id, "name": name, "description": description},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    async def retrieve_project(
        self,
        org_id: str,
        project_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a project."""
        return await self._get(
            "/paas/project.get",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
                query={"orgId": org_id, "projectId": project_id},
            ),
            cast_to=object,
        )

    async def update_project(
        self,
        org_id: str,
        project_id: str,
        *,
        name: str | NotGiven = NOT_GIVEN,
        description: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update a project."""
        return await self._post(
            "/paas/project.update",
            body={
                "orgId": org_id, "projectId": project_id,
                "name": name, "description": description,
            },
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    async def delete_project(
        self,
        org_id: str,
        project_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a project."""
        return await self._post(
            "/paas/project.delete",
            body={"orgId": org_id, "projectId": project_id},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Environments ──────────────────────────────────────────────────

    async def list_environments(
        self,
        org_id: str,
        project_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List environments for a project."""
        return await self._get(
            "/paas/environment.list",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
                query={"orgId": org_id, "projectId": project_id},
            ),
            cast_to=object,
        )

    async def create_environment(
        self,
        *,
        org_id: str,
        project_id: str,
        name: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create an environment."""
        return await self._post(
            "/paas/environment.create",
            body={"orgId": org_id, "projectId": project_id, "name": name},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Containers ────────────────────────────────────────────────────

    async def list_containers(
        self,
        org_id: str,
        project_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List containers for a project."""
        return await self._get(
            "/paas/container.list",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
                query={"orgId": org_id, "projectId": project_id},
            ),
            cast_to=object,
        )

    async def create_container(
        self,
        *,
        org_id: str,
        project_id: str,
        name: str,
        image: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a container."""
        return await self._post(
            "/paas/container.create",
            body={
                "orgId": org_id, "projectId": project_id,
                "name": name, "image": image,
            },
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    async def retrieve_container(
        self,
        org_id: str,
        project_id: str,
        container_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a container."""
        return await self._get(
            "/paas/container.get",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
                query={
                    "orgId": org_id, "projectId": project_id,
                    "containerId": container_id,
                },
            ),
            cast_to=object,
        )

    async def update_container(
        self,
        org_id: str,
        project_id: str,
        container_id: str,
        *,
        image: str | NotGiven = NOT_GIVEN,
        name: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update a container."""
        return await self._post(
            "/paas/container.update",
            body={
                "orgId": org_id, "projectId": project_id,
                "containerId": container_id,
                "image": image, "name": name,
            },
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    async def delete_container(
        self,
        org_id: str,
        project_id: str,
        container_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a container."""
        return await self._post(
            "/paas/container.delete",
            body={
                "orgId": org_id, "projectId": project_id,
                "containerId": container_id,
            },
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    async def redeploy_container(
        self,
        org_id: str,
        project_id: str,
        container_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Redeploy a container."""
        return await self._post(
            "/paas/container.redeploy",
            body={
                "orgId": org_id, "projectId": project_id,
                "containerId": container_id,
            },
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    async def container_logs(
        self,
        org_id: str,
        project_id: str,
        container_id: str,
        *,
        lines: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get container logs."""
        return await self._get(
            "/paas/container.logs",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
                query={
                    "orgId": org_id, "projectId": project_id,
                    "containerId": container_id, "lines": lines,
                },
            ),
            cast_to=object,
        )

    # ── Clusters ──────────────────────────────────────────────────────

    async def list_clusters(
        self,
        org_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List clusters for an organization."""
        return await self._get(
            "/paas/cluster.list",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
                query={"orgId": org_id},
            ),
            cast_to=object,
        )

    async def create_cluster(
        self,
        *,
        org_id: str,
        name: str,
        provider: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a cluster."""
        return await self._post(
            "/paas/cluster.create",
            body={"orgId": org_id, "name": name, "provider": provider},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    async def retrieve_cluster(
        self,
        org_id: str,
        cluster_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a cluster."""
        return await self._get(
            "/paas/cluster.get",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
                query={"orgId": org_id, "clusterId": cluster_id},
            ),
            cast_to=object,
        )

    # ── Builds ────────────────────────────────────────────────────────

    async def list_builds(
        self,
        org_id: str,
        project_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List builds for a project."""
        return await self._get(
            "/paas/build.list",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
                query={"orgId": org_id, "projectId": project_id},
            ),
            cast_to=object,
        )

    async def trigger_build(
        self,
        *,
        org_id: str,
        project_id: str,
        container_id: str,
        ref: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Trigger a build."""
        return await self._post(
            "/paas/build.trigger",
            body={
                "orgId": org_id, "projectId": project_id,
                "containerId": container_id, "ref": ref,
            },
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    async def retrieve_build(
        self,
        org_id: str,
        project_id: str,
        build_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get build status."""
        return await self._get(
            "/paas/build.get",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
                query={
                    "orgId": org_id, "projectId": project_id,
                    "buildId": build_id,
                },
            ),
            cast_to=object,
        )

    async def build_logs(
        self,
        org_id: str,
        project_id: str,
        build_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get build logs."""
        return await self._get(
            "/paas/build.logs",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
                query={
                    "orgId": org_id, "projectId": project_id,
                    "buildId": build_id,
                },
            ),
            cast_to=object,
        )

    async def cancel_build(
        self,
        org_id: str,
        project_id: str,
        build_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Cancel a build."""
        return await self._post(
            "/paas/build.cancel",
            body={
                "orgId": org_id, "projectId": project_id,
                "buildId": build_id,
            },
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Domains ───────────────────────────────────────────────────────

    async def list_domains(
        self,
        org_id: str,
        project_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List domains for a project."""
        return await self._get(
            "/paas/domain.list",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
                query={"orgId": org_id, "projectId": project_id},
            ),
            cast_to=object,
        )

    async def add_domain(
        self,
        *,
        org_id: str,
        project_id: str,
        domain: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Add a domain to a project."""
        return await self._post(
            "/paas/domain.add",
            body={"orgId": org_id, "projectId": project_id, "domain": domain},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    async def remove_domain(
        self,
        *,
        org_id: str,
        project_id: str,
        domain: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Remove a domain from a project."""
        return await self._post(
            "/paas/domain.remove",
            body={"orgId": org_id, "projectId": project_id, "domain": domain},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    async def verify_domain(
        self,
        *,
        org_id: str,
        project_id: str,
        domain: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Verify a domain."""
        return await self._post(
            "/paas/domain.verify",
            body={"orgId": org_id, "projectId": project_id, "domain": domain},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Repositories ──────────────────────────────────────────────────

    async def list_repositories(
        self,
        org_id: str,
        *,
        search: str | NotGiven = NOT_GIVEN,
        limit: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List repositories."""
        return await self._get(
            "/paas/repository.list",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
                query={"orgId": org_id, "search": search, "limit": limit},
            ),
            cast_to=object,
        )

    # ── Team ──────────────────────────────────────────────────────────

    async def list_team(
        self,
        org_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List team members for an organization."""
        return await self._get(
            "/paas/orgTeam.list",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
                query={"orgId": org_id},
            ),
            cast_to=object,
        )

    async def invite_member(
        self,
        *,
        org_id: str,
        email: str,
        role: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Invite a team member."""
        return await self._post(
            "/paas/orgTeam.invite",
            body={"orgId": org_id, "email": email, "role": role},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    async def remove_member(
        self,
        *,
        org_id: str,
        user_id: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Remove a team member."""
        return await self._post(
            "/paas/orgTeam.remove",
            body={"orgId": org_id, "userId": user_id},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Audit ─────────────────────────────────────────────────────────

    async def list_audit_events(
        self,
        org_id: str,
        *,
        limit: int | NotGiven = NOT_GIVEN,
        offset: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List audit events for an organization."""
        return await self._get(
            "/paas/audit.list",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
                query={"orgId": org_id, "limit": limit, "offset": offset},
            ),
            cast_to=object,
        )

    # ── VMs ───────────────────────────────────────────────────────────

    async def list_vms(
        self,
        org_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List VMs for an organization."""
        return await self._get(
            "/paas/vm.list",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
                query={"orgId": org_id},
            ),
            cast_to=object,
        )

    async def create_vm(
        self,
        *,
        org_id: str,
        name: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a VM."""
        return await self._post(
            "/paas/vm.create",
            body={"orgId": org_id, "name": name},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )

    async def retrieve_vm(
        self,
        org_id: str,
        vm_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a VM."""
        return await self._get(
            "/paas/vm.get",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
                query={"orgId": org_id, "vmId": vm_id},
            ),
            cast_to=object,
        )

    async def delete_vm(
        self,
        org_id: str,
        vm_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a VM."""
        return await self._post(
            "/paas/vm.delete",
            body={"orgId": org_id, "vmId": vm_id},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query,
                extra_body=extra_body, timeout=timeout,
            ),
            cast_to=object,
        )


# ══════════════════════════════════════════════════════════════════════
#  Raw response wrappers
# ══════════════════════════════════════════════════════════════════════

# All method names that exist on both sync and async resources.
_METHOD_NAMES = [
    "health", "stats", "me",
    # orgs
    "list_organizations", "create_organization", "retrieve_organization",
    "update_organization", "delete_organization",
    # projects
    "list_projects", "create_project", "retrieve_project",
    "update_project", "delete_project",
    # environments
    "list_environments", "create_environment",
    # containers
    "list_containers", "create_container", "retrieve_container",
    "update_container", "delete_container", "redeploy_container",
    "container_logs",
    # clusters
    "list_clusters", "create_cluster", "retrieve_cluster",
    # builds
    "list_builds", "trigger_build", "retrieve_build",
    "build_logs", "cancel_build",
    # domains
    "list_domains", "add_domain", "remove_domain", "verify_domain",
    # repos
    "list_repositories",
    # team
    "list_team", "invite_member", "remove_member",
    # audit
    "list_audit_events",
    # vms
    "list_vms", "create_vm", "retrieve_vm", "delete_vm",
]


class PaaSResourceWithRawResponse:
    def __init__(self, paas: PaaSResource) -> None:
        self._paas = paas
        for name in _METHOD_NAMES:
            setattr(self, name, to_raw_response_wrapper(getattr(paas, name)))


class AsyncPaaSResourceWithRawResponse:
    def __init__(self, paas: AsyncPaaSResource) -> None:
        self._paas = paas
        for name in _METHOD_NAMES:
            setattr(self, name, async_to_raw_response_wrapper(getattr(paas, name)))


class PaaSResourceWithStreamingResponse:
    def __init__(self, paas: PaaSResource) -> None:
        self._paas = paas
        for name in _METHOD_NAMES:
            setattr(self, name, to_streamed_response_wrapper(getattr(paas, name)))


class AsyncPaaSResourceWithStreamingResponse:
    def __init__(self, paas: AsyncPaaSResource) -> None:
        self._paas = paas
        for name in _METHOD_NAMES:
            setattr(self, name, async_to_streamed_response_wrapper(getattr(paas, name)))
