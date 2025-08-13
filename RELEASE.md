# Release Process for Hanzo Python SDK

This document describes the automated release process for all Python packages in this repository.

## 📦 Packages

The following Python packages are managed in this repository:

- **hanzo** - Core Hanzo AI SDK
- **hanzo-network** - Network utilities for Hanzo AI
- **hanzo-mcp** - Model Context Protocol implementation
- **hanzo-agents** - Agent framework for Hanzo AI
- **hanzo-memory** - Memory management for AI agents
- **hanzo-aci** - AI Chain Infrastructure
- **hanzo-repl** - REPL for Hanzo AI

## 🚀 Automated Release Process

### CI/CD Pipeline

The release process is fully automated through GitHub Actions with two methods:

#### Method 1: Automatic Version Detection (Recommended)
**Every push to `main` branch automatically:**
1. Runs all tests
2. Checks each package's version against PyPI
3. Publishes any packages with new versions
4. Skips packages already published

**To release this way:**
```bash
# Update version in pyproject.toml
# Commit and push to main
git add -A
git commit -m "bump: hanzo-mcp to v1.2.3"
git push origin main
# CI automatically publishes if version is new!
```

#### Method 2: Tag-based Release
1. **Tests Run First**: All tests must pass before any package is published
2. **Tag-based Triggers**: Pushing a tag triggers the release process
3. **Automatic PyPI Upload**: Packages are automatically built and uploaded to PyPI

### Workflow Files

- **`.github/workflows/publish-pypi.yml`**: Main publishing workflow
- **`.github/workflows/hanzo-packages-ci.yml`**: CI with integrated publishing
- **`.github/workflows/test.yml`**: Test suite that must pass

## 📝 How to Release

### Option 1: Automatic (Easiest) 🎯

Simply update the version and push to main:

```bash
# Update version in package's pyproject.toml
vim pkg/hanzo-mcp/pyproject.toml  # Change version = "1.2.3"

# Commit and push
git add -A
git commit -m "Release hanzo-mcp v1.2.3"
git push origin main

# CI will automatically detect and publish the new version!
```

### Option 2: Using Tags

#### Release All Packages

To release all packages with the same version:

```bash
# Update version in all pyproject.toml files
# Then create and push a tag
git tag v1.2.3
git push origin v1.2.3
```

#### Release Individual Package

To release a specific package:

```bash
# Update version in the specific package's pyproject.toml
# Then create and push a package-specific tag
git tag hanzo-mcp-1.2.3
git push origin hanzo-mcp-1.2.3
```

### Tag Naming Convention

- **`v*`** - Releases all packages (e.g., `v1.2.3`)
- **`hanzo-*`** - Releases the main hanzo package (e.g., `hanzo-1.2.3`)
- **`hanzo-network-*`** - Releases hanzo-network package
- **`hanzo-mcp-*`** - Releases hanzo-mcp package
- **`hanzo-agents-*`** - Releases hanzo-agents package
- **`hanzo-memory-*`** - Releases hanzo-memory package
- **`hanzo-aci-*`** - Releases hanzo-aci package
- **`hanzo-repl-*`** - Releases hanzo-repl package

## 🔧 Manual Release (Emergency)

If automated release fails, you can manually publish:

```bash
# Set PyPI token
export PYPI_TOKEN=your_token_here

# Publish all packages
./bin/publish-all-packages.sh

# Or publish specific package
./bin/publish-all-packages.sh hanzo-mcp
```

## ✅ Release Checklist

Before creating a release tag:

1. [ ] Update version in `pyproject.toml` file(s)
2. [ ] Update CHANGELOG if applicable
3. [ ] Ensure all tests pass locally
4. [ ] Commit all changes
5. [ ] Create and push tag

## 🔒 Security

- PyPI tokens are stored as GitHub secrets
- Use `HANZO_PYPI_TOKEN` or `PYPI_TOKEN` secret names
- Tokens have package-specific or organization-wide permissions

## 📊 Release Status

You can monitor release status at:

- [GitHub Actions](https://github.com/hanzoai/python-sdk/actions)
- [PyPI - hanzo](https://pypi.org/project/hanzo/)
- [PyPI - hanzo-network](https://pypi.org/project/hanzo-network/)
- [PyPI - hanzo-mcp](https://pypi.org/project/hanzo-mcp/)
- [PyPI - hanzo-agents](https://pypi.org/project/hanzo-agents/)
- [PyPI - hanzo-memory](https://pypi.org/project/hanzo-memory/)
- [PyPI - hanzo-aci](https://pypi.org/project/hanzo-aci/)
- [PyPI - hanzo-repl](https://pypi.org/project/hanzo-repl/)

## 🐛 Troubleshooting

### Tests Failing

If tests fail, the release will not proceed. Check:
- Test logs in GitHub Actions
- Local test execution with `pytest`

### PyPI Upload Fails

Common issues:
- Version already exists on PyPI
- Invalid PyPI token
- Network issues

Solutions:
- Bump version number
- Check GitHub secrets configuration
- Retry the workflow

### Package Not Publishing

Ensure:
- Tag matches the naming convention
- Package directory exists in `pkg/`
- `pyproject.toml` is properly configured

## 📈 Version Management

We follow semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking API changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

## 🤝 Contributing

When adding a new package:

1. Create package directory in `pkg/`
2. Add `pyproject.toml` with proper configuration
3. Update CI workflows to include the new package
4. Add package to this documentation

---

For questions or issues, please open an issue on [GitHub](https://github.com/hanzoai/python-sdk/issues).