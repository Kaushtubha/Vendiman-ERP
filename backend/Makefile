# =============================================================================
# Makefile — Developer Command Center
# =============================================================================
#
# WHY a Makefile:
#   Self-documenting commands for the entire team. New developers run
#   `make help` and understand the full workflow. No need to remember
#   long docker compose + uvicorn + alembic commands.
#
# USAGE:
#   make up         — Start all services
#   make down       — Stop all services
#   make logs       — Tail API logs
#   make migrate    — Run pending migrations
#   make test       — Run test suite
#   make lint       — Run linter
#   make shell      — Open Python shell inside API container
#
# =============================================================================

COMPOSE = docker compose
API_CONTAINER = erp_api
PYTHON = python3

.PHONY: help up down restart logs shell \
        migrate migrate-create migrate-rollback migrate-history \
        test test-unit test-integration test-coverage \
        lint format typecheck \
        clean superuser

# ── Default target ────────────────────────────────────────────────────────────
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo ""
	@echo "╔══════════════════════════════════════════╗"
	@echo "║   Mini Blinkit ERP — Developer Commands  ║"
	@echo "╚══════════════════════════════════════════╝"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'
	@echo ""

# ── Docker ────────────────────────────────────────────────────────────────────
up: ## Start all services (detached)
	$(COMPOSE) up -d
	@echo "✅ Services started. API: http://localhost:8000/docs"
	@echo "   Flower: http://localhost:5555"

up-build: ## Rebuild images and start all services
	$(COMPOSE) up -d --build

down: ## Stop all services
	$(COMPOSE) down

down-volumes: ## Stop all services and remove volumes (DESTROYS DATA)
	@echo "⚠️  This will destroy all database and Redis data!"
	@read -p "Type 'yes' to confirm: " confirm && [ "$$confirm" = "yes" ]
	$(COMPOSE) down -v

restart: ## Restart the API service (after code changes)
	$(COMPOSE) restart api

logs: ## Tail API logs
	$(COMPOSE) logs -f api

logs-worker: ## Tail Celery worker logs
	$(COMPOSE) logs -f celery_worker

logs-all: ## Tail all service logs
	$(COMPOSE) logs -f

ps: ## Show running service status
	$(COMPOSE) ps

# ── Database Migrations ───────────────────────────────────────────────────────
migrate: ## Apply all pending migrations
	$(COMPOSE) exec api alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create MSG="add product table")
	$(COMPOSE) exec api alembic revision --autogenerate -m "$(MSG)"

migrate-rollback: ## Roll back one migration
	$(COMPOSE) exec api alembic downgrade -1

migrate-history: ## Show migration history
	$(COMPOSE) exec api alembic history --verbose

migrate-current: ## Show current migration version
	$(COMPOSE) exec api alembic current

migrate-sql: ## Generate SQL migration script (offline mode, no DB needed)
	$(COMPOSE) exec api alembic upgrade head --sql

# ── Testing ───────────────────────────────────────────────────────────────────
test: ## Run full test suite (requires services up)
	$(COMPOSE) exec api pytest tests/ -v

test-unit: ## Run unit tests only (fast, no DB)
	$(COMPOSE) exec api pytest tests/ -v -m unit

test-integration: ## Run integration tests (requires DB)
	$(COMPOSE) exec api pytest tests/ -v -m integration

test-coverage: ## Run tests with coverage report
	$(COMPOSE) exec api pytest tests/ --cov=app --cov-report=html --cov-report=term-missing
	@echo "Coverage report: backend/htmlcov/index.html"

test-specific: ## Run specific test (usage: make test-specific TEST=tests/test_health.py)
	$(COMPOSE) exec api pytest $(TEST) -v

# ── Code Quality ──────────────────────────────────────────────────────────────
lint: ## Run Ruff linter
	$(COMPOSE) exec api ruff check app/ tests/

lint-fix: ## Run Ruff linter with auto-fix
	$(COMPOSE) exec api ruff check app/ tests/ --fix

format: ## Format code with Ruff formatter
	$(COMPOSE) exec api ruff format app/ tests/

typecheck: ## Run mypy type checking
	$(COMPOSE) exec api mypy app/

quality: lint typecheck ## Run all quality checks

# ── Development Utilities ─────────────────────────────────────────────────────
shell: ## Open Python REPL inside API container
	$(COMPOSE) exec api python -c "import IPython; IPython.embed()"

bash: ## Open bash shell inside API container
	$(COMPOSE) exec api bash

db-shell: ## Connect to PostgreSQL
	$(COMPOSE) exec postgres psql -U erp_user -d erp_db

redis-cli: ## Connect to Redis CLI
	$(COMPOSE) exec redis redis-cli -a redis_password

superuser: ## Create admin superuser
	$(COMPOSE) exec api python -m scripts.create_superuser

# ── Cleanup ───────────────────────────────────────────────────────────────────
clean: ## Remove Python cache files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true

# ── Setup ─────────────────────────────────────────────────────────────────────
setup: ## Initial setup: copy .env, start services, run migrations
	@[ -f .env ] || cp .env.example .env && echo "Created .env from .env.example"
	$(COMPOSE) up -d postgres redis
	@echo "Waiting for database to be ready..."
	@sleep 5
	$(COMPOSE) up -d
	@sleep 3
	$(MAKE) migrate
	@echo ""
	@echo "✅ Setup complete!"
	@echo "   API Docs: http://localhost:8000/docs"
	@echo "   Flower:   http://localhost:5555"
