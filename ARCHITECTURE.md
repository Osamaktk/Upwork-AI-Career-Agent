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

The provider boundary accepts Pydantic response models. The deterministic analyzer remains available when the provider is disabled, while matching owns the final score regardless of whether an AI explanation is requested.

## Phase 2 data flow

```text
Synthetic profile + verified claims + portfolio
                         |
sample_jobs/*.json -> validated ingestion -> structured analysis
                                                |
                                                v
                          deterministic matching + optional AI relations
                                                |
                                                v
                          persisted match -> ranked API -> dashboard
```

The version 1 score is reproducible: 75 points are allocated across required skills (`exact = 1.0`, explicitly related = `0.6`), 15 points require a verified portfolio match, and 10 points require relevant verified experience. The score is capped at 100. Missing and unknown requirements receive no points, unverified evidence is excluded, and the AI provider cannot modify the score.

## Phase gates

1. Foundation: architecture, schema, auth, health, audit primitives, tests. **Complete.**
2. Verified profile, claims, portfolio, sample-job ingestion, job analysis, deterministic matching, and live workflow views. **Complete.**
3. Client analysis and portfolio-selection refinement.
4. Proposal generation.
5. Claim-level fact checking.
6. CRM and approval workflow.
7. Message analysis.
8. Analytics and scheduled reports.
9. Authorized Upwork adapter, only after its permissions are documented and approved.
10. Production hardening and evaluations.

Each phase must pass tests and update documentation before the next phase begins.
