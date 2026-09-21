# Upwork AI Career Agent

A human-controlled freelancing workflow system. Development starts with local sample jobs and a source-agnostic engine. No Upwork connection, browser automation, scraping, cookie reuse, or account-affecting automation is included in the initial phases.

## Current milestone

Phase 1 provides:

- a FastAPI application with health and authentication endpoints;
- SQLAlchemy models for the planned product data model;
- an initial Alembic migration;
- audit-ready user and workflow entities;
- three local sample jobs for future engine phases;
- a minimal Next.js dashboard shell;
- automated API, authentication, schema, and sample-data tests.

The analyzer, matcher, proposal generator, and fact checker are intentionally scheduled for later tested phases. See [ARCHITECTURE.md](ARCHITECTURE.md) for the implementation sequence.

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".\backend[dev]"
Copy-Item .env.example .env
alembic -c backend/alembic.ini upgrade head
uvicorn app.main:app --app-dir backend --reload
```

In another terminal:

```powershell
Set-Location frontend
npm install
npm run dev
```

Run backend tests with `python -m pytest backend/tests`.
