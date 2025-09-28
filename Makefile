#* Variables
SHELL := /usr/bin/env bash
PYTHON := python3
PYTHONPATH := `pwd`

#* Setup
.PHONY: $(shell sed -n -e '/^$$/ { n ; /^[^ .\#][^ ]*:/ { s/:.*$$// ; p ; } ; }' $(MAKEFILE_LIST))
.DEFAULT_GOAL := help

help: ## list make commands
	@echo ${MAKEFILE_LIST}
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# https://jupyter-docker-stacks.readthedocs.io/en/latest/
run-nb: ## run jupyter notebook on port 10000
	@echo ""
	@echo "http://<hostname>:10000/?token=<token>"
	@echo "http://127.0.0.1:10000/lab"
	@echo ""
	docker run -it --rm -p 10000:8888 -v "${HOME}/repos/_tmp":/home/jovyan/work jupyter/datascience-notebook:85f615d5cafa

#* UV Package Manager
uv-install: ## install uv
	curl -LsSf https://astral.sh/uv/install.sh | sh

uv-remove: ## remove uv
	rm -rf ~/.local/bin/uv

#* Installation & Dependencies
install: ## install dependencies with uv
	uv sync

install-dev: ## install with dev dependencies
	uv sync --extra test --extra dev

install-all: ## install all dependencies including dev tools
	uv sync --extra test --extra dev
	uv run pre-commit install

#* Development Commands
dev: ## start development environment
	uv sync --extra test --extra dev
	uv run pre-commit install
	@echo "Development environment ready!"

#* Testing
test: ## run tests
	uv run pytest

test-verbose: ## run tests with verbose output
	uv run pytest -v

test-coverage: ## run tests with coverage
	uv run pytest --cov=mgmt --cov-report=html --cov-report=term

#* Code Quality
lint: ## run linting with ruff
	uv run ruff check mgmt/ tests/

lint-fix: ## fix linting issues with ruff
	uv run ruff check --fix mgmt/ tests/

format: ## format code with ruff
	uv run ruff format mgmt/ tests/

format-check: ## check code formatting with ruff
	uv run ruff format --check mgmt/ tests/

lint-all: ## run all linting checks
	uv run ruff check mgmt/ tests/
	uv run ruff format --check mgmt/ tests/

#* Pre-commit
pcreset: ## reset pre-commit
	uv run pre-commit uninstall
	uv run pre-commit clean
	uv run pre-commit install

pcrun: ## pre-commit run --all-files with uv
	uv run pre-commit run --all-files

#* CLI Commands
cli-help: ## show CLI help
	uv run mgmt --help

cli-version: ## show CLI version
	uv run mgmt --version

#* Build & Distribution
build: ## build package
	uv build

publish: ## publish to PyPI (requires authentication)
	uv publish

#* Documentation
docs-serve: ## serve documentation locally
	@echo "Documentation server not configured yet"

#* Database & Data
data-clean: ## clean up test data and temporary files
	rm -f test_file*
	rm -f *.tar.gz
	rm -f *.zip

#* Cleaning
pycache-remove: ## cleanup subcommand - pycache-remove
	find . | grep -E "(__pycache__|\.pyc|\.pyo$$)" | xargs rm -rf

dsstore-remove: ## cleanup subcommand - dsstore-remove
	find . | grep -E ".DS_Store" | xargs rm -rf

mypycache-remove: ## cleanup subcommand - mypycache-remove
	find . | grep -E ".mypy_cache" | xargs rm -rf

ipynbcheckpoints-remove: ## cleanup subcommand - ipynbcheckpoints-remove
	find . | grep -E ".ipynb_checkpoints" | xargs rm -rf

pytestcache-remove: ## cleanup subcommand - pytestcache-remove
	find . | grep -E ".pytest_cache" | xargs rm -rf

uvcache-remove: ## cleanup subcommand - uvcache-remove
	rm -rf .uv/

build-remove: ## build-remove
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/

cleanup: pycache-remove dsstore-remove mypycache-remove ipynbcheckpoints-remove pytestcache-remove uvcache-remove build-remove data-clean

#* Quick Commands
quick-test: ## quick test run
	uv run pytest -x

quick-lint: ## quick lint check with ruff
	uv run ruff check mgmt/ tests/

quick-format: ## quick format check with ruff
	uv run ruff format --check mgmt/ tests/

#* Setup Commands
setup: ## complete project setup
	@echo "Setting up media-mgmt-cli project..."
	uv sync --extra test --extra dev
	uv run pre-commit install
	@echo "✅ Project setup complete!"
	@echo "Run 'make help' to see all available commands"

#* Status Commands
status: ## show project status
	@echo "📦 Package Manager: uv"
	@echo "🐍 Python Version: $(shell uv run python --version)"
	@echo "📋 Dependencies: $(shell uv pip list | wc -l) packages installed"
	@echo "🧪 Tests: $(shell uv run pytest --collect-only -q | grep -c 'test session starts' || echo '0') test files"
