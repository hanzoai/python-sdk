# Hanzo AI SDK

from __future__ import annotations

from typing import Any, Dict, List

import httpx

from .._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._base_client import make_request_options


class PolicyResource(SyncAPIResource):
    """Policy management and access control."""

    @cached_property
    def with_raw_response(self) -> PolicyResourceWithRawResponse:
        return PolicyResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> PolicyResourceWithStreamingResponse:
        return PolicyResourceWithStreamingResponse(self)

    def lint(
        self,
        *,
        policy: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Lint a policy file."""
        return self._post(
            "/policy/lint",
            body={"policy": policy},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def validate(
        self,
        *,
        policy: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Validate a policy."""
        return self._post(
            "/policy/validate",
            body={"policy": policy},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def format(
        self,
        *,
        policy: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Format a policy file."""
        return self._post(
            "/policy/format",
            body={"policy": policy},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def diff(
        self,
        *,
        policy: str,
        dry_run: bool | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Diff policy against current state."""
        return self._post(
            "/policy/diff",
            body={"policy": policy, "dry_run": dry_run},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def apply(
        self,
        *,
        policy: str,
        dry_run: bool | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Apply a policy."""
        return self._post(
            "/policy/apply",
            body={"policy": policy, "dry_run": dry_run},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def explain(
        self,
        *,
        principal: str,
        action: str,
        resource: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Explain policy evaluation."""
        return self._post(
            "/policy/explain",
            body={"principal": principal, "action": action, "resource": resource},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def who_can(
        self,
        *,
        action: str,
        resource: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Find who can perform an action."""
        return self._get(
            "/policy/who-can",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"action": action, "resource": resource},
            ),
            cast_to=object,
        )

    def list(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List policies."""
        return self._get(
            "/policy",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class AsyncPolicyResource(AsyncAPIResource):
    """Policy management and access control."""

    @cached_property
    def with_raw_response(self) -> AsyncPolicyResourceWithRawResponse:
        return AsyncPolicyResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncPolicyResourceWithStreamingResponse:
        return AsyncPolicyResourceWithStreamingResponse(self)

    async def lint(
        self,
        *,
        policy: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Lint a policy file."""
        return await self._post(
            "/policy/lint",
            body={"policy": policy},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def validate(
        self,
        *,
        policy: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Validate a policy."""
        return await self._post(
            "/policy/validate",
            body={"policy": policy},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def format(
        self,
        *,
        policy: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Format a policy file."""
        return await self._post(
            "/policy/format",
            body={"policy": policy},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def diff(
        self,
        *,
        policy: str,
        dry_run: bool | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Diff policy against current state."""
        return await self._post(
            "/policy/diff",
            body={"policy": policy, "dry_run": dry_run},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def apply(
        self,
        *,
        policy: str,
        dry_run: bool | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Apply a policy."""
        return await self._post(
            "/policy/apply",
            body={"policy": policy, "dry_run": dry_run},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def explain(
        self,
        *,
        principal: str,
        action: str,
        resource: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Explain policy evaluation."""
        return await self._post(
            "/policy/explain",
            body={"principal": principal, "action": action, "resource": resource},
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def who_can(
        self,
        *,
        action: str,
        resource: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Find who can perform an action."""
        return await self._get(
            "/policy/who-can",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"action": action, "resource": resource},
            ),
            cast_to=object,
        )

    async def list(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List policies."""
        return await self._get(
            "/policy",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class PolicyResourceWithRawResponse:
    def __init__(self, policy: PolicyResource) -> None:
        self._policy = policy


class AsyncPolicyResourceWithRawResponse:
    def __init__(self, policy: AsyncPolicyResource) -> None:
        self._policy = policy


class PolicyResourceWithStreamingResponse:
    def __init__(self, policy: PolicyResource) -> None:
        self._policy = policy


class AsyncPolicyResourceWithStreamingResponse:
    def __init__(self, policy: AsyncPolicyResource) -> None:
        self._policy = policy
