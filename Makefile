# Project Settings
PROJECT_NAME=hexagon
PYTHON=python3
VENV=.venv
ACTIVATE=. $(VENV)/bin/activate

# Default target
.PHONY: help
help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  venv           Create virtual environment"
	@echo "  install        Install dependencies"
	@echo "  run            Run FastAPI app"
	@echo "  dev            Run development server with reload"
	@echo "  test           Run tests"
	@echo "  lint           Run flake8 linter"
	@echo "  format         Format code with black"
	@echo "  check          Run all checks (lint, test, security)"
	@echo "  security       Run full security audit"
	@echo "  security-deps  Check for vulnerable dependencies"
	@echo "  security-audit Run comprehensive security check"
	@echo "  reset-db       Run habit reset task"
	@echo "  clean          Remove temporary files"

# Basic targets
venv:
	$(PYTHON) -m venv $(VENV)

install:
	$(ACTIVATE) && pip install -r requirements.txt

run:
	$(ACTIVATE) && uvicorn app.main:app --reload

test:
	$(ACTIVATE) && pytest tests/

lint:
	$(ACTIVATE) && flake8 app tasks tests

# Security targets
.PHONY: security security-deps security-audit install-security-tools

install-security-tools:
	@echo "Installing security tools..."
	$(ACTIVATE) && pip install pip-audit safety

security-deps:
	@echo "🔍 Checking for vulnerable dependencies..."
	$(ACTIVATE) && pip-audit --desc

security-audit:
	@echo "🛡️  Running comprehensive security audit..."
	$(ACTIVATE) && python security_audit.py

security: install-security-tools security-audit
	@echo "✅ Security audit complete!"

# Development targets
.PHONY: dev check format

dev:
	@echo "🚀 Starting development server..."
	$(ACTIVATE) && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

check: lint test security-deps
	@echo "✅ All checks passed!"

format:
	@echo "🎨 Formatting code..."
	$(ACTIVATE) && black app tasks tests

# Database targets
.PHONY: reset-db

reset-db:
	@echo "🔄 Running habit reset task..."
	$(ACTIVATE) && python -m tasks.reset_habits

clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache $(VENV)
