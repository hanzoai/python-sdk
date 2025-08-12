"""Wallet and Web3 integration for agents.

This module provides wallet capabilities for agents to interact with blockchain networks,
enabling on-chain payments, identity, and decentralized coordination.
"""

import hashlib
import secrets
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from eth_account import Account
from eth_account.hdaccount import generate_mnemonic

# Try to import web3 dependencies
try:
    from web3 import Web3
    from eth_typing import HexStr, Address
    from web3.types import Wei, TxParams

    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    Web3 = None
    TxParams = Dict[str, Any]
    Wei = int
    Address = str
    HexStr = str


@dataclass
class WalletConfig:
    """Configuration for agent wallet."""

    private_key: Optional[str] = None
    mnemonic: Optional[str] = None
    account_index: int = 0
    network_rpc: str = "http://localhost:8545"
    chain_id: int = 31337  # Default to local hardhat/anvil
    gas_limit: int = 3000000
    gas_price_gwei: int = 20

    def __post_init__(self):
        """Validate configuration."""
        if not self.private_key and not self.mnemonic:
            # Generate a new random private key if none provided
            self.private_key = "0x" + secrets.token_hex(32)


@dataclass
class Transaction:
    """Represents a blockchain transaction."""

    hash: str
    from_address: str
    to_address: str
    value: Wei
    gas_used: Optional[int] = None
    status: Optional[bool] = None
    block_number: Optional[int] = None


class WalletInterface(ABC):
    """Abstract interface for wallet implementations."""

    @abstractmethod
    def get_address(self) -> str:
        """Get the wallet's address."""
        pass

    @abstractmethod
    def get_balance(self) -> Wei:
        """Get the wallet's balance in Wei."""
        pass

    @abstractmethod
    def sign_message(self, message: str) -> str:
        """Sign a message with the wallet's private key."""
        pass

    @abstractmethod
    def send_transaction(
        self,
        to: str,
        value: Wei,
        data: Optional[bytes] = None,
        gas_limit: Optional[int] = None,
        gas_price: Optional[Wei] = None,
    ) -> Transaction:
        """Send a transaction."""
        pass

    @abstractmethod
    def call_contract(
        self, contract_address: str, function_signature: str, *args, **kwargs
    ) -> Any:
        """Call a smart contract function."""
        pass


class Web3Wallet(WalletInterface):
    """Web3-based wallet implementation."""

    def __init__(self, config: WalletConfig):
        """Initialize Web3 wallet."""
        if not WEB3_AVAILABLE:
            raise ImportError(
                "Web3 dependencies not available. Install with: pip install web3 eth-account"
            )

        self.config = config
        self.w3 = Web3(Web3.HTTPProvider(config.network_rpc))

        # Initialize account from private key or mnemonic
        if config.private_key:
            self.account = Account.from_key(config.private_key)
        elif config.mnemonic:
            # Derive account from mnemonic at given index
            Account.enable_unaudited_hdwallet_features()
            self.account = Account.from_mnemonic(
                config.mnemonic, account_path=f"m/44'/60'/0'/0/{config.account_index}"
            )
        else:
            raise ValueError("Either private_key or mnemonic must be provided")

        # Ensure connection
        if not self.w3.is_connected():
            raise ConnectionError(f"Cannot connect to {config.network_rpc}")

    def get_address(self) -> str:
        """Get the wallet's address."""
        return self.account.address

    def get_balance(self) -> Wei:
        """Get the wallet's balance in Wei."""
        return self.w3.eth.get_balance(self.account.address)

    def sign_message(self, message: str) -> str:
        """Sign a message with the wallet's private key."""
        message_hash = hashlib.sha256(message.encode()).digest()
        signed = self.account.signHash(message_hash)
        return signed.signature.hex()

    def send_transaction(
        self,
        to: str,
        value: Wei,
        data: Optional[bytes] = None,
        gas_limit: Optional[int] = None,
        gas_price: Optional[Wei] = None,
    ) -> Transaction:
        """Send a transaction."""
        # Build transaction
        tx: TxParams = {
            "from": self.account.address,
            "to": to,
            "value": value,
            "gas": gas_limit or self.config.gas_limit,
            "gasPrice": gas_price or Web3.to_wei(self.config.gas_price_gwei, "gwei"),
            "nonce": self.w3.eth.get_transaction_count(self.account.address),
            "chainId": self.config.chain_id,
        }

        if data:
            tx["data"] = data

        # Sign transaction
        signed_tx = self.account.sign_transaction(tx)

        # Send transaction
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)

        # Wait for receipt
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        return Transaction(
            hash=tx_hash.hex(),
            from_address=self.account.address,
            to_address=to,
            value=value,
            gas_used=receipt["gasUsed"],
            status=receipt["status"] == 1,
            block_number=receipt["blockNumber"],
        )

    def call_contract(
        self, contract_address: str, function_signature: str, *args, **kwargs
    ) -> Any:
        """Call a smart contract function.

        This is a simplified interface. For complex contracts,
        use web3.py directly with the contract ABI.
        """
        # This would need the contract ABI for proper encoding
        # For now, raise NotImplementedError
        raise NotImplementedError(
            "Contract calls require ABI. Use web3.py directly for now."
        )


class MockWallet(WalletInterface):
    """Mock wallet for testing without blockchain."""

    def __init__(self, config: WalletConfig):
        """Initialize mock wallet."""
        self.config = config
        self.address = (
            "0x"
            + hashlib.sha256(
                (config.private_key or config.mnemonic or "mock").encode()
            ).hexdigest()[:40]
        )
        self.balance = Wei(1000000000000000000000)  # 1000 ETH
        self.transactions: List[Transaction] = []

    def get_address(self) -> str:
        """Get the wallet's address."""
        return self.address

    def get_balance(self) -> Wei:
        """Get the wallet's balance in Wei."""
        return self.balance

    def sign_message(self, message: str) -> str:
        """Sign a message (mock)."""
        return "0x" + hashlib.sha256(f"{self.address}:{message}".encode()).hexdigest()

    def send_transaction(
        self,
        to: str,
        value: Wei,
        data: Optional[bytes] = None,
        gas_limit: Optional[int] = None,
        gas_price: Optional[Wei] = None,
    ) -> Transaction:
        """Send a transaction (mock)."""
        if value > self.balance:
            raise ValueError("Insufficient balance")

        self.balance -= value

        tx = Transaction(
            hash="0x" + secrets.token_hex(32),
            from_address=self.address,
            to_address=to,
            value=value,
            gas_used=21000,
            status=True,
            block_number=len(self.transactions),
        )

        self.transactions.append(tx)
        return tx

    def call_contract(
        self, contract_address: str, function_signature: str, *args, **kwargs
    ) -> Any:
        """Call a smart contract function (mock)."""
        return f"Mock result for {function_signature}"


class AgentWallet:
    """High-level wallet interface for agents."""

    def __init__(self, config: Optional[WalletConfig] = None):
        """Initialize agent wallet."""
        self.config = config or WalletConfig()

        # Use mock wallet if web3 not available or in test mode
        if WEB3_AVAILABLE and not self.config.network_rpc.startswith("mock://"):
            self.wallet = Web3Wallet(self.config)
        else:
            self.wallet = MockWallet(self.config)

    @property
    def address(self) -> str:
        """Get wallet address."""
        return self.wallet.get_address()

    @property
    def balance(self) -> Wei:
        """Get wallet balance."""
        return self.wallet.get_balance()

    def send_payment(
        self, to: str, amount_ether: float, memo: Optional[str] = None
    ) -> Transaction:
        """Send a payment to another address.

        Args:
            to: Recipient address
            amount_ether: Amount in Ether (not Wei)
            memo: Optional memo (stored off-chain)

        Returns:
            Transaction object
        """
        amount_wei = Wei(int(amount_ether * 10**18))

        # Log memo if provided (would be stored in agent memory)
        if memo:
            print(f"Payment memo: {memo}")

        return self.wallet.send_transaction(to, amount_wei)

    def sign_message(self, message: str) -> str:
        """Sign a message for authentication."""
        return self.wallet.sign_message(message)

    def verify_signature(
        self, message: str, signature: str, expected_address: str
    ) -> bool:
        """Verify a signature matches expected address.

        This is a simplified version. Real implementation would
        recover the address from signature and compare.
        """
        # TODO: Implement proper signature verification
        return True  # Placeholder


def generate_shared_mnemonic() -> str:
    """Generate a shared mnemonic for a network of agents."""
    return generate_mnemonic(num_words=12, lang="english")


def derive_agent_wallet(mnemonic: str, agent_index: int, **kwargs) -> AgentWallet:
    """Derive an agent wallet from shared mnemonic.

    Args:
        mnemonic: Shared network mnemonic
        agent_index: Unique index for this agent
        **kwargs: Additional wallet config options

    Returns:
        AgentWallet instance
    """
    config = WalletConfig(mnemonic=mnemonic, account_index=agent_index, **kwargs)
    return AgentWallet(config)


# Tool functions for agent use
def create_wallet_tool():
    """Create a tool that agents can use for wallet operations."""
    from ..tool import Tool

    class WalletTool(Tool):
        """Tool for wallet operations."""

        def __init__(self, wallet: AgentWallet):
            self.wallet = wallet
            self.name = "wallet"
            self.description = "Interact with blockchain wallet"

        async def get_balance(self) -> float:
            """Get wallet balance in Ether."""
            balance_wei = self.wallet.balance
            return float(balance_wei) / 10**18

        async def send_payment(
            self, to_address: str, amount_ether: float, reason: Optional[str] = None
        ) -> str:
            """Send payment to another address.

            Args:
                to_address: Recipient blockchain address
                amount_ether: Amount to send in Ether
                reason: Optional reason for payment

            Returns:
                Transaction hash
            """
            tx = self.wallet.send_payment(to_address, amount_ether, reason)
            return f"Sent {amount_ether} ETH to {to_address}. Tx: {tx.hash}"

        async def get_address(self) -> str:
            """Get this wallet's address."""
            return self.wallet.address

        async def sign_message(self, message: str) -> str:
            """Sign a message for authentication."""
            return self.wallet.sign_message(message)

    return WalletTool
