# Phase 3 report

## Files created

- Client intelligence and evidence schemas, repositories, services, agents, and API routes under `backend/app/`.
- Alembic migration `c1e0b5296b18_phase_3_client_intelligence_and_evidence.py`.
- Client and evidence test modules under `backend/tests/`.
- Versioned evaluation dataset under `evaluation_data/`.
- Client list and detail views under `frontend/app/clients/`.

## Files modified

- Domain enums/models, database metadata exports, sample-job schemas and ingestion, job routes, application wiring, and environment configuration.
- Job-detail UI, navigation, and frontend API types.
- Architecture, API, database, environment, security, and README documentation.

## Database changes

- Added nullable company and website fields to clients.
- Added source-linked `client_facts` with classification, verification state, and first/last-seen timestamps.
- Added persistent structured `client_analyses` per client/job pair.
- Added persistent deterministic `portfolio_selections` per user/job pair.
- Added foreign-key-backed `evidence_links` across jobs, requirements, verified skills, verified claims, and optional verified projects.

## API endpoints

- Client create/list/retrieve/update, source creation, fact creation/listing, and structured analysis.
- Portfolio selection create/retrieve per job.
- Evidence graph rebuild/retrieve per job.
- Phase 3 evaluation endpoint.

## AI components

- `ClientAnalyzerAgent` supports deterministic output and optional Pydantic-validated AI analysis.
- `PortfolioMatcherAgent` owns deterministic ranking and allows optional bounded explanations.
- Unsupported client fact IDs, project IDs, and claim IDs are rejected.
- AI cannot alter fact classifications, verification state, or deterministic portfolio scores.

## Evidence controls

- FACT records require an attached source and VERIFIED state.
- INFERENCE and UNKNOWN records cannot be VERIFIED.
- Proposal-ready graph links are built only from verified skills and verified claims.
- Unverified claims are excluded from evidence links and portfolio citations.

## Evaluation

- Dataset categories: strong match, weak/related match, unrelated job, ambiguous job, and missing information.
- Metrics: skill extraction accuracy, portfolio selection accuracy, unsupported claim rate, and false match rate.
- Current deterministic baseline: 100.00%, 100.00%, 0.00%, and 0.00%, respectively, across five synthetic cases.

## Tests run

- Full backend API/service/model suite.
- Ruff static analysis.
- Alembic drift check, existing database upgrade, fresh SQLite round trip, and PostgreSQL offline rendering.
- Frontend lint and production build.
- Frontend dependency audit.

## Test results

- `python -m pytest backend/tests -q`: **37 passed**.
- `alembic check`: **passed; no new upgrade operations detected**.
- Existing SQLite database upgrade: **passed**.
- Fresh SQLite upgrade/downgrade/upgrade round trip: **passed**.
- PostgreSQL offline migration rendering: **passed**.

## Lint results

- `python -m ruff check backend`: **passed**.
- `npm run lint`: **passed**.

## Build results

- `npm run build`: **passed** with client list/detail and existing application routes.
- `npm audit --audit-level=low`: **passed; 0 vulnerabilities**.

## Security review

- No external client-data fetch, Upwork connection, scraping, browser automation, or account action was added.
- Source attribution is preserved separately from AI analysis.
- AI output is treated as untrusted structured input and checked against supplied IDs.
- Sensitive personal-characteristic inference is explicitly prohibited in the client-analysis prompt.

## Known limitations

- Client intelligence accepts only sample or explicitly supplied permitted information; no public-web research adapter exists.
- Evaluation cases are synthetic and intentionally small; production datasets are needed before changing ranking rules.
- Portfolio relevance uses a versioned explicit relationship vocabulary rather than embeddings.
- No proposal generation or fact checker exists yet.

## Recommended Phase 4

Implement proposal drafts with sentence-level evidence citations, a fact checker that classifies each claim as SUPPORTED, UNSUPPORTED, or UNCERTAIN, immutable approved versions, and explicit user approval. Any unsupported statement must block approval, and Phase 4 must not submit proposals externally.
