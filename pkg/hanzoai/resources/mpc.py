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

__all__ = ["MPCResource", "AsyncMPCResource"]


class MPCResource(SyncAPIResource):
    """Multi-party computation: CGGMP21/FROST threshold signing, vaults, policies, smart wallets."""

    @cached_property
    def with_raw_response(self) -> MPCResourceWithRawResponse:
        return MPCResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> MPCResourceWithStreamingResponse:
        return MPCResourceWithStreamingResponse(self)

    # ── Status ────────────────────────────────────────────────────────────

    def status(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get MPC service health and status."""
        return self._get(
            "/mpc/status",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Vaults ────────────────────────────────────────────────────────────

    def list_vaults(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all vaults."""
        return self._get(
            "/mpc/vaults",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def create_vault(
        self,
        *,
        name: str,
        description: str | NotGiven = NOT_GIVEN,
        type: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a new vault."""
        return self._post(
            "/mpc/vaults",
            body={
                "name": name,
                "description": description,
                "type": type,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def retrieve_vault(
        self,
        vault_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get vault details."""
        return self._get(
            f"/mpc/vaults/{vault_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def update_vault(
        self,
        vault_id: str,
        *,
        name: str | NotGiven = NOT_GIVEN,
        description: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update a vault."""
        return self._patch(
            f"/mpc/vaults/{vault_id}",
            body={
                "name": name,
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

    def delete_vault(
        self,
        vault_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a vault."""
        return self._delete(
            f"/mpc/vaults/{vault_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Wallets (Key Generation Ceremony) ─────────────────────────────────

    def list_wallets(
        self,
        vault_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List wallets in a vault."""
        return self._get(
            f"/mpc/vaults/{vault_id}/wallets",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def create_wallet(
        self,
        vault_id: str,
        *,
        name: str,
        curve: str | NotGiven = NOT_GIVEN,
        threshold: int | NotGiven = NOT_GIVEN,
        parties: int | NotGiven = NOT_GIVEN,
        protocol: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a wallet and initiate key generation ceremony.

        Args:
            vault_id: Vault to create the wallet in.
            name: Wallet name.
            curve: Elliptic curve - "secp256k1", "ed25519", or "stark".
            threshold: Minimum signers required (t of n).
            parties: Total number of key shares (n).
            protocol: MPC protocol - "cggmp21" or "frost".
        """
        return self._post(
            f"/mpc/vaults/{vault_id}/wallets",
            body={
                "name": name,
                "curve": curve,
                "threshold": threshold,
                "parties": parties,
                "protocol": protocol,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def retrieve_wallet(
        self,
        wallet_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get wallet details including public key and addresses."""
        return self._get(
            f"/mpc/wallets/{wallet_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def delete_wallet(
        self,
        wallet_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a wallet."""
        return self._delete(
            f"/mpc/wallets/{wallet_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Transactions (Signing Ceremony) ───────────────────────────────────

    def list_transactions(
        self,
        *,
        wallet_id: str | NotGiven = NOT_GIVEN,
        status: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List transactions, optionally filtered by wallet or status."""
        return self._get(
            "/mpc/transactions",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={
                    "wallet_id": wallet_id,
                    "status": status,
                },
            ),
            cast_to=object,
        )

    def create_transaction(
        self,
        *,
        wallet_id: str,
        type: str,
        chain: str | NotGiven = NOT_GIVEN,
        to: str | NotGiven = NOT_GIVEN,
        amount: str | NotGiven = NOT_GIVEN,
        data: str | NotGiven = NOT_GIVEN,
        gas_limit: str | NotGiven = NOT_GIVEN,
        gas_price: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a signing request.

        Args:
            wallet_id: Wallet to sign with.
            type: Transaction type - "transfer", "contract_call", "message_sign", or "typed_data".
            chain: Target blockchain network.
            to: Recipient address.
            amount: Transfer amount.
            data: Calldata or message payload.
            gas_limit: Gas limit for EVM transactions.
            gas_price: Gas price for EVM transactions.
        """
        return self._post(
            "/mpc/transactions",
            body={
                "wallet_id": wallet_id,
                "type": type,
                "chain": chain,
                "to": to,
                "amount": amount,
                "data": data,
                "gas_limit": gas_limit,
                "gas_price": gas_price,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def retrieve_transaction(
        self,
        transaction_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get transaction status and details."""
        return self._get(
            f"/mpc/transactions/{transaction_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def approve_transaction(
        self,
        transaction_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Approve a signing request (as a party)."""
        return self._post(
            f"/mpc/transactions/{transaction_id}/approve",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def reject_transaction(
        self,
        transaction_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Reject a signing request."""
        return self._post(
            f"/mpc/transactions/{transaction_id}/reject",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def broadcast_transaction(
        self,
        transaction_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Broadcast a signed transaction to the network."""
        return self._post(
            f"/mpc/transactions/{transaction_id}/broadcast",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Policies ──────────────────────────────────────────────────────────

    def list_policies(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List signing policies."""
        return self._get(
            "/mpc/policies",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def create_policy(
        self,
        *,
        name: str,
        rules: List[Dict[str, Any]],
        vault_id: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a signing policy.

        Args:
            name: Policy name.
            rules: Policy rules (spending limits, time locks, whitelist, multi-approval).
            vault_id: Vault to attach the policy to.
        """
        return self._post(
            "/mpc/policies",
            body={
                "name": name,
                "rules": rules,
                "vault_id": vault_id,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def retrieve_policy(
        self,
        policy_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get policy details."""
        return self._get(
            f"/mpc/policies/{policy_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def update_policy(
        self,
        policy_id: str,
        *,
        name: str | NotGiven = NOT_GIVEN,
        rules: List[Dict[str, Any]] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update a policy."""
        return self._patch(
            f"/mpc/policies/{policy_id}",
            body={
                "name": name,
                "rules": rules,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def delete_policy(
        self,
        policy_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a policy."""
        return self._delete(
            f"/mpc/policies/{policy_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Webhooks ──────────────────────────────────────────────────────────

    def list_webhooks(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List webhooks."""
        return self._get(
            "/mpc/webhooks",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def create_webhook(
        self,
        *,
        url: str,
        events: List[str],
        secret: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a webhook.

        Args:
            url: Webhook endpoint URL.
            events: Events to subscribe to (e.g. "transaction.created",
                    "transaction.signed", "transaction.broadcast",
                    "wallet.created", "policy.triggered").
            secret: HMAC secret for webhook signature verification.
        """
        return self._post(
            "/mpc/webhooks",
            body={
                "url": url,
                "events": events,
                "secret": secret,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def delete_webhook(
        self,
        webhook_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a webhook."""
        return self._delete(
            f"/mpc/webhooks/{webhook_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Smart Wallets (Account Abstraction) ───────────────────────────────

    def list_smart_wallets(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List smart wallets."""
        return self._get(
            "/mpc/smart-wallets",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def deploy_smart_wallet(
        self,
        *,
        wallet_id: str,
        chain: str,
        type: str | NotGiven = NOT_GIVEN,
        salt: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Deploy a smart wallet (account abstraction).

        Args:
            wallet_id: MPC wallet backing the smart wallet.
            chain: Target chain for deployment.
            type: Smart wallet type - "safe", "light", or "kernel".
            salt: Deterministic deployment salt.
        """
        return self._post(
            "/mpc/smart-wallets",
            body={
                "wallet_id": wallet_id,
                "chain": chain,
                "type": type,
                "salt": salt,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def retrieve_smart_wallet(
        self,
        smart_wallet_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get smart wallet details."""
        return self._get(
            f"/mpc/smart-wallets/{smart_wallet_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def execute_smart_wallet(
        self,
        smart_wallet_id: str,
        *,
        calls: List[Dict[str, Any]],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Execute a user operation on a smart wallet.

        Args:
            smart_wallet_id: Smart wallet to execute on.
            calls: Batch of calls to execute (to, value, data).
        """
        return self._post(
            f"/mpc/smart-wallets/{smart_wallet_id}/execute",
            body={"calls": calls},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Bridge Signing ────────────────────────────────────────────────────

    def sign_bridge(
        self,
        *,
        wallet_id: str,
        source_chain: str,
        dest_chain: str,
        token: str,
        amount: str,
        recipient: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Sign a cross-chain bridge transaction.

        Args:
            wallet_id: MPC wallet to sign with.
            source_chain: Source chain identifier.
            dest_chain: Destination chain identifier.
            token: Token address or symbol.
            amount: Amount to bridge.
            recipient: Recipient address on destination chain.
        """
        return self._post(
            "/mpc/bridge/sign",
            body={
                "wallet_id": wallet_id,
                "source_chain": source_chain,
                "dest_chain": dest_chain,
                "token": token,
                "amount": amount,
                "recipient": recipient,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def bridge_status(
        self,
        tx_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get bridge transaction status."""
        return self._get(
            f"/mpc/bridge/status/{tx_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ── API Keys ──────────────────────────────────────────────────────────

    def list_api_keys(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List API keys."""
        return self._get(
            "/mpc/api-keys",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def create_api_key(
        self,
        *,
        name: str,
        permissions: List[str] | NotGiven = NOT_GIVEN,
        expires_at: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create an API key.

        Args:
            name: Key name.
            permissions: List of permissions for the key.
            expires_at: ISO 8601 expiration timestamp.
        """
        return self._post(
            "/mpc/api-keys",
            body={
                "name": name,
                "permissions": permissions,
                "expires_at": expires_at,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def delete_api_key(
        self,
        key_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Revoke an API key."""
        return self._delete(
            f"/mpc/api-keys/{key_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Whitelist ─────────────────────────────────────────────────────────

    def list_whitelist(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List whitelisted addresses."""
        return self._get(
            "/mpc/whitelist",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def add_to_whitelist(
        self,
        *,
        address: str,
        chain: str,
        label: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Add an address to the whitelist.

        Args:
            address: Blockchain address to whitelist.
            chain: Chain the address belongs to.
            label: Human-readable label.
        """
        return self._post(
            "/mpc/whitelist",
            body={
                "address": address,
                "chain": chain,
                "label": label,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def remove_from_whitelist(
        self,
        whitelist_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Remove an address from the whitelist."""
        return self._delete(
            f"/mpc/whitelist/{whitelist_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class AsyncMPCResource(AsyncAPIResource):
    """Multi-party computation: CGGMP21/FROST threshold signing, vaults, policies, smart wallets (async)."""

    @cached_property
    def with_raw_response(self) -> AsyncMPCResourceWithRawResponse:
        return AsyncMPCResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncMPCResourceWithStreamingResponse:
        return AsyncMPCResourceWithStreamingResponse(self)

    # ── Status ────────────────────────────────────────────────────────────

    async def status(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get MPC service health and status."""
        return await self._get(
            "/mpc/status",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Vaults ────────────────────────────────────────────────────────────

    async def list_vaults(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all vaults."""
        return await self._get(
            "/mpc/vaults",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def create_vault(
        self,
        *,
        name: str,
        description: str | NotGiven = NOT_GIVEN,
        type: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a new vault."""
        return await self._post(
            "/mpc/vaults",
            body={
                "name": name,
                "description": description,
                "type": type,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def retrieve_vault(
        self,
        vault_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get vault details."""
        return await self._get(
            f"/mpc/vaults/{vault_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def update_vault(
        self,
        vault_id: str,
        *,
        name: str | NotGiven = NOT_GIVEN,
        description: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update a vault."""
        return await self._patch(
            f"/mpc/vaults/{vault_id}",
            body={
                "name": name,
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

    async def delete_vault(
        self,
        vault_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a vault."""
        return await self._delete(
            f"/mpc/vaults/{vault_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Wallets (Key Generation Ceremony) ─────────────────────────────────

    async def list_wallets(
        self,
        vault_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List wallets in a vault."""
        return await self._get(
            f"/mpc/vaults/{vault_id}/wallets",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def create_wallet(
        self,
        vault_id: str,
        *,
        name: str,
        curve: str | NotGiven = NOT_GIVEN,
        threshold: int | NotGiven = NOT_GIVEN,
        parties: int | NotGiven = NOT_GIVEN,
        protocol: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a wallet and initiate key generation ceremony.

        Args:
            vault_id: Vault to create the wallet in.
            name: Wallet name.
            curve: Elliptic curve - "secp256k1", "ed25519", or "stark".
            threshold: Minimum signers required (t of n).
            parties: Total number of key shares (n).
            protocol: MPC protocol - "cggmp21" or "frost".
        """
        return await self._post(
            f"/mpc/vaults/{vault_id}/wallets",
            body={
                "name": name,
                "curve": curve,
                "threshold": threshold,
                "parties": parties,
                "protocol": protocol,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def retrieve_wallet(
        self,
        wallet_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get wallet details including public key and addresses."""
        return await self._get(
            f"/mpc/wallets/{wallet_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def delete_wallet(
        self,
        wallet_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a wallet."""
        return await self._delete(
            f"/mpc/wallets/{wallet_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Transactions (Signing Ceremony) ───────────────────────────────────

    async def list_transactions(
        self,
        *,
        wallet_id: str | NotGiven = NOT_GIVEN,
        status: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List transactions, optionally filtered by wallet or status."""
        return await self._get(
            "/mpc/transactions",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={
                    "wallet_id": wallet_id,
                    "status": status,
                },
            ),
            cast_to=object,
        )

    async def create_transaction(
        self,
        *,
        wallet_id: str,
        type: str,
        chain: str | NotGiven = NOT_GIVEN,
        to: str | NotGiven = NOT_GIVEN,
        amount: str | NotGiven = NOT_GIVEN,
        data: str | NotGiven = NOT_GIVEN,
        gas_limit: str | NotGiven = NOT_GIVEN,
        gas_price: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a signing request.

        Args:
            wallet_id: Wallet to sign with.
            type: Transaction type - "transfer", "contract_call", "message_sign", or "typed_data".
            chain: Target blockchain network.
            to: Recipient address.
            amount: Transfer amount.
            data: Calldata or message payload.
            gas_limit: Gas limit for EVM transactions.
            gas_price: Gas price for EVM transactions.
        """
        return await self._post(
            "/mpc/transactions",
            body={
                "wallet_id": wallet_id,
                "type": type,
                "chain": chain,
                "to": to,
                "amount": amount,
                "data": data,
                "gas_limit": gas_limit,
                "gas_price": gas_price,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def retrieve_transaction(
        self,
        transaction_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get transaction status and details."""
        return await self._get(
            f"/mpc/transactions/{transaction_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def approve_transaction(
        self,
        transaction_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Approve a signing request (as a party)."""
        return await self._post(
            f"/mpc/transactions/{transaction_id}/approve",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def reject_transaction(
        self,
        transaction_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Reject a signing request."""
        return await self._post(
            f"/mpc/transactions/{transaction_id}/reject",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def broadcast_transaction(
        self,
        transaction_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Broadcast a signed transaction to the network."""
        return await self._post(
            f"/mpc/transactions/{transaction_id}/broadcast",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Policies ──────────────────────────────────────────────────────────

    async def list_policies(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List signing policies."""
        return await self._get(
            "/mpc/policies",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def create_policy(
        self,
        *,
        name: str,
        rules: List[Dict[str, Any]],
        vault_id: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a signing policy.

        Args:
            name: Policy name.
            rules: Policy rules (spending limits, time locks, whitelist, multi-approval).
            vault_id: Vault to attach the policy to.
        """
        return await self._post(
            "/mpc/policies",
            body={
                "name": name,
                "rules": rules,
                "vault_id": vault_id,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def retrieve_policy(
        self,
        policy_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get policy details."""
        return await self._get(
            f"/mpc/policies/{policy_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def update_policy(
        self,
        policy_id: str,
        *,
        name: str | NotGiven = NOT_GIVEN,
        rules: List[Dict[str, Any]] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Update a policy."""
        return await self._patch(
            f"/mpc/policies/{policy_id}",
            body={
                "name": name,
                "rules": rules,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def delete_policy(
        self,
        policy_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a policy."""
        return await self._delete(
            f"/mpc/policies/{policy_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Webhooks ──────────────────────────────────────────────────────────

    async def list_webhooks(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List webhooks."""
        return await self._get(
            "/mpc/webhooks",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def create_webhook(
        self,
        *,
        url: str,
        events: List[str],
        secret: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a webhook.

        Args:
            url: Webhook endpoint URL.
            events: Events to subscribe to (e.g. "transaction.created",
                    "transaction.signed", "transaction.broadcast",
                    "wallet.created", "policy.triggered").
            secret: HMAC secret for webhook signature verification.
        """
        return await self._post(
            "/mpc/webhooks",
            body={
                "url": url,
                "events": events,
                "secret": secret,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def delete_webhook(
        self,
        webhook_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a webhook."""
        return await self._delete(
            f"/mpc/webhooks/{webhook_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Smart Wallets (Account Abstraction) ───────────────────────────────

    async def list_smart_wallets(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List smart wallets."""
        return await self._get(
            "/mpc/smart-wallets",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def deploy_smart_wallet(
        self,
        *,
        wallet_id: str,
        chain: str,
        type: str | NotGiven = NOT_GIVEN,
        salt: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Deploy a smart wallet (account abstraction).

        Args:
            wallet_id: MPC wallet backing the smart wallet.
            chain: Target chain for deployment.
            type: Smart wallet type - "safe", "light", or "kernel".
            salt: Deterministic deployment salt.
        """
        return await self._post(
            "/mpc/smart-wallets",
            body={
                "wallet_id": wallet_id,
                "chain": chain,
                "type": type,
                "salt": salt,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def retrieve_smart_wallet(
        self,
        smart_wallet_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get smart wallet details."""
        return await self._get(
            f"/mpc/smart-wallets/{smart_wallet_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def execute_smart_wallet(
        self,
        smart_wallet_id: str,
        *,
        calls: List[Dict[str, Any]],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Execute a user operation on a smart wallet.

        Args:
            smart_wallet_id: Smart wallet to execute on.
            calls: Batch of calls to execute (to, value, data).
        """
        return await self._post(
            f"/mpc/smart-wallets/{smart_wallet_id}/execute",
            body={"calls": calls},
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Bridge Signing ────────────────────────────────────────────────────

    async def sign_bridge(
        self,
        *,
        wallet_id: str,
        source_chain: str,
        dest_chain: str,
        token: str,
        amount: str,
        recipient: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Sign a cross-chain bridge transaction.

        Args:
            wallet_id: MPC wallet to sign with.
            source_chain: Source chain identifier.
            dest_chain: Destination chain identifier.
            token: Token address or symbol.
            amount: Amount to bridge.
            recipient: Recipient address on destination chain.
        """
        return await self._post(
            "/mpc/bridge/sign",
            body={
                "wallet_id": wallet_id,
                "source_chain": source_chain,
                "dest_chain": dest_chain,
                "token": token,
                "amount": amount,
                "recipient": recipient,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def bridge_status(
        self,
        tx_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get bridge transaction status."""
        return await self._get(
            f"/mpc/bridge/status/{tx_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ── API Keys ──────────────────────────────────────────────────────────

    async def list_api_keys(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List API keys."""
        return await self._get(
            "/mpc/api-keys",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def create_api_key(
        self,
        *,
        name: str,
        permissions: List[str] | NotGiven = NOT_GIVEN,
        expires_at: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create an API key.

        Args:
            name: Key name.
            permissions: List of permissions for the key.
            expires_at: ISO 8601 expiration timestamp.
        """
        return await self._post(
            "/mpc/api-keys",
            body={
                "name": name,
                "permissions": permissions,
                "expires_at": expires_at,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def delete_api_key(
        self,
        key_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Revoke an API key."""
        return await self._delete(
            f"/mpc/api-keys/{key_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ── Whitelist ─────────────────────────────────────────────────────────

    async def list_whitelist(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List whitelisted addresses."""
        return await self._get(
            "/mpc/whitelist",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def add_to_whitelist(
        self,
        *,
        address: str,
        chain: str,
        label: str | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Add an address to the whitelist.

        Args:
            address: Blockchain address to whitelist.
            chain: Chain the address belongs to.
            label: Human-readable label.
        """
        return await self._post(
            "/mpc/whitelist",
            body={
                "address": address,
                "chain": chain,
                "label": label,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def remove_from_whitelist(
        self,
        whitelist_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Remove an address from the whitelist."""
        return await self._delete(
            f"/mpc/whitelist/{whitelist_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class MPCResourceWithRawResponse:
    def __init__(self, mpc: MPCResource) -> None:
        self._mpc = mpc
        # Status
        self.status = to_raw_response_wrapper(mpc.status)
        # Vaults
        self.list_vaults = to_raw_response_wrapper(mpc.list_vaults)
        self.create_vault = to_raw_response_wrapper(mpc.create_vault)
        self.retrieve_vault = to_raw_response_wrapper(mpc.retrieve_vault)
        self.update_vault = to_raw_response_wrapper(mpc.update_vault)
        self.delete_vault = to_raw_response_wrapper(mpc.delete_vault)
        # Wallets
        self.list_wallets = to_raw_response_wrapper(mpc.list_wallets)
        self.create_wallet = to_raw_response_wrapper(mpc.create_wallet)
        self.retrieve_wallet = to_raw_response_wrapper(mpc.retrieve_wallet)
        self.delete_wallet = to_raw_response_wrapper(mpc.delete_wallet)
        # Transactions
        self.list_transactions = to_raw_response_wrapper(mpc.list_transactions)
        self.create_transaction = to_raw_response_wrapper(mpc.create_transaction)
        self.retrieve_transaction = to_raw_response_wrapper(mpc.retrieve_transaction)
        self.approve_transaction = to_raw_response_wrapper(mpc.approve_transaction)
        self.reject_transaction = to_raw_response_wrapper(mpc.reject_transaction)
        self.broadcast_transaction = to_raw_response_wrapper(mpc.broadcast_transaction)
        # Policies
        self.list_policies = to_raw_response_wrapper(mpc.list_policies)
        self.create_policy = to_raw_response_wrapper(mpc.create_policy)
        self.retrieve_policy = to_raw_response_wrapper(mpc.retrieve_policy)
        self.update_policy = to_raw_response_wrapper(mpc.update_policy)
        self.delete_policy = to_raw_response_wrapper(mpc.delete_policy)
        # Webhooks
        self.list_webhooks = to_raw_response_wrapper(mpc.list_webhooks)
        self.create_webhook = to_raw_response_wrapper(mpc.create_webhook)
        self.delete_webhook = to_raw_response_wrapper(mpc.delete_webhook)
        # Smart Wallets
        self.list_smart_wallets = to_raw_response_wrapper(mpc.list_smart_wallets)
        self.deploy_smart_wallet = to_raw_response_wrapper(mpc.deploy_smart_wallet)
        self.retrieve_smart_wallet = to_raw_response_wrapper(mpc.retrieve_smart_wallet)
        self.execute_smart_wallet = to_raw_response_wrapper(mpc.execute_smart_wallet)
        # Bridge
        self.sign_bridge = to_raw_response_wrapper(mpc.sign_bridge)
        self.bridge_status = to_raw_response_wrapper(mpc.bridge_status)
        # API Keys
        self.list_api_keys = to_raw_response_wrapper(mpc.list_api_keys)
        self.create_api_key = to_raw_response_wrapper(mpc.create_api_key)
        self.delete_api_key = to_raw_response_wrapper(mpc.delete_api_key)
        # Whitelist
        self.list_whitelist = to_raw_response_wrapper(mpc.list_whitelist)
        self.add_to_whitelist = to_raw_response_wrapper(mpc.add_to_whitelist)
        self.remove_from_whitelist = to_raw_response_wrapper(mpc.remove_from_whitelist)


class AsyncMPCResourceWithRawResponse:
    def __init__(self, mpc: AsyncMPCResource) -> None:
        self._mpc = mpc
        # Status
        self.status = async_to_raw_response_wrapper(mpc.status)
        # Vaults
        self.list_vaults = async_to_raw_response_wrapper(mpc.list_vaults)
        self.create_vault = async_to_raw_response_wrapper(mpc.create_vault)
        self.retrieve_vault = async_to_raw_response_wrapper(mpc.retrieve_vault)
        self.update_vault = async_to_raw_response_wrapper(mpc.update_vault)
        self.delete_vault = async_to_raw_response_wrapper(mpc.delete_vault)
        # Wallets
        self.list_wallets = async_to_raw_response_wrapper(mpc.list_wallets)
        self.create_wallet = async_to_raw_response_wrapper(mpc.create_wallet)
        self.retrieve_wallet = async_to_raw_response_wrapper(mpc.retrieve_wallet)
        self.delete_wallet = async_to_raw_response_wrapper(mpc.delete_wallet)
        # Transactions
        self.list_transactions = async_to_raw_response_wrapper(mpc.list_transactions)
        self.create_transaction = async_to_raw_response_wrapper(mpc.create_transaction)
        self.retrieve_transaction = async_to_raw_response_wrapper(mpc.retrieve_transaction)
        self.approve_transaction = async_to_raw_response_wrapper(mpc.approve_transaction)
        self.reject_transaction = async_to_raw_response_wrapper(mpc.reject_transaction)
        self.broadcast_transaction = async_to_raw_response_wrapper(mpc.broadcast_transaction)
        # Policies
        self.list_policies = async_to_raw_response_wrapper(mpc.list_policies)
        self.create_policy = async_to_raw_response_wrapper(mpc.create_policy)
        self.retrieve_policy = async_to_raw_response_wrapper(mpc.retrieve_policy)
        self.update_policy = async_to_raw_response_wrapper(mpc.update_policy)
        self.delete_policy = async_to_raw_response_wrapper(mpc.delete_policy)
        # Webhooks
        self.list_webhooks = async_to_raw_response_wrapper(mpc.list_webhooks)
        self.create_webhook = async_to_raw_response_wrapper(mpc.create_webhook)
        self.delete_webhook = async_to_raw_response_wrapper(mpc.delete_webhook)
        # Smart Wallets
        self.list_smart_wallets = async_to_raw_response_wrapper(mpc.list_smart_wallets)
        self.deploy_smart_wallet = async_to_raw_response_wrapper(mpc.deploy_smart_wallet)
        self.retrieve_smart_wallet = async_to_raw_response_wrapper(mpc.retrieve_smart_wallet)
        self.execute_smart_wallet = async_to_raw_response_wrapper(mpc.execute_smart_wallet)
        # Bridge
        self.sign_bridge = async_to_raw_response_wrapper(mpc.sign_bridge)
        self.bridge_status = async_to_raw_response_wrapper(mpc.bridge_status)
        # API Keys
        self.list_api_keys = async_to_raw_response_wrapper(mpc.list_api_keys)
        self.create_api_key = async_to_raw_response_wrapper(mpc.create_api_key)
        self.delete_api_key = async_to_raw_response_wrapper(mpc.delete_api_key)
        # Whitelist
        self.list_whitelist = async_to_raw_response_wrapper(mpc.list_whitelist)
        self.add_to_whitelist = async_to_raw_response_wrapper(mpc.add_to_whitelist)
        self.remove_from_whitelist = async_to_raw_response_wrapper(mpc.remove_from_whitelist)


class MPCResourceWithStreamingResponse:
    def __init__(self, mpc: MPCResource) -> None:
        self._mpc = mpc
        # Status
        self.status = to_streamed_response_wrapper(mpc.status)
        # Vaults
        self.list_vaults = to_streamed_response_wrapper(mpc.list_vaults)
        self.create_vault = to_streamed_response_wrapper(mpc.create_vault)
        self.retrieve_vault = to_streamed_response_wrapper(mpc.retrieve_vault)
        self.update_vault = to_streamed_response_wrapper(mpc.update_vault)
        self.delete_vault = to_streamed_response_wrapper(mpc.delete_vault)
        # Wallets
        self.list_wallets = to_streamed_response_wrapper(mpc.list_wallets)
        self.create_wallet = to_streamed_response_wrapper(mpc.create_wallet)
        self.retrieve_wallet = to_streamed_response_wrapper(mpc.retrieve_wallet)
        self.delete_wallet = to_streamed_response_wrapper(mpc.delete_wallet)
        # Transactions
        self.list_transactions = to_streamed_response_wrapper(mpc.list_transactions)
        self.create_transaction = to_streamed_response_wrapper(mpc.create_transaction)
        self.retrieve_transaction = to_streamed_response_wrapper(mpc.retrieve_transaction)
        self.approve_transaction = to_streamed_response_wrapper(mpc.approve_transaction)
        self.reject_transaction = to_streamed_response_wrapper(mpc.reject_transaction)
        self.broadcast_transaction = to_streamed_response_wrapper(mpc.broadcast_transaction)
        # Policies
        self.list_policies = to_streamed_response_wrapper(mpc.list_policies)
        self.create_policy = to_streamed_response_wrapper(mpc.create_policy)
        self.retrieve_policy = to_streamed_response_wrapper(mpc.retrieve_policy)
        self.update_policy = to_streamed_response_wrapper(mpc.update_policy)
        self.delete_policy = to_streamed_response_wrapper(mpc.delete_policy)
        # Webhooks
        self.list_webhooks = to_streamed_response_wrapper(mpc.list_webhooks)
        self.create_webhook = to_streamed_response_wrapper(mpc.create_webhook)
        self.delete_webhook = to_streamed_response_wrapper(mpc.delete_webhook)
        # Smart Wallets
        self.list_smart_wallets = to_streamed_response_wrapper(mpc.list_smart_wallets)
        self.deploy_smart_wallet = to_streamed_response_wrapper(mpc.deploy_smart_wallet)
        self.retrieve_smart_wallet = to_streamed_response_wrapper(mpc.retrieve_smart_wallet)
        self.execute_smart_wallet = to_streamed_response_wrapper(mpc.execute_smart_wallet)
        # Bridge
        self.sign_bridge = to_streamed_response_wrapper(mpc.sign_bridge)
        self.bridge_status = to_streamed_response_wrapper(mpc.bridge_status)
        # API Keys
        self.list_api_keys = to_streamed_response_wrapper(mpc.list_api_keys)
        self.create_api_key = to_streamed_response_wrapper(mpc.create_api_key)
        self.delete_api_key = to_streamed_response_wrapper(mpc.delete_api_key)
        # Whitelist
        self.list_whitelist = to_streamed_response_wrapper(mpc.list_whitelist)
        self.add_to_whitelist = to_streamed_response_wrapper(mpc.add_to_whitelist)
        self.remove_from_whitelist = to_streamed_response_wrapper(mpc.remove_from_whitelist)


class AsyncMPCResourceWithStreamingResponse:
    def __init__(self, mpc: AsyncMPCResource) -> None:
        self._mpc = mpc
        # Status
        self.status = async_to_streamed_response_wrapper(mpc.status)
        # Vaults
        self.list_vaults = async_to_streamed_response_wrapper(mpc.list_vaults)
        self.create_vault = async_to_streamed_response_wrapper(mpc.create_vault)
        self.retrieve_vault = async_to_streamed_response_wrapper(mpc.retrieve_vault)
        self.update_vault = async_to_streamed_response_wrapper(mpc.update_vault)
        self.delete_vault = async_to_streamed_response_wrapper(mpc.delete_vault)
        # Wallets
        self.list_wallets = async_to_streamed_response_wrapper(mpc.list_wallets)
        self.create_wallet = async_to_streamed_response_wrapper(mpc.create_wallet)
        self.retrieve_wallet = async_to_streamed_response_wrapper(mpc.retrieve_wallet)
        self.delete_wallet = async_to_streamed_response_wrapper(mpc.delete_wallet)
        # Transactions
        self.list_transactions = async_to_streamed_response_wrapper(mpc.list_transactions)
        self.create_transaction = async_to_streamed_response_wrapper(mpc.create_transaction)
        self.retrieve_transaction = async_to_streamed_response_wrapper(mpc.retrieve_transaction)
        self.approve_transaction = async_to_streamed_response_wrapper(mpc.approve_transaction)
        self.reject_transaction = async_to_streamed_response_wrapper(mpc.reject_transaction)
        self.broadcast_transaction = async_to_streamed_response_wrapper(mpc.broadcast_transaction)
        # Policies
        self.list_policies = async_to_streamed_response_wrapper(mpc.list_policies)
        self.create_policy = async_to_streamed_response_wrapper(mpc.create_policy)
        self.retrieve_policy = async_to_streamed_response_wrapper(mpc.retrieve_policy)
        self.update_policy = async_to_streamed_response_wrapper(mpc.update_policy)
        self.delete_policy = async_to_streamed_response_wrapper(mpc.delete_policy)
        # Webhooks
        self.list_webhooks = async_to_streamed_response_wrapper(mpc.list_webhooks)
        self.create_webhook = async_to_streamed_response_wrapper(mpc.create_webhook)
        self.delete_webhook = async_to_streamed_response_wrapper(mpc.delete_webhook)
        # Smart Wallets
        self.list_smart_wallets = async_to_streamed_response_wrapper(mpc.list_smart_wallets)
        self.deploy_smart_wallet = async_to_streamed_response_wrapper(mpc.deploy_smart_wallet)
        self.retrieve_smart_wallet = async_to_streamed_response_wrapper(mpc.retrieve_smart_wallet)
        self.execute_smart_wallet = async_to_streamed_response_wrapper(mpc.execute_smart_wallet)
        # Bridge
        self.sign_bridge = async_to_streamed_response_wrapper(mpc.sign_bridge)
        self.bridge_status = async_to_streamed_response_wrapper(mpc.bridge_status)
        # API Keys
        self.list_api_keys = async_to_streamed_response_wrapper(mpc.list_api_keys)
        self.create_api_key = async_to_streamed_response_wrapper(mpc.create_api_key)
        self.delete_api_key = async_to_streamed_response_wrapper(mpc.delete_api_key)
        # Whitelist
        self.list_whitelist = async_to_streamed_response_wrapper(mpc.list_whitelist)
        self.add_to_whitelist = async_to_streamed_response_wrapper(mpc.add_to_whitelist)
        self.remove_from_whitelist = async_to_streamed_response_wrapper(mpc.remove_from_whitelist)
