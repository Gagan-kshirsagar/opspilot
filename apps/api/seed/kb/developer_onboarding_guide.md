# Engineering Developer Onboarding and Workflow Guide

## 1. Local Environment Setup
To configure the OpsPilot development environment on macOS or Linux:

1. Clone the monorepo: `git clone https://github.com/opspilot/opspilot.git`.
2. Backend setup:
   - `cd apps/api`
   - Create Python 3.11 virtualenv: `python3.11 -m venv .venv && source .venv/bin/activate`
   - Install dependencies: `pip install -e ".[dev]"`
   - Apply database migrations: `alembic upgrade head`
   - Seed database: `python -m app.seed.seed`
   - Ingest Knowledge Base: `python -m app.rag.ingest`
   - Run backend dev server: `uvicorn app.main:app --reload --port 8000`
3. Frontend setup:
   - `cd apps/web`
   - Install dependencies: `npm install`
   - Run frontend dev server: `npm run dev` (starts on `http://localhost:3000`)

## 2. Code Quality & Testing Standards
- **Linting**:
  - Backend: `ruff check .` and `mypy .`
  - Frontend: `npm run lint` and `npm run typecheck`
- **Testing**:
  - Backend: `pytest`
  - Frontend: `npx vitest run`
- **Conventional Commits**: Every commit must follow Conventional Commits standard (e.g. `feat:`, `fix:`, `chore:`, `test:`).

## 3. Pull Request Guidelines
- All PRs must target `main` and have 100% passing CI checks before merging.
- Non-trivial architecture or library additions require updating `DECISIONS.md`.
