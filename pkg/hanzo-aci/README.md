# Agent-Computer Interface (ACI) for Dev

An Agent-Computer Interface (ACI) designed for software development agents [Dev](https://github.com/hanzoai/Dev). This package provides essential tools and interfaces for AI agents to interact with computer systems for software development tasks.

## Features

- **Code Editor Interface**: Sophisticated editing capabilities through the `editor` module
  - File creation and modification
  - Code editing
  - Configuration management

- **Code Linting**: Built-in linting capabilities via the `linter` module
  - Tree-sitter based code analysis
  - Python-specific linting support

- **Utility Functions**: Helper modules for common operations
  - Shell command execution utilities
  - Diff generation and analysis
  - Logging functionality

## Installation

```bash
pip install dev-aci
```

Or using Poetry:

```bash
poetry add dev-aci
```

## Project Structure

```
dev_aci/
├── editor/           # Code editing functionality
├── linter/           # Code linting capabilities
└── utils/            # Utility functions
```

## Development

1. Clone the repository:
```bash
git clone https://github.com/hanzoai/dev-aci.git
cd dev-aci
```

2. Install development dependencies:
```bash
poetry install
```

3. Configure pre-commit-hooks
```bash
make install-pre-commit-hooks
```

4. Run tests:
```bash
poetry run pytest
```

## License

This project is licensed under the MIT License.
