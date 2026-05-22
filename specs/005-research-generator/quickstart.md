# Quickstart: Research Generator

## Prerequisites

- Python 3.12
- Node.js 22
- PostgreSQL running locally (or Railway)
- Railway CLI installed and authenticated
- Make available in the local shell
- `OPENROUTER_API_KEY` with access to `deepseek/deepseek-v4-pro:nitro`
- Auth0 tenant configured (existing from feature 003)

## Expected Repository Layout

```text
apps/backend/
apps/frontend/
infra/railway/
Makefile
specs/005-research-generator/
```

## New Environment Variables

Add to `apps/backend/.env`:

```bash
RESEARCH_AGENT_MODEL=deepseek/deepseek-v4-pro:nitro
```

Existing variables remain unchanged:
- `DATABASE_URL`, `OPENROUTER_API_KEY`, `AUTH0_*`, `LANGWATCH_*`

## Local Run

```bash
make install
make db-up
make migrate        # runs new 002_research_schema migration
make dev
```

Open:

- Home page (research hub): `http://localhost:4321/`
- Research session: `http://localhost:4321/research/{session_id}`
- Chat (existing): `http://localhost:4321/chat`
- Backend health: `http://localhost:8000/health`

## Local Verification

```bash
make check
make test
```

Manual smoke flow:

1. Open home page (`/`). Confirm compose area (textarea + "Research & draft") and paginated list are visible.
2. Enter a research topic (e.g., "The state of WebAssembly in 2026"). Click "Research & draft."
3. Confirm redirect to `/research/{session_id}`.
4. Confirm left panel streams agent reasoning/chain-of-thought and the research plan.
5. Confirm right panel shows loading state initially, then the full article with TL;DR, sections, code examples, and source list.
6. Confirm article has at least 3 source URLs in the source list.
7. Confirm version badge shows "v1" on the right panel.
8. Send a follow-up prompt: "Add a section about performance benchmarks."
9. Confirm send is disabled during the agent run; Stop button is visible.
10. Confirm article updates to v2 with the new section; status reverts to draft.
11. Toggle status to "published" via the article panel control.
12. Confirm status shows "published" in both the article panel and the home page list.
13. Click the `.md` download button and confirm a valid markdown file is downloaded.
14. Return to home page. Confirm the session shows with article H1 as title and "published" status.
15. Change page size to 5 and confirm pagination updates.

## Latency Validation (SC-001, SC-004, SC-008)

Measure locally after `make dev` with a warmed backend:

| Criterion | Target | How to measure |
|-----------|--------|----------------|
| SC-001 | Idea to draft in <3 min (excl. search latency) | Submit idea; record time from submit to article appearing in right panel. |
| SC-004 | Article update within 2s after refinement finishes | Send refinement prompt; record time from `done` SSE event to right panel re-render. |
| SC-008 | Pagination <1s for 500 sessions | Seed 500 test sessions; measure list API response time. |

## Railway Deployment

```bash
make railway-deploy     # deploys both services
make railway-status     # verify services running
```

New deployment checklist:
- [ ] `RESEARCH_AGENT_MODEL` env var set on backend service
- [ ] `OPENROUTER_API_KEY` has access to `deepseek/deepseek-v4-pro:nitro`
- [ ] Migration `002_research_schema` applied
- [ ] Health check passes
- [ ] Research endpoints accessible (authenticated)

## Completion Criteria

- Home page shows compose area + paginated research list.
- Submitting an idea creates a session and redirects to the workspace.
- Agent generates a structured markdown article with TL;DR, sections, and ≥3 cited sources.
- Full reasoning/chain-of-thought is visible in the research chat panel.
- Refinement prompts update the article (new version, status auto-reverts to draft).
- Status toggle (draft ↔ published) works bidirectionally.
- Download `.md` produces valid markdown.
- Pagination handles page size changes and navigation.
- All endpoints require authentication; unauthenticated users are redirected.
- LangWatch traces capture research agent runs with model ID.
