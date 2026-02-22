"""Hanzo Web3 Client - Sync and Async clients for blockchain APIs."""

from __future__ import annotations

import os
from typing import Any, Optional

import httpx
from pydantic import BaseModel

from hanzo_web3.types import Chain, Network
from hanzo_web3.exceptions import HanzoWeb3Error, AuthenticationError


class ClientConfig(BaseModel):
    """Client configuration."""

    api_key: str
    base_url: str = "https://api.web3.hanzo.ai"
    timeout: float = 30.0
    max_retries: int = 3


class RPCClient:
    """JSON-RPC client for blockchain interactions."""

    def __init__(self, http_client: httpx.AsyncClient, config: ClientConfig):
        self._http = http_client
        self._config = config

    async def call(
        self,
        method: str,
        params: list[Any] | None = None,
        chain: str = "ethereum",
        network: str = "mainnet",
    ) -> Any:
        """Execute JSON-RPC call.

        Args:
            method: RPC method name (e.g., "eth_blockNumber")
            params: RPC parameters
            chain: Chain name (ethereum, polygon, arbitrum, etc.)
            network: Network name (mainnet, sepolia, etc.)

        Returns:
            RPC result
        """
        response = await self._http.post(
            f"{self._config.base_url}/v1/rpc/{chain}/{network}",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": method,
                "params": params or [],
            },
            headers={"X-API-Key": self._config.api_key},
        )

        if response.status_code == 401:
            raise AuthenticationError("Invalid API key")

        data = response.json()
        if "error" in data:
            raise HanzoWeb3Error(f"RPC error: {data['error']}")

        return data.get("result")

    async def eth_block_number(
        self, chain: str = "ethereum", network: str = "mainnet"
    ) -> int:
        """Get latest block number."""
        result = await self.call("eth_blockNumber", chain=chain, network=network)
        return int(result, 16)

    async def eth_get_balance(
        self, address: str, chain: str = "ethereum", network: str = "mainnet"
    ) -> int:
        """Get ETH balance for address."""
        result = await self.call(
            "eth_getBalance", [address, "latest"], chain=chain, network=network
        )
        return int(result, 16)


class TokensClient:
    """Token API client."""

    def __init__(self, http_client: httpx.AsyncClient, config: ClientConfig):
        self._http = http_client
        self._config = config

    async def get_balances(
        self,
        address: str,
        chain: str = "ethereum",
        network: str = "mainnet",
    ) -> list[dict[str, Any]]:
        """Get all token balances for address.

        Args:
            address: Wallet address
            chain: Chain name
            network: Network name

        Returns:
            List of token balances
        """
        response = await self._http.get(
            f"{self._config.base_url}/v1/tokens/{chain}/{network}/balances/{address}",
            headers={"X-API-Key": self._config.api_key},
        )
        return response.json().get("balances", [])

    async def get_metadata(
        self,
        contract_address: str,
        chain: str = "ethereum",
        network: str = "mainnet",
    ) -> dict[str, Any]:
        """Get token metadata.

        Args:
            contract_address: Token contract address
            chain: Chain name
            network: Network name

        Returns:
            Token metadata (name, symbol, decimals, etc.)
        """
        response = await self._http.get(
            f"{self._config.base_url}/v1/tokens/{chain}/{network}/metadata/{contract_address}",
            headers={"X-API-Key": self._config.api_key},
        )
        return response.json()


class NFTsClient:
    """NFT API client."""

    def __init__(self, http_client: httpx.AsyncClient, config: ClientConfig):
        self._http = http_client
        self._config = config

    async def get_owned(
        self,
        address: str,
        chain: str = "ethereum",
        network: str = "mainnet",
    ) -> list[dict[str, Any]]:
        """Get all NFTs owned by address.

        Args:
            address: Wallet address
            chain: Chain name
            network: Network name

        Returns:
            List of owned NFTs
        """
        response = await self._http.get(
            f"{self._config.base_url}/v1/nfts/{chain}/{network}/owned/{address}",
            headers={"X-API-Key": self._config.api_key},
        )
        return response.json().get("nfts", [])

    async def get_metadata(
        self,
        contract_address: str,
        token_id: str,
        chain: str = "ethereum",
        network: str = "mainnet",
    ) -> dict[str, Any]:
        """Get NFT metadata.

        Args:
            contract_address: NFT contract address
            token_id: Token ID
            chain: Chain name
            network: Network name

        Returns:
            NFT metadata
        """
        response = await self._http.get(
            f"{self._config.base_url}/v1/nfts/{chain}/{network}/metadata/{contract_address}/{token_id}",
            headers={"X-API-Key": self._config.api_key},
        )
        return response.json()


class WalletsClient:
    """Smart Wallet (ERC-4337) client."""

    def __init__(self, http_client: httpx.AsyncClient, config: ClientConfig):
        self._http = http_client
        self._config = config

    async def create(
        self,
        owner: str,
        chain: str = "ethereum",
        network: str = "mainnet",
    ) -> dict[str, Any]:
        """Create a new smart wallet.

        Args:
            owner: Owner EOA address
            chain: Chain name
            network: Network name

        Returns:
            Smart wallet details (address, etc.)
        """
        response = await self._http.post(
            f"{self._config.base_url}/v1/wallets/{chain}/{network}/create",
            json={"owner": owner},
            headers={"X-API-Key": self._config.api_key},
        )
        return response.json()

    async def get(
        self,
        address: str,
        chain: str = "ethereum",
        network: str = "mainnet",
    ) -> dict[str, Any]:
        """Get smart wallet details.

        Args:
            address: Smart wallet address
            chain: Chain name
            network: Network name

        Returns:
            Wallet details
        """
        response = await self._http.get(
            f"{self._config.base_url}/v1/wallets/{chain}/{network}/{address}",
            headers={"X-API-Key": self._config.api_key},
        )
        return response.json()


class WebhooksClient:
    """Webhooks client."""

    def __init__(self, http_client: httpx.AsyncClient, config: ClientConfig):
        self._http = http_client
        self._config = config

    async def create(
        self,
        url: str,
        event_type: str,
        chain: str = "ethereum",
        network: str = "mainnet",
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a webhook.

        Args:
            url: Webhook URL
            event_type: Event type (ADDRESS_ACTIVITY, NFT_ACTIVITY, etc.)
            chain: Chain name
            network: Network name
            filters: Event filters

        Returns:
            Webhook details
        """
        response = await self._http.post(
            f"{self._config.base_url}/v1/webhooks",
            json={
                "url": url,
                "event_type": event_type,
                "chain": chain,
                "network": network,
                "filters": filters or {},
            },
            headers={"X-API-Key": self._config.api_key},
        )
        return response.json()

    async def list(self) -> list[dict[str, Any]]:
        """List all webhooks.

        Returns:
            List of webhooks
        """
        response = await self._http.get(
            f"{self._config.base_url}/v1/webhooks",
            headers={"X-API-Key": self._config.api_key},
        )
        return response.json().get("webhooks", [])

    async def delete(self, webhook_id: str) -> bool:
        """Delete a webhook.

        Args:
            webhook_id: Webhook ID

        Returns:
            True if deleted
        """
        response = await self._http.delete(
            f"{self._config.base_url}/v1/webhooks/{webhook_id}",
            headers={"X-API-Key": self._config.api_key},
        )
        return response.status_code == 204


class AsyncClient:
    """Async Hanzo Web3 client.

    Example:
        >>> client = AsyncClient(api_key="hz_live_...")
        >>> balance = await client.tokens.get_balances("0x...")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.web3.hanzo.ai",
        timeout: float = 30.0,
    ):
        """Initialize async client.

        Args:
            api_key: API key (or set HANZO_WEB3_API_KEY env var)
            base_url: API base URL
            timeout: Request timeout in seconds
        """
        api_key = api_key or os.environ.get("HANZO_WEB3_API_KEY")
        if not api_key:
            raise AuthenticationError(
                "API key required. Pass api_key or set HANZO_WEB3_API_KEY env var."
            )

        self._config = ClientConfig(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
        )
        self._http = httpx.AsyncClient(timeout=timeout)

        # Initialize sub-clients
        self.rpc = RPCClient(self._http, self._config)
        self.tokens = TokensClient(self._http, self._config)
        self.nfts = NFTsClient(self._http, self._config)
        self.wallets = WalletsClient(self._http, self._config)
        self.webhooks = WebhooksClient(self._http, self._config)

    async def __aenter__(self) -> "AsyncClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self._http.aclose()

    async def close(self) -> None:
        """Close the client."""
        await self._http.aclose()


class Client:
    """Sync Hanzo Web3 client (wrapper around AsyncClient).

    Example:
        >>> client = Client(api_key="hz_live_...")
        >>> balance = client.rpc.eth_block_number()
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.web3.hanzo.ai",
        timeout: float = 30.0,
    ):
        """Initialize sync client.

        Args:
            api_key: API key (or set HANZO_WEB3_API_KEY env var)
            base_url: API base URL
            timeout: Request timeout in seconds
        """
        import asyncio

        self._async_client = AsyncClient(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
        )
        self._loop = asyncio.new_event_loop()

    def _run(self, coro: Any) -> Any:
        """Run async coroutine synchronously."""
        return self._loop.run_until_complete(coro)

    @property
    def rpc(self) -> "SyncRPCClient":
        return SyncRPCClient(self._async_client.rpc, self._run)

    @property
    def tokens(self) -> "SyncTokensClient":
        return SyncTokensClient(self._async_client.tokens, self._run)

    @property
    def nfts(self) -> "SyncNFTsClient":
        return SyncNFTsClient(self._async_client.nfts, self._run)

    @property
    def wallets(self) -> "SyncWalletsClient":
        return SyncWalletsClient(self._async_client.wallets, self._run)

    @property
    def webhooks(self) -> "SyncWebhooksClient":
        return SyncWebhooksClient(self._async_client.webhooks, self._run)

    def close(self) -> None:
        """Close the client."""
        self._run(self._async_client.close())
        self._loop.close()


# Sync wrapper classes
class SyncRPCClient:
    def __init__(self, async_client: RPCClient, runner: Any):
        self._async = async_client
        self._run = runner

    def call(self, method: str, params: list | None = None, **kwargs: Any) -> Any:
        return self._run(self._async.call(method, params, **kwargs))

    def eth_block_number(self, **kwargs: Any) -> int:
        return self._run(self._async.eth_block_number(**kwargs))

    def eth_get_balance(self, address: str, **kwargs: Any) -> int:
        return self._run(self._async.eth_get_balance(address, **kwargs))


class SyncTokensClient:
    def __init__(self, async_client: TokensClient, runner: Any):
        self._async = async_client
        self._run = runner

    def get_balances(self, address: str, **kwargs: Any) -> list:
        return self._run(self._async.get_balances(address, **kwargs))

    def get_metadata(self, contract_address: str, **kwargs: Any) -> dict:
        return self._run(self._async.get_metadata(contract_address, **kwargs))


class SyncNFTsClient:
    def __init__(self, async_client: NFTsClient, runner: Any):
        self._async = async_client
        self._run = runner

    def get_owned(self, address: str, **kwargs: Any) -> list:
        return self._run(self._async.get_owned(address, **kwargs))

    def get_metadata(self, contract_address: str, token_id: str, **kwargs: Any) -> dict:
        return self._run(self._async.get_metadata(contract_address, token_id, **kwargs))


class SyncWalletsClient:
    def __init__(self, async_client: WalletsClient, runner: Any):
        self._async = async_client
        self._run = runner

    def create(self, owner: str, **kwargs: Any) -> dict:
        return self._run(self._async.create(owner, **kwargs))

    def get(self, address: str, **kwargs: Any) -> dict:
        return self._run(self._async.get(address, **kwargs))


class SyncWebhooksClient:
    def __init__(self, async_client: WebhooksClient, runner: Any):
        self._async = async_client
        self._run = runner

    def create(self, url: str, event_type: str, **kwargs: Any) -> dict:
        return self._run(self._async.create(url, event_type, **kwargs))

    def list(self) -> list:
        return self._run(self._async.list())

    def delete(self, webhook_id: str) -> bool:
        return self._run(self._async.delete(webhook_id))
