# Implementation Plan: Research Generator

**Branch**: `005-research-generator` | **Date**: 2026-05-20 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-research-generator/spec.md`

## Summary

Add a Research Generator feature to the home page. Users enter a research idea into a compose area above a paginated session list, the system creates a dedicated research session, redirects to a two-panel workspace (`/research/{session_id}`), and a backend Agno agent powered by OpenRouter `deepseek/deepseek-v4-pro:nitro` searches the web via DuckDuckGoTools, plans an article, and generates a full markdown draft. Users refine via chat prompts; articles are versioned with draft/published status. The right panel renders read-only markdown with download support. All data is separate from the existing `/chat` feature.

## Technical Context

**Language/Version**: Python 3.12 for backend; Node.js 22 and TypeScript 5.x for frontend
**Primary Dependencies**: FastAPI, Agno/AgentOS, Agno DuckDuckGoTools, OpenRouter (`deepseek/deepseek-v4-pro:nitro`), Pydantic, SQLAlchemy, Alembic, Astro, React (island components), LangWatch
**Storage**: PostgreSQL — new research tables alongside existing chat tables; no vector search for this feature
**Testing**: pytest for backend unit/integration/contract tests; Astro check/build for frontend; manual verification for agent quality
**Target Platform**: Local macOS/Linux development and Railway Linux services
**Project Type**: RAG web application extension (new feature module in existing monorepo)
**Performance Goals**: Idea-to-draft in under 3 minutes (SC-001); article panel update within 2 seconds after refinement (SC-004); pagination within 1 second for 500 sessions (SC-008)
**Constraints**: All pages private (Auth0); DuckDuckGo only for v1; manual edit deferred; no public URLs; desktop-first
**Scale/Scope**: Extension of existing two-service app; adds ~4 new DB tables, ~6 new API endpoints, 2 new frontend pages/components, 1 new Agno agent

**Environment variables (new)**:
- `RESEARCH_AGENT_MODEL` — `deepseek/deepseek-v4-pro:nitro` (OpenRouter model for research)
- Existing `OPENROUTER_API_KEY` reused

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Grounded RAG and Agent Behavior**: PASS. DuckDuckGoTools is the grounding source (multi-search per article, min 3 cited URLs). The research agent has explicit tool permissions (web search only), streams full chain-of-thought (spec exception for research vs safe-progress in chat), redacts secrets/system prompts, and all runs are traced via LangWatch. Each run receives full session history + latest article + original idea.
- **Auth0-Centered Security Boundaries**: PASS. All pages private; Auth0 JWT required. Research sessions are owner-scoped; backend filters by `user_identity_id` before any read/write. New endpoints follow existing JWT middleware pattern.
- **Typed API and UI Contracts**: PASS. New FastAPI routes with Pydantic request/response schemas. Frontend handles loading, generating, error/retry, empty list, pagination, and authentication redirect states.
- **PostgreSQL and pgvector Integrity**: PASS. New tables via Alembic migration. Owner-filtered queries. No vector search needed. Indexes on session owner + updated_at for pagination, article version ordering.
- **Railway-Ready Delivery and Observability**: PASS. Same two Railway services. New env var `RESEARCH_AGENT_MODEL`. Health checks cover new endpoints. LangWatch captures research agent traces with model ID. No new Railway services needed.

**Post-Design Recheck**: PASS. Research, data model, contracts, and quickstart preserve all constitution gates. No violations.

## Project Structure

### Documentation (this feature)

```text
specs/005-research-generator/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── research-api.md
│   └── research-ui.md
└── tasks.md
```

### Source Code (repository root)

```text
apps/
├── backend/
│   ├── src/agentos_chat/
│   │   ├── agents/
│   │   │   ├── search_agent.py          # Existing chat agent
│   │   │   └── research_agent.py        # NEW: research agent factory
│   │   ├── api/
│   │   │   ├── stream.py               # Existing chat SSE
│   │   │   ├── sessions.py             # Existing chat sessions
│   │   │   ├── research_sessions.py    # NEW: research session CRUD + list
│   │   │   ├── research_stream.py      # NEW: research chat SSE streaming
│   │   │   └── research_articles.py    # NEW: article status + download
│   │   ├── db/
│   │   │   ├── models.py              # Existing + NEW research models
│   │   │   ├── research_repository.py # NEW: research session/message/article queries
│   │   │   └── ...
│   │   ├── services/
│   │   │   ├── research_service.py    # NEW: research agent orchestration
│   │   │   └── ...
│   │   ├── settings.py                # Add RESEARCH_AGENT_MODEL
│   │   └── main.py                    # Mount new research routers
│   └── migrations/
│       └── versions/
│           └── 002_research_schema.py # NEW: research tables
└── frontend/
    ├── src/
    │   ├── pages/
    │   │   ├── index.astro            # UPDATE: research hub (was redirect)
    │   │   └── research/
    │   │       └── [sessionId].astro  # NEW: two-panel research workspace
    │   ├── components/
    │   │   ├── ChatBox.tsx            # Existing chat component
    │   │   ├── ResearchCompose.tsx    # NEW: idea textarea + submit
    │   │   ├── ResearchList.tsx       # NEW: paginated session list
    │   │   ├── ResearchChat.tsx       # NEW: left panel chat with CoT
    │   │   ├── ArticlePreview.tsx     # NEW: right panel markdown renderer
    │   │   └── ArticleControls.tsx    # NEW: version badge, status toggle, download
    │   └── services/
    │       ├── chatApi.ts             # Existing
    │       └── researchApi.ts         # NEW: research API client
    └── tests/
```

**Structure Decision**: Extend the existing `apps/` monorepo. Research lives as a parallel module to chat in backend (`agents/research_agent.py`, `api/research_*.py`, `db/research_repository.py`, `services/research_service.py`) and as new pages/components in frontend. Shared infrastructure (auth, DB session, SSE pattern, LangWatch) is reused.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
