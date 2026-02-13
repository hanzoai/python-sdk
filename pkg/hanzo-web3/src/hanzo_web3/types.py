"""Hanzo Web3 SDK types."""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel


class Chain(str, Enum):
    """Supported blockchains."""

    ETHEREUM = "ethereum"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    BASE = "base"
    AVALANCHE = "avalanche"
    BNB = "bnb"
    LUX = "lux"
    SOLANA = "solana"
    BITCOIN = "bitcoin"


class Network(str, Enum):
    """Network types."""

    MAINNET = "mainnet"
    TESTNET = "testnet"
    SEPOLIA = "sepolia"
    GOERLI = "goerli"
    HOLESKY = "holesky"
    DEVNET = "devnet"


class TokenBalance(BaseModel):
    """Token balance."""

    contract_address: str
    symbol: str
    name: str
    decimals: int
    balance: str
    balance_formatted: float
    logo_uri: Optional[str] = None
    price_usd: Optional[float] = None
    value_usd: Optional[float] = None


class NFTMetadata(BaseModel):
    """NFT metadata."""

    contract_address: str
    token_id: str
    name: Optional[str] = None
    description: Optional[str] = None
    image_uri: Optional[str] = None
    animation_uri: Optional[str] = None
    external_uri: Optional[str] = None
    attributes: list[dict[str, Any]] = []
    token_standard: str = "ERC721"


class Transaction(BaseModel):
    """Transaction details."""

    hash: str
    block_number: int
    block_hash: str
    from_address: str
    to_address: Optional[str] = None
    value: str
    gas: int
    gas_price: str
    gas_used: Optional[int] = None
    nonce: int
    status: int = 1  # 1 = success, 0 = failed
    timestamp: Optional[int] = None


class Webhook(BaseModel):
    """Webhook configuration."""

    id: str
    url: str
    event_type: str
    chain: str
    network: str
    filters: dict[str, Any] = {}
    active: bool = True
    created_at: str


class WebhookEventType(str, Enum):
    """Webhook event types."""

    ADDRESS_ACTIVITY = "ADDRESS_ACTIVITY"
    MINED_TRANSACTION = "MINED_TRANSACTION"
    NFT_ACTIVITY = "NFT_ACTIVITY"
    TOKEN_TRANSFER = "TOKEN_TRANSFER"
    INTERNAL_TRANSFER = "INTERNAL_TRANSFER"
    NEW_BLOCK = "NEW_BLOCK"


class SmartWallet(BaseModel):
    """Smart wallet (ERC-4337)."""

    address: str
    owner: str
    chain: str
    network: str
    factory: str
    is_deployed: bool = False
    nonce: int = 0
    created_at: str


class UserOperation(BaseModel):
    """ERC-4337 User Operation."""

    sender: str
    nonce: str
    init_code: str = "0x"
    call_data: str
    call_gas_limit: str
    verification_gas_limit: str
    pre_verification_gas: str
    max_fee_per_gas: str
    max_priority_fee_per_gas: str
    paymaster_and_data: str = "0x"
    signature: str = "0x"


class GasEstimate(BaseModel):
    """Gas price estimate."""

    chain: str
    network: str
    base_fee: str
    max_fee: str
    max_priority_fee: str
    gas_price: str  # Legacy gas price
    timestamp: int
