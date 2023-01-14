#* Variables
SHELL := /usr/bin/env bash
PYTHON := python
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

#* Poetry
poetry-download: ## poetry-download
	curl -sSL https://install.python-poetry.org | $(PYTHON) -

poetry-remove: ## poetry-remove
	curl -sSL https://install.python-poetry.org | $(PYTHON) - --uninstall

#* Installation
install: ## install
	poetry lock -n && poetry export --without-hashes > requirements.txt
	poetry install -n
	-poetry run mypy --install-types --non-interactive ./

pc-init: ## pre-commit install within poetry
	poetry run pre-commit install

pc-run: ## pre-commit run --all-files within poetry
	poetry run pre-commit run --all-files

#* Formatters
codestyle: ## codestyle
	poetry run pyupgrade --exit-zero-even-if-changed --py39-plus **/*.py
	poetry run isort --settings-path pyproject.toml ./
	poetry run black --config pyproject.toml ./

check-codestyle: ## check-codestyle
	poetry run isort --diff --check-only --settings-path pyproject.toml ./
	poetry run black --diff --check --config pyproject.toml ./

mypy: ## mypy
	poetry run mypy --config-file pyproject.toml ./

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

build-remove: ## build-remove
	rm -rf build/

cleanup: pycache-remove dsstore-remove mypycache-remove ipynbcheckpoints-remove pytestcache-remove
