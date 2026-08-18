# Mini Blinkit ERP & Warehouse Automation Platform

> Enterprise-grade ERP system replacing Excel-based warehouse operations for a Blinkit-style quick-commerce company.

## Architecture

- **Backend**: FastAPI + SQLAlchemy async + PostgreSQL + Redis + Celery
- **Frontend**: React 18 + TypeScript + Vite + TailwindCSS + Shadcn UI
- **Patterns**: Clean Architecture, Repository Pattern, Domain-Driven Design, CQRS (reports)

---

## Quick Start

### Prerequisites

- Docker Desktop (with Docker Compose v2)
- Git
- Node.js 20+ (for local frontend dev only)
- Python 3.12+ (for local backend dev only)

### 1. Clone and Setup

```bash
git clone <repo-url>
cd Vendiman
cd backend
cp .env.example .env
# Edit .env with your values (especially SECRET_KEY)
```

### 2. Generate a secure SECRET_KEY

```bash
python -c "import secrets; print(secrets.token_hex(64))"
# Copy the output into .env → SECRET_KEY=...
```

### 3. Start all services

```bash
# From backend/ directory:
make setup    # Creates .env, starts Docker, runs migrations

# OR manually:
make up       # Start Docker Compose services
make migrate  # Run Alembic migrations
```

### 4. Access the application

| Service | URL |
|---------|-----|
| **API Docs (Swagger)** | http://localhost:8000/docs |
| **API Docs (ReDoc)** | http://localhost:8000/redoc |
| **Health Check** | http://localhost:8000/api/v1/health |
| **Celery Monitor (Flower)** | http://localhost:5555 |
| **Frontend (Dev)** | http://localhost:5173 |

### 5. Start Frontend (Development)

```bash
cd frontend
npm install
npm run dev
```

---

## Developer Commands

All commands run from the `backend/` directory:

```bash
make help           # Show all available commands

# Docker
make up             # Start all services
make down           # Stop all services
make logs           # Tail API logs
make restart        # Restart API (after code changes, auto-reloads in dev)

# Database
make migrate        # Apply pending migrations
make migrate-create MSG="add product table"  # Create new migration
make migrate-rollback                        # Rollback last migration
make migrate-history                         # Show all migrations

# Testing
make test           # Run full test suite
make test-unit      # Unit tests only (fast)
make test-coverage  # With coverage report

# Code Quality
make lint           # Run Ruff linter
make lint-fix       # Auto-fix lint issues
make format         # Format code
make typecheck      # Run mypy

# Utilities
make shell          # Python REPL inside API container
make db-shell       # PostgreSQL shell
make redis-cli      # Redis CLI
make superuser      # Create admin user
```

---

## Project Structure

```
Vendiman/
├── backend/
│   ├── app/
│   │   ├── core/          # Config, DB, Redis, Security, DI, Exceptions
│   │   ├── domain/        # ORM models, Pydantic schemas, Enums
│   │   ├── repositories/  # Data access layer (Repository Pattern)
│   │   ├── services/      # Business logic layer
│   │   ├── api/v1/        # FastAPI routers (presentation layer)
│   │   ├── workers/       # Celery async tasks
│   │   └── utils/         # PDF gen, Excel, pagination, number gen
│   ├── alembic/           # Database migrations
│   ├── tests/             # Pytest unit + integration tests
│   ├── Dockerfile         # Multi-stage: dev + production
│   ├── docker-compose.yml # PostgreSQL, Redis, API, Celery, Flower
│   ├── requirements.txt   # Pinned production dependencies
│   └── Makefile           # Developer command center
│
└── frontend/
    └── src/
        ├── api/           # Axios client + per-module API functions
        ├── types/         # TypeScript interfaces (mirrors Pydantic)
        ├── hooks/         # React Query hooks per module
        ├── stores/        # Zustand global state (auth, UI)
        ├── components/    # ui/ (Shadcn), common/, modules/
        ├── pages/         # Route-level components
        ├── lib/           # Zod schemas, formatters, constants
        └── router/        # React Router v6 + RBAC guards
```

---

## Module Build Status

| # | Module | Status |
|---|--------|--------|
| 1 | Project Scaffold & DevOps | ✅ Complete |
| 2 | Authentication & RBAC | 🔲 Next |
| 3 | Product & Category | 🔲 Pending |
| 4 | Supplier | 🔲 Pending |
| 5 | Purchase Orders | 🔲 Pending |
| 6 | GRN | 🔲 Pending |
| 7 | Inventory | 🔲 Pending |
| 8 | Warehouse & Transfers | 🔲 Pending |
| 9 | Customer Orders | 🔲 Pending |
| 10 | Delivery Challans | 🔲 Pending |
| 11 | Dashboard & KPIs | 🔲 Pending |
| 12 | Reports & Analytics | 🔲 Pending |
| 13 | Excel Import | 🔲 Pending |
| 14 | Frontend (Full UI) | 🔲 Pending |

---

## Environment Variables

See [`backend/.env.example`](backend/.env.example) for all required variables with documentation.

**Critical variables to change in production:**
- `SECRET_KEY` — Generate with `python -c "import secrets; print(secrets.token_hex(64))"`
- `POSTGRES_PASSWORD` — Use a strong random password
- `REDIS_PASSWORD` — Use a strong random password
- `DEBUG=false`
- `APP_ENV=production`

---

## API Response Format

All endpoints return the standard response envelope:

```json
{
  "success": true,
  "message": "Operation successful",
  "data": { ... },
  "meta": {
    "page": 1,
    "limit": 25,
    "total": 150,
    "total_pages": 6,
    "has_next": true,
    "has_previous": false
  }
}
```

---

## Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Python Framework | FastAPI | Native async, Pydantic v2, automatic OpenAPI |
| ORM | SQLAlchemy 2.0 async | asyncpg driver, async session, 2.0 style |
| DB Driver | asyncpg | 2-5x faster than psycopg3 for async reads |
| Task Queue | Celery + Redis | Durable tasks, separable queues, proven at scale |
| PDF Generation | ReportLab | Industry standard, pixel-precise layout |
| Excel | openpyxl | Read + Write .xlsx, full formatting support |
| Cache | Redis | Broker + cache + pub-sub in one service |
| Frontend Build | Vite | Native ESM dev, Rollup production, instant HMR |
| State | Zustand | Selector subscriptions, tiny API, persist built-in |
| HTTP Client | Axios | Interceptors for token refresh, typed responses |
| Validation | Zod | Runtime + type-safe schema validation |
