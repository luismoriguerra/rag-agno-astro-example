# Railway deployment

Project: **web0personal-vector**
Dashboard: https://railway.com/project/10ed6588-8533-4040-8a52-c26ab8f4e676

All app-specific settings live in [project.env](project.env). For adopting
the same scripts in a new repo, see [TEMPLATE.md](TEMPLATE.md).

## Architecture

```text
Browser
  -> agentos-chat-frontend (static Astro, serve)
  -> agentos-chat-backend  (FastAPI, public HTTPS)
  -> Postgres              (private DATABASE_URL)
```

| Service | Name | URL |
|---------|------|-----|
| Backend | `agentos-chat-backend` | https://agentos-chat-backend-production.up.railway.app |
| Frontend | `agentos-chat-frontend` | https://agentos-chat-frontend-production.up.railway.app |
| Database | `Postgres` | `${{Postgres.DATABASE_URL}}` on backend |

Chat UI: https://agentos-chat-frontend-production.up.railway.app/chat/

## Commands

```bash
make railway-preflight   # check railway + jq installed
make railway-up          # init project, add Postgres, sync .env vars
make railway-deploy      # deploy backend + frontend (Dockerfile, --path-as-root)
make railway-cleanup     # wire DB var, sync URLs, clear dashboard drift, smoke
make railway-smoke       # HTTP check using current Railway domains
make railway-logs-backend
make railway-logs-frontend
```

## Required variables (this app)

**Backend:** `DATABASE_URL` (via `${{Postgres.DATABASE_URL}}`), `MOCK_AUTH_SUBJECT`,
`CORS_ORIGINS`, `OPENROUTER_API_KEY`, `AGENT_MODEL`, `AGNO_TELEMETRY=false`,
optional `LANGWATCH_API_KEY`/`LANGWATCH_ENDPOINT`, `APP_ENVIRONMENT=production`.

**Frontend (build-time):** `PUBLIC_AGENTOS_API_BASE_URL`, `PUBLIC_MOCK_IDENTITY`.

The lists of keys synced from local `.env` files into Railway live in
[project.env](project.env) (`BACKEND_ENV_SYNC_KEYS`, `FRONTEND_ENV_SYNC_KEYS`).

## Notes

- Frontend uses `serve dist` (no `-s`); `-s` enables SPA mode and breaks `/chat/`.
- Astro `PUBLIC_*` vars are build-time; redeploy the frontend after they change.
- Production must use real Auth0; mock identity is for local/staging only.
- After manual edits in the Railway UI, run `make railway-cleanup` to reassert
  Dockerfile-driven deploy config.
