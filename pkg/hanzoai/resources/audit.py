# Hanzo AI SDK

from __future__ import annotations

from typing import Dict, Any, List

import httpx

from .._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._base_client import make_request_options


class AuditResource(SyncAPIResource):
    """Audit logging and compliance."""

    @cached_property
    def with_raw_response(self) -> AuditResourceWithRawResponse:
        return AuditResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AuditResourceWithStreamingResponse:
        return AuditResourceWithStreamingResponse(self)

    def events(
        self,
        *,
        since: str | NotGiven = NOT_GIVEN,
        until: str | NotGiven = NOT_GIVEN,
        actor: str | NotGiven = NOT_GIVEN,
        resource: str | NotGiven = NOT_GIVEN,
        action: str | NotGiven = NOT_GIVEN,
        limit: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List audit events."""
        return self._get(
            "/audit/events",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={
                    "since": since,
                    "until": until,
                    "actor": actor,
                    "resource": resource,
                    "action": action,
                    "limit": limit,
                },
            ),
            cast_to=object,
        )

    def tail(
        self,
        *,
        follow: bool | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Tail audit events in real-time."""
        return self._get(
            "/audit/tail",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"follow": follow},
            ),
            cast_to=object,
        )

    def export(
        self,
        *,
        since: str,
        until: str,
        format: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Export audit logs."""
        return self._post(
            "/audit/export",
            body={"since": since, "until": until, "format": format},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class AsyncAuditResource(AsyncAPIResource):
    """Audit logging and compliance."""

    @cached_property
    def with_raw_response(self) -> AsyncAuditResourceWithRawResponse:
        return AsyncAuditResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncAuditResourceWithStreamingResponse:
        return AsyncAuditResourceWithStreamingResponse(self)

    async def events(
        self,
        *,
        since: str | NotGiven = NOT_GIVEN,
        until: str | NotGiven = NOT_GIVEN,
        actor: str | NotGiven = NOT_GIVEN,
        resource: str | NotGiven = NOT_GIVEN,
        action: str | NotGiven = NOT_GIVEN,
        limit: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List audit events."""
        return await self._get(
            "/audit/events",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={
                    "since": since,
                    "until": until,
                    "actor": actor,
                    "resource": resource,
                    "action": action,
                    "limit": limit,
                },
            ),
            cast_to=object,
        )

    async def tail(
        self,
        *,
        follow: bool | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Tail audit events in real-time."""
        return await self._get(
            "/audit/tail",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"follow": follow},
            ),
            cast_to=object,
        )

    async def export(
        self,
        *,
        since: str,
        until: str,
        format: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Export audit logs."""
        return await self._post(
            "/audit/export",
            body={"since": since, "until": until, "format": format},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class AuditResourceWithRawResponse:
    def __init__(self, audit: AuditResource) -> None:
        self._audit = audit

class AsyncAuditResourceWithRawResponse:
    def __init__(self, audit: AsyncAuditResource) -> None:
        self._audit = audit

class AuditResourceWithStreamingResponse:
    def __init__(self, audit: AuditResource) -> None:
        self._audit = audit

class AsyncAuditResourceWithStreamingResponse:
    def __init__(self, audit: AsyncAuditResource) -> None:
        self._audit = audit
