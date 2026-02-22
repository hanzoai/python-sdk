# Hanzo AI SDK

from __future__ import annotations

from typing import Any, Dict, List

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

__all__ = ["ObservabilityResource", "AsyncObservabilityResource"]


class ObservabilityResource(SyncAPIResource):
    """Metrics, logs, and tracing."""

    @cached_property
    def with_raw_response(self) -> ObservabilityResourceWithRawResponse:
        return ObservabilityResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ObservabilityResourceWithStreamingResponse:
        return ObservabilityResourceWithStreamingResponse(self)

    def metrics(
        self,
        *,
        names: List[str] | NotGiven = NOT_GIVEN,
        start_time: str | NotGiven = NOT_GIVEN,
        end_time: str | NotGiven = NOT_GIVEN,
        step: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Query metrics."""
        return self._get(
            "/operations/observability/metrics",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={
                    "names": names,
                    "start_time": start_time,
                    "end_time": end_time,
                    "step": step,
                },
            ),
            cast_to=object,
        )

    def logs(
        self,
        *,
        query: str | NotGiven = NOT_GIVEN,
        start_time: str | NotGiven = NOT_GIVEN,
        end_time: str | NotGiven = NOT_GIVEN,
        limit: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Query logs."""
        return self._get(
            "/operations/observability/logs",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={
                    "query": query,
                    "start_time": start_time,
                    "end_time": end_time,
                    "limit": limit,
                },
            ),
            cast_to=object,
        )

    def traces(
        self,
        *,
        trace_id: str | NotGiven = NOT_GIVEN,
        service: str | NotGiven = NOT_GIVEN,
        start_time: str | NotGiven = NOT_GIVEN,
        end_time: str | NotGiven = NOT_GIVEN,
        limit: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Query traces."""
        return self._get(
            "/operations/observability/traces",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={
                    "trace_id": trace_id,
                    "service": service,
                    "start_time": start_time,
                    "end_time": end_time,
                    "limit": limit,
                },
            ),
            cast_to=object,
        )

    def get_trace(
        self,
        trace_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a specific trace."""
        return self._get(
            f"/operations/observability/traces/{trace_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def alerts(
        self,
        *,
        status: str | NotGiven = NOT_GIVEN,
        severity: str | NotGiven = NOT_GIVEN,
        limit: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List alerts."""
        return self._get(
            "/operations/observability/alerts",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"status": status, "severity": severity, "limit": limit},
            ),
            cast_to=object,
        )

    def create_alert(
        self,
        *,
        name: str,
        query: str,
        threshold: float,
        severity: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create an alert rule."""
        return self._post(
            "/operations/observability/alerts",
            body={
                "name": name,
                "query": query,
                "threshold": threshold,
                "severity": severity,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def health(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get system health status."""
        return self._get(
            "/operations/observability/health",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class AsyncObservabilityResource(AsyncAPIResource):
    """Metrics, logs, and tracing (async)."""

    @cached_property
    def with_raw_response(self) -> AsyncObservabilityResourceWithRawResponse:
        return AsyncObservabilityResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(
        self,
    ) -> AsyncObservabilityResourceWithStreamingResponse:
        return AsyncObservabilityResourceWithStreamingResponse(self)

    async def metrics(
        self,
        *,
        names: List[str] | NotGiven = NOT_GIVEN,
        start_time: str | NotGiven = NOT_GIVEN,
        end_time: str | NotGiven = NOT_GIVEN,
        step: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            "/operations/observability/metrics",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={
                    "names": names,
                    "start_time": start_time,
                    "end_time": end_time,
                    "step": step,
                },
            ),
            cast_to=object,
        )

    async def logs(
        self,
        *,
        query: str | NotGiven = NOT_GIVEN,
        start_time: str | NotGiven = NOT_GIVEN,
        end_time: str | NotGiven = NOT_GIVEN,
        limit: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            "/operations/observability/logs",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={
                    "query": query,
                    "start_time": start_time,
                    "end_time": end_time,
                    "limit": limit,
                },
            ),
            cast_to=object,
        )

    async def traces(
        self,
        *,
        trace_id: str | NotGiven = NOT_GIVEN,
        service: str | NotGiven = NOT_GIVEN,
        start_time: str | NotGiven = NOT_GIVEN,
        end_time: str | NotGiven = NOT_GIVEN,
        limit: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            "/operations/observability/traces",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={
                    "trace_id": trace_id,
                    "service": service,
                    "start_time": start_time,
                    "end_time": end_time,
                    "limit": limit,
                },
            ),
            cast_to=object,
        )

    async def get_trace(
        self,
        trace_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            f"/operations/observability/traces/{trace_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def alerts(
        self,
        *,
        status: str | NotGiven = NOT_GIVEN,
        severity: str | NotGiven = NOT_GIVEN,
        limit: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            "/operations/observability/alerts",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"status": status, "severity": severity, "limit": limit},
            ),
            cast_to=object,
        )

    async def create_alert(
        self,
        *,
        name: str,
        query: str,
        threshold: float,
        severity: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._post(
            "/operations/observability/alerts",
            body={
                "name": name,
                "query": query,
                "threshold": threshold,
                "severity": severity,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def health(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        return await self._get(
            "/operations/observability/health",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class ObservabilityResourceWithRawResponse:
    def __init__(self, observability: ObservabilityResource) -> None:
        self._observability = observability
        self.metrics = to_raw_response_wrapper(observability.metrics)
        self.logs = to_raw_response_wrapper(observability.logs)
        self.traces = to_raw_response_wrapper(observability.traces)
        self.get_trace = to_raw_response_wrapper(observability.get_trace)
        self.alerts = to_raw_response_wrapper(observability.alerts)
        self.create_alert = to_raw_response_wrapper(observability.create_alert)
        self.health = to_raw_response_wrapper(observability.health)


class AsyncObservabilityResourceWithRawResponse:
    def __init__(self, observability: AsyncObservabilityResource) -> None:
        self._observability = observability
        self.metrics = async_to_raw_response_wrapper(observability.metrics)
        self.logs = async_to_raw_response_wrapper(observability.logs)
        self.traces = async_to_raw_response_wrapper(observability.traces)
        self.get_trace = async_to_raw_response_wrapper(observability.get_trace)
        self.alerts = async_to_raw_response_wrapper(observability.alerts)
        self.create_alert = async_to_raw_response_wrapper(observability.create_alert)
        self.health = async_to_raw_response_wrapper(observability.health)


class ObservabilityResourceWithStreamingResponse:
    def __init__(self, observability: ObservabilityResource) -> None:
        self._observability = observability
        self.metrics = to_streamed_response_wrapper(observability.metrics)
        self.logs = to_streamed_response_wrapper(observability.logs)
        self.traces = to_streamed_response_wrapper(observability.traces)
        self.get_trace = to_streamed_response_wrapper(observability.get_trace)
        self.alerts = to_streamed_response_wrapper(observability.alerts)
        self.create_alert = to_streamed_response_wrapper(observability.create_alert)
        self.health = to_streamed_response_wrapper(observability.health)


class AsyncObservabilityResourceWithStreamingResponse:
    def __init__(self, observability: AsyncObservabilityResource) -> None:
        self._observability = observability
        self.metrics = async_to_streamed_response_wrapper(observability.metrics)
        self.logs = async_to_streamed_response_wrapper(observability.logs)
        self.traces = async_to_streamed_response_wrapper(observability.traces)
        self.get_trace = async_to_streamed_response_wrapper(observability.get_trace)
        self.alerts = async_to_streamed_response_wrapper(observability.alerts)
        self.create_alert = async_to_streamed_response_wrapper(
            observability.create_alert
        )
        self.health = async_to_streamed_response_wrapper(observability.health)
