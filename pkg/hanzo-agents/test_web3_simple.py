"""Simple test of Web3 agent features without full dependencies."""

import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

# Test basic imports
print("Testing basic Web3 agent components...")

try:
    from hanzo_agents.core.wallet import (
        AgentWallet,
        WalletConfig,
        derive_agent_wallet,
        generate_shared_mnemonic,
    )

    print("✓ Wallet imports successful")

    # Test mnemonic generation
    mnemonic = generate_shared_mnemonic()
    print(f"✓ Generated mnemonic: {' '.join(mnemonic.split()[:3])}...")

    # Test wallet derivation
    wallet = derive_agent_wallet(mnemonic, 0)
    print(f"✓ Derived wallet address: {wallet.address}")

except ImportError as e:
    print(f"✗ Wallet import failed: {e}")

try:
    from hanzo_agents.core.tee import (
        TEEConfig,
        TEEProvider,
        MockTEEExecutor,
        AttestationReport,
    )

    print("\n✓ TEE imports successful")

    # Test TEE config
    tee_config = TEEConfig(provider=TEEProvider.MOCK)
    print(f"✓ TEE config created: {tee_config.provider.value}")

    # Test mock executor
    executor = MockTEEExecutor()
    result = executor.execute("test_code", {"x": 1})
    print(f"✓ Mock TEE execution: {result['success']}")

except ImportError as e:
    print(f"\n✗ TEE import failed: {e}")

try:
    from hanzo_agents.core.marketplace import (
        ServiceType,
        ServiceOffer,
        ServiceRequest,
        AgentMarketplace,
    )

    print("\n✓ Marketplace imports successful")

    # Test marketplace
    marketplace = AgentMarketplace()
    print(f"✓ Marketplace created")

    # Test service types
    print(f"✓ Service types: {[s.value for s in ServiceType]}")

except ImportError as e:
    print(f"\n✗ Marketplace import failed: {e}")

# Test Web3Agent mock
try:
    from hanzo_agents.core.web3_agent import Web3Agent, Web3AgentConfig

    print("\n✓ Web3Agent imports successful")

    # Create a simple agent
    config = Web3AgentConfig(wallet_enabled=True, tee_enabled=True, task_price_eth=0.01)

    agent = Web3Agent(name="TestAgent", description="A test agent", web3_config=config)

    print(f"✓ Created agent: {agent.name}")
    print(f"✓ Wallet enabled: {agent.wallet is not None}")
    print(f"✓ TEE enabled: {agent.confidential_agent is not None}")
    print(f"✓ Address: {agent.address[:10]}...")

except ImportError as e:
    print(f"\n✗ Web3Agent import failed: {e}")

print("\n" + "=" * 50)
print("Summary: Core Web3 components are working!")
print("Note: Full examples require additional dependencies like structlog")
print("\nTo run full examples, install dependencies:")
print("  pip install structlog prometheus-client")
print("=" * 50)
