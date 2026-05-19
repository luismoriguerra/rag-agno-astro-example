# Railway deploy template

Reusable scaffold for apps shaped as **backend + static frontend + Postgres** on
Railway. Copy this folder into a new repo, edit one config file, and the
scripts work without further code changes.

## Stack assumed

- Monorepo with `apps/<backend>` and `apps/<frontend>` directories
- Backend Dockerfile in the backend directory (exposes `$PORT`, has `/health`)
- Frontend Dockerfile that builds a static site and serves it (no `serve -s`)
- One Railway `Postgres` service for the database

## Adopt in a new repo

1. Copy `infra/railway/` and the `make railway-*` targets in the [Makefile](../../Makefile) into the new repo.
2. Copy each app's `Dockerfile` and `railway.toml` (use this repo's [backend](../../apps/backend/) and [frontend](../../apps/frontend/) as references).
3. `cp infra/railway/project.env.example infra/railway/project.env` and edit:
   - `RAILWAY_PROJECT_NAME`, `BACKEND_SERVICE`, `FRONTEND_SERVICE`
   - `BACKEND_DIR`, `FRONTEND_DIR`
   - `BACKEND_CORS_VAR`, `FRONTEND_API_VAR` (names of the vars that hold the cross-service URLs)
   - `SMOKE_BACKEND_PATH`, `SMOKE_FRONTEND_PATH`
   - `BACKEND_ENV_SYNC_KEYS`, `FRONTEND_ENV_SYNC_KEYS` (which keys from local `.env` to push)
   - `BACKEND_DEFAULT_VARS` (constants applied every run)
4. Run the workflow:

   ```bash
   make railway-preflight
   make railway-up        # init project, add Postgres, sync .env vars
   make railway-deploy    # build + deploy both services
   make railway-cleanup   # link DB var, sync URLs, clear dashboard drift
   make railway-smoke     # HTTP check of backend + frontend
   ```

## What lives where

| File | Responsibility |
|------|----------------|
| [project.env](project.env) | Per-repo names, paths, var keys (only file to edit) |
| [common.sh](common.sh) | `load_project_env` and Railway helper functions |
| [railway_up.sh](railway_up.sh) | `railway init`, add Postgres, sync env vars from local `.env` |
| [configure_urls.sh](configure_urls.sh) | Set `CORS` and frontend API URL from public domains |
| [cleanup.sh](cleanup.sh) | Wire `DATABASE_URL`, clear dashboard `startCommand`/`buildCommand`, dedupe Postgres, smoke |
| [smoke_test.py](smoke_test.py) | HTTP check; fails on directory listings |

## Pitfalls (do not re-learn the hard way)

- Always deploy a monorepo app with `railway up <dir> --path-as-root` so Railpack/Dockerfile sees the right root.
- Static frontend served by [`serve`](https://www.npmjs.com/package/serve): pass the dist directory *without* `-s`. The `-s` flag enables SPA mode and returns a directory listing for nested paths like `/chat/`.
- Astro `PUBLIC_*` variables are **build-time**. Redeploy the frontend after `make railway-cleanup` updates them.
- Railway dashboard fields (`startCommand`, `buildCommand`) override the Dockerfile until cleared. `make railway-cleanup` nulls them.
- `railway environment edit` accepts JSON on stdin; the interactive form can hang in scripts.

## When this template stops fitting

- API-only or no database: simplify [railway_up.sh](railway_up.sh) and [cleanup.sh](cleanup.sh) (remove Postgres + cross-service URL logic).
- Single service (e.g. Next.js full-stack): collapse backend and frontend env handling and drop [configure_urls.sh](configure_urls.sh).
- Multiple databases or Redis: extend [common.sh](common.sh) helpers and add wiring steps to [cleanup.sh](cleanup.sh).
