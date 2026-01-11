# Migration from mypy to ty

## Overview

This document outlines the implementation plan for migrating from **mypy** to **ty** as the type checker for the media-mgmt-cli project. ty is an extremely fast Python type checker written in Rust, offering 10x-100x performance improvements over mypy while maintaining comprehensive type checking capabilities.

**Reference**: [ty documentation](https://docs.astral.sh/ty/)

## Current State Analysis

### Current mypy Configuration

The project currently uses mypy with the following setup:

1. **Dependencies**:
   - `mypy>=1.7.0` in `[project.optional-dependencies].dev`
   - `mypy>=1.14.1` in `[tool.uv].dev-dependencies`

2. **Configuration** (`pyproject.toml`):
   - Python version: `3.8`
   - Basic type checking (not too strict)
   - Module overrides for: `boto3.*`, `botocore.*`, `rarfile.*`, `toml.*`, `typer.*`, `rich.*`, `dotenv.*`
   - All overrides set `ignore_missing_imports = true`

3. **Pre-commit hook**:
   - Uses `pre-commit/mirrors-mypy` repository
   - Hook version: `v1.7.1`

4. **Makefile**:
   - No dedicated type-check command currently

### Key mypy Settings to Migrate

| mypy Setting | Current Value | Purpose |
|-------------|---------------|---------|
| `python_version` | `3.8` | Target Python version |
| `warn_return_any` | `true` | Warn on returning Any |
| `warn_unused_configs` | `true` | Warn on unused configs |
| `disallow_untyped_defs` | `false` | Allow untyped function definitions |
| `disallow_incomplete_defs` | `false` | Allow incomplete type definitions |
| `check_untyped_defs` | `true` | Check untyped definitions |
| `disallow_untyped_decorators` | `false` | Allow untyped decorators |
| `no_implicit_optional` | `true` | Require explicit Optional |
| `warn_redundant_casts` | `true` | Warn on redundant casts |
| `warn_unused_ignores` | `true` | Warn on unused ignore comments |
| `warn_no_return` | `true` | Warn on missing return |
| `warn_unreachable` | `true` | Warn on unreachable code |
| `strict_equality` | `false` | Don't require strict equality |
| `ignore_missing_imports` | `true` | Ignore missing imports globally |
| `allow_redefinition` | `false` | Don't allow redefinitions |

## Migration Steps

### Phase 1: Preparation

1. **Document current type checking status**
   - Run mypy to capture baseline: `uv run mypy mgmt/ tests/`
   - Save output for comparison: `mypy mgmt/ tests/ > mypy-baseline.txt`
   - Note any existing type errors or warnings

2. **Review ty documentation**
   - Familiarize with ty's rule system
   - Understand configuration options
   - Review compatibility with existing codebase

### Phase 2: Installation and Initial Setup

1. **Add ty to dependencies**
   - Add `ty>=0.1.0` to `[project.optional-dependencies].dev` in `pyproject.toml`
   - Add `ty>=0.1.0` to `[tool.uv].dev-dependencies` in `pyproject.toml`
   - Run `uv sync --extra dev` to install

2. **Create initial ty configuration**
   - Add `[tool.ty]` section to `pyproject.toml`
   - Map mypy settings to ty equivalents (see Configuration Mapping below)

3. **Test ty installation**
   - Run `uvx ty check` to verify installation
   - Check that ty can analyze the project

### Phase 3: Configuration Migration

1. **Map mypy settings to ty rules**
   - Convert mypy configuration to ty rule levels
   - Set up module overrides for third-party libraries
   - Configure file exclusions if needed

2. **Update pre-commit configuration**
   - Replace mypy hook with ty hook
   - Update `.pre-commit-config.yaml`

3. **Add Makefile command**
   - Add `type-check` target to Makefile
   - Use `uv run ty check` command

### Phase 4: Testing and Validation

1. **Run ty on codebase**
   - Execute `uv run ty check mgmt/ tests/`
   - Compare results with mypy baseline
   - Document any differences in type checking behavior

2. **Fix type errors (if any)**
   - Address any new type errors discovered by ty
   - Update type hints as needed
   - Use suppression comments if necessary

3. **Verify pre-commit hook**
   - Test pre-commit hook with ty
   - Ensure it runs correctly on commit

4. **Performance comparison**
   - Time mypy execution: `time uv run mypy mgmt/ tests/`
   - Time ty execution: `time uv run ty check mgmt/ tests/`
   - Document performance improvements

### Phase 5: Cleanup

1. **Remove mypy dependencies**
   - Remove `mypy` from `[project.optional-dependencies].dev`
   - Remove `mypy` from `[tool.uv].dev-dependencies`
   - Remove `[tool.mypy]` section from `pyproject.toml`

2. **Update documentation**
   - Update README.md to reference ty instead of mypy
   - Update any other documentation mentioning mypy
   - Update `docs/IMPROVEMENT_PLAN.md` if needed

3. **Sync dependencies**
   - Run `uv sync --extra dev` to remove mypy
   - Verify mypy is no longer installed

## Configuration Mapping

### Base Configuration

**mypy** (`pyproject.toml`):
```toml
[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false
disallow_incomplete_defs = false
check_untyped_defs = true
disallow_untyped_decorators = false
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = false
ignore_missing_imports = true
allow_redefinition = false
```

**ty** (equivalent configuration):
```toml
[tool.ty.environment]
python-version = "3.8"

[tool.ty.rules]
# Map mypy settings to ty rules
# Note: ty uses different rule names and severity levels (ignore/warn/error)
possibly-returning-any = "warn"           # warn_return_any
unused-ignore-comment = "warn"            # warn_unused_ignores
redundant-cast = "warn"                   # warn_redundant_casts
possibly-missing-return = "warn"          # warn_no_return
unreachable-code = "warn"                 # warn_unreachable
possibly-unresolved-reference = "ignore" # ignore_missing_imports
# Note: Some mypy settings don't have direct ty equivalents
# ty is designed to be more permissive by default for adoption
```

### Module Overrides

**mypy**:
```toml
[[tool.mypy.overrides]]
module = [
    "boto3.*",
    "botocore.*",
    "rarfile.*",
    "toml.*",
    "typer.*",
    "rich.*",
    "dotenv.*",
]
ignore_missing_imports = true
```

**ty** (equivalent):
```toml
[[tool.ty.overrides]]
include = [
    "**/boto3/**",
    "**/botocore/**",
    "**/rarfile/**",
    "**/toml/**",
    "**/typer/**",
    "**/rich/**",
    "**/dotenv/**",
]
[tool.ty.overrides.rules]
possibly-unresolved-reference = "ignore"
```

## Complete ty Configuration

Here's the complete `[tool.ty]` section to add to `pyproject.toml`:

```toml
[tool.ty.environment]
python-version = "3.9"  # Note: Update to match project's requires-python (>=3.9)

[tool.ty.rules]
# Type checking rules - mapped from mypy settings
possibly-returning-any = "warn"
unused-ignore-comment = "warn"
redundant-cast = "warn"
possibly-missing-return = "warn"
unreachable-code = "warn"
possibly-unresolved-reference = "ignore"  # Global: ignore missing imports

# Additional ty-specific rules (optional, can be enabled later)
# possibly-missing-attribute = "warn"
# possibly-missing-import = "warn"

# Module-specific overrides for third-party libraries
[[tool.ty.overrides]]
include = [
    "**/boto3/**",
    "**/botocore/**",
    "**/rarfile/**",
    "**/toml/**",
    "**/typer/**",
    "**/rich/**",
    "**/dotenv/**",
]
[tool.ty.overrides.rules]
possibly-unresolved-reference = "ignore"
```

## Pre-commit Hook Update

**Current** (`.pre-commit-config.yaml`):
```yaml
- repo: https://github.com/pre-commit/mirrors-mypy
  rev: v1.7.1
  hooks:
    - id: mypy
```

**Updated** (use ty via uvx):
```yaml
- repo: local
  hooks:
    - id: ty
      name: ty
      entry: uvx ty check
      language: system
      types: [python]
      pass_filenames: false
      always_run: true
```

**Alternative** (if a ty pre-commit hook becomes available):
```yaml
# Check ty documentation for official pre-commit hook when available
- repo: https://github.com/astral-sh/ty-pre-commit  # Verify this exists
  rev: v0.1.0  # Use appropriate version
  hooks:
    - id: ty
```

## Makefile Updates

Add the following to `Makefile`:

```makefile
#* Type Checking
type-check: ## run type checking with ty
	uv run ty check mgmt/ tests/

type-check-watch: ## run type checking in watch mode (if supported)
	uv run ty check --watch mgmt/ tests/
```

## Testing Checklist

- [ ] ty is installed and accessible via `uv run ty check`
- [ ] ty configuration in `pyproject.toml` is correct
- [ ] ty runs without errors on the codebase
- [ ] Pre-commit hook works with ty
- [ ] Makefile `type-check` target works
- [ ] Performance improvement is noticeable
- [ ] All type errors are addressed or documented
- [ ] Documentation is updated
- [ ] mypy is completely removed

## Rollback Plan

If issues arise during migration:

1. **Keep mypy configuration** in a backup branch
2. **Revert pre-commit changes** if ty hook causes issues
3. **Temporarily keep both** mypy and ty during transition period
4. **Document any incompatibilities** for future reference

## Expected Benefits

1. **Performance**: 10x-100x faster type checking
2. **Modern tooling**: Built with Rust, actively maintained by Astral
3. **Better IDE integration**: Language server support
4. **Incremental analysis**: Fast updates when editing files
5. **Advanced features**: First-class intersection types, sophisticated reachability analysis

## Notes and Considerations

1. **Rule differences**: ty uses different rule names than mypy. Some mypy settings may not have direct equivalents.

2. **Strictness**: ty is designed for adoption and may be more permissive by default. Adjust rule levels as needed.

3. **Python version**: Update `python-version` in ty config to match project's `requires-python` (currently `>=3.9`).

4. **Third-party libraries**: Module overrides for boto3, botocore, etc. should work similarly in ty.

5. **Gradual migration**: Consider running both mypy and ty in parallel initially to compare results.

6. **Language server**: ty includes a language server for better IDE integration - consider setting this up separately.

## References

- [ty Documentation](https://docs.astral.sh/ty/)
- [ty Configuration Reference](https://docs.astral.sh/ty/reference/configuration/)
- [ty Rules Reference](https://docs.astral.sh/ty/rules/)
- [ty Installation Guide](https://docs.astral.sh/ty/guides/installation/)

## Implementation Timeline

**Estimated time**: 2-4 hours

1. **Preparation** (30 min): Document current state, run baseline
2. **Installation** (15 min): Install ty, create initial config
3. **Configuration** (45 min): Map settings, update files
4. **Testing** (60 min): Run checks, fix issues, verify
5. **Cleanup** (30 min): Remove mypy, update docs

**Total**: ~3 hours

---

*Last updated: [Date]*
*Status: Ready for implementation*
