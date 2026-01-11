# PyPI Release Automation Design Document

## Overview

This document outlines the design for automating PyPI package releases using GitHub Actions. The workflow will automatically create GitHub releases and publish packages to PyPI whenever a git tag is pushed to the repository.

## Goals

- **Automate the release process**: Eliminate manual steps for creating releases and publishing to PyPI
- **Ensure consistency**: Standardize version management and release artifacts
- **Maintain security**: Securely handle PyPI credentials and tokens
- **Provide traceability**: Link git tags, GitHub releases, and PyPI packages

## Architecture

### Workflow Components

The automation consists of two GitHub Actions workflows:

1. **Release Creation Workflow** (`create-release.yml`)
   - Triggered by: Git tag push (e.g., `v1.0.0`)
   - Purpose: Create a GitHub release from the tag
   - Output: GitHub release with release notes

2. **PyPI Publishing Workflow** (`publish-pypi.yml`)
   - Triggered by: GitHub release creation
   - Purpose: Build and publish package to PyPI
   - Output: Published package on PyPI

### Workflow Diagram

```
Developer Action
    │
    ├─> git tag v1.0.0
    │   └─> git push origin v1.0.0
    │
    └─> GitHub receives tag push
        │
        ├─> [Workflow 1] create-release.yml
        │   ├─> Extract version from tag
        │   ├─> Generate release notes (optional)
        │   └─> Create GitHub Release
        │
        └─> [Workflow 2] publish-pypi.yml (triggered by release)
            ├─> Checkout code
            ├─> Set up Python/uv
            ├─> Build package (hatchling)
            ├─> Publish to PyPI
            └─> Verify publication
```

## Detailed Workflow Design

### Workflow 1: Create Release (`create-release.yml`)

**Trigger**: `push` event with tag pattern `v*`

**Steps**:

1. **Extract version from tag**
   - Parse tag name (e.g., `v1.0.0` → `1.0.0`)
   - Validate semantic versioning format
   - Verify tag matches `pyproject.toml` version (optional check)

2. **Generate release notes** (optional)
   - Extract changelog from commits since last tag
   - Or use tag message as release notes
   - Or read from `CHANGELOG.md` if present

3. **Create GitHub Release**
   - Use GitHub API or `gh` CLI
   - Set release title: `v{version}`
   - Set release body: Generated notes or tag message
   - Mark as latest release if appropriate

**Configuration**:

- Workflow file: `.github/workflows/create-release.yml`
- Permissions: `contents: write` (to create releases)

### Workflow 2: Publish to PyPI (`publish-pypi.yml`)

**Trigger**: `release` event with `published` action

**Steps**:

1. **Environment Setup**
   - Checkout repository code
   - Set up Python (using `actions/setup-python`)
   - Install `uv` (or use existing setup)
   - Install build dependencies

2. **Version Verification**
   - Extract version from release tag
   - Verify `pyproject.toml` version matches tag version
   - Fail if versions don't match (prevents publishing wrong version)

3. **Build Package**
   - Run `uv build` or `python -m build`
   - Generate source distribution (sdist) and wheel
   - Verify build artifacts

4. **Publish to PyPI**
   - Use `uv publish` or `twine upload`
   - Authenticate using PyPI API token (stored as GitHub secret)
   - Upload both sdist and wheel
   - Handle existing version errors gracefully

5. **Verification** (optional)
   - Wait for PyPI to process upload
   - Verify package is available on PyPI
   - Optionally run smoke test installation

**Configuration**:

- Workflow file: `.github/workflows/publish-pypi.yml`
- Permissions: `contents: read` (to checkout code)
- Secrets required: `PYPI_API_TOKEN`

## Implementation Details

### Version Management

**Current State**: Version is defined in `pyproject.toml`:

```toml
[project]
version = "0.8.0"
```

**Requirements**:

- Tag format: `v{version}` (e.g., `v0.8.0`, `v1.0.0`)
- Tag version must match `pyproject.toml` version
- Semantic versioning recommended (MAJOR.MINOR.PATCH)

**Version Sync Strategy**:

- **Option A (Recommended)**: Manual sync - developer ensures tag matches `pyproject.toml` before tagging
- **Option B**: Automated sync - workflow updates `pyproject.toml` from tag (requires commit back to repo)
- **Option C**: Extract version from tag only - don't verify against `pyproject.toml`

**Recommendation**: Option A with validation check in workflow

### Security Considerations

**PyPI API Token**:

- Store as GitHub repository secret: `PYPI_API_TOKEN`
- Use PyPI trusted publishing (preferred) or API token
- Token should have minimal required permissions
- Never expose token in logs or outputs

**GitHub Permissions**:

- Use least-privilege principle
- Release workflow: `contents: write` (for creating releases)
- Publish workflow: `contents: read` (for checking out code)

**Token Setup Instructions**:

1. Create PyPI API token at <https://pypi.org/manage/account/token/>
2. Add as GitHub secret: Settings → Secrets and variables → Actions → New repository secret
3. Name: `PYPI_API_TOKEN`
4. Value: `pypi-...` (token string)

### Build Configuration

**Build Backend**: `hatchling` (already configured in `pyproject.toml`)

**Build Command Options**:

- `uv build` (if using uv 0.1.0+)
- `python -m build` (requires `build` package)
- `hatchling build` (direct)

**Publish Command Options**:

- `uv publish` (if using uv 0.1.0+)
- `twine upload dist/*` (traditional, requires `twine`)

**Recommendation**: Use `uv build` and `uv publish` for consistency with project tooling

### Release Notes Generation

**Options**:

1. **Tag message**: Use git tag annotation message
2. **Changelog file**: Read from `CHANGELOG.md` or `docs/release.md`
3. **Auto-generated**: Extract commits since last tag
4. **Manual**: Require release notes in tag message

**Recommendation**: Start with tag message, optionally enhance with auto-generated changelog

## Workflow Files Structure

```
.github/
└── workflows/
    ├── create-release.yml    # Creates GitHub release from tag
    └── publish-pypi.yml      # Publishes to PyPI on release
```

## Error Handling

### Common Failure Scenarios

1. **Tag version mismatch**
   - Tag: `v1.0.0`, `pyproject.toml`: `0.9.0`
   - Action: Fail workflow with clear error message

2. **PyPI version already exists**
   - Action: Fail gracefully with informative message
   - Note: PyPI doesn't allow overwriting versions

3. **Invalid tag format**
   - Tag: `release-1.0.0` (missing `v` prefix)
   - Action: Skip workflow or fail with guidance

4. **Build failures**
   - Action: Fail workflow, don't create release or publish

5. **Network/PyPI outages**
   - Action: Retry logic or manual intervention required

### Rollback Procedures

- **Before PyPI publish**: Delete GitHub release, delete tag
- **After PyPI publish**: Cannot delete from PyPI, but can yank version
    - Command: `twine yank --repository pypi mgmt==1.0.0`
    - Or via PyPI web interface

## Testing Strategy

### Local Testing

1. **Test build locally**:

   ```bash
   uv build
   ```

2. **Test publish to TestPyPI**:

   ```bash
   uv publish --repository testpypi
   ```

3. **Verify package installation**:

   ```bash
   pip install --index-url https://test.pypi.org/simple/ mgmt
   ```

### Workflow Testing

1. **Test with pre-release tag**: Use `v0.0.0-test` or similar
2. **Test with TestPyPI**: Configure workflow to use TestPyPI for testing
3. **Dry-run mode**: Use `--dry-run` flags where available

## Migration Plan

### Phase 1: Setup

1. Create GitHub Actions workflow files
2. Configure PyPI API token secret
3. Test with TestPyPI

### Phase 2: Validation

1. Create test tag and verify workflows
2. Test error scenarios
3. Document process

### Phase 3: Production

1. Update `docs/release.md` with new process
2. Create first production release
3. Monitor and iterate

## Example Usage

### Developer Workflow

```bash
# 1. Update version in pyproject.toml
# Edit: version = "0.9.0"

# 2. Commit changes
git add pyproject.toml
git commit -m "Bump version to 0.9.0"

# 3. Create and push tag
git tag -a v0.9.0 -m "Release version 0.9.0

- Feature: Added new search functionality
- Bug fix: Fixed download issue
- Documentation: Updated README"

git push origin main
git push origin v0.9.0

# 4. GitHub Actions automatically:
#    - Creates GitHub release
#    - Publishes to PyPI
```

## Future Enhancements

1. **Automated version bumping**: Update `pyproject.toml` from tag
2. **Changelog generation**: Auto-generate from commit messages
3. **Pre-release checks**: Run tests, linting before release
4. **Multi-environment**: Support TestPyPI and PyPI
5. **Release notifications**: Slack/Discord notifications on release
6. **Version validation**: Enforce semantic versioning rules
7. **Draft releases**: Support draft releases for review

## Dependencies

### Required GitHub Actions

- `actions/checkout@v4` (or latest)
- `actions/setup-python@v5` (or latest)
- `pypa/gh-action-pypi-publish@release/v1` (optional, for PyPI publishing)

### Required Python Packages (for build)

- `hatchling` (already in build-system)
- `build` (if not using uv)
- `twine` (if not using uv publish)

### Optional Tools

- `gh` CLI (for GitHub release creation)
- `uv` (already used in project)

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [PyPI Publishing Guide](https://packaging.python.org/en/latest/guides/publishing-package-distribution-files-to-pypi/)
- [Semantic Versioning](https://semver.org/)
- [Hatchling Documentation](https://hatch.pypa.io/latest/)
- [uv Documentation](https://docs.astral.sh/uv/)

## Open Questions

1. Should we validate version format (semantic versioning)?
2. Should we auto-generate changelog from commits?
3. Should we support pre-release versions (e.g., `v1.0.0-rc1`)?
4. Should we publish to TestPyPI first for validation?
5. Should we require all CI checks to pass before release?

## Approval

- [ ] Design reviewed
- [ ] Security considerations addressed
- [ ] Implementation plan approved
- [ ] Testing strategy validated

---

**Document Version**: 1.0
**Last Updated**: 2024
**Author**: Design Document
**Status**: Draft
