"""Web3-enabled network orchestration with deterministic execution."""

import json
import time
import hashlib
from typing import Any, Dict, List, Union, Generic, TypeVar, Optional
from dataclasses import dataclass

from .agent import Agent, InferenceResult
from .state import State
from .router import Router, RouterFn
from .wallet import derive_agent_wallet, generate_shared_mnemonic
from .network import Network
from .web3_agent import Web3Agent, Web3AgentConfig
from .marketplace import ServiceType, AgentMarketplace

S = TypeVar("S", bound=State)


@dataclass
class NetworkEconomics:
    """Economic configuration for agent network."""

    # Token economics
    network_token_symbol: str = "AI"
    initial_agent_balance: float = 1000.0  # In network tokens

    # Fee structure
    network_fee_percent: float = 0.01  # 1% network fee
    min_task_fee: float = 0.001  # Minimum fee per task

    # Incentives
    completion_bonus: float = 0.1  # Bonus for completing tasks
    quality_multiplier: float = 2.0  # Multiplier for high-quality work

    # Slashing
    failure_penalty: float = 0.05  # Penalty for failed tasks
    timeout_penalty: float = 0.02  # Penalty for timeouts


@dataclass
class DeterministicConfig:
    """Configuration for deterministic execution."""

    # Seed for randomness
    seed: int = 42

    # Execution order
    enforce_order: bool = True
    allow_parallel: bool = False

    # Reproducibility
    record_all_calls: bool = True
    verify_outputs: bool = True

    # Checkpointing
    checkpoint_every_n_steps: int = 10
    checkpoint_on_completion: bool = True


class Web3Network(Network[S], Generic[S]):
    """Network with Web3 integration and deterministic execution."""

    def __init__(
        self,
        *,
        state: S,
        agents: List[Union[Agent[S], Web3Agent]],
        router: Union[Router, RouterFn[S]],
        shared_mnemonic: Optional[str] = None,
        network_economics: Optional[NetworkEconomics] = None,
        deterministic_config: Optional[DeterministicConfig] = None,
        marketplace: Optional[AgentMarketplace] = None,
        **kwargs,
    ):
        """Initialize Web3-enabled network.

        Args:
            state: Initial state
            agents: List of agents (can be Web3Agent instances)
            router: Router for agent orchestration
            shared_mnemonic: Shared mnemonic for agent wallets
            network_economics: Economic configuration
            deterministic_config: Deterministic execution config
            marketplace: Agent marketplace instance
            **kwargs: Additional Network parameters
        """
        super().__init__(state=state, agents=agents, router=router, **kwargs)

        # Web3 configuration
        self.shared_mnemonic = shared_mnemonic or generate_shared_mnemonic()
        self.network_economics = network_economics or NetworkEconomics()
        self.deterministic_config = deterministic_config or DeterministicConfig()
        self.marketplace = marketplace or globals()["marketplace"]

        # Initialize Web3 agents
        self._initialize_web3_agents()

        # Economic tracking
        self.network_treasury = 0.0
        self.total_fees_collected = 0.0
        self.total_rewards_distributed = 0.0

        # Deterministic execution tracking
        self.execution_log: List[Dict[str, Any]] = []
        self.execution_hash: Optional[str] = None

    def _initialize_web3_agents(self):
        """Initialize Web3 capabilities for agents."""
        for i, agent_class in enumerate(self.agents):
            # Skip if already instantiated
            if isinstance(agent_class, Agent):
                agent = agent_class
            else:
                # Instantiate agent
                agent = agent_class()

            # If it's a Web3Agent, initialize wallet
            if isinstance(agent, Web3Agent):
                if not agent.wallet and agent.web3_config.wallet_enabled:
                    # Derive wallet from shared mnemonic
                    wallet = derive_agent_wallet(
                        self.shared_mnemonic,
                        agent_index=i,
                        network_rpc=(
                            agent.web3_config.wallet_config.network_rpc
                            if agent.web3_config.wallet_config
                            else "mock://localhost"
                        ),
                    )
                    agent.wallet = wallet

                    # Initial funding
                    agent.earnings = self.network_economics.initial_agent_balance

            # Store instance
            self._agent_instances[agent.name] = agent

    async def run(self) -> S:
        """Execute network with Web3 enhancements."""
        if self._running:
            raise RuntimeError("Network already running")

        self._running = True
        start_time = time.time()

        # Set deterministic seed
        import random

        import numpy as np

        random.seed(self.deterministic_config.seed)
        np.random.seed(self.deterministic_config.seed)

        try:
            step = 0
            while self.call_count < self.max_steps:
                # Checkpoint if needed
                if (
                    self.deterministic_config.checkpoint_every_n_steps > 0
                    and step % self.deterministic_config.checkpoint_every_n_steps == 0
                ):
                    await self._checkpoint(f"step_{step}")

                # Route to next agent
                next_agent = await self._route()
                if next_agent is None:
                    break

                # Record pre-execution state
                pre_state = (
                    self.state.to_dict()
                    if hasattr(self.state, "to_dict")
                    else str(self.state)
                )

                # Execute agent
                result = await self._execute_agent(next_agent)

                # Record execution
                self._record_execution(next_agent, result, pre_state)

                # Handle economics if Web3 agent
                if isinstance(next_agent, Web3Agent):
                    await self._handle_agent_economics(next_agent, result)

                # Check marketplace for matches
                await self._check_marketplace(next_agent, result)

                step += 1

            # Final checkpoint
            if self.deterministic_config.checkpoint_on_completion:
                await self._checkpoint("final")

            # Compute execution hash
            self.execution_hash = self._compute_execution_hash()

            # Log summary
            duration = time.time() - start_time
            print(f"\nNetwork execution completed:")
            print(f"  Duration: {duration:.2f}s")
            print(f"  Steps: {step}")
            print(f"  Fees collected: {self.total_fees_collected:.4f}")
            print(f"  Rewards distributed: {self.total_rewards_distributed:.4f}")
            print(f"  Execution hash: {self.execution_hash}")

        finally:
            self._running = False

        return self.state

    def _record_execution(self, agent: Agent, result: InferenceResult, pre_state: Any):
        """Record execution for determinism."""
        if not self.deterministic_config.record_all_calls:
            return

        record = {
            "step": len(self.execution_log),
            "timestamp": time.time(),
            "agent": agent.name,
            "pre_state": pre_state,
            "result": result.to_dict(),
            "post_state": (
                self.state.to_dict()
                if hasattr(self.state, "to_dict")
                else str(self.state)
            ),
        }

        self.execution_log.append(record)

    def _compute_execution_hash(self) -> str:
        """Compute hash of entire execution for verification."""
        # Create deterministic representation
        execution_data = {
            "seed": self.deterministic_config.seed,
            "agents": [a.name for a in self._agent_instances.values()],
            "log": self.execution_log,
        }

        # Compute hash
        json_str = json.dumps(execution_data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()

    async def _handle_agent_economics(self, agent: Web3Agent, result: InferenceResult):
        """Handle economic aspects of agent execution."""
        # Charge network fee
        task_fee = max(
            self.network_economics.min_task_fee,
            agent.web3_config.task_price_eth
            * self.network_economics.network_fee_percent,
        )

        if agent.balance_eth >= task_fee:
            # Deduct fee (in real implementation, this would be on-chain)
            agent.spending += task_fee
            self.network_treasury += task_fee
            self.total_fees_collected += task_fee

        # Reward for completion
        if result.content and "error" not in result.content.lower():
            reward = self.network_economics.completion_bonus

            # Quality bonus
            if result.metadata.get("quality_score", 0.5) > 0.8:
                reward *= self.network_economics.quality_multiplier

            agent.earnings += reward
            self.total_rewards_distributed += reward

            # Update reputation
            agent.update_reputation(0.1)
        else:
            # Penalty for failure
            penalty = self.network_economics.failure_penalty
            agent.spending += penalty
            agent.update_reputation(-0.1)

    async def _check_marketplace(self, agent: Agent, result: InferenceResult):
        """Check marketplace for service opportunities."""
        if not isinstance(agent, Web3Agent):
            return

        # Check if agent advertised any services
        if "service_offer" in result.metadata:
            offer = result.metadata["service_offer"]
            offer_id = self.marketplace.post_offer(
                agent=agent,
                service_type=ServiceType(offer.get("type", "custom")),
                description=offer.get("description", ""),
                price_eth=offer.get("price_eth", 0.01),
                requires_tee=offer.get("requires_tee", False),
            )
            print(f"Agent {agent.name} posted offer: {offer_id}")

        # Check if agent requested any services
        if "service_request" in result.metadata:
            request = result.metadata["service_request"]
            request_id = self.marketplace.post_request(
                agent=agent,
                service_type=ServiceType(request.get("type", "custom")),
                description=request.get("description", ""),
                max_price_eth=request.get("max_price_eth", 0.1),
                requires_tee=request.get("requires_tee", False),
            )
            print(f"Agent {agent.name} posted request: {request_id}")

    async def _checkpoint(self, name: str):
        """Create a checkpoint of current state."""
        if not self.checkpoint_dir:
            return

        checkpoint = {
            "name": name,
            "timestamp": time.time(),
            "state": (
                self.state.to_dict()
                if hasattr(self.state, "to_dict")
                else str(self.state)
            ),
            "history": [entry.to_dict() for entry in self.history.entries],
            "economics": {
                "treasury": self.network_treasury,
                "fees_collected": self.total_fees_collected,
                "rewards_distributed": self.total_rewards_distributed,
            },
            "execution_log": self.execution_log,
        }

        # Save checkpoint
        checkpoint_file = (
            self.checkpoint_dir / f"checkpoint_{name}_{int(time.time())}.json"
        )
        checkpoint_file.parent.mkdir(parents=True, exist_ok=True)

        with open(checkpoint_file, "w") as f:
            json.dump(checkpoint, f, indent=2)

        print(f"Checkpoint saved: {checkpoint_file}")

    def verify_execution(self, other_hash: str) -> bool:
        """Verify execution matches another run.

        Args:
            other_hash: Execution hash from another run

        Returns:
            True if executions match
        """
        if not self.execution_hash:
            self.execution_hash = self._compute_execution_hash()

        return self.execution_hash == other_hash

    def get_agent_stats(self) -> Dict[str, Any]:
        """Get statistics for all agents."""
        stats = {}

        for name, agent in self._agent_instances.items():
            if isinstance(agent, Web3Agent):
                stats[name] = agent.get_stats()
            else:
                stats[name] = {
                    "name": name,
                    "type": "standard",
                    "calls": sum(
                        1 for entry in self.execution_log if entry["agent"] == name
                    ),
                }

        return stats

    def get_network_stats(self) -> Dict[str, Any]:
        """Get network-wide statistics."""
        return {
            "agents": len(self._agent_instances),
            "total_steps": len(self.execution_log),
            "treasury_balance": self.network_treasury,
            "total_fees": self.total_fees_collected,
            "total_rewards": self.total_rewards_distributed,
            "marketplace_stats": self.marketplace.get_stats(),
            "execution_hash": self.execution_hash,
        }


# Factory function for easy network creation
def create_web3_network(
    agents: List[Agent],
    task: str,
    enable_wallets: bool = True,
    enable_tee: bool = False,
    deterministic: bool = True,
) -> Web3Network[State]:
    """Create a Web3-enabled network.

    Args:
        agents: List of agents to include
        task: Initial task/query
        enable_wallets: Enable wallet functionality
        enable_tee: Enable TEE support
        deterministic: Enable deterministic execution

    Returns:
        Configured Web3Network instance
    """
    # Configure agents
    web3_agents = []
    for agent in agents:
        if isinstance(agent, Web3Agent):
            web3_agents.append(agent)
        else:
            # Wrap in Web3Agent
            config = Web3AgentConfig(
                wallet_enabled=enable_wallets, tee_enabled=enable_tee
            )

            class Web3Wrapper(Web3Agent):
                async def _run_impl(self, state, history, network):
                    # Delegate to original agent
                    return await agent.run(state, history, network)

            wrapped = Web3Wrapper(
                name=agent.name,
                description=getattr(agent, "description", ""),
                web3_config=config,
            )
            wrapped.tools = getattr(agent, "tools", [])
            web3_agents.append(wrapped)

    # Create initial state
    state = State()
    state["task"] = task
    state["start_time"] = time.time()

    # Simple sequential router
    from .router import sequential_router

    router = sequential_router([a.name for a in web3_agents])

    # Create network
    return Web3Network(
        state=state,
        agents=web3_agents,
        router=router,
        deterministic_config=DeterministicConfig() if deterministic else None,
    )
