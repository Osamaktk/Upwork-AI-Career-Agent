# Setup

## Prerequisites

- Python 3.12 or newer
- Node.js 22 or newer
- PostgreSQL 16+ for shared/production environments

SQLite is supported for local development and tests. PostgreSQL/Supabase is the production target.

## Backend

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".\backend[dev]"
Copy-Item .env.example .env
alembic -c backend/alembic.ini upgrade head
uvicorn app.main:app --app-dir backend --reload
```

## Frontend

```powershell
Set-Location frontend
npm install
npm run dev
```

Open `http://localhost:3000`, register or sign in, then use the dashboard's development actions to seed the synthetic profile, import fixtures, and analyze/rank the jobs. The seed endpoint is rejected outside development/test environments.

## Verification

```powershell
python -m pytest backend/tests -q
python -m ruff check backend
alembic -c backend/alembic.ini check
Set-Location frontend
npm run lint
npm run build
```
