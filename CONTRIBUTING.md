# Contributing to Hanzo Python SDK

We welcome contributions to the Hanzo Python SDK! This document provides guidelines for contributing to the project.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct:
- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive criticism
- Accept feedback gracefully

## Getting Started

### Prerequisites

- Python 3.10 or higher
- `uv` package manager
- Git

### Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/your-username/python-sdk.git
   cd python-sdk
   ```

3. Install dependencies:
   ```bash
   make setup
   ```

4. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Workflow

### Code Style

We use `ruff` for linting and formatting:

```bash
# Format code
make format

# Check linting
make lint

# Type checking
make type-check
```

### Testing

All contributions must include tests:

```bash
# Run all tests
make test

# Run specific package tests
cd pkg/hanzo && pytest tests/

# Run with coverage
pytest tests/ --cov=hanzo --cov-report=html
```

### Documentation

- Update README files for any new features
- Add docstrings to all public functions/classes
- Include usage examples in docstrings
- Update API documentation if needed

## Contribution Process

### 1. Find or Create an Issue

- Check existing issues first
- Create a new issue for bugs or features
- Get feedback before starting major work

### 2. Make Changes

- Write clean, readable code
- Follow existing patterns and conventions
- Keep commits small and focused
- Write descriptive commit messages

### 3. Commit Guidelines

We follow conventional commits:

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Build/tooling changes

Examples:
```bash
feat(agents): add parallel execution support
fix(mcp): resolve file permission issue
docs(network): update API documentation
```

### 4. Submit Pull Request

1. Push your branch:
   ```bash
   git push origin feature/your-feature-name
   ```

2. Create a pull request on GitHub

3. Fill out the PR template:
   - Describe what changes you made
   - Link related issues
   - Include test results
   - Add screenshots if applicable

4. Wait for review and address feedback

## Package-Specific Guidelines

### Core SDK (`pkg/hanzoai`)
- Maintain OpenAI compatibility
- Preserve backward compatibility
- Document breaking changes

### CLI (`pkg/hanzo`)
- Keep commands intuitive
- Provide helpful error messages
- Include --help for all commands

### MCP (`pkg/hanzo-mcp`)
- Follow MCP specification
- Ensure tool safety
- Document permissions required

### Agents (`pkg/hanzo-agents`)
- Keep agents focused and specialized
- Provide clear agent descriptions
- Include usage examples

### Network (`pkg/hanzo-network`)
- Ensure thread safety
- Handle network failures gracefully
- Document resource requirements

## Testing Requirements

### Unit Tests
- Test individual functions/methods
- Mock external dependencies
- Aim for >80% coverage

### Integration Tests
- Test component interactions
- Use real services when possible
- Mark with `@pytest.mark.integration`

### End-to-End Tests
- Test complete workflows
- Run in CI/CD pipeline
- Document test scenarios

## Code Review Process

### What We Look For

- **Correctness**: Does it work as intended?
- **Tests**: Are there adequate tests?
- **Documentation**: Is it well-documented?
- **Style**: Does it follow our conventions?
- **Performance**: Are there any bottlenecks?
- **Security**: Are there security concerns?

### Review Timeline

- Initial review: Within 2-3 business days
- Follow-up reviews: Within 1-2 business days
- Small fixes: Same day if possible

## Release Process

1. **Version Bump**: Update version in `pyproject.toml`
2. **Changelog**: Update CHANGELOG.md
3. **Testing**: Run full test suite
4. **Documentation**: Update docs if needed
5. **Tag**: Create version tag
6. **Release**: Publish to PyPI

## Getting Help

### Resources

- [Documentation](https://docs.hanzo.ai)
- [Discord Community](https://discord.gg/hanzo)
- [GitHub Discussions](https://github.com/hanzoai/python-sdk/discussions)

### Contact

- General questions: support@hanzo.ai
- Security issues: security@hanzo.ai
- Partnership: partners@hanzo.ai

## Recognition

Contributors are recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project documentation

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.

Thank you for contributing to Hanzo! 🎉