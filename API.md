# API

Base path: `/api/v1`

## System

- `GET /health` - liveness and configuration-safe service status.

## Authentication

- `POST /api/v1/auth/register` - create a local user.
- `POST /api/v1/auth/login` - exchange email/password for a bearer token.
- `GET /api/v1/auth/me` - return the authenticated user.

OpenAPI documentation is available at `/docs` while the service is running.
