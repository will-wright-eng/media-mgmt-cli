#* Variables
SHELL := /usr/bin/env bash

#* Setup
.PHONY: $(shell sed -n -e '/^$$/ { n ; /^[^ .\#][^ ]*:/ { s/:.*$$// ; p ; } ; }' $(MAKEFILE_LIST))
.DEFAULT_GOAL := help

help: ## list make commands
	@echo ${MAKEFILE_LIST}
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

#* Installation & Setup
install: ## install dependencies with uv
	uv sync --extra test --extra dev

setup: ## complete project setup
	@echo "Setting up media-mgmt-cli project..."
	uv sync --extra test --extra dev
	@echo "✅ Project setup complete!"

#* Development
dev: ## start development environment
	uv sync --extra test --extra dev
	@echo "Development environment ready!"

#* Testing
test: ## run tests
	uv run pytest

test-coverage: ## run tests with coverage
	uv run pytest --cov=mgmt --cov-report=html --cov-report=term

#* Code Quality
lint: ## run linting and formatting checks
	uv run ruff check mgmt/ tests/
	uv run ruff format --check mgmt/ tests/

lint-fix: ## fix linting issues and format code
	uv run ruff check --fix mgmt/ tests/
	uv run ruff format mgmt/ tests/

#* CLI Commands
cli: ## show CLI help
	uv run mgmt --help

#* Build & Distribution
build: ## build package
	uv build

publish: ## publish to PyPI (requires authentication)
	uv publish

#* Cleaning
clean: ## clean up build artifacts, caches, and temp files
	rm -rf build/ dist/ *.egg-info/ .uv/
	rm -f test_file* *.tar.gz *.zip
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name ".DS_Store" -delete 2>/dev/null || true
	find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true

#* Status
status: ## show project status
	@echo "📦 Package Manager: uv"
	@echo "🐍 Python Version: $(shell uv run python --version)"
	@echo "📋 Dependencies: $(shell uv pip list | wc -l) packages installed"
