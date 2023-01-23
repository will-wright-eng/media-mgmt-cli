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

# ADD_REQ_TXT := $(shell cat requirements.txt | grep -E '^[^# ]' | cut -d= -f1 | xargs -n 1 poetry add)
# # ADD_REQ_TXT := $(shell cat requirements.txt | xargs poetry add) # <-- if version numbers aren't included in requirements txt
# poetry-init: ## init repo and add requirements.txt (with version numbers) to pypackage.toml
# 	poetry init # to generate pyproject toml (appended to existing)
# 	${ADD_REQ_TXT}

#* Installation
install: ## install
	poetry lock -n && poetry export --without-hashes > requirements.txt
	poetry install -n

pc-run: ## pre-commit run --all-files within poetry
	poetry run pre-commit run --all-files

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
