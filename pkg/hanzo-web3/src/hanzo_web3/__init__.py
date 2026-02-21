"""Hanzo Web3 SDK - Enterprise Blockchain Infrastructure.

Multi-chain RPC, Token APIs, NFT APIs, Smart Wallets, Webhooks, and more.

Example:
    >>> from hanzo_web3 import Client
    >>> client = Client(api_key="hz_live_...")
    >>> balance = await client.tokens.get_balance("0x...", chain="ethereum")
"""

from hanzo_web3.types import (
    Chain,
    Network,
    Webhook,
    NFTMetadata,
    SmartWallet,
    Transaction,
    TokenBalance,
)
from hanzo_web3.client import Client, AsyncClient
from hanzo_web3.exceptions import (
    HanzoWeb3Error,
    RateLimitError,
    AuthenticationError,
    ChainNotSupportedError,
)

__version__ = "0.1.0"
__all__ = [
    # Clients
    "Client",
    "AsyncClient",
    # Types
    "Chain",
    "Network",
    "TokenBalance",
    "NFTMetadata",
    "Transaction",
    "Webhook",
    "SmartWallet",
    # Exceptions
    "HanzoWeb3Error",
    "AuthenticationError",
    "RateLimitError",
    "ChainNotSupportedError",
]
