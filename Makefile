PYTHON ?= python3
VENV   := .venv
BIN    := $(VENV)/bin

.PHONY: setup lint test format

setup:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -e ".[dev]"
	$(BIN)/pre-commit install

lint:
	$(BIN)/ruff check .
	$(BIN)/ruff format --check .
	$(BIN)/mypy src tests

test:
	$(BIN)/pytest --cov --cov-report=term-missing

format:
	$(BIN)/ruff check --fix .
	$(BIN)/ruff format .
