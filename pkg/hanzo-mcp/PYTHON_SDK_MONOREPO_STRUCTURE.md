# Python SDK Monorepo Structure

Transform python-sdk into a monorepo with the following structure:

```
python-sdk/
├── pkg/
│   ├── hanzoai/               # Core SDK (current src/hanzoai)
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   └── src/
│   │       └── hanzoai/
│   │           ├── __init__.py
│   │           ├── agents.py
│   │           ├── mcp.py
│   │           ├── cluster.py
│   │           └── ... (existing SDK files)
│   │
│   ├── hanzo-cluster/         # Local AI cluster management
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   └── src/
│   │       └── hanzo_cluster/
│   │           ├── __init__.py
│   │           ├── cluster.py
│   │           ├── exo_integration.py
│   │           ├── models.py
│   │           └── api.py
│   │
│   ├── hanzo-miner/           # Distributed compute mining
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   └── src/
│   │       └── hanzo_miner/
│   │           ├── __init__.py
│   │           ├── miner.py
│   │           ├── wallet.py
│   │           ├── rewards.py
│   │           └── network.py
│   │
│   ├── hanzo-mcp/             # MCP tools (move from ide/pkg/mcp)
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   └── src/
│   │       └── hanzo_mcp/
│   │           └── ... (all current mcp code)
│   │
│   ├── hanzo-agents/          # Agent SDK (move from ide/pkg/agents)
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   └── src/
│   │       └── hanzo_agents/
│   │           └── ... (all current agents code)
│   │
│   ├── hanzo-network/         # Agent networks (move from ide/pkg)
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   └── src/
│   │       └── hanzo_network/
│   │           └── ... (all current network code)
│   │
│   ├── hanzo-memory/          # Memory tools
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   └── src/
│   │       └── hanzo_memory/
│   │           ├── __init__.py
│   │           ├── kv_store.py
│   │           ├── vector_store.py
│   │           └── rag.py
│   │
│   └── hanzo-tools/           # Unified tools package
│       ├── pyproject.toml
│       ├── README.md
│       └── src/
│           └── hanzo_tools/
│               ├── __init__.py
│               ├── filesystem/
│               ├── search/
│               ├── git/
│               ├── jupyter/
│               └── shell/
│
├── tests/                     # Unified test suite
│   ├── test_hanzoai/
│   ├── test_cluster/
│   ├── test_miner/
│   ├── test_mcp/
│   ├── test_agents/
│   ├── test_network/
│   ├── test_memory/
│   └── test_integration/
│
├── docs/                      # Unified documentation
│   ├── api/
│   ├── guides/
│   └── examples/
│
├── examples/                  # Example code
│   ├── local_ai/
│   ├── agent_networks/
│   ├── mining/
│   └── unified/
│
├── scripts/                   # Build and utility scripts
│   ├── build_all.py
│   ├── test_all.py
│   └── publish.py
│
├── Makefile                   # Top-level makefile
├── pyproject.toml            # Workspace configuration
├── README.md
└── .github/
    └── workflows/
        ├── ci.yml
        └── release.yml
```

## Migration Plan

### Phase 1: Setup Monorepo Structure
1. Create pkg/ directory structure
2. Move current src/hanzoai to pkg/hanzoai/src/hanzoai
3. Create workspace pyproject.toml with tool.rye.workspace

### Phase 2: Extract Modules
1. Extract cluster code from hanzoai/cluster.py to pkg/hanzo-cluster
2. Extract miner code to pkg/hanzo-miner  
3. Move hanzo-mcp from ide/pkg/mcp to pkg/hanzo-mcp
4. Move hanzo-agents from ide/pkg/agents to pkg/hanzo-agents
5. Move hanzo-network from ide/pkg to pkg/hanzo-network

### Phase 3: Create New Packages
1. Create hanzo-memory for memory/RAG tools
2. Create hanzo-tools as unified tool package

### Phase 4: Update Dependencies
1. Update hanzoai to import from hanzo-cluster, hanzo-miner, etc.
2. Update all cross-package dependencies
3. Create optional dependencies groups

### Phase 5: Testing & CI
1. Create unified test suite
2. Setup GitHub Actions for monorepo
3. Configure publishing workflow

## Workspace Configuration (pyproject.toml)

```toml
[project]
name = "hanzo-python-sdk"
version = "2.0.0"
description = "Hanzo AI Python SDK Monorepo"

[tool.rye]
managed = true
workspace = { members = ["pkg/*"] }

[tool.rye.scripts]
test = "pytest tests/"
lint = "ruff check pkg/"
format = "ruff format pkg/"
typecheck = "mypy pkg/"
build-all = "python scripts/build_all.py"
test-all = "python scripts/test_all.py"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

## Individual Package Structure

Each package follows the same pattern:

### pkg/hanzo-cluster/pyproject.toml
```toml
[project]
name = "hanzo-cluster"
version = "0.1.0"
description = "Local AI cluster management for Hanzo"
dependencies = [
    "exo-explore>=0.1.0",
    "httpx>=0.23.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = ["pytest", "pytest-asyncio"]

[project.urls]
Homepage = "https://github.com/hanzoai/python-sdk"
Repository = "https://github.com/hanzoai/python-sdk/tree/main/pkg/hanzo-cluster"
```

## Benefits

1. **Modular**: Each package can be installed independently
2. **Unified Development**: Single repo for all Python packages
3. **Consistent CI/CD**: One set of workflows for everything
4. **Easy Testing**: Test across packages easily
5. **Version Management**: Coordinate releases across packages

## Commands

```bash
# Install all packages in development mode
rye sync

# Run all tests
rye run test-all

# Build all packages
rye run build-all

# Work on specific package
cd pkg/hanzo-cluster
rye sync
rye test

# Install specific packages for users
pip install hanzoai  # Gets core SDK
pip install hanzoai[cluster]  # With cluster support
pip install hanzoai[miner]    # With mining support
pip install hanzoai[all]      # Everything
```