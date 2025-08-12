"""Simple test of hanzo-agents with Web3 features."""

import sys
import asyncio
from pathlib import Path

# Add hanzo_agents to path
sys.path.insert(0, str(Path(__file__).parent))

# Now import
from hanzo_agents import (
    Web3Agent,
    ServiceType,
    WalletConfig,
    Web3AgentConfig,
    AgentMarketplace,
    generate_shared_mnemonic,
)


async def test_basic_web3_agents():
    """Test basic Web3 agent functionality."""
    print("Testing Hanzo Agents with Web3 Integration")
    print("=" * 50)

    # Create shared mnemonic
    mnemonic = generate_shared_mnemonic()
    print(f"Generated mnemonic (first 3 words): {' '.join(mnemonic.split()[:3])}...")

    # Create two agents
    print("\nCreating Web3-enabled agents...")

    alice = Web3Agent(
        name="Alice",
        description="A helpful assistant",
        web3_config=Web3AgentConfig(
            wallet_enabled=True,
            tee_enabled=True,
            wallet_config=WalletConfig(
                mnemonic=mnemonic, account_index=0, network_rpc="mock://localhost"
            ),
        ),
    )

    bob = Web3Agent(
        name="Bob",
        description="A technical expert",
        web3_config=Web3AgentConfig(
            wallet_enabled=True,
            wallet_config=WalletConfig(
                mnemonic=mnemonic, account_index=1, network_rpc="mock://localhost"
            ),
        ),
    )

    # Give them some initial balance
    alice.earnings = 1.0
    bob.earnings = 0.5

    print(f"\nAlice:")
    print(f"  Address: {alice.address}")
    print(f"  Balance: {alice.balance_eth} ETH")
    print(f"  Has TEE: {alice.confidential_agent is not None}")

    print(f"\nBob:")
    print(f"  Address: {bob.address}")
    print(f"  Balance: {bob.balance_eth} ETH")
    print(f"  Has TEE: {bob.confidential_agent is not None}")

    # Test payment
    print("\n--- Testing Payments ---")

    # Bob requests payment from Alice
    payment_request = await bob.request_payment(
        from_address=alice.address,
        amount_eth=0.1,
        task_description="Technical consulting",
    )

    print(f"Bob requested {payment_request['amount_eth']} ETH from Alice")

    # Alice pays Bob
    tx = await alice.pay_agent(
        to_address=bob.address, amount_eth=0.1, reason="Payment for consulting"
    )

    if tx:
        print(f"Alice sent payment: {tx.hash}")
        print(f"Alice new balance: {alice.balance_eth} ETH")
        print(f"Bob new balance: {bob.balance_eth} ETH")

    # Test TEE execution
    print("\n--- Testing TEE Confidential Execution ---")

    if alice.confidential_agent:
        code = """
# Confidential computation
result = {
    "computation": "sensitive",
    "value": inputs["x"] * inputs["y"],
    "secure": True
}
"""

        result = await alice.execute_confidential(code, {"x": 42, "y": 2})

        print(f"TEE computation result: {result['result']['value']}")
        print(f"Attestation available: {'attestation' in result}")

    # Test marketplace
    print("\n--- Testing Marketplace ---")

    marketplace = AgentMarketplace()

    # Alice offers a service
    offer_id = marketplace.post_offer(
        agent=alice,
        service_type=ServiceType.CUSTOM,
        description="AI assistance and code review",
        price_eth=0.05,
    )

    print(f"Alice posted offer: {offer_id}")

    # Bob requests a service
    request_id = marketplace.post_request(
        agent=bob,
        service_type=ServiceType.CUSTOM,
        description="Need help with code review",
        max_price_eth=0.1,
    )

    print(f"Bob posted request: {request_id}")

    # Check matches
    if marketplace.matches:
        match = list(marketplace.matches.values())[0]
        print(
            f"Match found! {match.offer.agent_name} <-> {match.request.requester_name}"
        )

    # Test agent stats
    print("\n--- Agent Statistics ---")

    alice_stats = alice.get_stats()
    bob_stats = bob.get_stats()

    print(f"\nAlice stats:")
    for key, value in alice_stats.items():
        print(f"  {key}: {value}")

    print(f"\nBob stats:")
    for key, value in bob_stats.items():
        print(f"  {key}: {value}")

    print("\n✅ All tests completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_basic_web3_agents())
