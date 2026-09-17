.PHONY: help install dev-install test test-cov lint serve mcp platform clean build

PYTHON ?= python3
PORT ?= 8096
HOST ?= 0.0.0.0

help:
	@echo "DeepSearch Research Agent - Makefile commands:"
	@echo "  make install        Install package locally"
	@echo "  make dev-install    Install package in editable mode with dev dependencies"
	@echo "  make test           Run unit test suite via pytest"
	@echo "  make test-cov       Run test suite with coverage report"
	@echo "  make lint           Check code compilation and syntax"
	@echo "  make serve          Start Google Material 3 Deep Research Studio Web UI"
	@echo "  make mcp            Run stdio Model Context Protocol (MCP) server"
	@echo "  make platform       Run multi-OS platform diagnostics"
	@echo "  make clean          Clean build artifacts and cache directories"
	@echo "  make build          Build sdist and wheel packages"

install:
	$(PYTHON) -m pip install .

dev-install:
	$(PYTHON) -m pip install -e ".[dev]"

test:
	PYTHONPATH=src $(PYTHON) -m pytest tests/ -v

test-cov:
	PYTHONPATH=src $(PYTHON) -m pytest tests/ -v --cov=deepsearch_research_agent --cov-report=term-missing

lint:
	$(PYTHON) -m py_compile src/deepsearch_research_agent/*.py

serve:
	PYTHONPATH=src $(PYTHON) -m deepsearch_research_agent serve --host $(HOST) --port $(PORT)

mcp:
	PYTHONPATH=src $(PYTHON) -m deepsearch_research_agent mcp

platform:
	PYTHONPATH=src $(PYTHON) -m deepsearch_research_agent platform

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .coverage htmlcov/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	$(PYTHON) -m pip install --upgrade build
	$(PYTHON) -m build
