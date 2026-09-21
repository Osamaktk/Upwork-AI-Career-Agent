# Database

SQLAlchemy models are the application source of truth and Alembic migrations are the deployment history. The initial schema includes the requested user, profile, portfolio, job, client, matching, proposal, application, communication, task, notification, settings, and audit tables.

Production uses PostgreSQL/Supabase. Local tests use SQLite to keep the feedback loop deterministic. JSON columns contain source payloads and structured analysis; indexed scalar columns hold queryable identifiers and states.

Run migrations:

```powershell
alembic -c backend/alembic.ini upgrade head
```

Create a migration after changing models:

```powershell
alembic -c backend/alembic.ini revision --autogenerate -m "describe change"
```
