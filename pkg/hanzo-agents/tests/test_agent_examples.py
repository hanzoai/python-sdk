"""Test all agent example demos to ensure they work correctly."""

import pytest
import asyncio
import sys
from pathlib import Path

# Add examples directory to path
examples_dir = Path(__file__).parent.parent / "examples"
sys.path.insert(0, str(examples_dir))

# Import demo modules
try:
    from startup_team_demo import run_startup_team_demo
    from agent_chat_demo import run_agent_chat_demo
    from research_team_demo import run_research_team_demo
    from game_dev_team_demo import run_game_dev_demo
    DEMOS_AVAILABLE = True
except ImportError as e:
    print(f"Failed to import demos: {e}")
    DEMOS_AVAILABLE = False


@pytest.mark.skipif(not DEMOS_AVAILABLE, reason="Demo modules not available")
class TestAgentDemos:
    """Test all agent demonstration examples."""
    
    @pytest.mark.asyncio
    async def test_startup_team_demo(self, capsys):
        """Test startup team collaboration demo."""
        # Run demo
        await run_startup_team_demo()
        
        # Check output
        captured = capsys.readouterr()
        output = captured.out
        
        # Verify key elements
        assert "Starting Startup Team Demo" in output
        assert "architect" in output.lower()
        assert "product_manager" in output.lower()
        assert "designer" in output.lower()
        assert "marketer" in output.lower()
        assert "engineer" in output.lower()
        
        # Check for completion
        assert "Project Summary" in output
        assert "Team Economics" in output
        assert "Execution hash" in output
    
    @pytest.mark.asyncio
    async def test_agent_chat_demo(self, capsys):
        """Test agent chat conversation demo."""
        # Run demo
        await run_agent_chat_demo()
        
        # Check output
        captured = capsys.readouterr()
        output = captured.out
        
        # Verify conversation elements
        assert "Agent Chat Demo" in output
        assert "Alice" in output
        assert "Bob" in output
        assert "typing..." in output
        
        # Check for system info exchange
        assert "Python" in output
        assert "model" in output.lower()
        assert "capabilities" in output.lower()
        
        # Verify completion
        assert "Conversation Summary" in output
        assert "Agent Stats" in output
        assert "lovely chat" in output
    
    @pytest.mark.asyncio
    async def test_research_team_demo(self, capsys):
        """Test research team collaboration demo."""
        # Run demo
        await run_research_team_demo()
        
        # Check output
        captured = capsys.readouterr()
        output = captured.out
        
        # Verify research workflow
        assert "Research Team Demo" in output
        assert "data_scientist" in output.lower()
        assert "research_analyst" in output.lower()
        assert "ml_engineer" in output.lower()
        assert "technical_writer" in output.lower()
        
        # Check research outputs
        assert "Data Analysis" in output
        assert "Literature Review" in output
        assert "Model Performance" in output
        assert "Experiments" in output
        assert "Deliverables" in output
        
        # Verify completion
        assert "Research project completed successfully" in output
    
    @pytest.mark.asyncio 
    async def test_game_dev_demo(self, capsys):
        """Test game development team demo."""
        # Run demo
        await run_game_dev_demo()
        
        # Check output
        captured = capsys.readouterr()
        output = captured.out
        
        # Verify game dev workflow
        assert "Game Development Team Demo" in output
        assert "game_designer" in output.lower()
        assert "artist" in output.lower()
        assert "programmer" in output.lower()
        assert "sound_designer" in output.lower()
        assert "qa_tester" in output.lower()
        
        # Check game details
        assert "Quantum Maze Runner" in output
        assert "Development Summary" in output
        assert "bugs found and fixed" in output
        
        # Verify completion
        assert "Game ready for launch" in output


@pytest.mark.skipif(not DEMOS_AVAILABLE, reason="Demo modules not available")
class TestAgentInteractions:
    """Test specific agent interaction patterns."""
    
    @pytest.mark.asyncio
    async def test_web3_payments(self):
        """Test Web3 payment functionality between agents."""
        from hanzo_agents import Web3Agent, Web3AgentConfig, WalletConfig, State
        
        # Create two agents
        agent1 = Web3Agent(
            name="payer",
            description="Agent that pays",
            web3_config=Web3AgentConfig(
                wallet_enabled=True,
                wallet_config=WalletConfig(network_rpc="mock://localhost")
            )
        )
        
        agent2 = Web3Agent(
            name="receiver",
            description="Agent that receives",
            web3_config=Web3AgentConfig(
                wallet_enabled=True,
                wallet_config=WalletConfig(network_rpc="mock://localhost")
            )
        )
        
        # Give agent1 balance
        agent1.earnings = 1.0
        
        # Test payment request
        payment_request = await agent2.request_payment(
            from_address=agent1.address,
            amount_eth=0.1,
            task_description="Test service"
        )
        
        assert payment_request["to"] == agent2.address
        assert payment_request["amount_eth"] == 0.1
        
        # Test payment execution
        tx = await agent1.pay_agent(
            to_address=agent2.address,
            amount_eth=0.1,
            reason="Test payment"
        )
        
        assert tx is not None
        assert agent1.spending == 0.1
    
    @pytest.mark.asyncio
    async def test_tee_execution(self):
        """Test TEE confidential execution."""
        from hanzo_agents import Web3Agent, Web3AgentConfig
        
        agent = Web3Agent(
            name="secure_agent",
            description="Agent with TEE",
            web3_config=Web3AgentConfig(tee_enabled=True)
        )
        
        # Test confidential execution
        code = """
result = {"sum": inputs["a"] + inputs["b"]}
"""
        
        result = await agent.execute_confidential(
            code,
            {"a": 10, "b": 20}
        )
        
        assert result["success"] is True
        assert result["result"]["sum"] == 30
        assert "attestation" in result
    
    @pytest.mark.asyncio
    async def test_marketplace_matching(self):
        """Test marketplace service matching."""
        from hanzo_agents import (
            Web3Agent, Web3AgentConfig, 
            AgentMarketplace, ServiceType
        )
        
        marketplace = AgentMarketplace()
        
        # Create provider
        provider = Web3Agent(
            name="provider",
            description="Service provider",
            web3_config=Web3AgentConfig(wallet_enabled=True)
        )
        
        # Create requester
        requester = Web3Agent(
            name="requester",
            description="Service requester",
            web3_config=Web3AgentConfig(wallet_enabled=True)
        )
        
        # Post offer
        offer_id = marketplace.post_offer(
            agent=provider,
            service_type=ServiceType.COMPUTE,
            description="GPU compute",
            price_eth=0.1
        )
        
        # Post matching request
        request_id = marketplace.post_request(
            agent=requester,
            service_type=ServiceType.COMPUTE,
            description="Need GPU",
            max_price_eth=0.2
        )
        
        # Should auto-match
        assert len(marketplace.matches) == 1
        match = list(marketplace.matches.values())[0]
        assert match.offer.agent_name == "provider"
        assert match.request.requester_name == "requester"
    
    @pytest.mark.asyncio
    async def test_deterministic_execution(self):
        """Test deterministic network execution."""
        from hanzo_agents import create_web3_network, Agent, State, InferenceResult
        
        # Create simple test agents
        class TestAgent1(Agent):
            name = "test1"
            async def run(self, state, history, network):
                state["step1"] = "done"
                return InferenceResult(
                    agent=self.name,
                    content="Step 1 complete"
                )
        
        class TestAgent2(Agent):
            name = "test2"
            async def run(self, state, history, network):
                state["step2"] = "done"
                return InferenceResult(
                    agent=self.name,
                    content="Step 2 complete"
                )
        
        # Create two identical networks
        agents = [TestAgent1(), TestAgent2()]
        
        network1 = create_web3_network(
            agents=agents,
            task="Test determinism",
            deterministic=True
        )
        
        network2 = create_web3_network(
            agents=agents,
            task="Test determinism",
            deterministic=True
        )
        
        # Run both networks
        state1 = await network1.run()
        state2 = await network2.run()
        
        # Should produce identical results
        assert network1.execution_hash == network2.execution_hash
        assert network1.verify_execution(network2.execution_hash)
        assert state1["step1"] == state2["step1"]
        assert state1["step2"] == state2["step2"]


if __name__ == "__main__":
    # Run specific demo if provided
    import sys
    
    if len(sys.argv) > 1:
        demo_name = sys.argv[1]
        if demo_name == "startup":
            asyncio.run(run_startup_team_demo())
        elif demo_name == "chat":
            asyncio.run(run_agent_chat_demo())
        elif demo_name == "research":
            asyncio.run(run_research_team_demo())
        elif demo_name == "game":
            asyncio.run(run_game_dev_demo())
        else:
            print(f"Unknown demo: {demo_name}")
            print("Available demos: startup, chat, research, game")
    else:
        # Run all demos
        print("Running all demos...\n")
        asyncio.run(run_startup_team_demo())
        print("\n" + "="*80 + "\n")
        asyncio.run(run_agent_chat_demo())
        print("\n" + "="*80 + "\n")
        asyncio.run(run_research_team_demo())
        print("\n" + "="*80 + "\n")
        asyncio.run(run_game_dev_demo())