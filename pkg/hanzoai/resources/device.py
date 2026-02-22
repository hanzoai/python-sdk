# Hanzo AI SDK

from __future__ import annotations

from typing import Any, Dict, List

import httpx

from .._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._base_client import make_request_options


class DeviceResource(SyncAPIResource):
    """Device enrollment and posture management."""

    @cached_property
    def with_raw_response(self) -> DeviceResourceWithRawResponse:
        return DeviceResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> DeviceResourceWithStreamingResponse:
        return DeviceResourceWithStreamingResponse(self)

    def enroll(
        self,
        *,
        code: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Enroll a device (QR/one-time code)."""
        return self._post(
            "/device/enroll",
            body={"code": code},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
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
        """List enrolled devices."""
        return self._get(
            "/device",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def revoke(
        self,
        device_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Revoke a device."""
        return self._delete(
            f"/device/{device_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def posture(
        self,
        device_id: str | NotGiven = NOT_GIVEN,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get device posture."""
        return self._get(
            "/device/posture",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"device_id": device_id},
            ),
            cast_to=object,
        )

    def set_trust(
        self,
        device_id: str,
        *,
        trust_level: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Set device trust level."""
        return self._post(
            f"/device/{device_id}/trust",
            body={"trust_level": trust_level},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def get_trust(
        self,
        device_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get device trust level."""
        return self._get(
            f"/device/{device_id}/trust",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class AsyncDeviceResource(AsyncAPIResource):
    """Device enrollment and posture management."""

    @cached_property
    def with_raw_response(self) -> AsyncDeviceResourceWithRawResponse:
        return AsyncDeviceResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncDeviceResourceWithStreamingResponse:
        return AsyncDeviceResourceWithStreamingResponse(self)

    async def enroll(
        self,
        *,
        code: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Enroll a device (QR/one-time code)."""
        return await self._post(
            "/device/enroll",
            body={"code": code},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
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
        """List enrolled devices."""
        return await self._get(
            "/device",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def revoke(
        self,
        device_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Revoke a device."""
        return await self._delete(
            f"/device/{device_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def posture(
        self,
        device_id: str | NotGiven = NOT_GIVEN,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get device posture."""
        return await self._get(
            "/device/posture",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"device_id": device_id},
            ),
            cast_to=object,
        )

    async def set_trust(
        self,
        device_id: str,
        *,
        trust_level: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Set device trust level."""
        return await self._post(
            f"/device/{device_id}/trust",
            body={"trust_level": trust_level},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def get_trust(
        self,
        device_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get device trust level."""
        return await self._get(
            f"/device/{device_id}/trust",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class DeviceResourceWithRawResponse:
    def __init__(self, device: DeviceResource) -> None:
        self._device = device


class AsyncDeviceResourceWithRawResponse:
    def __init__(self, device: AsyncDeviceResource) -> None:
        self._device = device


class DeviceResourceWithStreamingResponse:
    def __init__(self, device: DeviceResource) -> None:
        self._device = device


class AsyncDeviceResourceWithStreamingResponse:
    def __init__(self, device: AsyncDeviceResource) -> None:
        self._device = device
