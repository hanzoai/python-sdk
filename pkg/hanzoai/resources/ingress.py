# Hanzo AI SDK

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

__all__ = ["IngressResource", "AsyncIngressResource"]


class IngressResource(SyncAPIResource):
    """Ingress resource — Traefik reverse proxy inspection + PaaS domain management."""

    @cached_property
    def with_raw_response(self) -> IngressResourceWithRawResponse:
        return IngressResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> IngressResourceWithStreamingResponse:
        return IngressResourceWithStreamingResponse(self)

    # ──────────────────────────────────────────────
    # Traefik API — HTTP routers
    # ──────────────────────────────────────────────

    def list_routers(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all HTTP routers (Traefik ingress rules)."""
        return self._get(
            "/ingress/routers",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def retrieve_router(
        self,
        name: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a specific HTTP router by name (e.g. 'my-router@docker')."""
        return self._get(
            f"/ingress/routers/{name}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ──────────────────────────────────────────────
    # Traefik API — HTTP services
    # ──────────────────────────────────────────────

    def list_services(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all backend services registered in Traefik."""
        return self._get(
            "/ingress/services",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def retrieve_service(
        self,
        name: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a specific backend service by name (e.g. 'my-svc@docker')."""
        return self._get(
            f"/ingress/services/{name}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ──────────────────────────────────────────────
    # Traefik API — middlewares
    # ──────────────────────────────────────────────

    def list_middlewares(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all middlewares (rate limiting, auth, headers, etc.)."""
        return self._get(
            "/ingress/middlewares",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def retrieve_middleware(
        self,
        name: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a specific middleware by name (e.g. 'rate-limit@docker')."""
        return self._get(
            f"/ingress/middlewares/{name}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ──────────────────────────────────────────────
    # Traefik API — entrypoints & overview
    # ──────────────────────────────────────────────

    def list_entrypoints(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all entrypoints (ports/protocols Traefik listens on)."""
        return self._get(
            "/ingress/entrypoints",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def overview(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get Traefik dashboard overview stats (router/service/middleware counts)."""
        return self._get(
            "/ingress/overview",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ──────────────────────────────────────────────
    # Traefik API — TCP routers & services
    # ──────────────────────────────────────────────

    def list_tcp_routers(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all TCP routers."""
        return self._get(
            "/ingress/tcp/routers",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def list_tcp_services(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all TCP services."""
        return self._get(
            "/ingress/tcp/services",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ──────────────────────────────────────────────
    # PaaS Domain Management (tRPC proxy)
    # ──────────────────────────────────────────────

    def list_domains(
        self,
        *,
        project_id: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List custom domains for a project."""
        return self._get(
            "/ingress/domains",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"project_id": project_id},
            ),
            cast_to=object,
        )

    def add_domain(
        self,
        *,
        project_id: str,
        domain: str,
        certificate_id: str | NotGiven = NOT_GIVEN,
        force_ssl: bool | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Add a custom domain to a project (creates DNS + TLS cert)."""
        return self._post(
            "/ingress/domains",
            body={
                "project_id": project_id,
                "domain": domain,
                "certificate_id": certificate_id,
                "force_ssl": force_ssl,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def remove_domain(
        self,
        domain: str,
        *,
        project_id: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Remove a custom domain from a project."""
        return self._delete(
            f"/ingress/domains/{domain}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"project_id": project_id},
            ),
            cast_to=object,
        )

    def verify_domain(
        self,
        domain: str,
        *,
        project_id: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Verify domain DNS configuration."""
        return self._post(
            f"/ingress/domains/{domain}/verify",
            body={"project_id": project_id},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def tls_status(
        self,
        domain: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get TLS certificate status for a domain."""
        return self._get(
            f"/ingress/domains/{domain}/tls",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class AsyncIngressResource(AsyncAPIResource):
    """Ingress resource — Traefik reverse proxy inspection + PaaS domain management (async)."""

    @cached_property
    def with_raw_response(self) -> AsyncIngressResourceWithRawResponse:
        return AsyncIngressResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncIngressResourceWithStreamingResponse:
        return AsyncIngressResourceWithStreamingResponse(self)

    # ──────────────────────────────────────────────
    # Traefik API — HTTP routers
    # ──────────────────────────────────────────────

    async def list_routers(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all HTTP routers (Traefik ingress rules)."""
        return await self._get(
            "/ingress/routers",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def retrieve_router(
        self,
        name: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a specific HTTP router by name (e.g. 'my-router@docker')."""
        return await self._get(
            f"/ingress/routers/{name}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ──────────────────────────────────────────────
    # Traefik API — HTTP services
    # ──────────────────────────────────────────────

    async def list_services(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all backend services registered in Traefik."""
        return await self._get(
            "/ingress/services",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def retrieve_service(
        self,
        name: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a specific backend service by name (e.g. 'my-svc@docker')."""
        return await self._get(
            f"/ingress/services/{name}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ──────────────────────────────────────────────
    # Traefik API — middlewares
    # ──────────────────────────────────────────────

    async def list_middlewares(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all middlewares (rate limiting, auth, headers, etc.)."""
        return await self._get(
            "/ingress/middlewares",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def retrieve_middleware(
        self,
        name: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a specific middleware by name (e.g. 'rate-limit@docker')."""
        return await self._get(
            f"/ingress/middlewares/{name}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ──────────────────────────────────────────────
    # Traefik API — entrypoints & overview
    # ──────────────────────────────────────────────

    async def list_entrypoints(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all entrypoints (ports/protocols Traefik listens on)."""
        return await self._get(
            "/ingress/entrypoints",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def overview(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get Traefik dashboard overview stats (router/service/middleware counts)."""
        return await self._get(
            "/ingress/overview",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ──────────────────────────────────────────────
    # Traefik API — TCP routers & services
    # ──────────────────────────────────────────────

    async def list_tcp_routers(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all TCP routers."""
        return await self._get(
            "/ingress/tcp/routers",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def list_tcp_services(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all TCP services."""
        return await self._get(
            "/ingress/tcp/services",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ──────────────────────────────────────────────
    # PaaS Domain Management (tRPC proxy)
    # ──────────────────────────────────────────────

    async def list_domains(
        self,
        *,
        project_id: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List custom domains for a project."""
        return await self._get(
            "/ingress/domains",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"project_id": project_id},
            ),
            cast_to=object,
        )

    async def add_domain(
        self,
        *,
        project_id: str,
        domain: str,
        certificate_id: str | NotGiven = NOT_GIVEN,
        force_ssl: bool | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Add a custom domain to a project (creates DNS + TLS cert)."""
        return await self._post(
            "/ingress/domains",
            body={
                "project_id": project_id,
                "domain": domain,
                "certificate_id": certificate_id,
                "force_ssl": force_ssl,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def remove_domain(
        self,
        domain: str,
        *,
        project_id: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Remove a custom domain from a project."""
        return await self._delete(
            f"/ingress/domains/{domain}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"project_id": project_id},
            ),
            cast_to=object,
        )

    async def verify_domain(
        self,
        domain: str,
        *,
        project_id: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Verify domain DNS configuration."""
        return await self._post(
            f"/ingress/domains/{domain}/verify",
            body={"project_id": project_id},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def tls_status(
        self,
        domain: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get TLS certificate status for a domain."""
        return await self._get(
            f"/ingress/domains/{domain}/tls",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class IngressResourceWithRawResponse:
    def __init__(self, ingress: IngressResource) -> None:
        self._ingress = ingress
        # Traefik — routers
        self.list_routers = to_raw_response_wrapper(ingress.list_routers)
        self.retrieve_router = to_raw_response_wrapper(ingress.retrieve_router)
        # Traefik — services
        self.list_services = to_raw_response_wrapper(ingress.list_services)
        self.retrieve_service = to_raw_response_wrapper(ingress.retrieve_service)
        # Traefik — middlewares
        self.list_middlewares = to_raw_response_wrapper(ingress.list_middlewares)
        self.retrieve_middleware = to_raw_response_wrapper(ingress.retrieve_middleware)
        # Traefik — entrypoints & overview
        self.list_entrypoints = to_raw_response_wrapper(ingress.list_entrypoints)
        self.overview = to_raw_response_wrapper(ingress.overview)
        # Traefik — TCP
        self.list_tcp_routers = to_raw_response_wrapper(ingress.list_tcp_routers)
        self.list_tcp_services = to_raw_response_wrapper(ingress.list_tcp_services)
        # PaaS domains
        self.list_domains = to_raw_response_wrapper(ingress.list_domains)
        self.add_domain = to_raw_response_wrapper(ingress.add_domain)
        self.remove_domain = to_raw_response_wrapper(ingress.remove_domain)
        self.verify_domain = to_raw_response_wrapper(ingress.verify_domain)
        self.tls_status = to_raw_response_wrapper(ingress.tls_status)


class AsyncIngressResourceWithRawResponse:
    def __init__(self, ingress: AsyncIngressResource) -> None:
        self._ingress = ingress
        # Traefik — routers
        self.list_routers = async_to_raw_response_wrapper(ingress.list_routers)
        self.retrieve_router = async_to_raw_response_wrapper(ingress.retrieve_router)
        # Traefik — services
        self.list_services = async_to_raw_response_wrapper(ingress.list_services)
        self.retrieve_service = async_to_raw_response_wrapper(ingress.retrieve_service)
        # Traefik — middlewares
        self.list_middlewares = async_to_raw_response_wrapper(ingress.list_middlewares)
        self.retrieve_middleware = async_to_raw_response_wrapper(ingress.retrieve_middleware)
        # Traefik — entrypoints & overview
        self.list_entrypoints = async_to_raw_response_wrapper(ingress.list_entrypoints)
        self.overview = async_to_raw_response_wrapper(ingress.overview)
        # Traefik — TCP
        self.list_tcp_routers = async_to_raw_response_wrapper(ingress.list_tcp_routers)
        self.list_tcp_services = async_to_raw_response_wrapper(ingress.list_tcp_services)
        # PaaS domains
        self.list_domains = async_to_raw_response_wrapper(ingress.list_domains)
        self.add_domain = async_to_raw_response_wrapper(ingress.add_domain)
        self.remove_domain = async_to_raw_response_wrapper(ingress.remove_domain)
        self.verify_domain = async_to_raw_response_wrapper(ingress.verify_domain)
        self.tls_status = async_to_raw_response_wrapper(ingress.tls_status)


class IngressResourceWithStreamingResponse:
    def __init__(self, ingress: IngressResource) -> None:
        self._ingress = ingress
        # Traefik — routers
        self.list_routers = to_streamed_response_wrapper(ingress.list_routers)
        self.retrieve_router = to_streamed_response_wrapper(ingress.retrieve_router)
        # Traefik — services
        self.list_services = to_streamed_response_wrapper(ingress.list_services)
        self.retrieve_service = to_streamed_response_wrapper(ingress.retrieve_service)
        # Traefik — middlewares
        self.list_middlewares = to_streamed_response_wrapper(ingress.list_middlewares)
        self.retrieve_middleware = to_streamed_response_wrapper(ingress.retrieve_middleware)
        # Traefik — entrypoints & overview
        self.list_entrypoints = to_streamed_response_wrapper(ingress.list_entrypoints)
        self.overview = to_streamed_response_wrapper(ingress.overview)
        # Traefik — TCP
        self.list_tcp_routers = to_streamed_response_wrapper(ingress.list_tcp_routers)
        self.list_tcp_services = to_streamed_response_wrapper(ingress.list_tcp_services)
        # PaaS domains
        self.list_domains = to_streamed_response_wrapper(ingress.list_domains)
        self.add_domain = to_streamed_response_wrapper(ingress.add_domain)
        self.remove_domain = to_streamed_response_wrapper(ingress.remove_domain)
        self.verify_domain = to_streamed_response_wrapper(ingress.verify_domain)
        self.tls_status = to_streamed_response_wrapper(ingress.tls_status)


class AsyncIngressResourceWithStreamingResponse:
    def __init__(self, ingress: AsyncIngressResource) -> None:
        self._ingress = ingress
        # Traefik — routers
        self.list_routers = async_to_streamed_response_wrapper(ingress.list_routers)
        self.retrieve_router = async_to_streamed_response_wrapper(ingress.retrieve_router)
        # Traefik — services
        self.list_services = async_to_streamed_response_wrapper(ingress.list_services)
        self.retrieve_service = async_to_streamed_response_wrapper(ingress.retrieve_service)
        # Traefik — middlewares
        self.list_middlewares = async_to_streamed_response_wrapper(ingress.list_middlewares)
        self.retrieve_middleware = async_to_streamed_response_wrapper(ingress.retrieve_middleware)
        # Traefik — entrypoints & overview
        self.list_entrypoints = async_to_streamed_response_wrapper(ingress.list_entrypoints)
        self.overview = async_to_streamed_response_wrapper(ingress.overview)
        # Traefik — TCP
        self.list_tcp_routers = async_to_streamed_response_wrapper(ingress.list_tcp_routers)
        self.list_tcp_services = async_to_streamed_response_wrapper(ingress.list_tcp_services)
        # PaaS domains
        self.list_domains = async_to_streamed_response_wrapper(ingress.list_domains)
        self.add_domain = async_to_streamed_response_wrapper(ingress.add_domain)
        self.remove_domain = async_to_streamed_response_wrapper(ingress.remove_domain)
        self.verify_domain = async_to_streamed_response_wrapper(ingress.verify_domain)
        self.tls_status = async_to_streamed_response_wrapper(ingress.tls_status)
