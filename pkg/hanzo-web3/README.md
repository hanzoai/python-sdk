# Hanzo Web3 SDK

Enterprise blockchain infrastructure SDK for Python. Multi-chain RPC, Token APIs, NFT APIs, Smart Wallets, Webhooks, and more.

## Installation

```bash
pip install hanzo-web3

# Or with uv
uv add hanzo-web3
```

## Quick Start

```python
from hanzo_web3 import Client

# Initialize client
client = Client(api_key="hz_live_...")

# Get latest block number
block = client.rpc.eth_block_number(chain="ethereum")
print(f"Latest block: {block}")

# Get token balances
balances = client.tokens.get_balances("0x...", chain="polygon")
for token in balances:
    print(f"{token['symbol']}: {token['balance_formatted']}")

# Get NFTs owned
nfts = client.nfts.get_owned("0x...", chain="ethereum")
for nft in nfts:
    print(f"{nft['name']} #{nft['token_id']}")
```

## Async Client

```python
import asyncio
from hanzo_web3 import AsyncClient

async def main():
    async with AsyncClient(api_key="hz_live_...") as client:
        # Parallel requests
        eth_block, polygon_block = await asyncio.gather(
            client.rpc.eth_block_number(chain="ethereum"),
            client.rpc.eth_block_number(chain="polygon"),
        )
        print(f"ETH: {eth_block}, Polygon: {polygon_block}")

asyncio.run(main())
```

## Features

### RPC API
Direct JSON-RPC access to 100+ chains:
```python
# Any RPC method
result = client.rpc.call("eth_getBalance", ["0x...", "latest"], chain="ethereum")

# Convenience methods
balance = client.rpc.eth_get_balance("0x...", chain="ethereum")
```

### Token API
ERC-20 token data:
```python
# Get all token balances
balances = client.tokens.get_balances("0x...", chain="ethereum")

# Get token metadata
metadata = client.tokens.get_metadata("0xA0b8...", chain="ethereum")
```

### NFT API
NFT collections and metadata:
```python
# Get owned NFTs
nfts = client.nfts.get_owned("0x...", chain="ethereum")

# Get NFT metadata
metadata = client.nfts.get_metadata("0x...", "1234", chain="ethereum")
```

### Smart Wallets (ERC-4337)
Account abstraction:
```python
# Create smart wallet
wallet = client.wallets.create(owner="0x...", chain="base")
print(f"Smart wallet: {wallet['address']}")

# Get wallet details
info = client.wallets.get(wallet['address'], chain="base")
```

### Webhooks
Real-time event notifications:
```python
# Create webhook
webhook = client.webhooks.create(
    url="https://your-server.com/webhook",
    event_type="ADDRESS_ACTIVITY",
    chain="ethereum",
    filters={"addresses": ["0x..."]}
)

# List webhooks
webhooks = client.webhooks.list()

# Delete webhook
client.webhooks.delete(webhook["id"])
```

## Supported Chains

| Chain | Networks |
|-------|----------|
| Ethereum | mainnet, sepolia, holesky |
| Polygon | mainnet, amoy |
| Arbitrum | mainnet, sepolia |
| Optimism | mainnet, sepolia |
| Base | mainnet, sepolia |
| Avalanche | mainnet, fuji |
| BNB Chain | mainnet, testnet |
| Lux | mainnet, testnet |
| Solana | mainnet, devnet |
| + 90 more | ... |

## Environment Variables

```bash
# API Key (alternative to passing in code)
export HANZO_WEB3_API_KEY=hz_live_...

# Custom API URL (for white-label deployments)
export HANZO_WEB3_BASE_URL=https://api.lux.cloud
```

## Error Handling

```python
from hanzo_web3 import Client
from hanzo_web3.exceptions import (
    AuthenticationError,
    RateLimitError,
    ChainNotSupportedError,
)

try:
    client = Client(api_key="invalid")
    client.rpc.eth_block_number()
except AuthenticationError:
    print("Invalid API key")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after}s")
except ChainNotSupportedError as e:
    print(f"Chain {e.chain} not supported")
```

## Links

- [Documentation](https://docs.web3.hanzo.ai)
- [Dashboard](https://web3.hanzo.ai)
- [API Reference](https://docs.web3.hanzo.ai/api)
- [GitHub](https://github.com/hanzoai/python-sdk)

## License

Apache 2.0 - See [LICENSE](LICENSE) for details.
