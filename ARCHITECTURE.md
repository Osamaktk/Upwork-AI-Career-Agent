# Architecture

## Product boundary

The first usable system is driven only by versioned JSON fixtures in `sample_jobs/`. The engine accepts a `JobSource` interface so an authorized Upwork adapter can be added later without changing analysis, matching, proposal, fact-checking, or dashboard contracts.

```text
SampleJobSource
      |
      v
Job ingestion -> Job analyzer -> Matching engine -> Client analyzer
                                                    |
                                                    v
Dashboard <- Fact checker <- Proposal generator <- Portfolio matcher
```

Consequential actions end at a review queue. Submission, messaging, contract acceptance, profile changes, and bid changes require a separate approval record and an authorized integration.

## Components

- `backend/app/api`: thin HTTP routes and dependency wiring.
- `backend/app/services`: deterministic business rules and orchestration.
- `backend/app/agents`: versioned AI task boundaries; no direct database or account access.
- `backend/app/repositories`: persistence abstractions.
- `backend/app/models`: relational domain model.
- `backend/app/schemas`: validated transport contracts.
- `sample_jobs`: deterministic development and evaluation inputs.
- `frontend`: review-oriented Next.js dashboard.

## Model routing

Model IDs are configuration, never domain logic. `AI_PRIMARY_MODEL` handles difficult analysis, proposal generation, and fact checking. `AI_FAST_MODEL` handles bounded extraction, tagging, and classification. `AI_PROVIDER_MODE=disabled` is the default so development and tests cannot make paid network calls accidentally.

## Phase gates

1. Foundation: architecture, schema, auth, health, audit primitives, tests.
2. Verified profile and portfolio.
3. Sample job ingestion and deduplication.
4. Job and client analysis.
5. Matching and portfolio selection.
6. Proposal generation.
7. Claim-level fact checking.
8. CRM and approval workflow.
9. Message analysis.
10. Dashboard and analytics.
11. Scheduled reports.
12. Authorized Upwork adapter, only after its permissions are documented and approved.
13. Production hardening and evaluations.

Each phase must pass tests and update documentation before the next phase begins.
