# Tasks: Research Generator

**Input**: Design documents from `/specs/005-research-generator/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Manual verification per quickstart.md smoke flow. Automated tests are not explicitly requested.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `apps/backend/src/agentos_chat/`
- **Frontend**: `apps/frontend/src/`
- **Migrations**: `apps/backend/migrations/versions/`

---

## Phase 1: Setup

**Purpose**: Add new dependencies and configuration for the research feature

- [x] T001 Add `RESEARCH_AGENT_MODEL` setting (default `deepseek/deepseek-v4-pro:nitro`) to `apps/backend/src/agentos_chat/settings.py`
- [x] T002 [P] Add `react-markdown`, `remark-gfm`, `rehype-highlight`, and `rehype-raw` to `apps/frontend/package.json`
- [x] T003 [P] Add research Pydantic request/response schemas to `apps/backend/src/agentos_chat/models/research_schemas.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Database models, migration, and repository layer that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Add SQLAlchemy models for `ResearchSession`, `ResearchMessage`, `ResearchArticle`, `ResearchArticleVersion`, and `ResearchAgentRun` with enums (`ResearchMessageRoleEnum`, `ResearchMessageStatusEnum`, `ResearchRunStatusEnum`, `ArticleStatusEnum`, `ChangeSourceEnum`) to `apps/backend/src/agentos_chat/db/models.py`
- [x] T005 Create Alembic migration `apps/backend/migrations/versions/002_research_schema.py` with all research tables, indexes per data-model.md (composite on session owner+updated_at, message session+seq, article session unique, version article+number, run session+status+started_at)
- [x] T006 [P] Implement `ResearchRepository` in `apps/backend/src/agentos_chat/db/research_repository.py` with methods: `create_session`, `get_session_for_owner`, `list_sessions_paginated` (with total count), `create_message`, `list_messages`, `create_article`, `get_article_for_session`, `create_article_version`, `get_latest_version`, `update_version_status`, `create_agent_run`, `get_run_for_owner`, `update_run_status`, `has_active_run`, `update_session_title`
- [x] T007 Mount research API routers in `apps/backend/src/agentos_chat/main.py` with `Depends(get_current_identity)` Auth0 JWT middleware on all research endpoints (reuse existing auth pattern)

**Checkpoint**: Foundation ready — user story implementation can begin

---

## Phase 3: US1 + US6 — Home Page Research Hub (Priority: P1) 🎯 MVP

**Goal**: Home page serves as research entry point with compose area + paginated session list. Submitting an idea creates a session and redirects to `/research/{session_id}`.

**Independent Test**: Enter an idea on `/`, click submit, verify redirect. Return to `/` and confirm the session appears in the paginated list.

### Backend for US1 + US6

- [x] T008 [US1] Implement `POST /api/research/sessions` endpoint (validates idea not empty, creates session + user message + agent run, returns session_id + run_id) in `apps/backend/src/agentos_chat/api/research_sessions.py`
- [x] T009 [US6] Implement `GET /api/research/sessions` endpoint (paginated, owner-filtered, returns sessions with derived status + is_generating flag, total count) in `apps/backend/src/agentos_chat/api/research_sessions.py`

### Frontend for US1 + US6

- [x] T010 [P] [US6] Create `researchApi.ts` service with `createSession(idea)`, `listSessions(page, pageSize)`, and TypeScript types matching API contract in `apps/frontend/src/services/researchApi.ts`
- [x] T011 [P] [US1] Create `ResearchCompose.tsx` component: always-visible textarea + "Research & draft" button, empty validation, calls `createSession` then redirects to `/research/{session_id}` in `apps/frontend/src/components/ResearchCompose.tsx`
- [x] T012 [P] [US6] Create `ResearchList.tsx` component: paginated table with title + status badge (draft/published/generating), page size dropdown (5/10/20/50, default 10), page navigation, empty state message, row click navigates to `/research/{session_id}` in `apps/frontend/src/components/ResearchList.tsx`
- [x] T013 [US6] Update `apps/frontend/src/pages/index.astro` from redirect-to-chat to Research Hub layout: AppLayout with ResearchCompose above ResearchList, authenticated-only, include nav link to `/chat` so existing chat feature remains accessible

**Checkpoint**: Home page shows compose + paginated list. Submitting creates a session and redirects. Sessions appear in the list immediately.

---

## Phase 4: US2 — Agent Researches and Generates Article (Priority: P1) 🎯 MVP

**Goal**: Backend agent searches the web, plans article structure, and generates a full markdown article. Left panel streams reasoning; right panel shows the completed article.

**Independent Test**: Create a session, verify the agent produces reasoning messages and a complete article with TL;DR, sections, code examples, and ≥3 cited sources.

### Backend for US2

- [x] T014 [US2] Create `build_research_agent()` factory in `apps/backend/src/agentos_chat/agents/research_agent.py` using `OpenRouter(id=settings.research_agent_model)` with DuckDuckGoTools, research system prompt (plan → write with TL;DR, sections, sources), `show_tool_calls=True`, and `markdown=True`
- [x] T015 [US2] Implement `ResearchService` in `apps/backend/src/agentos_chat/services/research_service.py` with `run_research(session_id, user_identity_id)` that: loads full chat history + latest article + original idea, invokes research agent, streams SSE events (thinking, reasoning, token), separates agent output into `content` (chat-visible) and `reasoning_content` (chain-of-thought stored in ResearchMessage), extracts article markdown from agent output, creates ArticleVersion, extracts H1 for session title update, emits `article` SSE event, redacts secrets/internal prompts before storage, handles errors/timeout
- [x] T016 [US2] Implement research SSE streaming endpoint `GET /api/research/runs/{run_id}/stream` with event types: `thinking`, `reasoning`, `token`, `article`, `done`, `error` in `apps/backend/src/agentos_chat/api/research_stream.py`
- [x] T017 [US2] Implement `GET /api/research/sessions/{session_id}` endpoint returning session + article (latest version) + messages in `apps/backend/src/agentos_chat/api/research_sessions.py`
- [x] T018 [US2] Wire session creation (T008) to trigger `ResearchService.run_research` as a background task after creating the session

### Frontend for US2

- [x] T019 [P] [US2] Add `getSession(sessionId)`, `streamRun(runId)` (SSE client with reasoning/token/article/done/error events), and related types to `apps/frontend/src/services/researchApi.ts`
- [x] T020 [US2] Create `ResearchChat.tsx` component: message thread (user + agent), streaming reasoning/chain-of-thought display, streaming indicator during active run, ordered by sequence_index in `apps/frontend/src/components/ResearchChat.tsx`
- [x] T021 [P] [US2] Create `ArticlePreview.tsx` component: renders markdown with `react-markdown` + `remark-gfm` + `rehype-highlight` + `rehype-raw`, loading/placeholder state until first article, headings/code/tables/lists/blockquotes/links/ASCII art in `apps/frontend/src/components/ArticlePreview.tsx`
- [x] T022 [US2] Create research workspace page `apps/frontend/src/pages/research/[sessionId].astro` with AppLayout, full-width two-panel layout (ResearchChat left, ArticlePreview right), loads session data on mount, connects to SSE stream for active runs

**Checkpoint**: Submitting an idea → agent produces reasoning in chat + complete article in preview panel. Full end-to-end flow works.

---

## Phase 5: US3 — Refine Article via Chat Prompts (Priority: P2)

**Goal**: User sends follow-up prompts in the chat to refine the article. Agent updates the article with a new version.

**Independent Test**: After initial article generation, send "Add a section about performance benchmarks" and verify article updates with the new section.

### Backend for US3

- [x] T023 [US3] Implement `POST /api/research/sessions/{session_id}/messages` endpoint (validates content not empty, rejects if active run via 409, creates user message + triggers agent run) in `apps/backend/src/agentos_chat/api/research_sessions.py`
- [x] T024 [US3] Extend `ResearchService.run_research` to handle refinement runs: load full history including previous messages, include latest article in context, create new ArticleVersion (version_number incremented), update session title if H1 changed

### Frontend for US3

- [x] T025 [US3] Add chat input area to `ResearchChat.tsx`: text input + send button, disabled during active run with Stop button visible, calls `sendMessage` API then connects to new run SSE stream
- [x] T026 [US3] Add `sendMessage(sessionId, content)` and `stopRun(runId)` to `apps/frontend/src/services/researchApi.ts`
- [x] T027 [US3] Implement `POST /api/research/runs/{run_id}/stop` endpoint in `apps/backend/src/agentos_chat/api/research_stream.py` (validates ownership, transitions run to stopping→stopped, cancels agent)
- [x] T028 [US3] Wire article panel update on `article` SSE event in `[sessionId].astro` — replace ArticlePreview content with new version markdown when refinement completes

**Checkpoint**: Full refinement loop works. Send prompt → agent updates article → new version displayed. Send disabled during run. Stop cancels active run.

---

## Phase 6: US5 — Article Versioning and Status (Priority: P2)

**Goal**: Version counter badge on article panel. Bidirectional draft ↔ published status toggle. Agent updates auto-revert to draft.

**Independent Test**: Make multiple refinements → verify version badge increments. Toggle draft/published → verify in article view and home list. Refine a published article → verify status reverts to draft.

### Backend for US5

- [x] T029 [US5] Implement `PATCH /api/research/articles/{article_id}/status` endpoint (validates draft/published, updates latest version status, owner-filtered) in `apps/backend/src/agentos_chat/api/research_articles.py`
- [x] T030 [US5] Ensure `ResearchService` auto-reverts status to draft when creating a new agent-produced ArticleVersion (update logic in `apps/backend/src/agentos_chat/services/research_service.py`)

### Frontend for US5

- [x] T031 [P] [US5] Create `ArticleControls.tsx` component: version badge ("v{N}"), draft/published status toggle button, calls `updateArticleStatus` API on toggle in `apps/frontend/src/components/ArticleControls.tsx`
- [x] T032 [US5] Add `updateArticleStatus(articleId, status)` to `apps/frontend/src/services/researchApi.ts`
- [x] T033 [US5] Integrate `ArticleControls` into the article panel header in `[sessionId].astro`, update version badge and status from SSE `article` event data

**Checkpoint**: Version badge shows correct count. Status toggle works bidirectionally. Agent updates revert published to draft.

---

## Phase 7: US4 — Download Article as Markdown (Priority: P3)

**Goal**: User downloads the article as a `.md` file.

**Independent Test**: Click `.md` download button → valid markdown file downloaded with filename from title.

- [x] T034 [US4] Add download `.md` button to `ArticleControls.tsx` that creates a client-side Blob from current article markdown, generates filename from title slug, and triggers browser download in `apps/frontend/src/components/ArticleControls.tsx`

**Checkpoint**: Download produces valid `.md` file with correct content and filename.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Error handling, retry, edge cases, and deployment readiness

- [x] T035 [P] Implement `POST /api/research/sessions/{session_id}/retry` endpoint (validates no active run, re-triggers agent on same session with original idea) in `apps/backend/src/agentos_chat/api/research_sessions.py`
- [x] T036 [P] Add Retry button UI to `ResearchChat.tsx` for failed agent messages, calls retry API and connects to new SSE stream
- [x] T037 [P] Add LangWatch trace integration to `ResearchService` — record research agent runs with model ID, session ID, and run ID in `apps/backend/src/agentos_chat/services/research_service.py`
- [x] T038 [P] Handle edge cases in `ResearchChat.tsx`: empty search results message, rate-limit gap flagging, malformed markdown graceful degradation
- [x] T039 [P] Handle edge cases in `ArticlePreview.tsx`: malformed markdown renders raw text rather than breaking the page
- [x] T040 [P] Add `RESEARCH_AGENT_MODEL` to Railway backend service env vars documentation in `infra/railway/` or Makefile
- [ ] T041 Run quickstart.md manual verification (15-step smoke flow) and record results (requires running app)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1+US6 (Phase 3)**: Depends on Foundational — home page hub
- **US2 (Phase 4)**: Depends on Foundational + US1 (needs session creation flow)
- **US3 (Phase 5)**: Depends on US2 (needs initial article to refine)
- **US5 (Phase 6)**: Depends on US2 (needs article versions to display/toggle)
- **US4 (Phase 7)**: Depends on US2 (needs article content to download)
- **Polish (Phase 8)**: Can start after US2; most tasks are parallelizable

### User Story Dependencies

- **US1+US6 (P1)**: Start after Foundational — no dependencies on other stories
- **US2 (P1)**: Depends on US1 (session creation), but US2 is the core agent flow
- **US3 (P2)**: Depends on US2 (needs article to refine)
- **US5 (P2)**: Depends on US2 (needs article versions); can parallel with US3
- **US4 (P3)**: Depends on US2 (needs article content); can parallel with US3/US5

### Within Each User Story

- Models → Repository → Services → Endpoints → Frontend components → Page integration
- Core implementation before edge case handling

### Parallel Opportunities

- T002 + T003 can run in parallel (different files)
- T008 then T009 (same file, sequential)
- T010 + T011 + T012 are different frontend files, fully parallel
- T019 + T021 are different files, parallel
- T031 + T032 are different files, parallel
- All Phase 8 tasks marked [P] can run in parallel

---

## Parallel Example: Phase 3 (US1 + US6)

```text
# Backend endpoints (after foundational):
Task T008: POST /api/research/sessions
Task T009: GET /api/research/sessions (paginated)

# Frontend components (parallel, different files):
Task T010: researchApi.ts service
Task T011: ResearchCompose.tsx
Task T012: ResearchList.tsx

# Then wire together:
Task T013: index.astro integration
```

## Parallel Example: Phase 4 (US2)

```text
# Backend (sequential within service layer):
Task T014: research_agent.py factory
Task T015: research_service.py orchestration
Task T016: research_stream.py SSE endpoint
Task T017: GET session detail endpoint
Task T018: Wire session creation to agent

# Frontend (parallel components):
Task T019: researchApi.ts streaming client
Task T021: ArticlePreview.tsx markdown renderer

# Then wire together:
Task T020: ResearchChat.tsx
Task T022: [sessionId].astro workspace page
```

---

## Implementation Strategy

### MVP First (US1 + US6 + US2)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: US1+US6 — Home page with compose + list
4. Complete Phase 4: US2 — Agent generates article
5. **STOP and VALIDATE**: Full idea → article flow works end-to-end
6. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Database ready
2. US1+US6 → Home page compose + list → Demo session creation
3. US2 → Full agent flow → Demo article generation (MVP!)
4. US3 → Refinement loop → Demo iterative editing
5. US5 → Version/status → Demo publishing workflow
6. US4 → Download → Demo export
7. Polish → Edge cases, retry, observability

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story
- US1 and US6 are combined in Phase 3 because they share the home page
- US2 is the heaviest phase (agent + streaming + workspace page)
- US4 is the lightest (single button, client-side only)
- Total: 41 tasks across 8 phases
