"""Test Web3 integration with hanzo-agents SDK and local compute."""

import pytest

# Import hanzo-agents components
try:
    from hanzo_agents import (
        WEB3_AVAILABLE,
        Tool,
        Agent,
        State,
        Network,
        TEEConfig,
        AgentWallet,
        TEEProvider,
        WalletConfig,
        ConfidentialAgent,
        generate_shared_mnemonic,
    )
    from hanzo_agents.core.web3_agent import Web3Agent, Web3AgentConfig
    from hanzo_agents.core.marketplace import ServiceType, AgentMarketplace
    from hanzo_agents.core.web3_network import Web3Network, create_web3_network

    HANZO_AGENTS_AVAILABLE = True
except ImportError:
    HANZO_AGENTS_AVAILABLE = False

# hanzo-agents is now always available

# Import hanzo-network components
try:
    from hanzo_network import (
        LOCAL_COMPUTE_AVAILABLE,
        ModelConfig,
        ModelProvider,
        InferenceRequest,
        LocalComputeNode,
        LocalComputeOrchestrator,
    )

    HANZO_NETWORK_AVAILABLE = True
except ImportError:
    HANZO_NETWORK_AVAILABLE = False


class TestWeb3Integration:
    """Test Web3 capabilities in hanzo-agents SDK."""

    def test_wallet_creation(self):
        """Test agent wallet creation."""
        # Generate shared mnemonic
        mnemonic = generate_shared_mnemonic()
        assert len(mnemonic.split()) == 12

        # Create wallet config
        config = WalletConfig(mnemonic=mnemonic, account_index=0, network_rpc="mock://localhost")

        # Create wallet
        wallet = AgentWallet(config)
        assert wallet.address is not None
        assert wallet.balance >= 0

    def test_web3_agent_creation(self):
        """Test Web3Agent creation."""
        # Create Web3 config
        web3_config = Web3AgentConfig(wallet_enabled=True, tee_enabled=True, task_price_eth=0.01)

        # Create agent
        agent = Web3Agent(name="test_agent", description="Test Web3 agent", web3_config=web3_config)

        assert agent.name == "test_agent"
        assert agent.wallet is not None
        assert agent.confidential_agent is not None
        assert agent.balance_eth >= 0

    @pytest.mark.asyncio
    async def test_agent_payment(self):
        """Test payment between agents."""
        # Create two agents with wallets
        agent1 = Web3Agent(
            name="payer",
            description="Agent that pays",
            web3_config=Web3AgentConfig(wallet_enabled=True),
        )

        agent2 = Web3Agent(
            name="payee",
            description="Agent that receives payment",
            web3_config=Web3AgentConfig(wallet_enabled=True),
        )

        # Give agent1 some balance
        agent1.earnings = 10.0

        # Request payment
        payment_request = await agent2.request_payment(
            from_address=agent1.address, amount_eth=1.0, task_description="Test service"
        )

        assert payment_request["to"] == agent2.address
        assert payment_request["amount_eth"] == 1.0

        # Make payment (mock)
        if agent1.wallet:
            tx = await agent1.pay_agent(to_address=agent2.address, amount_eth=1.0, reason="Test payment")
            assert tx is not None

    def test_tee_execution(self):
        """Test TEE confidential execution."""
        agent = Web3Agent(
            name="tee_agent",
            description="Agent with TEE",
            web3_config=Web3AgentConfig(tee_enabled=True),
        )

        # Execute confidential task
        task_code = """
result = {"sum": inputs["a"] + inputs["b"]}
"""

        result = agent.confidential_agent.execute_confidential(task_code, {"a": 5, "b": 3})

        assert result["success"] is True
        assert result["result"]["sum"] == 8
        tool_helper.assert_in_result("attestation", result)

    def test_marketplace_interaction(self):
        """Test agent marketplace."""
        marketplace = AgentMarketplace()

        # Create provider agent
        provider = Web3Agent(
            name="provider",
            description="Service provider",
            web3_config=Web3AgentConfig(wallet_enabled=True),
        )

        # Post offer
        offer_id = marketplace.post_offer(
            agent=provider,
            service_type=ServiceType.COMPUTE,
            description="GPU compute for AI",
            price_eth=0.1,
            requires_tee=True,
        )

        assert offer_id.startswith("offer_")
        assert len(marketplace.offers) == 1

        # Create requester agent
        requester = Web3Agent(
            name="requester",
            description="Service requester",
            web3_config=Web3AgentConfig(wallet_enabled=True),
        )

        # Post request
        request_id = marketplace.post_request(
            agent=requester,
            service_type=ServiceType.COMPUTE,
            description="Need GPU for training",
            max_price_eth=0.2,
        )

        # Should auto-match
        assert len(marketplace.matches) == 1
        match = list(marketplace.matches.values())[0]
        assert match.offer.agent_name == "provider"
        assert match.request.requester_name == "requester"


@pytest.mark.skipif(
    not (HANZO_AGENTS_AVAILABLE and HANZO_NETWORK_AVAILABLE),
    reason="Both hanzo-agents and hanzo-network required",
)
class TestLocalComputeIntegration:
    """Test local compute with agent networks."""

    @pytest.mark.asyncio
    async def test_local_compute_node(self):
        """Test local compute node creation."""
        node = LocalComputeNode(
            node_id="test_node",
            wallet_address="0x1234567890123456789012345678901234567890",
        )

        # List models
        models = node.list_models()
        assert len(models) > 0
        assert models[0]["name"] == "hanzo-nano"

        # Create inference request
        request = InferenceRequest(
            request_id="test_001",
            prompt="Hello, world!",
            max_tokens=10,
            max_price_eth=0.001,
        )

        # Process request
        result = await node.process_request(request)
        assert result.request_id == "test_001"
        assert len(result.text) > 0

    @pytest.mark.asyncio
    async def test_compute_marketplace_integration(self):
        """Test compute marketplace with agents."""
        # Create compute node
        node = LocalComputeNode(node_id="gpu_node")

        # Create agent that provides compute
        compute_agent = Web3Agent(
            name="compute_provider",
            description="Provides local AI compute",
            web3_config=Web3AgentConfig(wallet_enabled=True, tee_enabled=True),
        )

        # Link node to agent
        compute_agent.compute_node = node

        # Create marketplace
        marketplace = AgentMarketplace()

        # Agent posts compute offer
        offer_id = marketplace.post_offer(
            agent=compute_agent,
            service_type=ServiceType.COMPUTE,
            description="Local GPU inference - Mistral 7B",
            price_eth=0.0001,  # Per inference
            metadata={
                "model": "hanzo-nano",
                "tokens_per_second": 20,
                "max_tokens": 1000,
            },
        )

        # Another agent requests compute
        user_agent = Web3Agent(name="user", description="Needs AI inference")

        request_id = marketplace.post_request(
            agent=user_agent,
            service_type=ServiceType.COMPUTE,
            description="Need to run inference on prompt",
            max_price_eth=0.001,
            metadata={"prompt": "What is the meaning of life?", "max_tokens": 100},
        )

        # Should match
        assert len(marketplace.matches) == 1


class TestDeterministicExecution:
    """Test deterministic network execution."""

    @pytest.mark.asyncio
    async def test_deterministic_network(self):
        """Test deterministic execution of agent network."""

        # Create agents
        class Agent1(Agent):
            name = "agent1"

            async def run(self, state, history, network):
                state["step1"] = "completed"
                return InferenceResult(agent=self.name, content="Step 1 done")

        class Agent2(Agent):
            name = "agent2"

            async def run(self, state, history, network):
                state["step2"] = "completed"
                return InferenceResult(agent=self.name, content="Step 2 done")

        # Create network
        network = create_web3_network(
            agents=[Agent1(), Agent2()],
            task="Test deterministic execution",
            deterministic=True,
        )

        # Run network
        final_state = await network.run()

        # Get execution hash
        hash1 = network.execution_hash
        assert hash1 is not None

        # Run again with same config
        network2 = create_web3_network(
            agents=[Agent1(), Agent2()],
            task="Test deterministic execution",
            deterministic=True,
        )

        final_state2 = await network2.run()
        hash2 = network2.execution_hash

        # Should produce same hash
        assert hash1 == hash2

        # Verify execution
        assert network2.verify_execution(hash1)


@pytest.mark.asyncio
async def test_full_integration():
    """Test full integration of all components."""
    if not (HANZO_AGENTS_AVAILABLE and HANZO_NETWORK_AVAILABLE):
        pytest.skip("Full integration requires all components")

    # 1. Create shared mnemonic for network
    mnemonic = generate_shared_mnemonic()

    # 2. Create compute nodes
    compute_orchestrator = LocalComputeOrchestrator()

    node1 = LocalComputeNode(node_id="node_001")
    node2 = LocalComputeNode(node_id="node_002")

    compute_orchestrator.register_node(node1)
    compute_orchestrator.register_node(node2)

    # 3. Create marketplace
    marketplace = AgentMarketplace()

    # 4. Create Web3 agents
    data_agent = Web3Agent(
        name="data_provider",
        description="Provides training data",
        web3_config=Web3AgentConfig(
            wallet_enabled=True,
            wallet_config=WalletConfig(mnemonic=mnemonic, account_index=0),
        ),
    )

    compute_agent = Web3Agent(
        name="compute_provider",
        description="Provides GPU compute",
        web3_config=Web3AgentConfig(
            wallet_enabled=True,
            tee_enabled=True,
            wallet_config=WalletConfig(mnemonic=mnemonic, account_index=1),
        ),
    )

    orchestrator_agent = Web3Agent(
        name="orchestrator",
        description="Orchestrates the workflow",
        web3_config=Web3AgentConfig(
            wallet_enabled=True,
            wallet_config=WalletConfig(mnemonic=mnemonic, account_index=2),
        ),
    )

    # 5. Create network
    from hanzo_agents.core.router import sequential_router

    network = Web3Network(
        state=State({"task": "Train a small AI model"}),
        agents=[orchestrator_agent, data_agent, compute_agent],
        router=sequential_router(["orchestrator", "data_provider", "compute_provider"]),
        shared_mnemonic=mnemonic,
        marketplace=marketplace,
    )

    # 6. Run network
    final_state = await network.run()

    # 7. Check results
    stats = network.get_network_stats()
    print("\nNetwork execution complete!")
    print(f"Total steps: {stats['total_steps']}")
    print(f"Treasury: {stats['treasury_balance']:.4f}")
    print(f"Marketplace activity: {stats['marketplace_stats']}")

    # Verify some execution occurred
    assert stats["total_steps"] > 0
    assert network.execution_hash is not None


# if __name__ == "__main__":
#     # Run integration test
#     asyncio.run(test_full_integration())
