# Project Settings
PROJECT_NAME=hexagon
PYTHON=python3
VENV=venv
ACTIVATE=. $(VENV)/bin/activate

# Default target
.PHONY: help
help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  venv           Create virtual environment"
	@echo "  install        Install dependencies"
	@echo "  run            Run Streamlit app"
	@echo "  test           Run tests"
	@echo "  lint           Run flake8 linter"
	@echo "  clean          Remove temporary files"

venv:
	$(PYTHON) -m venv $(VENV)

install:
	$(ACTIVATE) && pip install -r requirements.txt

run:
	$(ACTIVATE) && uvicorn main:app --reload --app-dir app

test:
	$(ACTIVATE) && pytest tests/

lint:
	$(ACTIVATE) && flake8 .

clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache $(VENV)
