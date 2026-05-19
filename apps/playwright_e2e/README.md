# Playwright E2E

End-to-end tests for the chat UI at `http://localhost:4321/chat`.

## Prerequisites

1. **Backend + database** (for integration tests):

   ```bash
   make db-up
   make migrate
   # terminal 1
   make dev-backend
   ```

2. **Frontend** on port 4321:

   ```bash
   make dev-frontend
   # or: make dev
   ```

   To let Playwright start the frontend instead, set `PLAYWRIGHT_START_WEB_SERVER=1`.

3. **Agent answers** (optional): set `OPENROUTER_API_KEY` in `apps/backend/.env` for full submit/stream coverage.

## Setup

```bash
cd apps/playwright_e2e
npm install
npx playwright install chromium
```

From repo root:

```bash
make e2e-install
```

## Run

```bash
# from repo root (backend must be up for "with backend" tests)
make e2e

# headed / UI mode
cd apps/playwright_e2e && npm run test:headed
cd apps/playwright_e2e && npm run test:ui
```

## Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `PLAYWRIGHT_BASE_URL` | `http://localhost:4321` | Astro app base URL |
| `PLAYWRIGHT_BACKEND_HEALTH_URL` | `http://localhost:8000/health` | Skip backend tests if down |
| `PLAYWRIGHT_START_WEB_SERVER` | unset | Set to `1` to auto-start Astro before tests |
