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
3. Client intelligence, sourced facts, evidence graph, portfolio selection, and evaluation baseline. **Complete.**
4. Proposal generation and claim-level fact checking.
5. Application CRM and communication intelligence.
6. Scheduling, background tasks, and notifications.
7. Analytics, feedback, model usage, and evaluation expansion.
8. Authorized Upwork adapter, only after its permissions are documented and approved.
9. Production hardening, deployment, security, and monitoring.

Each phase must pass tests and update documentation before the next phase begins.

## Phase 3 evidence boundary

```text
Sourced client record -> FACT | INFERENCE | UNKNOWN -> structured client analysis

Job requirement -> verified skill -> verified claim -> optional verified portfolio project
                                                       |
                                                       v
                                              proposal-ready evidence link
```

Only database-verified skills and claims can produce proposal-ready links. Portfolio relevance uses versioned deterministic weights: 70 points for exact/related requirement coverage and 30 points for verified project claims, with projects lacking requirement overlap excluded. AI may explain a ranking but cannot change its score or cite IDs outside the supplied evidence set.
