# Quickstart: AgentOS Chat Search

## Prerequisites

- Python 3.12
- Node.js 22
- Railway CLI installed and authenticated
- Make available in the local shell
- Required AI/search provider secrets available in the local environment

## Expected Repository Layout

```text
apps/backend/
apps/frontend/
infra/railway/
Makefile
```

## Local Environment

Create local environment files during implementation:

```bash
cp apps/backend/.env.example apps/backend/.env
cp apps/frontend/.env.example apps/frontend/.env
```

Required backend values:

- `DATABASE_URL`
- `MOCK_AUTH_SUBJECT` — stable subject for mocked identity (sent as `X-Mock-Identity` header in local dev)
- `AGNO_TELEMETRY`
- Model provider key used by the Agno agent

Required frontend values:

- `PUBLIC_AGENTOS_API_BASE_URL`

## Local Run

```bash
make install
make db-up
make migrate
make dev
```

Open:

- Frontend: `http://localhost:4321/chat`
- Backend health: `http://localhost:8000/health`

## Local Verification

```bash
make check
make test
make smoke-local
```

Manual smoke flow:

1. Open `/chat`.
2. Submit a question that requires public web search.
3. Confirm safe thinking/progress text appears.
4. Confirm answer text streams visibly.
5. Confirm at least one source is visible when search results are used.
6. Press New Chat and confirm a new session is created.
7. Ask a follow-up in a session with history and confirm prior messages are used as context.
8. Press Stop during a response and confirm prior messages remain.
9. Delete the active session and confirm its messages are not restored or used as context.

## Latency Validation (SC-001, SC-004, SC-009)

Measure locally after `make dev` with a warmed backend and database:

| Criterion | Target | How to measure |
|-----------|--------|----------------|
| SC-001 | 90% of valid searchable questions show a visible answer within 10s | Submit 10 public-web questions; record time from submit to first visible answer text (not thinking status). |
| SC-004 | 95% of available history restores within 2s | Reload `/chat` 20 times with an active session that has history; record time from page load to transcript ready. |
| SC-009 | 95% of successful responses start streaming within 3s of generation | For 20 successful runs, record time from backend `thinking` event to first `token` event. |

Record results in the implementation PR or a local notes file. Automated coverage lives in `apps/backend/tests/integration/test_chat_latency.py` (tasks T076–T078).

## Railway Setup and Deploy

Deployment is local-first through the Makefile. GitHub Actions is out of scope for this release.
The Makefile should adapt the Agno PAL Railway setup flow: preflight, project/service creation,
database provisioning, service variables, deploy, domain creation, logs, and smoke checks.

```bash
make railway-preflight
make railway-up
make railway-deploy
make railway-status
make railway-smoke
```

Railway services:

- `agentos-chat-backend`
- `agentos-chat-frontend`
- `pgvector`

Resource constraint:

- Configure project and services with minimum CPU and memory settings available in Railway.
- If Railway rejects minimum settings for any service, document the exception before considering
  deployment complete.

Useful logs:

```bash
make railway-logs-backend
make railway-logs-frontend
```

## Completion Criteria

- `/chat` is reachable locally and after deployment.
- Backend health check passes.
- Chat stream shows safe progress and visible streamed answer text.
- DuckDuckGo-grounded answers show source links or labels.
- Agent runs include current identity active session history only.
- Deleted, inactive, and other-identity sessions are excluded from context.
- Makefile deploy and smoke targets complete without GitHub Actions.
