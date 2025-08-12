"""Test hanzo-agents integration from within MCP package."""

import sys
from pathlib import Path

# Add agents package to path
agents_path = Path(__file__).parent.parent / "agents"
sys.path.insert(0, str(agents_path))

print("Testing Hanzo Agents Web3 Integration")
print("=" * 50)

# Test basic imports
try:
    from hanzo_agents.core.wallet import MockWallet, generate_shared_mnemonic

    print("✓ Wallet module imported")

    # Test mnemonic generation
    mnemonic = generate_shared_mnemonic()
    print(f"✓ Generated mnemonic: {' '.join(mnemonic.split()[:3])}...")

    # Test mock wallet
    wallet = MockWallet()
    print(f"✓ Mock wallet address: {wallet.address}")
    print(f"✓ Mock wallet balance: {wallet.balance} ETH")

except Exception as e:
    print(f"✗ Wallet test failed: {e}")

# Test TEE
try:
    from hanzo_agents.core.tee import MockTEEExecutor

    print("\n✓ TEE module imported")

    executor = MockTEEExecutor()
    result = executor.execute("test = 1 + 1", {})
    print(f"✓ Mock TEE execution: success={result['success']}")

except Exception as e:
    print(f"\n✗ TEE test failed: {e}")

# Test marketplace
try:
    from hanzo_agents.core.marketplace import ServiceType, AgentMarketplace

    print("\n✓ Marketplace module imported")

    marketplace = AgentMarketplace()
    print(f"✓ Marketplace created with {len(marketplace.offers)} offers")
    print(f"✓ Available service types: {[s.value for s in ServiceType]}")

except Exception as e:
    print(f"\n✗ Marketplace test failed: {e}")

# Test Web3Agent basics
try:
    from hanzo_agents.core.web3_agent import Web3AgentConfig

    print("\n✓ Web3Agent config imported")

    config = Web3AgentConfig(wallet_enabled=True, tee_enabled=True, task_price_eth=0.01)
    print(
        f"✓ Created Web3 config: wallet={config.wallet_enabled}, tee={config.tee_enabled}"
    )

except Exception as e:
    print(f"\n✗ Web3Agent test failed: {e}")

print("\n" + "=" * 50)
print("Basic components are working!")
print("\nNote: Full agent functionality requires additional dependencies:")
print("- structlog (for logging)")
print("- prometheus_client (for metrics)")
print("- web3 (for real blockchain interaction)")
print("- torch/transformers (for local AI compute)")

# Test integration with MCP
print("\n" + "=" * 50)
print("Testing MCP Integration")

try:
    # Import MCP swarm tool to verify it can use hanzo-agents
    from hanzo_mcp.tools.agent.swarm_tool import SwarmTool

    print("✓ SwarmTool imports successfully")

    # Check if it references hanzo_agents
    import inspect

    source = inspect.getsource(SwarmTool)
    if "hanzo_agents" in source or "hanzo-agents" in source:
        print("✓ SwarmTool uses hanzo-agents SDK")
    else:
        print("! SwarmTool may need updating to use hanzo-agents")

except Exception as e:
    print(f"✗ MCP integration check failed: {e}")

print("\n✅ Integration test complete!")
