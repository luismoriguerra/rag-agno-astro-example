# Data Model: Backend Agentic Architecture Refactor

## Overview

This refactor introduces a **two-layer persistence model** without breaking existing PostgreSQL entities. The **agent session store** (Agno `PostgresDb` tables) is authoritative for conversation history used by agents at runtime. **Domain tables** remain the owner-scoped projection consumed by REST restore endpoints and the frontend.

No pgvector changes. One optional Alembic migration may add indexes; Agno auto-provisions session tables via `create_schema=True`.

## Layer Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│  Agent Runtime (Agno Agent / Team)                          │
│  session_id = str(chat_session_id | research_session_id)    │
│  add_history_to_context=True                                │
└──────────────────────────┬──────────────────────────────────┘
                           │ read/write authoritative history
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Agent Session Store (PostgresDb)                           │
│  chat_agno_sessions  |  research_agno_sessions (existing)   │
└──────────────────────────┬──────────────────────────────────┘
                           │ projection after run events
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Domain Tables (SQLAlchemy)                                 │
│  chat_messages, research_messages, agent_runs, ...          │
└─────────────────────────────────────────────────────────────┘
```

## Agent Session Store Tables (Agno-managed)

### `chat_agno_sessions` (NEW table name via PostgresDb config)

| Aspect | Detail |
|--------|--------|
| Owner | Agno `PostgresDb(session_table="chat_agno_sessions")` |
| Purpose | Authoritative chat conversation history for agent context |
| Key | `session_id` maps to `chat_sessions.id` (UUID string) |
| Lifecycle | Created on first message; appended each run |

### `research_agno_sessions` (EXISTING)

| Aspect | Detail |
|--------|--------|
| Owner | Agno `PostgresDb(session_table="research_agno_sessions")` |
| Purpose | Authoritative research team conversation history |
| Key | `session_id` maps to `research_sessions.id` |

## Domain Entities (Existing — Projection Rules)

### ChatMessage (projection)

| Field | Projection rule |
|-------|-------------------|
| `content` | Updated incrementally on `RunContentEvent`; final on complete |
| `status` | `streaming` → `complete` / `stopped` / `failed` |
| `role` | `user` on submit; `assistant` placeholder created at run start |
| `sequence_index` | Monotonic per session (unchanged) |

**Invariant**: After run terminal state, domain row MUST match final agent session assistant turn content.

### AgentRun (unchanged schema, enriched behavior)

| Status | Transition trigger |
|--------|-------------------|
| `queued` | Message accepted |
| `running` | Executor starts `arun` |
| `stopping` | User stop requested |
| `stopped` | Cancel acknowledged; partial content kept |
| `completed` | Normal finish |
| `failed` | Timeout, error, or orphaned on startup |

**New guard queries**:
- `has_active_chat_run(session_id)` — `agent_runs` where status ∈ `{queued, running, stopping}`
- `has_active_research_run(session_id)` — `research_agent_runs` where status ∈ `{queued, running, stopping}`
- `count_active_runs_for_user(user_identity_id)` — **sum** of active rows in `agent_runs` **and** `research_agent_runs`; MUST be `< 10` before starting a new run (FR-009a)

### ResearchMessage (projection)

Same projection rules as chat. `reasoning_content` stores operator-only detail for debugging/restore; SSE `reasoning` event emits redacted phase summary only (never raw CoT).

### SearchResult (enhanced population)

| Field | Source |
|-------|--------|
| `title` | Tavily result `title` |
| `url` | Tavily result `url` |
| `snippet` | Tavily result `content` (truncated) |
| `rank` | Order in tool results, deduped |

### ResearchResult (runtime Pydantic — not persisted as row)

Structured output from research `Team`:

| Field | Maps to |
|-------|---------|
| `chat_response` | `research_messages.content` |
| `article_markdown` | new `research_article_versions` row (if non-empty) |
| `article_title` | session title update |
| `suggested_actions` | SSE `actions` event |

## State Transitions: Run Lifecycle

```text
queued ──► running ──► completed
              │
              ├──► stopping ──► stopped (partial content kept)
              │
              └──► failed (timeout | error | orphaned)
```

**Concurrent submission while `queued|running|stopping`**: HTTP 409 `run_in_progress`.

**User at 10 active runs globally**: HTTP 409 `concurrent_run_limit`.

## Migration & Backfill

| Step | Action |
|------|--------|
| Deploy | Agno creates `chat_agno_sessions` if missing (`auto_provision_dbs=True`) |
| Backfill | One-time script: for each `chat_session`, if agent store empty, import `chat_messages` history |
| Verify | Restore API messages match agent store turns for sampled sessions |

No destructive migration. Existing rows preserved.

## Indexes (recommended)

| Table | Index | Reason |
|-------|-------|--------|
| `agent_runs` | `(user_identity_id via join, status)` | Per-user active run count |
| Existing | Keep current indexes | No regression |

Add composite query for active runs by owner if not already efficient.

## Data NOT in Scope

- New vector embeddings or pgvector tables
- New user-facing entities
- Changes to `research_articles` / version schema (behavior only)
