# Hanzo AI SDK

from __future__ import annotations

from typing import Any, Dict, List

import httpx

from .._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._base_client import make_request_options


class KMSResource(SyncAPIResource):
    """Key Management Service with HSM semantics."""

    @cached_property
    def with_raw_response(self) -> KMSResourceWithRawResponse:
        return KMSResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> KMSResourceWithStreamingResponse:
        return KMSResourceWithStreamingResponse(self)

    # Key management
    def create_key(
        self,
        *,
        name: str,
        type: str,
        algorithm: str | NotGiven = NOT_GIVEN,
        description: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a new cryptographic key."""
        return self._post(
            "/kms/keys",
            body={
                "name": name,
                "type": type,
                "algorithm": algorithm,
                "description": description,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def list_keys(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all keys."""
        return self._get(
            "/kms/keys",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def describe_key(
        self,
        key_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get key details."""
        return self._get(
            f"/kms/keys/{key_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def enable_key(
        self,
        key_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Enable a key."""
        return self._post(
            f"/kms/keys/{key_id}/enable",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def disable_key(
        self,
        key_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Disable a key."""
        return self._post(
            f"/kms/keys/{key_id}/disable",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def delete_key(
        self,
        key_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Schedule key for deletion."""
        return self._delete(
            f"/kms/keys/{key_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def rotate_key(
        self,
        key_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Rotate a key to new version."""
        return self._post(
            f"/kms/keys/{key_id}/rotate",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def list_key_versions(
        self,
        key_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List key versions."""
        return self._get(
            f"/kms/keys/{key_id}/versions",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def rollback_key(
        self,
        key_id: str,
        *,
        version: int,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Rollback to previous key version."""
        return self._post(
            f"/kms/keys/{key_id}/rollback",
            body={"version": version},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # Crypto operations
    def encrypt(
        self,
        *,
        key_id: str,
        plaintext: str,
        context: Dict[str, str] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Encrypt data with a key."""
        return self._post(
            "/kms/encrypt",
            body={"key_id": key_id, "plaintext": plaintext, "context": context},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def decrypt(
        self,
        *,
        key_id: str,
        ciphertext: str,
        context: Dict[str, str] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Decrypt data with a key."""
        return self._post(
            "/kms/decrypt",
            body={"key_id": key_id, "ciphertext": ciphertext, "context": context},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def sign(
        self,
        *,
        key_id: str,
        message: str,
        algorithm: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Sign data with a key."""
        return self._post(
            "/kms/sign",
            body={"key_id": key_id, "message": message, "algorithm": algorithm},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def verify(
        self,
        *,
        key_id: str,
        message: str,
        signature: str,
        algorithm: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Verify signature with a key."""
        return self._post(
            "/kms/verify",
            body={
                "key_id": key_id,
                "message": message,
                "signature": signature,
                "algorithm": algorithm,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # Access control
    def create_grant(
        self,
        key_id: str,
        *,
        principal: str,
        operations: List[str],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a grant for key access."""
        return self._post(
            f"/kms/keys/{key_id}/grants",
            body={"principal": principal, "operations": operations},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def revoke_grant(
        self,
        key_id: str,
        grant_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Revoke a grant."""
        return self._delete(
            f"/kms/keys/{key_id}/grants/{grant_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def list_grants(
        self,
        key_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List grants for a key."""
        return self._get(
            f"/kms/keys/{key_id}/grants",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # Audit
    def audit(
        self,
        *,
        key_id: str | NotGiven = NOT_GIVEN,
        since: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get audit logs for KMS operations."""
        return self._get(
            "/kms/audit",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"key_id": key_id, "since": since},
            ),
            cast_to=object,
        )


class AsyncKMSResource(AsyncAPIResource):
    """Key Management Service with HSM semantics."""

    @cached_property
    def with_raw_response(self) -> AsyncKMSResourceWithRawResponse:
        return AsyncKMSResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncKMSResourceWithStreamingResponse:
        return AsyncKMSResourceWithStreamingResponse(self)

    async def create_key(
        self,
        *,
        name: str,
        type: str,
        algorithm: str | NotGiven = NOT_GIVEN,
        description: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a new cryptographic key."""
        return await self._post(
            "/kms/keys",
            body={
                "name": name,
                "type": type,
                "algorithm": algorithm,
                "description": description,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def list_keys(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all keys."""
        return await self._get(
            "/kms/keys",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def describe_key(
        self,
        key_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get key details."""
        return await self._get(
            f"/kms/keys/{key_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def enable_key(
        self,
        key_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Enable a key."""
        return await self._post(
            f"/kms/keys/{key_id}/enable",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def disable_key(
        self,
        key_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Disable a key."""
        return await self._post(
            f"/kms/keys/{key_id}/disable",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def delete_key(
        self,
        key_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Schedule key for deletion."""
        return await self._delete(
            f"/kms/keys/{key_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def rotate_key(
        self,
        key_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Rotate a key to new version."""
        return await self._post(
            f"/kms/keys/{key_id}/rotate",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def list_key_versions(
        self,
        key_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List key versions."""
        return await self._get(
            f"/kms/keys/{key_id}/versions",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def rollback_key(
        self,
        key_id: str,
        *,
        version: int,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Rollback to previous key version."""
        return await self._post(
            f"/kms/keys/{key_id}/rollback",
            body={"version": version},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def encrypt(
        self,
        *,
        key_id: str,
        plaintext: str,
        context: Dict[str, str] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Encrypt data with a key."""
        return await self._post(
            "/kms/encrypt",
            body={"key_id": key_id, "plaintext": plaintext, "context": context},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def decrypt(
        self,
        *,
        key_id: str,
        ciphertext: str,
        context: Dict[str, str] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Decrypt data with a key."""
        return await self._post(
            "/kms/decrypt",
            body={"key_id": key_id, "ciphertext": ciphertext, "context": context},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def sign(
        self,
        *,
        key_id: str,
        message: str,
        algorithm: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Sign data with a key."""
        return await self._post(
            "/kms/sign",
            body={"key_id": key_id, "message": message, "algorithm": algorithm},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def verify(
        self,
        *,
        key_id: str,
        message: str,
        signature: str,
        algorithm: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Verify signature with a key."""
        return await self._post(
            "/kms/verify",
            body={
                "key_id": key_id,
                "message": message,
                "signature": signature,
                "algorithm": algorithm,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def create_grant(
        self,
        key_id: str,
        *,
        principal: str,
        operations: List[str],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a grant for key access."""
        return await self._post(
            f"/kms/keys/{key_id}/grants",
            body={"principal": principal, "operations": operations},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def revoke_grant(
        self,
        key_id: str,
        grant_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Revoke a grant."""
        return await self._delete(
            f"/kms/keys/{key_id}/grants/{grant_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def list_grants(
        self,
        key_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List grants for a key."""
        return await self._get(
            f"/kms/keys/{key_id}/grants",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def audit(
        self,
        *,
        key_id: str | NotGiven = NOT_GIVEN,
        since: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get audit logs for KMS operations."""
        return await self._get(
            "/kms/audit",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={"key_id": key_id, "since": since},
            ),
            cast_to=object,
        )


class KMSResourceWithRawResponse:
    def __init__(self, kms: KMSResource) -> None:
        self._kms = kms


class AsyncKMSResourceWithRawResponse:
    def __init__(self, kms: AsyncKMSResource) -> None:
        self._kms = kms


class KMSResourceWithStreamingResponse:
    def __init__(self, kms: KMSResource) -> None:
        self._kms = kms


class AsyncKMSResourceWithStreamingResponse:
    def __init__(self, kms: AsyncKMSResource) -> None:
        self._kms = kms
