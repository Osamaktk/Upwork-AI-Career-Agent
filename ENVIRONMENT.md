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
| `SAMPLE_JOBS_DIR` | No | Path to local JSON sample jobs |
| `LOG_LEVEL` | No | Application log level |
| `CORS_ORIGINS` | No | JSON list of allowed dashboard origins |

Provider credentials will be documented when the AI integration phase begins. Never commit secrets.
