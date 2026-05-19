# Data Model: AgentOS Chat Search

## Overview

The feature stores persisted chat history in PostgreSQL, partitioned by an Auth0-compatible user
identity. The first implementation uses a mocked authenticated identity, but the model preserves
the ownership boundary required for real Auth0 validation later. Vector search is out of scope;
pgvector may be provisioned but no vector fields are required.

## Entities

### UserIdentity

Represents the owner of persisted chat history.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | UUID | Yes | Internal primary key |
| `auth_subject` | Text | Yes | Auth0 `sub` or mocked Auth0-compatible subject |
| `display_name` | Text | No | Optional UI label for mock/local use |
| `created_at` | Timestamp | Yes | Server-generated |
| `updated_at` | Timestamp | Yes | Server-generated |

**Validation rules**:
- `auth_subject` must be unique.
- Mock subjects must use a stable prefix such as `mock|`.
- All session queries must filter by `UserIdentity.id`.

### ChatSession

Represents one persisted chat thread owned by a single identity.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | UUID | Yes | Public session identifier |
| `user_identity_id` | UUID | Yes | Owner, references `UserIdentity.id` |
| `title` | Text | No | Derived from first user message or default |
| `status` | Enum | Yes | `active`, `inactive`, `deleted` |
| `created_at` | Timestamp | Yes | Server-generated |
| `updated_at` | Timestamp | Yes | Updated when messages change |
| `deleted_at` | Timestamp | No | Set when user deletes history |

**Validation rules**:
- Only one session is selected as active per identity in the UI at a time.
- Deleted sessions must not be restored or included in agent context.
- New Chat creates a new `active` session without deleting prior sessions.

**State transitions**:
- `active` -> `inactive`: user starts or selects another session.
- `active` or `inactive` -> `deleted`: user deletes the session/history.
- `deleted` has no transition back in this feature.

### ChatMessage

Represents a user message or agent message in a session transcript.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | UUID | Yes | Public message identifier |
| `session_id` | UUID | Yes | References `ChatSession.id` |
| `role` | Enum | Yes | `user`, `assistant`, `system_status` |
| `content` | Text | Yes | User-visible content only |
| `status` | Enum | Yes | `complete`, `streaming`, `stopped`, `failed` |
| `sequence_index` | Integer | Yes | Monotonic per session |
| `created_at` | Timestamp | Yes | Server-generated |
| `completed_at` | Timestamp | No | Set when assistant output finishes |

**Validation rules**:
- Messages must be inserted only for sessions owned by the current identity.
- Assistant messages must not store raw hidden reasoning, internal prompts, or secrets.
- Deleted session messages must not be returned through restore or context APIs.

### AgentRun

Tracks one backend agent execution for streaming, stop, and observability.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | UUID | Yes | Public run identifier |
| `session_id` | UUID | Yes | References `ChatSession.id` |
| `user_message_id` | UUID | Yes | Message that triggered the run |
| `assistant_message_id` | UUID | No | Assistant message being streamed |
| `status` | Enum | Yes | `queued`, `running`, `stopping`, `stopped`, `completed`, `failed` |
| `started_at` | Timestamp | No | Set when execution starts |
| `completed_at` | Timestamp | No | Set when terminal |
| `error_code` | Text | No | Stable failure category |
| `error_message` | Text | No | User-safe failure summary |

**Validation rules**:
- Stop can only affect runs owned by the current identity.
- Stopped runs preserve prior completed messages.
- No new answer text may be appended after cancellation completes.

### SearchResult

Represents public web result metadata used to ground an answer.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | UUID | Yes | Public source identifier |
| `agent_run_id` | UUID | Yes | References `AgentRun.id` |
| `title` | Text | Yes | Source title |
| `url` | Text | Yes | Source URL |
| `snippet` | Text | No | Source snippet or summary |
| `rank` | Integer | Yes | Order returned or selected by agent |
| `created_at` | Timestamp | Yes | Server-generated |

**Validation rules**:
- `url` must be absolute HTTP(S).
- Sources must be returned only with agent responses owned by the current identity.

### DeploymentConfiguration

Documents Railway and local Makefile deployment settings.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `service_name` | Text | Yes | `frontend`, `backend`, or database service name |
| `railway_environment` | Text | Yes | Target Railway environment |
| `minimum_cpu` | Text | Yes | Minimum value requested/applied |
| `minimum_memory` | Text | Yes | Minimum value requested/applied |
| `exception_reason` | Text | No | Required if minimum settings cannot be applied |
| `required_variables` | Text[] | Yes | Variables needed before deployment |

**Validation rules**:
- Exceptions must be documented before deployment is considered complete.
- Makefile smoke test must verify frontend-to-backend connectivity after deployment.

## Relationships

- `UserIdentity` 1:N `ChatSession`
- `ChatSession` 1:N `ChatMessage`
- `ChatSession` 1:N `AgentRun`
- `AgentRun` 1:1 optional assistant `ChatMessage`
- `AgentRun` 1:N `SearchResult`
- `DeploymentConfiguration` is documentation/configuration, not user-owned runtime data.

## Query and Index Expectations

- Unique index on `UserIdentity.auth_subject`.
- Composite index on `ChatSession(user_identity_id, status, updated_at)`.
- Composite index on `ChatMessage(session_id, sequence_index)`.
- Composite index on `AgentRun(session_id, status, started_at)`.
- Composite index on `SearchResult(agent_run_id, rank)`.

## Privacy and Ownership Rules

- Every read and write path must resolve the current mocked/Auth0-compatible identity first.
- Restore, context, stop, delete, and source queries must filter by owner identity.
- Deleted sessions are retained only if needed for audit/debug policy; they are not restored or
  included in agent context for this feature.
- User-facing progress status must never include raw hidden reasoning, chain-of-thought, internal
  prompts, or secrets.
