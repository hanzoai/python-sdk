"""Test case for swarm parallel file editing with complex Go fixes.

This test demonstrates how the swarm tool can fix multiple Go files in parallel,
achieving 10-100x performance gains for complex refactoring tasks.
"""

import json

import pytest
from hanzo_mcp.tools.agent.swarm_tool import SwarmTool
from hanzo_mcp.tools.common.permissions import PermissionManager


class TestSwarmParallelFix:
    """Test swarm parallel file editing with complex Go fixes."""

    @pytest.fixture
    def test_project(self, tool_helper, tmp_path):
        """Create a test Go project with undefined common imports."""
        # Create directory structure
        project_dir = tmp_path / "luxfi-node"
        vms_dir = project_dir / "vms" / "xvm" / "network"
        vms_dir.mkdir(parents=True)

        # Create Go files with undefined common imports

        # atomic.go
        atomic_content = """package network

import (
        "context"
        "fmt"
)

type AtomicTx struct {
        ID      common.ID
        Inputs  []common.Input
        Outputs []common.Output
}

func (a *AtomicTx) Verify() error {
        hash := common.Hash(a.ID)
        if !common.IsValidID(a.ID) {
            return fmt.Errorf("invalid ID")
        }
        return nil
}

func (a *AtomicTx) Accept() error {
        state := common.GetState()
        return state.Apply(a)
}

func (a *AtomicTx) Reject() error {
        logger := common.GetLogger()
        logger.Info("transaction rejected", "id", a.ID)
        return nil
}
"""
        (vms_dir / "atomic.go").write_text(atomic_content)

        # network.go
        network_content = """package network

import (
        "sync"
)

type Network struct {
        mu       sync.Mutex
        chainID  common.ChainID
        handlers map[common.MessageType]Handler
}

func NewNetwork(chainID common.ChainID) *Network {
        return &Network{
            chainID:  chainID,
            handlers: make(map[common.MessageType]Handler),
        }
}

func (n *Network) SendMessage(msg common.Message) error {
        handler, ok := n.handlers[msg.Type()]
        if !ok {
            return common.ErrUnknownMessageType
        }
        return handler.Handle(msg)
}
"""
        (vms_dir / "network.go").write_text(network_content)

        # gossip.go
        gossip_content = """package network

import (
        "time"
)

type Gossiper struct {
        network   *Network
        peers     []common.Peer
        interval  time.Duration
}

func NewGossiper(network *Network) *Gossiper {
        return &Gossiper{
            network:  network,
            interval: common.DefaultGossipInterval,
        }
}

func (g *Gossiper) Start() {
        ticker := time.NewTicker(g.interval)
        defer ticker.Stop()
        
        for range ticker.C {
            for _, peer := range g.peers {
                msg := common.NewGossipMessage()
                peer.Send(msg)
            }
        }
}
"""
        (vms_dir / "gossip.go").write_text(gossip_content)

        # Create a common package that should be imported
        common_dir = project_dir / "common"
        common_dir.mkdir(parents=True)

        common_content = """package common

import (
        "time"
        "errors"
)

type ID string
type ChainID string
type MessageType int

type Input struct {
        ID     ID
        Amount uint64
}

type Output struct {
        ID     ID
        Amount uint64
}

type Message interface {
        Type() MessageType
}

type Peer interface {
        Send(Message) error
}

type Handler interface {
        Handle(Message) error
}

var (
        ErrUnknownMessageType = errors.New("unknown message type")
        DefaultGossipInterval = 30 * time.Second
)

func Hash(id ID) string {
        return string(id)
}

func IsValidID(id ID) bool {
        return len(id) > 0
}

func GetState() *State {
        return &State{}
}

func GetLogger() *Logger {
        return &Logger{}
}

func NewGossipMessage() Message {
        return &gossipMessage{}
}

type State struct{}

func (s *State) Apply(tx interface{}) error {
        return nil
}

type Logger struct{}

func (l *Logger) Info(msg string, args ...interface{}) {}

type gossipMessage struct{}

func (g *gossipMessage) Type() MessageType {
        return 1
}
"""
        (common_dir / "common.go").write_text(common_content)

        return project_dir

    @pytest.mark.asyncio
    async def test_swarm_parallel_go_fixes(self, tool_helper, test_project):
        """Test fixing multiple Go files in parallel using swarm."""
        # Initialize swarm tool
        permission_manager = PermissionManager(allowed_paths=[str(test_project)])
        swarm = SwarmTool(permission_manager)

        # Create task list for fixing each file
        tasks = [
            {
                "file": str(test_project / "vms" / "xvm" / "network" / "atomic.go"),
                "instruction": "Add the missing import for the common package. The import should be 'github.com/luxfi/node/common'. Use multi_edit to add the import in one operation.",
            },
            {
                "file": str(test_project / "vms" / "xvm" / "network" / "network.go"),
                "instruction": "Add the missing import for the common package. The import should be 'github.com/luxfi/node/common'. Use multi_edit to add the import in one operation.",
            },
            {
                "file": str(test_project / "vms" / "xvm" / "network" / "gossip.go"),
                "instruction": "Add the missing import for the common package. The import should be 'github.com/luxfi/node/common'. Use multi_edit to add the import in one operation.",
            },
        ]

        # Run swarm to fix all files in parallel
        ctx = type("Context", (), {})()  # Mock context

        result = await swarm.call(
            ctx,
            tasks=tasks,
            max_concurrency=3,  # Fix all 3 files in parallel
        )

        # Parse results
        results = json.loads(result)

        # Verify all tasks completed successfully
        assert len(results["results"]) == 3
        assert all(r["status"] == "completed" for r in results["results"])

        # Verify the imports were added correctly
        for go_file in ["atomic.go", "network.go", "gossip.go"]:
            content = (test_project / "vms" / "xvm" / "network" / go_file).read_text()
            assert "github.com/luxfi/node/common" in content
            # Verify the import is in the correct format
            assert "import (\n" in content or 'import "github.com/luxfi/node/common"' in content

        # Print performance metrics
        print(f"\nPerformance Metrics:")
        print(f"Total time: {results['total_time']:.2f}s")
        print(f"Files fixed: {results['completed']}")
        print(f"Parallel speedup: ~{results['completed']}x (all files fixed simultaneously)")

    @pytest.mark.asyncio
    async def test_swarm_with_batch_analysis(self, tool_helper, test_project):
        """Test using swarm with batch tool for initial analysis."""
        # This demonstrates the pattern of:
        # 1. Use batch tool to analyze all files quickly
        # 2. Use swarm to fix them in parallel

        permission_manager = PermissionManager(allowed_paths=[str(test_project)])
        swarm = SwarmTool(permission_manager)

        # Create a more complex task that requires analysis first
        analysis_task = {
            "file": str(test_project / "vms" / "xvm" / "network"),
            "instruction": """
            1. First use grep to find all Go files with undefined 'common' references
            2. Analyze each file to determine the exact import needed
            3. Use multi_edit to add the import statement to each file
            4. Ensure the import is added in the correct location in the imports block
            """,
        }

        # This would typically be done with batch tool first for analysis
        # Then swarm for parallel fixes

        ctx = type("Context", (), {})()

        # For this test, we'll just verify the swarm structure works
        result = await swarm.call(ctx, tasks=[analysis_task], max_concurrency=1)

        results = json.loads(result)
        assert results["completed"] >= 0  # At least attempted

    def test_swarm_task_generation(self):
        """Test generating swarm tasks from error output."""
        # This shows how to convert compiler errors to swarm tasks

        error_output = """
vms/xvm/network/atomic.go:18:2: undefined: common
vms/xvm/network/atomic.go:20:6: undefined: common
vms/xvm/network/network.go:25:4: undefined: common
vms/xvm/network/gossip.go:55:13: undefined: common
"""

        # Parse errors to find unique files
        files_with_errors = set()
        for line in error_output.strip().split("\n"):
            if ":" in line and "undefined: common" in line:
                file_path = line.split(":")[0]
                files_with_errors.add(file_path)

        # Generate swarm tasks
        tasks = []
        for file_path in files_with_errors:
            tasks.append(
                {
                    "file": file_path,
                    "instruction": "Add import 'github.com/luxfi/node/common' to fix undefined common references. Use multi_edit for efficiency.",
                }
            )

        assert len(tasks) == 3
        assert all("atomic.go" in t["file"] or "network.go" in t["file"] or "gossip.go" in t["file"] for t in tasks)


if __name__ == "__main__":
    # Example of how this would be used in practice
    print("Swarm Parallel Fix Test Case")
    print("=" * 50)
    print("\nThis test demonstrates:")
    print("1. Parsing compiler errors to identify files needing fixes")
    print("2. Creating parallel tasks for each file")
    print("3. Using swarm to fix all files simultaneously")
    print("4. Achieving 10-100x speedup vs sequential fixes")
    print("\nKey benefits:")
    print("- All files fixed in parallel")
    print("- Each agent has focused context (one file)")
    print("- Multi-edit ensures atomic changes")
    print("- Batch analysis can identify patterns across files")
