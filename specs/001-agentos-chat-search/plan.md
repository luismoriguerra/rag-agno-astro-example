# Implementation Plan: AgentOS Chat Search

**Branch**: `001-agentos-chat-search` | **Date**: 2026-05-18 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-agentos-chat-search/spec.md`

## Summary

Build a two-service RAG-style chat experience: an Astro `/chat` frontend calls a
FastAPI/AgentOS backend with a single DuckDuckGo-enabled Agno agent. Chat sessions are persisted
per Auth0-compatible identity using a mocked identity until Auth0 is integrated. Every agent run
receives the active session history, streams safe answer text and progress status, and excludes
deleted, inactive, or other-identity sessions. Deployment is local-first through a Makefile that
creates/configures separate Railway services with minimum CPU and memory settings.

## Technical Context

**Language/Version**: Python 3.12 for backend; Node.js 22 and TypeScript 5.x for frontend  
**Primary Dependencies**: FastAPI, Agno/AgentOS, Agno DuckDuckGoTools, Pydantic, PostgreSQL
driver, Astro, Railway CLI  
**Storage**: PostgreSQL with pgvector-capable Railway service; vector search unused for this
feature, chat history stored relationally and partitioned by owner identity  
**Testing**: pytest for backend unit/integration/contract tests; Astro check/build plus frontend
interaction tests for `/chat`; Makefile smoke tests for deployed services  
**Target Platform**: Local macOS/Linux development and Railway Linux services  
**Project Type**: RAG web application with separate backend API service and frontend web service  
**Performance Goals**: 90% of valid searchable questions answer visibly within 10 seconds; 95%
of successful responses start streaming text within 3 seconds of generation; 95% of available
history restores within 2 seconds  
**Constraints**: Minimum Railway CPU/memory settings; no GitHub Actions in this release; mocked
Auth0-compatible identity now, replaceable with real Auth0; no raw hidden reasoning in progress
status; every agent run receives only the current identity's active session history

**Environment (local/staging)**:
- `MOCK_AUTH_SUBJECT` — stable subject for mocked identity during development
- `AUTH0_*` — reserved for future real Auth0 integration (not required for initial mock-only release)  
**Scale/Scope**: First-release single-agent app with DuckDuckGo search, persisted chat sessions,
two Railway services, local Makefile automation, and post-deploy smoke verification

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Grounded RAG and Agent Behavior**: PASS. Public DuckDuckGo search results are the grounding
  source. No document chunking or embeddings are used in this feature. The single Agno agent gets
  only DuckDuckGo search tool access, active-session history, safe progress status, and explicit
  fallback behavior for insufficient search context.
- **Auth0-Centered Security Boundaries**: PASS WITH MOCK (non-production). Persisted sessions are owned by an
  Auth0-compatible identity. Initial implementation uses a mocked identity dependency, with API
  boundaries and data filters designed to swap in real Auth0 token validation later. Production
  Railway deployment requires real Auth0 validation before exposing persisted history or agent tools.
- **Typed API and UI Contracts**: PASS. FastAPI exposes typed session/message/stream/stop/delete
  contracts. Astro `/chat` handles loading, empty input, streaming text, safe thinking status,
  stop, new chat, retryable failures, deleted active session, and unauthorized/mock-identity failures.
- **PostgreSQL and pgvector Integrity**: PASS. PostgreSQL stores identities, sessions, messages,
  runs, and sources. pgvector-capable service is provisioned by default for project alignment, but
  vector search and embeddings are explicitly out of scope.
- **Railway-Ready Delivery and Observability**: PASS. Plan includes two Railway services,
  minimum CPU/memory settings, required env vars, health checks, structured logs, Makefile
  targets, bounded Railway log commands, and post-deploy smoke tests.

**Post-Design Recheck**: PASS. Research, data model, contracts, and quickstart preserve all
constitution gates and introduce no justified violations.

## Project Structure

### Documentation (this feature)

```text
specs/001-agentos-chat-search/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── openapi.yaml
│   └── chat-ui.md
└── tasks.md
```

### Source Code (repository root)

```text
apps/
├── backend/
│   ├── pyproject.toml
│   ├── src/agentos_chat/
│   │   ├── agents/
│   │   ├── api/
│   │   ├── auth/
│   │   ├── db/
│   │   ├── models/
│   │   ├── services/
│   │   └── main.py
│   ├── migrations/
│   └── tests/
│       ├── contract/
│       ├── integration/
│       └── unit/
└── frontend/
    ├── package.json
    ├── astro.config.ts
    ├── src/
    │   ├── components/
    │   ├── pages/
    │   │   └── chat.astro
    │   ├── layouts/
    │   └── services/
    └── tests/

infra/
└── railway/

Makefile
```

**Structure Decision**: Use the existing `apps/` folder as a two-app monorepo root. Keep backend
and frontend dependencies isolated while sharing root Makefile and Railway documentation.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
