"""Web3-enabled agent with wallet and TEE support."""

from typing import Any, Dict, Optional
from dataclasses import dataclass

from .tee import (
    TEEConfig,
    TEEProvider,
    ConfidentialAgent,
    create_attestation_verifier_tool,
)
from .agent import Agent, InferenceResult
from .state import State
from .wallet import AgentWallet, Transaction, WalletConfig, create_wallet_tool


@dataclass
class Web3AgentConfig:
    """Configuration for Web3-enabled agents."""

    # Wallet configuration
    wallet_enabled: bool = False
    wallet_config: Optional[WalletConfig] = None

    # TEE configuration
    tee_enabled: bool = False
    tee_config: Optional[TEEConfig] = None
    tee_provider: TEEProvider = TEEProvider.MOCK

    # Economic parameters
    min_payment_eth: float = 0.001  # Minimum payment to accept
    task_price_eth: float = 0.01  # Default price for tasks
    reputation_threshold: float = 0.8  # Min reputation to work with

    # On-chain identity
    agent_nft_address: Optional[str] = None
    reputation_contract: Optional[str] = None


class Web3Agent(Agent):
    """Agent with Web3 capabilities including wallet and TEE support."""

    def __init__(
        self,
        name: str,
        description: str,
        web3_config: Optional[Web3AgentConfig] = None,
        **kwargs,
    ):
        """Initialize Web3-enabled agent.

        Args:
            name: Agent name
            description: Agent description
            web3_config: Web3 configuration
            **kwargs: Additional agent parameters
        """
        super().__init__(**kwargs)
        self.name = name
        self.description = description
        self.web3_config = web3_config or Web3AgentConfig()

        # Initialize wallet if enabled
        self.wallet: Optional[AgentWallet] = None
        if self.web3_config.wallet_enabled:
            wallet_config = self.web3_config.wallet_config or WalletConfig()
            self.wallet = AgentWallet(wallet_config)

            # Add wallet tool to agent's tools
            WalletTool = create_wallet_tool()
            self.wallet_tool = WalletTool(self.wallet)
            if not hasattr(self, "tools"):
                self.tools = []
            self.tools.append(self.wallet_tool)

        # Initialize TEE wrapper if enabled
        self.confidential_agent: Optional[ConfidentialAgent] = None
        if self.web3_config.tee_enabled:
            self.confidential_agent = ConfidentialAgent(
                self, self.web3_config.tee_config
            )

            # Add attestation verifier tool
            AttestationTool = create_attestation_verifier_tool()
            self.attestation_tool = AttestationTool()
            if not hasattr(self, "tools"):
                self.tools = []
            self.tools.append(self.attestation_tool)

        # Track economic activity
        self.earnings: float = 0.0
        self.spending: float = 0.0
        self.completed_tasks: int = 0
        self.reputation_score: float = 1.0

    @property
    def address(self) -> Optional[str]:
        """Get agent's blockchain address."""
        return self.wallet.address if self.wallet else None

    @property
    def balance_eth(self) -> float:
        """Get wallet balance in ETH."""
        if not self.wallet:
            return 0.0
        return float(self.wallet.balance) / 10**18

    async def request_payment(
        self, from_address: str, amount_eth: float, task_description: str
    ) -> Dict[str, Any]:
        """Request payment for a task.

        Args:
            from_address: Payer's address
            amount_eth: Payment amount in ETH
            task_description: Description of the task

        Returns:
            Payment request details
        """
        if not self.wallet:
            return {"error": "Wallet not enabled"}

        if amount_eth < self.web3_config.min_payment_eth:
            return {
                "error": f"Payment too low. Minimum: {self.web3_config.min_payment_eth} ETH"
            }

        return {
            "to": self.wallet.address,
            "amount_eth": amount_eth,
            "task": task_description,
            "request_id": f"req_{self.name}_{self.completed_tasks + 1}",
        }

    async def verify_payment(self, tx_hash: str, expected_amount_eth: float) -> bool:
        """Verify a payment was received.

        In a real implementation, this would check the blockchain.
        For now, we'll use a simplified version.
        """
        # TODO: Implement blockchain verification
        # For now, just track it
        self.earnings += expected_amount_eth
        return True

    async def pay_agent(
        self, to_address: str, amount_eth: float, reason: str
    ) -> Optional[Transaction]:
        """Pay another agent.

        Args:
            to_address: Recipient agent's address
            amount_eth: Payment amount
            reason: Reason for payment

        Returns:
            Transaction object if successful
        """
        if not self.wallet:
            print("Wallet not enabled")
            return None

        if amount_eth > self.balance_eth:
            print(f"Insufficient balance. Have: {self.balance_eth}, Need: {amount_eth}")
            return None

        try:
            tx = self.wallet.send_payment(to_address, amount_eth, reason)
            self.spending += amount_eth
            return tx
        except Exception as e:
            print(f"Payment failed: {e}")
            return None

    async def execute_confidential(
        self, task_code: str, inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute task in TEE for confidentiality.

        Args:
            task_code: Python code to execute
            inputs: Input data for the task

        Returns:
            Execution result with attestation
        """
        if not self.confidential_agent:
            return {"error": "TEE not enabled"}

        result = self.confidential_agent.execute_confidential(task_code, inputs)

        return result

    async def run(self, state: State, history, network) -> InferenceResult:
        """Execute agent with Web3 enhancements.

        This adds economic and TEE considerations to agent execution.
        """
        # Check if this is a paid task
        task_payment = state.get("task_payment", 0)
        if task_payment > 0:
            # Verify payment before proceeding
            tx_hash = state.get("payment_tx")
            if tx_hash:
                verified = await self.verify_payment(tx_hash, task_payment)
                if not verified:
                    return InferenceResult(
                        agent=self.name,
                        content="Payment verification failed. Cannot proceed with task.",
                        metadata={"payment_required": True},
                    )

        # Check if confidential execution is requested
        if state.get("require_tee", False) and self.confidential_agent:
            # Execute in TEE
            task_code = state.get("task_code", "")
            task_inputs = state.get("task_inputs", {})

            tee_result = await self.execute_confidential(task_code, task_inputs)

            return InferenceResult(
                agent=self.name,
                content="Task executed in TEE",
                metadata={
                    "tee_result": tee_result,
                    "attestation": tee_result.get("attestation"),
                },
            )

        # Regular execution - must be implemented by subclass
        return await self._run_impl(state, history, network)

    async def _run_impl(self, state: State, history, network) -> InferenceResult:
        """Actual agent implementation - override in subclass."""
        return InferenceResult(
            agent=self.name,
            content=f"{self.name} is ready to work. Balance: {self.balance_eth:.4f} ETH",
        )

    def update_reputation(self, delta: float):
        """Update agent's reputation score.

        Args:
            delta: Change in reputation (-1 to 1)
        """
        self.reputation_score = max(0, min(1, self.reputation_score + delta))

    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics."""
        stats = {
            "name": self.name,
            "address": self.address,
            "balance_eth": self.balance_eth,
            "earnings_eth": self.earnings,
            "spending_eth": self.spending,
            "completed_tasks": self.completed_tasks,
            "reputation": self.reputation_score,
            "wallet_enabled": self.web3_config.wallet_enabled,
            "tee_enabled": self.web3_config.tee_enabled,
        }

        if self.confidential_agent:
            stats["attestations"] = len(
                self.confidential_agent.get_attestation_history()
            )

        return stats


# Example Web3-enabled agents


class DataProviderAgent(Web3Agent):
    """Agent that provides data for payment."""

    def __init__(self, **kwargs):
        super().__init__(
            name="data_provider",
            description="Provides high-quality data for AI training",
            **kwargs,
        )
        self.data_catalog = {
            "weather": {"price_eth": 0.01, "size_mb": 100},
            "finance": {"price_eth": 0.05, "size_mb": 500},
            "research": {"price_eth": 0.1, "size_mb": 1000},
        }

    async def _run_impl(self, state: State, history, network) -> InferenceResult:
        """Provide data based on request."""
        request = state.get("data_request", {})
        dataset = request.get("dataset")

        if dataset not in self.data_catalog:
            return InferenceResult(
                agent=self.name,
                content=f"Unknown dataset: {dataset}. Available: {list(self.data_catalog.keys())}",
            )

        data_info = self.data_catalog[dataset]

        # Request payment
        payment_request = await self.request_payment(
            from_address=request.get("requester_address", ""),
            amount_eth=data_info["price_eth"],
            task_description=f"Provide {dataset} dataset",
        )

        return InferenceResult(
            agent=self.name,
            content=f"Dataset {dataset} available for {data_info['price_eth']} ETH",
            metadata={"payment_request": payment_request, "data_info": data_info},
        )


class ComputeProviderAgent(Web3Agent):
    """Agent that provides GPU compute for payment."""

    def __init__(self, **kwargs):
        super().__init__(
            name="compute_provider",
            description="Provides GPU compute resources",
            web3_config=Web3AgentConfig(
                wallet_enabled=True,
                tee_enabled=True,
                task_price_eth=0.1,  # Per hour
            ),
            **kwargs,
        )
        self.gpu_specs = {"model": "NVIDIA H100", "memory_gb": 80, "tflops": 1000}

    async def _run_impl(self, state: State, history, network) -> InferenceResult:
        """Offer compute resources."""
        compute_request = state.get("compute_request", {})
        duration_hours = compute_request.get("duration_hours", 1)

        total_price = self.web3_config.task_price_eth * duration_hours

        # Create compute offer
        offer = {
            "provider": self.address,
            "gpu": self.gpu_specs,
            "price_per_hour_eth": self.web3_config.task_price_eth,
            "total_price_eth": total_price,
            "tee_enabled": self.web3_config.tee_enabled,
            "min_duration_hours": 0.1,
            "max_duration_hours": 24,
        }

        # If TEE is requested, provide attestation
        if compute_request.get("require_tee", False) and self.confidential_agent:
            dummy_attestation = self.confidential_agent.tee_executor.get_attestation()
            offer["attestation"] = dummy_attestation.to_dict()

        return InferenceResult(
            agent=self.name,
            content=f"GPU compute available: {self.gpu_specs['model']} for {total_price} ETH",
            metadata={"compute_offer": offer},
        )
