# Railway deployment

Two services plus PostgreSQL (pgvector image):

| Service | Name | Notes |
|---------|------|-------|
| Backend | `agentos-chat-backend` | FastAPI on port 8000, `/health` |
| Frontend | `agentos-chat-frontend` | Astro static/preview on port 4321 |
| Database | `pgvector` | PostgreSQL 16 with pgvector extension |

## Required variables

**Backend**

- `DATABASE_URL` — from Railway Postgres plugin
- `MOCK_AUTH_SUBJECT` — only for non-production mock identity
- `CORS_ORIGINS` — frontend public URL
- `OPENROUTER_API_KEY` — model provider for Agno agent
- `AGNO_TELEMETRY` — `false` recommended
- `AGENT_MODEL` — e.g. `openrouter/google/gemini-2.0-flash-001`

**Frontend**

- `PUBLIC_AGENTOS_API_BASE_URL` — backend public URL
- `PUBLIC_MOCK_IDENTITY` — must match backend mock subject in non-prod

## Minimum CPU/memory

`railway_up.sh` requests the smallest available CPU and memory per service. If Railway rejects a value, document the exception in this file before marking deployment complete.

## Commands

```bash
make railway-preflight
make railway-up
make railway-deploy
make railway-status
make railway-smoke
make railway-logs-backend
make railway-logs-frontend
```

Production deployments must use real Auth0 validation; mock identity is for local/staging only.
