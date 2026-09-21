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
