# Data Model: LangWatch Backend Observability

## Overview

This feature does not introduce PostgreSQL tables or migrations. Observability data is exported to
LangWatch as traces/spans. The data model below describes trace metadata and configuration
entities aligned with the feature spec and existing chat entities from `001-agentos-chat-search`.

## External Entities (LangWatch)

### AgentRunTrace

Represents one exported observability record for a single `AgentRun` execution in the chat backend.

| Field / attribute | Type | Required | Source |
|-------------------|------|----------|--------|
| `run_id` | UUID (string) | Yes | `AgentRun.id` |
| `session_id` | UUID (string) | Yes | `ChatSession.id` |
| `auth_subject` | Text | Yes | Auth0-compatible subject from request/mock header |
| `environment` | Enum | Yes | `local`, `staging`, `production` from `APP_ENVIRONMENT` |
| Model/tool spans | Nested spans | Yes | Auto-captured by `AgnoInstrumentor` |
| Prompt/response content | Text | Yes | Full content per clarification (all environments) |
| `status` | Enum | Yes | Derived from run outcome: completed, failed, stopped, timeout |

**Validation rules**:
- `run_id`, `session_id`, and `auth_subject` MUST match the chat system records for that execution.
- `environment` MUST be one of the three allowed values.
- Secrets MUST NOT appear in trace attributes (API keys, tokens).

**Relationships**:
- One `AgentRun` → one root LangWatch trace per execution attempt.
- One `ChatSession` → many traces over time (one per message/run).
- One `UserIdentity` → many traces via `auth_subject` correlation.

### LangWatchConfiguration

Runtime configuration loaded at backend startup (not persisted in app DB).

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `api_key` | Secret | No | From `LANGWATCH_API_KEY`; empty disables export |
| `endpoint` | URL | No | From `LANGWATCH_ENDPOINT`; SaaS default if unset |
| `app_environment` | Enum | Yes | Default `local`; maps to trace `environment` tag |
| `enabled` | Boolean | Derived | True when `api_key` is non-empty |

## Unchanged Persistent Entities

The following remain defined in `specs/001-agentos-chat-search/data-model.md` with no schema changes:

- `UserIdentity`
- `ChatSession`
- `ChatMessage`
- `AgentRun`
- `SearchResult` (stored per run in PostgreSQL; also visible in tool spans when search runs)

## State Transitions (Trace vs Run)

Trace export is best-effort and does not gate chat run state machines:

| Chat `AgentRun.status` | Expected trace signal |
|------------------------|------------------------|
| `running` | In-progress root trace / child spans |
| `completed` | Root trace closed with success |
| `failed` | Root trace shows error |
| `stopped` | Root trace shows cancellation |
| `stopping` | May show partial spans before stop |

## Privacy and Retention

- Full message content is stored in LangWatch per product clarification; retention follows
  LangWatch project settings, not application DB retention rules.
- Application chat history retention (indefinite until user delete) is unchanged.
