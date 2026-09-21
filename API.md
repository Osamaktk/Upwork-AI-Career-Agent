# API

Base path: `/api/v1`

## System

- `GET /health` - liveness and configuration-safe service status.

## Authentication

- `POST /api/v1/auth/register` - create a local user.
- `POST /api/v1/auth/login` - exchange email/password for a bearer token.
- `GET /api/v1/auth/me` - return the authenticated user.

All endpoints below require a bearer token.

## Profile and evidence

- `POST /api/v1/profile` - create the current user's professional profile.
- `GET /api/v1/profile` - retrieve the profile and completeness score.
- `PATCH /api/v1/profile` - update supplied profile fields.
- `POST /api/v1/claims` - create an unverified evidence claim.
- `GET /api/v1/claims` - list claims, optionally filtered by verification status.
- `PATCH /api/v1/claims/{claim_id}` - update claim content without bypassing its lifecycle.
- `POST /api/v1/claims/{claim_id}/verify` - verify a claim and write an audit record.
- `POST /api/v1/claims/{claim_id}/unverify` - mark a claim unverified and audit the transition.
- `POST /api/v1/claims/{claim_id}/expire` - expire a claim and audit the transition.

## Portfolio

- `POST /api/v1/portfolio` - create a project and attach owned, verified claim IDs.
- `GET /api/v1/portfolio` - list active projects.
- `GET /api/v1/portfolio/{project_id}` - retrieve a project.
- `PATCH /api/v1/portfolio/{project_id}` - update a project.
- `DELETE /api/v1/portfolio/{project_id}` - soft-delete a project.

## Jobs and matching

- `POST /api/v1/jobs/import/sample` - validate and idempotently import `sample_jobs/*.json`.
- `GET /api/v1/jobs` - paginate jobs and filter by skill, status, budget, source, date, or compatibility status.
- `POST /api/v1/jobs` - create a normalized job from an allowed local/source-neutral payload.
- `GET /api/v1/jobs/{job_id}` - retrieve a job with its latest analysis and match.
- `PATCH /api/v1/jobs/{job_id}` - update a job.
- `POST /api/v1/jobs/{job_id}/analyze` - persist structured analysis.
- `POST /api/v1/jobs/{job_id}/match` - calculate and persist a reproducible match.
- `POST /api/v1/jobs/analyze/batch` - analyze, match, and rank stored jobs.
- `POST /api/v1/jobs/{job_id}/portfolio-selection` - rank verified projects using deterministic relevance rules.
- `GET /api/v1/jobs/{job_id}/portfolio-selection` - retrieve the persisted portfolio selection.
- `POST /api/v1/jobs/{job_id}/evidence/rebuild` - rebuild verified requirement-to-evidence links.
- `GET /api/v1/jobs/{job_id}/evidence` - retrieve the evidence graph and unsupported requirements.

## Client intelligence

- `POST /api/v1/clients` - create a source-scoped client record.
- `GET /api/v1/clients` - list client records.
- `GET /api/v1/clients/{client_id}` - retrieve client sources, facts, and analyses.
- `PATCH /api/v1/clients/{client_id}` - update allowed client fields.
- `POST /api/v1/clients/{client_id}/sources` - attach a permitted/public source.
- `POST /api/v1/clients/{client_id}/facts` - add a validated FACT, INFERENCE, or UNKNOWN record.
- `GET /api/v1/clients/{client_id}/facts` - list visibly classified facts with source metadata.
- `POST /api/v1/clients/{client_id}/analyze?job_id=...` - persist structured client/job analysis.

FACT records require a source and VERIFIED state. INFERENCE and UNKNOWN records cannot be marked VERIFIED. AI analysis rejects unsupported fact IDs and never writes classifications back to authoritative fact records.

## Evaluations

- `GET /api/v1/evaluations/phase3` - run the versioned local Phase 3 evaluation dataset and return extraction, portfolio-selection, unsupported-claim, and false-match metrics.

## Dashboard and development

- `GET /api/v1/dashboard/summary` - return live workflow metrics.
- `POST /api/v1/development/seed` - idempotently load the explicitly synthetic profile, claims, and portfolio in development/test environments only.

OpenAPI documentation is available at `/docs` while the service is running.
