# Railway deployment

Project: **web0personal-vector**
Dashboard: https://railway.com/project/<YOUR_PROJECT_ID>

All app-specific settings live in [project.env](project.env). For adopting
the same scripts in a new repo, see [TEMPLATE.md](TEMPLATE.md).

## Architecture

```text
Browser
  -> agentos-chat-frontend (Astro SSR + Auth0 session gate)
  -> agentos-chat-backend  (FastAPI + Auth0 JWT, public HTTPS)
  -> Postgres              (private DATABASE_URL)
  -> Auth0 tenant          (Terraform: infra/auth0-terraform)
```

| Service | Name | URL |
|---------|------|-----|
| Backend | `agentos-chat-backend` | `https://<backend-service>-production.up.railway.app` |
| Frontend | `agentos-chat-frontend` | `https://<frontend-service>-production.up.railway.app` |
| Database | `Postgres` | `${{Postgres.DATABASE_URL}}` on backend |

Chat UI: `https://<frontend-service>-production.up.railway.app/chat/`

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

**Backend:** `DATABASE_URL` (via `${{Postgres.DATABASE_URL}}`), `AUTH0_DOMAIN`,
`AUTH0_ISSUER`, `AUTH0_API_AUDIENCE`, `CORS_ORIGINS`, `OPENROUTER_API_KEY`,
`AGENT_MODEL`, `AGNO_TELEMETRY=false`, optional `LANGWATCH_API_KEY`/`LANGWATCH_ENDPOINT`,
`APP_ENVIRONMENT=production`.

**Frontend:** `PUBLIC_AUTH0_DOMAIN`, `PUBLIC_AUTH0_CLIENT_ID`, `PUBLIC_AUTH0_AUDIENCE`,
`PUBLIC_AGENTOS_API_BASE_URL`, `AUTH0_SECRET` (server-only session cookie signing).

The lists of keys synced from local `.env` files into Railway live in
[project.env](project.env) (`BACKEND_ENV_SYNC_KEYS`, `FRONTEND_ENV_SYNC_KEYS`).

Provision Auth0 via [infra/auth0-terraform/README.md](../auth0-terraform/README.md) and
map outputs per [specs/003-auth0-integration/contracts/terraform-env-mapping.md](../../specs/003-auth0-integration/contracts/terraform-env-mapping.md).

## Smoke test expectations

- Backend `/health` must return **2xx** without authentication.
- Frontend `/` (unauthenticated) may return **302/307** redirect to Auth0 login — that counts as success.

## Notes

- Frontend runs Astro SSR (`node ./dist/server/entry.mjs`), not static `serve dist`.
- Astro `PUBLIC_*` vars are build-time; redeploy the frontend after they change.
- All environments use real Auth0 (no mock identity). See [specs/003-auth0-integration/quickstart.md](../../specs/003-auth0-integration/quickstart.md).
- After manual edits in the Railway UI, run `make railway-cleanup` to reassert
  Dockerfile-driven deploy config.
