# hanzo-tools-repl

Multi-language REPL tool with Jupyter kernel backend for interactive code evaluation.

## Features

- **Multi-language support**: Python, Node.js/TypeScript, Bash, Ruby, Go, Rust
- **Persistent sessions**: Maintain state across evaluations
- **Jupyter kernels**: Uses standard Jupyter infrastructure
- **Agent-friendly**: Designed for AI agent workflows

## Installation

```bash
pip install hanzo-tools-repl

# With all kernels
pip install hanzo-tools-repl[full]
```

## Usage

```python
from hanzo_tools.repl import ReplTool

repl = ReplTool()

# Start a Python session
await repl.call(action="start", language="python")

# Evaluate code
result = await repl.call(action="eval", code="x = 1 + 1\nprint(x)")
# Output: [1] 2

# Node.js/TypeScript
await repl.call(action="start", language="node")
result = await repl.call(action="eval", code="const arr = [1,2,3].map(n => n*2)")

# List sessions
await repl.call(action="list")

# Get history
await repl.call(action="history", limit=10)

# Stop session
await repl.call(action="stop")
```

## Supported Languages

| Language | Kernel | Install |
|----------|--------|---------|
| Python | ipykernel | `pip install ipykernel` |
| Node.js/TypeScript | tslab | `npm install -g tslab && tslab install` |
| Bash | bash_kernel | `pip install bash_kernel` |
| Ruby | iruby | `gem install iruby` |
| Go | gophernotes | See gophernotes docs |
| Rust | evcxr | `cargo install evcxr_jupyter` |

## License

MIT - Hanzo Industries Inc
