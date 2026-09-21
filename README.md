# Upwork AI Career Agent

A human-controlled freelancing workflow system. Development starts with local sample jobs and a source-agnostic engine. No Upwork connection, browser automation, scraping, cookie reuse, or account-affecting automation is included in the initial phases.

## Current milestone

Phase 2 provides a complete local/sample-data matching workflow:

- authenticated profile, verified-claim, and portfolio management;
- idempotent ingestion and database-backed querying of synthetic jobs;
- structured job analysis with a disabled-by-default AI provider boundary;
- deterministic, reproducible skill, evidence, and portfolio matching;
- persisted compatibility results and ranked batch analysis;
- live dashboard, jobs, job-detail, profile, and portfolio views;
- a clearly synthetic, development-only seed dataset; and
- backend, migration, lint, and production-build verification.

Proposal generation, fact checking, CRM workflows, and any authorized Upwork adapter remain later phases. See [ARCHITECTURE.md](ARCHITECTURE.md) for the implementation sequence.

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

After registering or signing in through the dashboard, run these local workflow actions in order: **Seed synthetic profile**, **Import sample jobs**, then **Analyze and rank**. No step connects to Upwork.
