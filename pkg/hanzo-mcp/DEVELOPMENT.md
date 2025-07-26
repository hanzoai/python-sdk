# Hanzo MCP Development Guide

This guide explains how to work with and publish the `hanzo-mcp` package within the Hanzo IDE monorepo.

## Overview

The `hanzo-mcp` package is integrated into the IDE monorepo as a local development dependency. This allows:

1. **Seamless Development**: Changes to MCP are immediately available in the IDE
2. **Independent Publishing**: MCP can be published to PyPI separately
3. **Version Control**: Both IDE and MCP share the same git history

## Project Structure

```
ide/
├── app/dev/
│   ├── pyproject.toml          # IDE dependencies (includes hanzo-mcp as local dep)
│   └── ide/                    # IDE source code
├── pkg/
│   ├── mcp/                    # hanzo-mcp package
│   │   ├── pyproject.toml      # MCP package config
│   │   ├── hanzo_mcp/          # MCP source code
│   │   ├── Makefile            # MCP-specific commands
│   │   └── scripts/
│   │       └── publish.sh      # Publishing helper
│   ├── aci/                    # hanzo-aci package
│   └── mcp-client/             # hanzo-mcp-client package
```

## Development Workflow

### 1. Local Development

The IDE uses MCP as a local development dependency:

```toml
# In app/dev/pyproject.toml
hanzo-mcp = { path = "../../pkg/mcp", develop = true }
```

This means:
- Changes to MCP code are immediately reflected in IDE
- No need to reinstall after changes
- IDE and MCP can be developed together

### 2. Making Changes

```bash
# From the IDE root
cd pkg/mcp

# Make your changes to hanzo_mcp/
vim hanzo_mcp/tools/my_new_tool.py

# Run tests
make test

# Format code
make format

# The changes are immediately available in IDE!
```

### 3. Testing in IDE

```bash
# From IDE root
cd app/dev
make dev  # Starts IDE with your MCP changes
```

## Publishing Workflow

### Quick Method: Using the Makefile

```bash
cd pkg/mcp

# Check current version
make version

# Bump version (choose one)
make bump-patch  # 0.6.13 -> 0.6.14
make bump-minor  # 0.6.13 -> 0.7.0
make bump-major  # 0.6.13 -> 1.0.0

# Run full release process
make release
```

### Detailed Method: Step by Step

1. **Update Version**:
   ```bash
   cd pkg/mcp
   # Edit pyproject.toml and update version
   vim pyproject.toml
   ```

2. **Run Tests**:
   ```bash
   make test
   make lint
   ```

3. **Build Package**:
   ```bash
   make build
   ```

4. **Publish to Test PyPI** (recommended first):
   ```bash
   make publish-test
   # Test installation:
   pip install -i https://test.pypi.org/simple/ hanzo-mcp==0.6.14
   ```

5. **Publish to PyPI**:
   ```bash
   make publish
   ```

### Using the Publish Script

For a guided publishing experience:

```bash
cd pkg/mcp
./scripts/publish.sh
```

This script will:
- Check for uncommitted changes
- Run tests and linting
- Build the package
- Guide you through publishing to Test PyPI or PyPI
- Create a git tag

## Version Management

### Version Conventions

- **Patch** (0.6.X): Bug fixes, minor improvements
- **Minor** (0.X.0): New features, backwards compatible
- **Major** (X.0.0): Breaking changes

### Coordinating with IDE Versions

The IDE and MCP can have independent version numbers. However:

1. **IDE Release**: Can pin to specific MCP version
2. **MCP Update**: IDE automatically uses latest local version
3. **Production**: IDE Docker images include specific MCP version

### After Publishing

1. **Create Git Tag**:
   ```bash
   git tag -a "mcp-v0.6.14" -m "Release hanzo-mcp 0.6.14"
   git push origin mcp-v0.6.14
   ```

2. **Update IDE** (if needed):
   ```bash
   # If you want IDE to use the published version instead of local
   cd app/dev
   # Edit pyproject.toml:
   # hanzo-mcp = "^0.6.14"  # Instead of path dependency
   ```

3. **Update Docker Images**:
   ```bash
   # The build process will use the wheel from pkg/mcp/dist/
   cd app/dev
   make build-docker
   ```

## CI/CD Integration

### GitHub Actions

Push a tag to trigger automated publishing:

```bash
git tag -a "mcp-v0.6.14" -m "Release hanzo-mcp 0.6.14"
git push origin mcp-v0.6.14
```

This will:
1. Run tests
2. Build packages
3. Publish to PyPI
4. Create GitHub release

### Manual Workflow Dispatch

From GitHub Actions tab:
1. Select "Publish Hanzo MCP" workflow
2. Click "Run workflow"
3. Enter version and choose PyPI/Test PyPI

## Troubleshooting

### Common Issues

1. **Import Errors in IDE**:
   ```bash
   cd app/dev
   poetry install  # Reinstall dependencies
   ```

2. **Tests Failing**:
   ```bash
   # Run specific test
   pytest tests/test_specific.py -v
   
   # Run with debugging
   pytest -vvs
   ```

3. **Build Errors**:
   ```bash
   # Clean and rebuild
   make clean
   make build
   ```

4. **Publishing Authentication**:
   ```bash
   # Create ~/.pypirc with your API token
   cat > ~/.pypirc << EOF
   [pypi]
     username = __token__
     password = pypi-...your-token...
   EOF
   ```

### PyPI API Tokens

1. Go to https://pypi.org/manage/account/token/
2. Create a token scoped to `hanzo-mcp`
3. Add to `~/.pypirc` or GitHub secrets

## Best Practices

1. **Test Locally First**: Always test changes in IDE before publishing
2. **Use Test PyPI**: Test package installation before production
3. **Semantic Versioning**: Follow version conventions
4. **Document Changes**: Update CHANGELOG.md
5. **Backwards Compatibility**: Avoid breaking changes in minor versions

## Docker Considerations

When building IDE Docker images:

1. **Wheels are cached**: Built wheels in `pkg/mcp/dist/` are used
2. **Version in Docker**: Check `wheels/hanzo_mcp-*.whl` in Dockerfile
3. **Update Process**:
   ```bash
   cd pkg/mcp
   make build  # Creates wheel
   cd ../../app/dev
   make build-docker  # Uses the wheel
   ```

## Questions?

- **IDE Integration**: Check `app/dev/pyproject.toml`
- **MCP Package**: See `pkg/mcp/README.md`
- **Publishing**: Run `make help` in `pkg/mcp/`