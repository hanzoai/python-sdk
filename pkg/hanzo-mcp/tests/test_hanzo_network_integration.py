"""Integration tests for hanzo-network multi-agent orchestration."""

import tempfile
from typing import Any, Dict
from pathlib import Path

import pytest

# Try to import hanzo-network components
try:
    from hanzo_network import (
        Tool,
        Agent,
        State,
        Network,
        NetworkConfig,
        LocalComputeNode,
        LocalComputeOrchestrator,
        create_agent_network,
    )
    from hanzo_network.tools import MemoryTool, create_memory_tool

    HANZO_NETWORK_AVAILABLE = True
except ImportError:
    HANZO_NETWORK_AVAILABLE = False

# Try to import hanzo-agents
try:
    from hanzo_agents import (
        Agent as HanzoAgent,
        Network as HanzoNetwork,
        create_agent,
        create_network,
    )

    HANZO_AGENTS_AVAILABLE = True
except ImportError:
    HANZO_AGENTS_AVAILABLE = False


class TestHanzoNetworkIntegration:
    """Test hanzo-network multi-agent orchestration capabilities."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    async def basic_network(self):
        """Create a basic agent network."""
        # Define network configuration
        config = NetworkConfig(
            name="test-network",
            description="Test multi-agent network",
            max_agents=5,
            enable_memory=True,
        )

        # Create network
        network = await create_agent_network(config)
        yield network

        # Cleanup
        await network.shutdown()

    async def test_network_creation(self, tool_helper, basic_network):
        """Test that a network can be created successfully."""
        assert basic_network is not None
        assert basic_network.name == "test-network"
        assert basic_network.max_agents == 5
        assert basic_network.is_running

    async def test_agent_addition(self, tool_helper, basic_network):
        """Test adding agents to the network."""
        # Create agents with different roles
        architect = Agent(
            name="architect",
            role="System Architect",
            capabilities=["design", "planning", "architecture"],
            model="gpt-4",
        )

        developer = Agent(
            name="developer",
            role="Software Developer",
            capabilities=["coding", "testing", "debugging"],
            model="claude-3-sonnet",
        )

        # Add agents to network
        await basic_network.add_agent(architect)
        await basic_network.add_agent(developer)

        # Verify agents were added
        assert len(basic_network.agents) == 2
        assert "architect" in basic_network.agents
        assert "developer" in basic_network.agents

    async def test_agent_communication(self, tool_helper, basic_network):
        """Test agent-to-agent communication."""
        # Create communicating agents
        agent1 = Agent(name="agent1", role="Coordinator", capabilities=["coordination", "planning"])

        agent2 = Agent(name="agent2", role="Worker", capabilities=["execution", "reporting"])

        # Add message handler to agent2
        messages_received = []

        async def handle_message(message: Dict[str, Any]):
            messages_received.append(message)
            return {
                "status": "received",
                "content": f"Acknowledged: {message['content']}",
            }

        agent2.on_message = handle_message

        # Add agents to network
        await basic_network.add_agent(agent1)
        await basic_network.add_agent(agent2)

        # Send message from agent1 to agent2
        response = await basic_network.send_message(
            from_agent="agent1", to_agent="agent2", content="Please execute task X"
        )

        # Verify communication
        assert len(messages_received) == 1
        assert messages_received[0]["content"] == "Please execute task X"
        assert response["status"] == "received"

    async def test_tool_sharing(self, tool_helper, basic_network, temp_dir):
        """Test tool sharing between agents."""

        # Create a file tool
        class FileTool(Tool):
            def __init__(self, base_path: Path):
                super().__init__(name="file_tool", description="Read and write files")
                self.base_path = base_path

            async def execute(self, action: str, **kwargs) -> Dict[str, Any]:
                if action == "write":
                    path = self.base_path / kwargs["filename"]
                    path.write_text(kwargs["content"])
                    return {"status": "success", "path": str(path)}
                elif action == "read":
                    path = self.base_path / kwargs["filename"]
                    content = path.read_text() if path.exists() else None
                    return {"status": "success", "content": content}

        # Create agents
        writer = Agent(name="writer", role="Content Writer")
        reader = Agent(name="reader", role="Content Reader")

        # Create and share tool
        file_tool = FileTool(temp_dir)
        await basic_network.add_shared_tool(file_tool)

        # Add agents
        await basic_network.add_agent(writer)
        await basic_network.add_agent(reader)

        # Writer uses tool to create file
        write_result = await basic_network.execute_tool(
            agent_name="writer",
            tool_name="file_tool",
            action="write",
            filename="shared.txt",
            content="This is shared content",
        )

        assert write_result["status"] == "success"

        # Reader uses tool to read file
        read_result = await basic_network.execute_tool(
            agent_name="reader",
            tool_name="file_tool",
            action="read",
            filename="shared.txt",
        )

        assert read_result["status"] == "success"
        assert read_result["content"] == "This is shared content"

    async def test_memory_sharing(self, tool_helper, basic_network):
        """Test shared memory between agents."""
        # Create memory tool
        memory_tool = create_memory_tool("test-memory")
        await basic_network.add_shared_tool(memory_tool)

        # Create agents
        learner = Agent(name="learner", role="Knowledge Collector")
        teacher = Agent(name="teacher", role="Knowledge Provider")

        await basic_network.add_agent(learner)
        await basic_network.add_agent(teacher)

        # Teacher stores knowledge
        await basic_network.execute_tool(
            agent_name="teacher",
            tool_name="test-memory",
            action="store",
            key="python_tip",
            value="Use list comprehensions for cleaner code",
        )

        # Learner retrieves knowledge
        result = await basic_network.execute_tool(
            agent_name="learner",
            tool_name="test-memory",
            action="retrieve",
            key="python_tip",
        )

        assert result["value"] == "Use list comprehensions for cleaner code"

    async def test_orchestrated_workflow(self, tool_helper, basic_network, temp_dir):
        """Test a complete orchestrated workflow with multiple agents."""
        # Create specialized agents
        pm = Agent(
            name="project_manager",
            role="Project Manager",
            capabilities=["planning", "coordination"],
            model="gpt-4",
        )

        architect = Agent(
            name="architect",
            role="Software Architect",
            capabilities=["design", "architecture"],
            model="claude-3-sonnet",
        )

        developer = Agent(
            name="developer",
            role="Developer",
            capabilities=["coding", "implementation"],
            model="gpt-3.5-turbo",
        )

        tester = Agent(
            name="tester",
            role="QA Engineer",
            capabilities=["testing", "validation"],
            model="gpt-3.5-turbo",
        )

        # Add all agents
        for agent in [pm, architect, developer, tester]:
            await basic_network.add_agent(agent)

        # Define workflow
        workflow = {
            "name": "feature_development",
            "steps": [
                {
                    "agent": "project_manager",
                    "task": "Define requirements for user authentication feature",
                    "output": "requirements",
                },
                {
                    "agent": "architect",
                    "task": "Design system architecture based on {requirements}",
                    "depends_on": ["requirements"],
                    "output": "architecture",
                },
                {
                    "agent": "developer",
                    "task": "Implement authentication based on {architecture}",
                    "depends_on": ["architecture"],
                    "output": "implementation",
                },
                {
                    "agent": "tester",
                    "task": "Test the {implementation}",
                    "depends_on": ["implementation"],
                    "output": "test_results",
                },
            ],
        }

        # Execute workflow
        results = await basic_network.execute_workflow(workflow)

        # Verify workflow completed
        assert "requirements" in results
        assert "architecture" in results
        assert "implementation" in results
        assert "test_results" in results

        # Each step should have produced output
        for step_output in results.values():
            assert step_output is not None
            assert "status" in step_output or "content" in step_output

    async def test_consensus_decision(self, tool_helper, basic_network):
        """Test consensus-based decision making."""
        # Create decision-making agents
        agents = []
        for i in range(3):
            agent = Agent(
                name=f"advisor_{i}",
                role=f"Technical Advisor {i}",
                model="gpt-3.5-turbo",
            )
            agents.append(agent)
            await basic_network.add_agent(agent)

        # Define decision question
        question = "Should we use microservices architecture for this project?"

        # Get consensus
        consensus_result = await basic_network.get_consensus(
            question=question,
            agents=["advisor_0", "advisor_1", "advisor_2"],
            threshold=0.66,  # 2 out of 3 must agree
        )

        # Verify consensus result
        assert "decision" in consensus_result
        assert "confidence" in consensus_result
        assert "votes" in consensus_result
        assert len(consensus_result["votes"]) == 3

    async def test_local_compute_orchestration(self, tool_helper, basic_network):
        """Test local compute orchestration for cost optimization."""
        # Create local compute orchestrator
        orchestrator = LocalComputeOrchestrator(
            preferred_local_model="llama2:7b",
            cost_threshold=0.01,  # Use local for tasks under 1 cent
        )

        # Attach to network
        basic_network.set_orchestrator(orchestrator)

        # Create mixed agents (some local, some API)
        local_agent = Agent(
            name="local_helper",
            role="Local Assistant",
            model="llama2:7b",
            is_local=True,
        )

        api_agent = Agent(name="api_expert", role="Expert Consultant", model="gpt-4", is_local=False)

        await basic_network.add_agent(local_agent)
        await basic_network.add_agent(api_agent)

        # Simple task (should go to local)
        simple_result = await basic_network.delegate_task(task='Format this JSON: {"name":"test"}', complexity="simple")

        assert simple_result["agent"] == "local_helper"
        assert simple_result["cost"] < 0.01

        # Complex task (should go to API)
        complex_result = await basic_network.delegate_task(
            task="Design a distributed system for handling 1M requests/second",
            complexity="complex",
        )

        assert complex_result["agent"] == "api_expert"

    async def test_agent_network_persistence(self, tool_helper, basic_network, temp_dir):
        """Test saving and loading agent network state."""
        # Add some agents and state
        agent1 = Agent(name="persistent_agent", role="Keeper")
        await basic_network.add_agent(agent1)

        # Add shared memory
        await basic_network.execute_tool(
            agent_name="persistent_agent",
            tool_name="memory",
            action="store",
            key="important_data",
            value="This must persist",
        )

        # Save network state
        state_file = temp_dir / "network_state.json"
        await basic_network.save_state(state_file)

        assert state_file.exists()

        # Create new network and load state
        new_network = await create_agent_network(NetworkConfig(name="restored-network"))

        await new_network.load_state(state_file)

        # Verify state was restored
        assert "persistent_agent" in new_network.agents

        # Check memory was restored
        memory_result = await new_network.execute_tool(
            agent_name="persistent_agent",
            tool_name="memory",
            action="retrieve",
            key="important_data",
        )

        assert memory_result["value"] == "This must persist"


@pytest.mark.skipif(
    not (HANZO_NETWORK_AVAILABLE and HANZO_AGENTS_AVAILABLE),
    reason="Both hanzo-network and hanzo-agents required",
)
class TestHanzoNetworkMCPIntegration:
    """Test hanzo-network integration with MCP tools and servers."""

    async def test_mcp_tool_integration(self, tool_helper, temp_dir):
        """Test agents using MCP tools through hanzo-network."""
        # Create network with MCP support
        network = await create_agent_network(
            NetworkConfig(
                name="mcp-network",
                enable_mcp_tools=True,
                mcp_allowed_paths=[str(temp_dir)],
            )
        )

        # Create agent with MCP access
        mcp_agent = Agent(
            name="mcp_agent",
            role="MCP Tool User",
            capabilities=["file_operations", "search"],
            has_mcp_access=True,
        )

        await network.add_agent(mcp_agent)

        # Use MCP write tool through agent
        write_result = await network.execute_mcp_tool(
            agent_name="mcp_agent",
            tool_name="write",
            arguments={
                "path": str(temp_dir / "mcp_test.txt"),
                "content": "Written through MCP",
            },
        )

        assert "success" in str(write_result).lower()
        assert (temp_dir / "mcp_test.txt").read_text() == "Written through MCP"

        # Use MCP search tool
        search_result = await network.execute_mcp_tool(
            agent_name="mcp_agent",
            tool_name="search",
            arguments={"pattern": "MCP", "path": str(temp_dir)},
        )

        assert "results" in search_result

    async def test_multi_agent_mcp_workflow(self, tool_helper, temp_dir):
        """Test multiple agents collaborating through MCP tools."""
        # Create network
        network = await create_agent_network(
            NetworkConfig(
                name="collaborative-mcp",
                enable_mcp_tools=True,
                mcp_allowed_paths=[str(temp_dir)],
            )
        )

        # Create specialized agents
        analyst = Agent(name="analyst", role="Code Analyst", has_mcp_access=True)

        refactorer = Agent(name="refactorer", role="Code Refactorer", has_mcp_access=True)

        reviewer = Agent(name="reviewer", role="Code Reviewer", has_mcp_access=True)

        for agent in [analyst, refactorer, reviewer]:
            await network.add_agent(agent)

        # Create a file with code to analyze
        code_file = temp_dir / "legacy_code.py"
        code_file.write_text(
            """
def calculate(x, y):
    # TODO: Add error handling
    result = x + y
    print(result)
    return result

def process_data(data):
    # Complex function that needs refactoring
    output = []
    for i in range(len(data)):
        if data[i] > 0:
            output.append(data[i] * 2)
    return output
"""
        )

        # Workflow: Analyze -> Refactor -> Review
        workflow_result = await network.execute_collaborative_task(
            task="Improve the code quality in legacy_code.py",
            steps=[
                {
                    "agent": "analyst",
                    "action": "analyze",
                    "mcp_tools": ["read", "search"],
                    "focus": "Identify code smells and TODOs",
                },
                {
                    "agent": "refactorer",
                    "action": "refactor",
                    "mcp_tools": ["read", "edit", "multi_edit"],
                    "focus": "Improve code based on analysis",
                },
                {
                    "agent": "reviewer",
                    "action": "review",
                    "mcp_tools": ["read", "critic"],
                    "focus": "Review changes and ensure quality",
                },
            ],
        )

        # Verify workflow completed
        assert workflow_result["status"] == "completed"
        assert len(workflow_result["steps"]) == 3

        # Check that code was actually modified
        modified_code = code_file.read_text()
        assert modified_code != code_file.read_text()  # Should be different

        # Should have better error handling and cleaner list comprehension
        assert "try:" in modified_code or "except:" in modified_code
        assert "[" in modified_code and "for" in modified_code  # List comprehension


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
