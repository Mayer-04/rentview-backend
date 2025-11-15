UV ?= uv
PY_SRC ?= src
APP_MODULE ?= src/app/app.py
ENV_FILE ?= .env
DEV_DOCKERFILE ?= docker/Dockerfile.dev
DEV_COMPOSE ?= docker/docker-compose.dev.yml
DEV_IMAGE ?= arrendamos-backend-dev
PORT ?= 8080

.PHONY: help install run lint fix fmt typecheck test cov check precommit clean docker-build docker-up docker-down

# Show all documented targets.
help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-16s\033[0m %s\n", $$1, $$2}'

# Dependency management ------------------------------------------------------
install: ## Sync dependencies with uv (creates/updates the virtual environment)
	$(UV) sync

# Load .env before running FastAPI dev server to mimic docker-compose behavior.
run: ## Start FastAPI in development mode loading variables from .env
	@set -a; \
	[ -f $(ENV_FILE) ] && source $(ENV_FILE); \
	set +a; \
	$(UV) run fastapi dev $(APP_MODULE) --host 0.0.0.0 --port $(PORT)

lint: ## Run Ruff lint checks
	$(UV) run ruff check $(PY_SRC)

fix: ## Run Ruff lint with auto-fixes
	$(UV) run ruff check $(PY_SRC) --fix

fmt: ## Format code with Ruff
	$(UV) run ruff format $(PY_SRC)

typecheck: ## Run mypy in strict mode
	$(UV) run mypy --strict --ignore-missing-imports --show-error-codes --python-version=3.13 $(PY_SRC)

test: ## Run pytest suite
	$(UV) run pytest

cov: ## Run pytest with coverage report
	$(UV) run pytest --cov=$(PY_SRC) --cov-report=term-missing

check: lint typecheck test ## Run lint, type checking, and tests

precommit: ## Run all pre-commit hooks
	$(UV) run pre-commit run --all-files

clean: ## Remove caches, build artifacts, and coverage files
	find $(PY_SRC) -type d -name '__pycache__' -exec rm -rf {} +
	rm -rf .ruff_cache .mypy_cache .pytest_cache .coverage htmlcov .uv .uvcache build dist

docker-build: ## Build the development Docker image
	docker build -f $(DEV_DOCKERFILE) -t $(DEV_IMAGE) .

docker-up: ## Start development docker-compose stack
	docker compose -f $(DEV_COMPOSE) up --build

docker-down: ## Stop development docker-compose stack
	docker compose -f $(DEV_COMPOSE) down -v
