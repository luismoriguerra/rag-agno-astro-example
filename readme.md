# web0personal-vector

AgentOS chat search: Astro `/chat` frontend + FastAPI/Agno backend with DuckDuckGo search and PostgreSQL history.

## Quick start

```bash
cp apps/backend/.env.example apps/backend/.env
cp apps/frontend/.env.example apps/frontend/.env
make install
make db-up
make migrate
make dev
```

- Chat: http://localhost:4321/chat
- Health: http://localhost:8000/health

## Commands

| Command | Description |
|---------|-------------|
| `make install` | Install backend and frontend dependencies |
| `make dev` | Run backend and frontend locally |
| `make check` | Lint and typecheck |
| `make test` | Run backend and frontend tests |
| `make e2e-install` | Install Playwright E2E dependencies and Chromium |
| `make e2e` | Run E2E tests against `http://localhost:4321/chat` (stack must be up) |
| `make railway-up` | Provision Railway services (local CLI) |

See [specs/001-agentos-chat-search/quickstart.md](specs/001-agentos-chat-search/quickstart.md) for full verification and deployment steps.

Optional LangWatch agent tracing: [specs/002-langwatch-backend/quickstart.md](specs/002-langwatch-backend/quickstart.md).
