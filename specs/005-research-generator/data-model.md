# Data Model: Research Generator

## Overview

The feature stores research sessions, chat messages, articles, and article versions in PostgreSQL, fully separate from the existing chat tables. All data is owner-scoped via `user_identity_id` referencing the existing `UserIdentity` table. No vector search is required.

## Entities

### ResearchSession

Represents a single research endeavor owned by one user.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | UUID | Yes | Primary key |
| `user_identity_id` | UUID | Yes | References `user_identities.id` |
| `idea` | Text | Yes | Original idea/prompt submitted by the user |
| `title` | String(500) | Yes | Display title; initially truncated idea (max 60 chars), updated to article H1 when available |
| `created_at` | Timestamp | Yes | Server-generated |
| `updated_at` | Timestamp | Yes | Updated on any session activity (message, article version) |

**Validation rules**:
- `idea` must not be empty.
- `title` defaults to first 60 characters of `idea`.
- All queries must filter by `user_identity_id`.

### ResearchMessage

A message in the research session's chat thread.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | UUID | Yes | Primary key |
| `session_id` | UUID | Yes | References `research_sessions.id` |
| `role` | Enum | Yes | `user`, `assistant` |
| `content` | Text | Yes | User-visible content (chat text, reasoning, plan) |
| `reasoning_content` | Text | No | Agent chain-of-thought content (stored separately for potential future filtering) |
| `status` | Enum | Yes | `complete`, `streaming`, `stopped`, `failed` |
| `sequence_index` | Integer | Yes | Monotonic per session |
| `created_at` | Timestamp | Yes | Server-generated |
| `completed_at` | Timestamp | No | Set when agent output finishes |

**Validation rules**:
- Messages must only be inserted for sessions owned by the current identity.
- Secrets and internal system prompts must be redacted before storage.

### ResearchArticle

The generated article for a research session. One article per session.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | UUID | Yes | Primary key |
| `session_id` | UUID | Yes | References `research_sessions.id`, unique constraint |
| `current_version` | Integer | Yes | Tracks the latest version number |
| `created_at` | Timestamp | Yes | Server-generated |
| `updated_at` | Timestamp | Yes | Updated when a new version is added |

**Validation rules**:
- One-to-one with `ResearchSession` (unique `session_id`).
- `current_version` increments with each new `ResearchArticleVersion`.

### ResearchArticleVersion

A snapshot of the article at a point in time.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | UUID | Yes | Primary key |
| `article_id` | UUID | Yes | References `research_articles.id` |
| `version_number` | Integer | Yes | Monotonically increasing per article |
| `markdown_content` | Text | Yes | Full article markdown |
| `status` | Enum | Yes | `draft`, `published`; defaults to `draft` |
| `change_source` | Enum | Yes | `agent` (manual deferred to future) |
| `created_at` | Timestamp | Yes | Server-generated |

**Validation rules**:
- Agent-created versions always default to `draft` (published auto-reverts).
- Status is user-updatable on the latest version only (bidirectional: draft ↔ published).
- `version_number` combined with `article_id` is unique.

**State transitions (status)**:
- `draft` → `published`: user sets via article panel control.
- `published` → `draft`: user sets manually, OR agent creates a new version (auto-revert).

### ResearchAgentRun

Tracks one research agent execution for streaming, stop, retry, and observability.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | UUID | Yes | Primary key |
| `session_id` | UUID | Yes | References `research_sessions.id` |
| `user_message_id` | UUID | Yes | References `research_messages.id` (trigger message) |
| `assistant_message_id` | UUID | No | References `research_messages.id` (agent response) |
| `status` | Enum | Yes | `queued`, `running`, `stopping`, `stopped`, `completed`, `failed` |
| `started_at` | Timestamp | No | Set when execution starts |
| `completed_at` | Timestamp | No | Set when terminal |
| `error_code` | String(100) | No | Stable failure category |
| `error_message` | Text | No | User-safe failure summary |

**Validation rules**:
- Stop can only affect runs owned by the current identity.
- Stopped runs preserve prior completed messages.
- No new content may be appended after cancellation completes.

## Relationships

- `UserIdentity` 1:N `ResearchSession`
- `ResearchSession` 1:N `ResearchMessage`
- `ResearchSession` 1:1 `ResearchArticle`
- `ResearchSession` 1:N `ResearchAgentRun`
- `ResearchArticle` 1:N `ResearchArticleVersion`
- `ResearchAgentRun` 1:1 optional assistant `ResearchMessage`

## Query and Index Expectations

- Composite index on `ResearchSession(user_identity_id, updated_at DESC)` — paginated home list.
- Composite index on `ResearchMessage(session_id, sequence_index)` — ordered chat history.
- Unique index on `ResearchArticle(session_id)` — one article per session.
- Composite index on `ResearchArticleVersion(article_id, version_number)` — version ordering.
- Composite index on `ResearchAgentRun(session_id, status, started_at)` — run lookup.

## Privacy and Ownership Rules

- Every read and write path must resolve the current Auth0-validated identity first.
- Session list, message history, article content, and version queries must filter by owner identity.
- Research data is fully separate from chat data — no cross-table queries between the two features.
- Agent chain-of-thought is visible in the research UI but secrets and internal system prompts are redacted before storage.
- Sessions cannot be deleted in v1; they persist for the owner.
