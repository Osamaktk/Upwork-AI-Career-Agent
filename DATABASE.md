# Database

SQLAlchemy models are the application source of truth and Alembic migrations are the deployment history. The initial schema includes the requested user, profile, portfolio, job, client, matching, proposal, application, communication, task, notification, settings, and audit tables.

The Phase 2 migration extends profiles with structured professional fields, adds typed skill and claim metadata, adds portfolio skill/verification data, adds job workflow states, and expands persisted job matches with exact/related/missing evidence, concerns, explanations, formula version, model name, and analysis timestamp. Existing rows receive safe defaults during migration.

Production uses PostgreSQL/Supabase. Local tests use SQLite to keep the feedback loop deterministic. JSON columns contain source payloads and structured analysis; indexed scalar columns hold queryable identifiers and states.

Run migrations:

```powershell
alembic -c backend/alembic.ini upgrade head
```

Create a migration after changing models:

```powershell
alembic -c backend/alembic.ini revision --autogenerate -m "describe change"
```
