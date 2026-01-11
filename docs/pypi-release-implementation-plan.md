# PyPI Release Automation Implementation Plan

**Based on**: `docs/pypi-release-automation-design.md`

## Overview

This plan outlines the implementation steps to automate PyPI package releases using GitHub Actions, following the design document's architecture of two interconnected workflows.

## Implementation Phases

### Phase 1: Prerequisites & Setup

**Tasks**:

1. Create PyPI API token at <https://pypi.org/manage/account/token/>
2. Add `PYPI_API_TOKEN` as GitHub repository secret:
   - Settings → Secrets and variables → Actions → New repository secret
3. Verify `pyproject.toml` has correct version format
4. Ensure project uses `hatchling` as build backend (already configured)

**Deliverables**: PyPI token configured, GitHub secret set

---

### Phase 2: Workflow Implementation

#### 2.1 Create Release Workflow (`create-release.yml`)

**File**: `.github/workflows/create-release.yml`

**Key Features**:

- Trigger: `push` event with tag pattern `v*`
- Extract version from tag (e.g., `v1.0.0` → `1.0.0`)
- Validate tag format
- Optional: Verify tag matches `pyproject.toml` version
- Create GitHub release using `gh` CLI or GitHub API
- Use tag message as release notes body

**Steps**:

1. Checkout code
2. Extract version from tag name
3. Validate version format
4. Create GitHub release with tag message

**Permissions**: `contents: write`

#### 2.2 Publish to PyPI Workflow (`publish-pypi.yml`)

**File**: `.github/workflows/publish-pypi.yml`

**Key Features**:

- Trigger: `release` event with `published` action
- Version verification (tag vs `pyproject.toml`)
- Build package using `uv build`
- Publish to PyPI using `uv publish` or `twine`
- Handle existing version errors gracefully

**Steps**:

1. Checkout code
2. Set up Python and `uv`
3. Extract version from release tag
4. Verify `pyproject.toml` version matches tag
5. Build package (`uv build`)
6. Publish to PyPI (`uv publish` with `PYPI_API_TOKEN`)
7. Optional: Verify publication

**Permissions**: `contents: read`
**Secrets**: `PYPI_API_TOKEN`

**Deliverables**: Both workflow files created and tested

---

### Phase 3: Testing & Validation

**Tasks**:

1. **Local Testing**:
   - Test build: `uv build`
   - Test publish to TestPyPI: `uv publish --repository testpypi`

2. **Workflow Testing**:
   - Create test tag: `v0.0.0-test`
   - Push tag and verify both workflows trigger
   - Verify GitHub release is created
   - Verify package publishes successfully (use TestPyPI initially)

3. **Error Scenarios**:
   - Test tag version mismatch
   - Test invalid tag format
   - Test duplicate version (already exists on PyPI)

**Deliverables**: All workflows tested and validated

---

### Phase 4: Documentation & Migration

**Tasks**:

1. Update `docs/release.md` with new automated release process
2. Document developer workflow:
   - Update version in `pyproject.toml`
   - Commit changes
   - Create and push annotated tag
   - Workflows automatically handle release and publish
3. Document rollback procedures:
   - How to yank a version from PyPI if needed
   - How to delete GitHub release and tag if needed

**Deliverables**: Release documentation updated

---

## Technical Implementation Details

### Workflow Dependencies

- `actions/checkout@v4`
- `actions/setup-python@v5`
- `uv` (already in project)

### Build & Publish Commands

- Build: `uv build` (generates sdist and wheel)
- Publish: `uv publish` (requires `PYPI_API_TOKEN`)

### Version Management Strategy

- Tag format: `v{version}` (e.g., `v0.9.0`)
- Tag version must match `pyproject.toml` version (validated in workflow)
- Manual sync: Developer ensures version matches before tagging

---

## Success Criteria

- [ ] Both workflows created and functional
- [ ] PyPI token configured securely
- [ ] Workflows trigger correctly on tag push and release
- [ ] Package builds and publishes successfully
- [ ] Version validation works correctly
- [ ] Error handling for common failure scenarios
- [ ] Documentation updated with new process

---

## Estimated Effort

- **Phase 1**: 15-30 minutes (token setup)
- **Phase 2**: 2-3 hours (workflow implementation)
- **Phase 3**: 1-2 hours (testing and validation)
- **Phase 4**: 30-60 minutes (documentation)

**Total**: ~4-6 hours

---

## Next Steps After Implementation

1. Create first production release using new automation
2. Monitor workflow execution and iterate as needed
3. Consider future enhancements (see design document)
