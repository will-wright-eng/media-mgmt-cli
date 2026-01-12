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

test: ## run tests
	uv run pytest

lint: ## run linting and formatting checks
	uv run ruff check mgmt/ tests/
	uv run ruff format --check mgmt/ tests/

lint-fix: ## fix linting issues and format code
	uv run ruff check --fix mgmt/ tests/
	uv run ruff format mgmt/ tests/

type-check: ## run type checking with ty
	uv run ty check mgmt/ tests/

cli: ## show CLI help
	uv run mgmt --help

check-tag-version: ## check that the most recent git tag matches pyproject.toml version
	@echo "Checking tag version alignment..."
	@VERSION=$$(grep '^version' pyproject.toml | sed -E 's/^version[[:space:]]*=[[:space:]]*"([^"]+)".*/\1/'); \
	if [ -z "$$VERSION" ]; then \
		echo "❌ Error: Could not extract version from pyproject.toml"; \
		exit 1; \
	fi; \
	echo "📋 pyproject.toml version: $$VERSION"; \
	TAG=$$(git describe --tags --abbrev=0 2>/dev/null || echo ""); \
	if [ -z "$$TAG" ]; then \
		echo "ℹ️  No git tags found in repository"; \
		echo "Expected tag format: v$$VERSION"; \
		exit 0; \
	fi; \
	echo "🏷️  Most recent git tag: $$TAG"; \
	EXPECTED_TAG="v$$VERSION"; \
	if [ "$$TAG" = "$$EXPECTED_TAG" ]; then \
		echo "✅ Tag version matches pyproject.toml version"; \
		exit 0; \
	else \
		echo "❌ Error: Tag version mismatch!"; \
		echo "   Expected: $$EXPECTED_TAG"; \
		echo "   Found: $$TAG"; \
		exit 1; \
	fi

tag: ## create a git tag based on pyproject.toml version (use TAG_MSG="message" for custom message)
	@echo "Creating git tag from pyproject.toml version..."
	@VERSION=$$(grep '^version' pyproject.toml | sed -E 's/^version[[:space:]]*=[[:space:]]*"([^"]+)".*/\1/'); \
	if [ -z "$$VERSION" ]; then \
		echo "❌ Error: Could not extract version from pyproject.toml"; \
		exit 1; \
	fi; \
	TAG_NAME="v$$VERSION"; \
	if git rev-parse "$$TAG_NAME" >/dev/null 2>&1; then \
		echo "❌ Error: Tag $$TAG_NAME already exists"; \
		exit 1; \
	fi; \
	if [ -n "$$TAG_MSG" ]; then \
		TAG_MESSAGE="$$TAG_MSG"; \
	else \
		TAG_MESSAGE="Release version $$VERSION"; \
	fi; \
	echo "📋 Creating tag: $$TAG_NAME"; \
	echo "📝 Tag message: $$TAG_MESSAGE"; \
	git tag -a "$$TAG_NAME" -m "$$TAG_MESSAGE"; \
	echo "✅ Tag $$TAG_NAME created successfully"; \
	echo "💡 To push the tag, run: git push origin $$TAG_NAME"

clean: ## clean up build artifacts, caches, and temp files
	rm -rf build/ dist/ *.egg-info/ .uv/ .venv/
	rm -f test_file* *.tar.gz *.zip
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name ".DS_Store" -delete 2>/dev/null || true
	find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true

status: ## show project status
	@echo "📦 Package Manager: uv"
	@echo "🐍 Python Version: $(shell uv run python --version)"
	@echo "📋 Dependencies: $(shell uv pip list | wc -l) packages installed"
