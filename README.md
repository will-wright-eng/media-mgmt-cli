# Media Management Command Line Interface

[![PyPI](https://img.shields.io/pypi/v/mgmt)](https://pypi.org/project/mgmt/)
[![Downloads](https://static.pepy.tech/badge/mgmt/month)](https://pepy.tech/project/mgmt)
[![Supported Versions](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11-blue)](https://pypi.org/project/mgmt/)
[![Contributors](https://img.shields.io/github/contributors/will-wright-eng/media-mgmt-cli.svg)](https://github.com/will-wright-eng/media-mgmt-cli/graphs/contributors)
[![Tests](https://github.com/will-wright-eng/media-mgmt-cli/workflows/Test/badge.svg)](https://github.com/will-wright-eng/media-mgmt-cli/actions?query=workflow%3ATest)
[![Codeball](https://github.com/will-wright-eng/media-mgmt-cli/actions/workflows/codeball.yml/badge.svg)](https://github.com/will-wright-eng/media-mgmt-cli/actions/workflows/codeball.yml)


## Summary

**An intuitive command line interface that wraps boto3 to search and manage media assets**

## Installing `mgmt` & Supported Versions

`mgmt` is available on PyPI:

```bash
# Using pip (traditional)
python -m pip install mgmt

# Using uv (recommended - faster and more reliable)
uv add mgmt

# Or install in a virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install mgmt
```

**Current Version**: 0.8.0

Media Management Command Line Interface officially supports Python 3.8, 3.9, 3.10, and 3.11+.

## Quick Start

- setup global config file `~/.config/mgmt/config`

```bash
mgmt config
```

*fill out prompts*

```bash
mgmt config
```

*check configs are correct*

```bash
mgmt ls
```

## Supported Features & Usage

For help, run:

```bash
mgmt --help
```

Commands:

```bash
➜ mgmt --help

 Usage: mgmt [OPTIONS] COMMAND [ARGS]...

╭─ Options ───────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --version          Show the version and exit.                                                                   │
│ --help             Show this message and exit.                                                                  │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ──────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ config        Configures the application                                                                        │
│ delete        Deletes the specified file from S3; requires confirmation                                         │
│ download      Downloads the specified file from S3                                                              │
│ ls            Lists the files in the specified location                                                         │
│ search        Searches for files that contain the specified keyword in their names                              │
│ status        Retrieves and prints the metadata of the specified file                                           │
│ upload        Uploads the specified file to S3                                                                  │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

Why not use `awscli`?

You can, and I do, in tandem with `mgmt` -- the purpose is to create an additional interface that minimized the lookup/copy/paste process I found myself frequently going through

## Development

To contribute to this tool, first checkout the code:

```bash
git clone https://github.com/will-wright-eng/media-mgmt-cli.git
cd media-mgmt-cli
```

### Prerequisites

This project uses `uv` for fast and reliable dependency management. Install `uv` if you haven't already:

```bash
# Install uv (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or via pip
pip install uv
```

### Development Setup

The project includes a comprehensive Makefile for development tasks:

```bash
# Complete project setup (installs dependencies and pre-commit hooks)
make setup

# Or manually:
uv sync --extra test --extra dev
uv run pre-commit install
```

### Available Development Commands

```bash
# Run tests
make test

# Run tests with coverage
make test-coverage

# Run linting and formatting
make lint

# Fix linting issues
make lint-fix

# Run pre-commit on all files
make pre-commit

# Show CLI help
make cli

# Build package
make build

# Clean up build artifacts
make clean

# Show project status
make status
```

### Testing

```bash
# Run tests
make test

# Run tests with coverage reporting
make test-coverage
```

### Code Quality

The project uses modern Python tooling for code quality:

- **Ruff**: Fast linting and formatting
- **MyPy**: Type checking
- **Pre-commit**: Automated quality checks
- **Codespell**: Spelling checks

All quality checks run automatically on commit via pre-commit hooks.

### Why `uv`?

This project uses `uv` for dependency management because it offers:

- **🚀 Speed**: 10-100x faster than pip for dependency resolution
- **🔒 Reliability**: Deterministic builds with lock files
- **🛠️ Modern tooling**: Built-in support for virtual environments, project management, and publishing
- **📦 Better dependency resolution**: More reliable conflict resolution than traditional tools
- **🔄 Drop-in replacement**: Compatible with existing pip workflows

### Project Status

This project follows modern Python development practices:

- ✅ **Modern dependency management** with `uv`
- ✅ **Comprehensive CI/CD** with GitHub Actions
- ✅ **Automated code quality** with Ruff, MyPy, and pre-commit
- ✅ **Type safety** with comprehensive type hints
- ✅ **Testing** with pytest and coverage reporting
- ✅ **Documentation** with automated quality checks

## Modern Python Development

This project showcases modern Python development practices:

- **`uv`** for fast dependency management and project tooling
- **Ruff** for lightning-fast linting and formatting
- **MyPy** for static type checking
- **Pre-commit** for automated quality gates
- **GitHub Actions** for CI/CD automation
- **Hatchling** for modern Python packaging

## References

- [PyPI Package](https://pypi.org/project/mgmt)
- [uv Documentation](https://docs.astral.sh/uv/)
- Based on cookiecutter template [will-wright-eng/click-app](https://github.com/will-wright-eng/click-app)
- Rewrite of original project [will-wright-eng/media_mgmt_cli](https://github.com/will-wright-eng/media_mgmt_cli)
