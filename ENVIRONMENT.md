# Environment

| Variable | Required | Purpose |
|---|---:|---|
| `APP_ENV` | No | `development`, `test`, or `production` |
| `DATABASE_URL` | Yes outside tests | SQLAlchemy async database URL |
| `JWT_SECRET` | Yes | Token signing secret; at least 32 random characters in production |
| `JWT_ALGORITHM` | No | JWT signing algorithm, default `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | Access-token lifetime |
| `AI_PRIMARY_MODEL` | No | Difficult reasoning model |
| `AI_FAST_MODEL` | No | High-volume bounded task model |
| `AI_PROVIDER_MODE` | No | `disabled` until an AI provider is deliberately enabled |
| `OPENAI_API_KEY` | Only in OpenAI mode | Provider credential; never expose it to the frontend or commit it |
| `SAMPLE_JOBS_DIR` | No | Path to local JSON sample jobs |
| `PHASE3_EVALUATION_FILE` | No | Path to the versioned Phase 3 evaluation dataset |
| `LOG_LEVEL` | No | Application log level |
| `CORS_ORIGINS` | No | JSON list of allowed dashboard origins |

`AI_PROVIDER_MODE=disabled` uses deterministic local analysis and is the supported default for development and tests. To deliberately enable structured OpenAI analysis, set `AI_PROVIDER_MODE=openai` and provide `OPENAI_API_KEY`; model selection still comes from `AI_PRIMARY_MODEL` and `AI_FAST_MODEL`.

The frontend accepts `NEXT_PUBLIC_API_URL` and defaults to `http://localhost:8000`. Never put a provider key in a `NEXT_PUBLIC_*` variable.
