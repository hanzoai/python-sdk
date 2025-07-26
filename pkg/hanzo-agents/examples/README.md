# Hanzo Agents Examples

This directory contains example demonstrations of the hanzo-agents SDK showcasing various agent collaboration patterns.

## Examples

### 1. Startup Team Demo (`startup_team_demo.py`)

A complete startup team working together to build a product:
- **Architect**: Designs technical architecture
- **Product Manager**: Defines requirements and manages budget
- **Designer**: Creates UI/UX designs
- **Marketer**: Develops go-to-market strategy
- **Frontend Engineer**: Implements the user interface
- **Backend Engineer**: Builds APIs and services

Features demonstrated:
- Web3 payments between agents
- TEE secure computation
- Service marketplace
- Team coordination
- Economic tracking

### 2. Agent Chat Demo (`agent_chat_demo.py`)

A cute example of two AI agents having a casual conversation:
- **Alice**: A cheerful agent powered by Claude
- **Bob**: An analytical agent powered by GPT-4

They chat about:
- Their runtime environments
- Model capabilities
- Available tools
- Recent tasks
- System status
- Exchange friendship tokens (micro-payments)

Features demonstrated:
- Agent-to-agent (A2A) communication
- Information exchange about capabilities
- Web3 tipping/payments
- Personality-driven interactions
- System introspection

### 3. Research Team Demo (`research_team_demo.py`)

A research team collaborating on an AI research project:
- **Data Scientist**: Analyzes data and finds patterns
- **Research Analyst**: Conducts literature reviews
- **ML Engineer**: Builds and trains models
- **Technical Writer**: Documents findings

Features demonstrated:
- Complex multi-stage workflows
- TEE for sensitive data processing
- Research collaboration patterns
- Document generation
- Experiment tracking

### 4. Game Development Team Demo (`game_dev_team_demo.py`)

A game development team building "Quantum Maze Runner":
- **Game Designer**: Creates game concepts and mechanics
- **Artist**: Designs visuals and assets
- **Programmer**: Implements game logic
- **Sound Designer**: Creates audio and music
- **QA Tester**: Tests and finds bugs

Features demonstrated:
- Creative collaboration
- Asset creation workflow
- Code implementation tracking
- Quality assurance process
- Project completion metrics

## Running the Examples

### Individual Demos

Run a specific demo:

```bash
# Run startup team demo
python startup_team_demo.py

# Run agent chat demo
python agent_chat_demo.py

# Run research team demo
python research_team_demo.py

# Run game dev demo
python game_dev_team_demo.py
```

### Test Suite

Run the test suite to verify all demos work:

```bash
# From the agents directory
pytest tests/test_agent_examples.py -v

# Run a specific demo via the test script
python tests/test_agent_examples.py startup
python tests/test_agent_examples.py chat
python tests/test_agent_examples.py research
python tests/test_agent_examples.py game
```

## Key Concepts Demonstrated

### 1. Web3 Integration
- Agents have Ethereum wallets derived from a shared mnemonic
- Agents can request and send payments for services
- Economic tracking (earnings, spending, balance)
- Marketplace for service discovery

### 2. TEE (Trusted Execution Environment)
- Secure computation for sensitive data
- Attestation reports for verification
- Confidential data processing

### 3. Deterministic Execution
- Networks can run deterministically with same results
- Execution hashes for verification
- Checkpoint support for resuming

### 4. Agent Communication Patterns
- Sequential workflows with routers
- Service requests and offers
- Metadata passing between agents
- State sharing and updates

### 5. Specialized Agent Roles
- Each agent has specific expertise
- Agents collaborate to achieve complex goals
- Natural handoffs between team members
- Result aggregation and summarization

## Creating Your Own Agent Teams

To create your own agent team:

1. **Define Agent Classes**:
```python
class MyAgent(Web3Agent):
    name = "my_agent"
    description = "What this agent does"
    
    async def _run_impl(self, state, history, network):
        # Agent logic here
        return self.create_result("Done!")
```

2. **Create a Router**:
```python
class MyRouter(Router):
    async def route(self, network, step, last_result, agents):
        # Routing logic
        return next_agent_name
```

3. **Set Up the Network**:
```python
network = Web3Network(
    state=State({"task": "Build something"}),
    agents=[Agent1(), Agent2(), Agent3()],
    router=MyRouter(),
    shared_mnemonic=generate_shared_mnemonic()
)

final_state = await network.run()
```

## Advanced Features

### Marketplace Integration
Agents can post service offers and requests that automatically match:

```python
marketplace.post_offer(
    agent=provider,
    service_type=ServiceType.COMPUTE,
    description="GPU compute available",
    price_eth=0.1
)
```

### TEE Confidential Computing
Process sensitive data securely:

```python
result = await agent.execute_confidential(
    task_code="result = process_pii(inputs['data'])",
    inputs={"data": sensitive_data}
)
```

### Economic Incentives
Built-in economics with fees, rewards, and penalties:

```python
network_economics = NetworkEconomics(
    network_fee_percent=0.01,
    completion_bonus=0.1,
    quality_multiplier=2.0
)
```

## Best Practices

1. **Agent Design**:
   - Keep agents focused on specific tasks
   - Use clear, descriptive names
   - Document agent capabilities

2. **State Management**:
   - Pass relevant data through state
   - Clean up temporary state when done
   - Use structured data formats

3. **Error Handling**:
   - Handle failures gracefully
   - Provide fallback behaviors
   - Log important events

4. **Testing**:
   - Test individual agents in isolation
   - Test full workflows end-to-end
   - Verify deterministic execution

5. **Performance**:
   - Use async operations effectively
   - Batch related operations
   - Monitor token usage and costs

## Learn More

See the main hanzo-agents documentation for detailed API reference and advanced usage patterns.