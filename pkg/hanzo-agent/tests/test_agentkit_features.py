#!/usr/bin/env python3
"""
Comprehensive tests for AgentKit-inspired features in Hanzo Agent SDK.
"""

import asyncio
import json
import os
import sys
import time
from typing import Any, Dict, List

# Add agent SDK to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from agents import Agent, Runner
from agents.run import RunConfig
from agents.network import create_network, SemanticRouter, RuleBasedRouter, LoadBalancingRouter
from agents.state import InMemoryStateStore, FileStateStore
from agents.memory import Memory, MemoryEntry, MemoryType
from agents.orchestration import Workflow, Step
from agents import function_tool as tool
from agents.exceptions import MaxTurnsExceeded


# Test fixtures
@pytest.fixture
def simple_agent():
    """Create a simple test agent."""
    return Agent(
        name="TestAgent",
        instructions="You are a helpful test assistant.",
        model="gpt-3.5-turbo"
    )


@pytest.fixture
def math_agent():
    """Create a math-focused agent."""
    return Agent(
        name="MathExpert",
        instructions="You are a math expert. Answer math questions concisely.",
        model="gpt-3.5-turbo"
    )


@pytest.fixture
def science_agent():
    """Create a science-focused agent."""
    return Agent(
        name="ScienceExpert",
        instructions="You are a science expert. Answer science questions concisely.",
        model="gpt-3.5-turbo"
    )


# Test 1: Multi-Agent Networks
class TestMultiAgentNetworks:
    """Test multi-agent network functionality."""
    
    def test_create_network(self, math_agent, science_agent):
        """Test creating a basic network."""
        network = create_network(
            agents=[math_agent, science_agent],
            name="Test Network"
        )
        
        assert network.config.name == "Test Network"
        assert len(network.nodes) == 2
        assert "MathExpert" in network.nodes
        assert "ScienceExpert" in network.nodes
        
    def test_semantic_router(self, math_agent, science_agent):
        """Test semantic routing between agents."""
        router = SemanticRouter()
        network = create_network(
            agents=[math_agent, science_agent],
            router=router
        )
        
        assert isinstance(network.router, SemanticRouter)
        
    def test_rule_based_router(self, math_agent, science_agent):
        """Test rule-based routing."""
        router = RuleBasedRouter()
        
        # Add routing rules
        router.add_rule(r".*math.*|.*calculate.*|.*number.*", "MathExpert")
        router.add_rule(r".*science.*|.*chemistry.*|.*physics.*", "ScienceExpert")
        
        network = create_network(
            agents=[math_agent, science_agent],
            router=router
        )
        
        assert isinstance(network.router, RuleBasedRouter)
        assert len(router.rules) == 2
        
    def test_load_balancing_router(self, math_agent, science_agent):
        """Test load balancing router."""
        router = LoadBalancingRouter()
        network = create_network(
            agents=[math_agent, science_agent],
            router=router
        )
        
        assert isinstance(network.router, LoadBalancingRouter)
        
    @pytest.mark.asyncio
    async def test_network_agent_addition(self):
        """Test adding agents to network dynamically."""
        network = create_network(agents=[])
        
        agent1 = Agent(name="Agent1", instructions="First agent")
        agent2 = Agent(name="Agent2", instructions="Second agent")
        
        node1 = network.add_agent(agent1, capabilities=["task1", "task2"])
        node2 = network.add_agent(agent2, capabilities=["task3", "task4"])
        
        assert len(network.nodes) == 2
        assert node1.capabilities == ["task1", "task2"]
        assert node2.capabilities == ["task3", "task4"]


# Test 2: State Management
class TestStateManagement:
    """Test state management across agents."""
    
    @pytest.mark.asyncio
    async def test_in_memory_state_store(self):
        """Test in-memory state store."""
        store = InMemoryStateStore()
        
        # Test basic operations
        await store.set("key1", "value1")
        assert await store.get("key1") == "value1"
        
        # Test namespaces
        await store.set("key2", "value2", namespace="ns1")
        assert await store.get("key2", namespace="ns1") == "value2"
        assert await store.get("key2") is None  # Different namespace
        
        # Test update
        result = await store.update(
            "counter",
            lambda x: (x or 0) + 1
        )
        assert result == 1
        
        result = await store.update(
            "counter",
            lambda x: (x or 0) + 1
        )
        assert result == 2
        
    @pytest.mark.asyncio
    async def test_file_state_store(self, tmp_path):
        """Test file-based state store."""
        store_path = tmp_path / "state_store.json"
        store = FileStateStore(str(store_path))
        
        # Test persistence
        await store.set("persistent_key", {"data": "test"})
        
        # Create new store instance
        store2 = FileStateStore(str(store_path))
        value = await store2.get("persistent_key")
        assert value == {"data": "test"}
        
    @pytest.mark.asyncio
    async def test_state_sharing_in_network(self, math_agent, science_agent):
        """Test state sharing between agents in a network."""
        store = InMemoryStateStore()
        network = create_network(
            agents=[math_agent, science_agent],
            state_store=store
        )
        
        # Set state from outside
        await store.set("shared_data", {"experiment": "quantum"})
        
        # Verify network has access to the store
        assert network.state_store is store
        data = await network.state_store.get("shared_data")
        assert data == {"experiment": "quantum"}


# Test 3: Memory System
class TestMemorySystem:
    """Test memory system with vector search."""
    
    def test_memory_entry_creation(self):
        """Test creating memory entries."""
        entry = MemoryEntry(
            id="mem1",
            type=MemoryType.FACT,
            content="The Earth orbits the Sun",
            metadata={"category": "astronomy"},
            importance=0.9
        )
        
        assert entry.id == "mem1"
        assert entry.type == MemoryType.FACT
        assert entry.importance == 0.9
        
        # Test serialization
        data = entry.to_dict()
        assert data["type"] == "fact"
        assert data["content"] == "The Earth orbits the Sun"
        
        # Test deserialization
        entry2 = MemoryEntry.from_dict(data)
        assert entry2.id == entry.id
        assert entry2.content == entry.content
        
    @pytest.mark.asyncio
    async def test_memory_operations(self):
        """Test memory storage and retrieval."""
        memory = Memory(max_entries=10)
        
        # Add memories
        entry1 = await memory.add(
            content="Python is a programming language",
            type=MemoryType.FACT,
            metadata={"topic": "programming"}
        )
        
        entry2 = await memory.add(
            content="The user asked about Python",
            type=MemoryType.CONVERSATION,
            metadata={"timestamp": time.time()}
        )
        
        assert len(await memory.get_all()) == 2
        
        # Test search
        results = await memory.search("Python", limit=1)
        assert len(results) == 1
        assert "Python" in results[0].content
        
    @pytest.mark.asyncio
    async def test_memory_compression(self):
        """Test memory compression when limit is reached."""
        memory = Memory(max_entries=3, auto_compress=True, compress_threshold=2)
        
        # Add memories beyond limit
        for i in range(5):
            await memory.add(
                content=f"Memory {i}",
                type=MemoryType.CONVERSATION
            )
        
        # Should compress old memories
        all_memories = await memory.get_all()
        assert len(all_memories) <= 3
        
    def test_memory_types(self):
        """Test different memory types."""
        types = [
            MemoryType.SHORT_TERM,
            MemoryType.LONG_TERM,
            MemoryType.WORKING,
            MemoryType.EPISODIC,
            MemoryType.SEMANTIC,
            MemoryType.CONVERSATION,
            MemoryType.FACT,
            MemoryType.PROCEDURE,
            MemoryType.REFLECTION
        ]
        
        for mem_type in types:
            entry = MemoryEntry(
                id=f"test_{mem_type.value}",
                type=mem_type,
                content=f"Test content for {mem_type.value}"
            )
            assert entry.type == mem_type


# Test 4: Workflow Orchestration
class TestWorkflowOrchestration:
    """Test workflow orchestration features."""
    
    def test_workflow_creation(self):
        """Test creating workflows."""
        workflow = Workflow(
            name="Test Workflow",
            description="A test workflow"
        )
        
        # Add steps
        step1 = workflow.add_step(Step.agent("Agent1", "Do task 1"))
        step2 = workflow.add_step(Step.agent("Agent2", "Do task 2"))
        
        assert len(workflow.steps) == 2
        assert workflow.entry_point == step1.id
        
    def test_parallel_steps(self):
        """Test parallel workflow steps."""
        workflow = Workflow(name="Parallel Test")
        
        # Create parallel steps
        parallel_step = Step.parallel([
            Step.agent("Agent1", "Task 1"),
            Step.agent("Agent2", "Task 2"),
            Step.agent("Agent3", "Task 3")
        ])
        
        workflow.add_step(parallel_step)
        assert parallel_step.type.value == "parallel"
        assert len(parallel_step.config["steps"]) == 3
        
    def test_conditional_steps(self):
        """Test conditional workflow steps."""
        workflow = Workflow(name="Conditional Test")
        
        # Create conditional step
        def check_condition(data):
            return data.get("value", 0) > 5
        
        true_step = Step.agent("HighValueAgent", "Handle high value")
        false_step = Step.agent("LowValueAgent", "Handle low value")
        
        conditional = Step.conditional(
            condition=check_condition,
            if_true=true_step,
            if_false=false_step
        )
        
        workflow.add_step(conditional)
        assert conditional.type.value == "conditional"
        
    def test_loop_steps(self):
        """Test loop workflow steps."""
        workflow = Workflow(name="Loop Test")
        
        # Create loop step
        body_step = Step.agent("ProcessAgent", "Process item")
        
        loop = Step.loop(
            over="items",  # Path to array in context
            body=body_step,
            max_iterations=10
        )
        
        workflow.add_step(loop)
        assert loop.type.value == "loop"
        assert loop.config["max_iterations"] == 10
        
    def test_workflow_validation(self):
        """Test workflow validation."""
        workflow = Workflow(name="Validation Test")
        
        # Empty workflow should have validation errors
        errors = workflow.validate()
        assert len(errors) > 0
        assert "No entry point defined" in errors
        
        # Add steps and validate
        workflow.add_step(Step.agent("Agent1", "Task"))
        errors = workflow.validate()
        assert len(errors) == 0
        
    def test_workflow_execution_order(self):
        """Test workflow execution order calculation."""
        workflow = Workflow(name="Order Test")
        
        step1 = workflow.add_step(Step.agent("Agent1", "Task 1"))
        step2 = workflow.add_step(Step.agent("Agent2", "Task 2"))
        step3 = workflow.add_step(Step.agent("Agent3", "Task 3"))
        
        # Add dependencies
        step2.depends_on = [step1.id]
        step3.depends_on = [step1.id]
        
        # Get execution order
        order = workflow.get_execution_order()
        
        # Step 1 should be first, steps 2 and 3 can be parallel
        assert len(order) == 2
        assert step1.id in order[0]
        assert step2.id in order[1] and step3.id in order[1]
        
    def test_workflow_serialization(self):
        """Test workflow serialization."""
        workflow = Workflow(name="Serialization Test")
        workflow.add_step(Step.agent("TestAgent", "Test task"))
        
        # Convert to dict
        data = workflow.to_dict()
        assert data["name"] == "Serialization Test"
        assert len(data["steps"]) == 1
        
        # Convert to Mermaid diagram
        mermaid = workflow.to_mermaid()
        assert "graph TD" in mermaid
        assert "TestAgent" in mermaid


# Test 5: Tool Integration
class TestToolIntegration:
    """Test tool integration with agents."""
    
    def test_tool_creation(self):
        """Test creating tools for agents."""
        
        @tool
        def calculate_sum(a: int, b: int) -> int:
            """Calculate the sum of two numbers.
            
            Args:
                a: First number
                b: Second number
                
            Returns:
                The sum of a and b
            """
            return a + b
        
        agent = Agent(
            name="CalculatorAgent",
            instructions="You can calculate sums.",
            tools=[calculate_sum]
        )
        
        assert len(agent.tools) == 1
        assert agent.tools[0].name == "calculate_sum"
        
    @pytest.mark.asyncio
    async def test_agent_with_tools(self):
        """Test agent using tools."""
        
        @tool
        def get_current_time() -> str:
            """Get the current time."""
            return time.strftime("%Y-%m-%d %H:%M:%S")
        
        agent = Agent(
            name="TimeAgent",
            instructions="You can tell the time.",
            tools=[get_current_time],
            model="gpt-3.5-turbo"
        )
        
        # This would require actual API call
        # Just verify agent is configured correctly
        assert agent.tools[0].name == "get_current_time"


# Test 6: Error Handling
class TestErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.mark.asyncio
    async def test_max_turns_exceeded(self, simple_agent):
        """Test max turns limit."""
        # This would require mocking to avoid actual API calls
        # Just test the configuration
        config = RunConfig(model="gpt-3.5-turbo")
        assert config.model == "gpt-3.5-turbo"
        
    def test_invalid_workflow(self):
        """Test invalid workflow configurations."""
        workflow = Workflow(name="Invalid Test")
        
        # Add circular dependency
        step1 = workflow.add_step(Step.agent("Agent1", "Task 1"))
        step2 = workflow.add_step(Step.agent("Agent2", "Task 2"))
        
        step1.depends_on = [step2.id]
        step2.depends_on = [step1.id]
        
        # Should detect circular dependency
        with pytest.raises(Exception):
            workflow.get_execution_order()
            
    def test_network_with_no_agents(self):
        """Test network with no agents."""
        network = create_network(agents=[])
        assert len(network.nodes) == 0
        
    @pytest.mark.asyncio
    async def test_state_store_error_handling(self):
        """Test state store error handling."""
        store = InMemoryStateStore()
        
        # Test getting non-existent key
        value = await store.get("non_existent")
        assert value is None
        
        # Test update on non-existent key
        result = await store.update(
            "new_key",
            lambda x: (x or 0) + 1
        )
        assert result == 1


# Test 7: Integration Tests
class TestIntegration:
    """Integration tests combining multiple features."""
    
    @pytest.mark.asyncio
    async def test_network_with_state_and_memory(self, math_agent, science_agent):
        """Test network with both state and memory."""
        # Create shared state
        state_store = InMemoryStateStore()
        await state_store.set("experiment_count", 0)
        
        # Create network
        network = create_network(
            agents=[math_agent, science_agent],
            state_store=state_store
        )
        
        # Create memory for each agent
        math_memory = Memory()
        science_memory = Memory()
        
        # Add some memories
        await math_memory.add(
            content="User prefers simple explanations",
            type=MemoryType.FACT
        )
        
        await science_memory.add(
            content="User is interested in physics",
            type=MemoryType.FACT
        )
        
        # Verify integration
        assert network.state_store is state_store
        assert len(await math_memory.get_all()) == 1
        assert len(await science_memory.get_all()) == 1
        
    def test_workflow_with_network(self, math_agent, science_agent):
        """Test workflow using network agents."""
        # Create network
        network = create_network(
            agents=[math_agent, science_agent]
        )
        
        # Create workflow
        workflow = Workflow(name="Math and Science Workflow")
        
        # Add steps using network agents
        math_step = workflow.add_step(
            Step.agent("MathExpert", "Calculate 2+2")
        )
        
        science_step = workflow.add_step(
            Step.agent("ScienceExpert", "Explain photosynthesis")
        )
        
        # Make science step depend on math step
        science_step.depends_on = [math_step.id]
        
        # Validate workflow
        errors = workflow.validate()
        assert len(errors) == 0
        
        # Check execution order
        order = workflow.get_execution_order()
        assert len(order) == 2
        assert math_step.id in order[0]
        assert science_step.id in order[1]


# Test runner
if __name__ == "__main__":
    print("🧪 Running Hanzo Agent SDK Tests")
    print("=" * 60)
    
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
