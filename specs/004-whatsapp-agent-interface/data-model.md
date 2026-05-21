# Data Model: WhatsApp Agent Interface

## Overview

Adds two application-owned PostgreSQL tables for runtime WhatsApp configuration. WhatsApp conversation sessions are stored separately via Agno's PostgreSQL storage adapter (not the existing `ChatSession` schema). No pgvector changes.

## New Entities

### WhatsAppSettings (singleton)

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUID | PK, default uuid4 | Single row expected |
| `enabled` | boolean | NOT NULL, default `false` | Profile toggle |
| `created_at` | timestamptz | server default now() | |
| `updated_at` | timestamptz | on update | |

**Lifecycle**: Lazy-created on first `GET /api/whatsapp/settings` or first webhook gate check if missing. Default: `enabled=false`.

**Uniqueness**: Application enforces singleton (query first row or fixed id); no multi-tenant settings.

### AllowedPhoneNumber

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUID | PK | |
| `settings_id` | UUID | FK → `whatsapp_settings.id`, ON DELETE CASCADE | |
| `phone_number` | varchar(20) | NOT NULL, UNIQUE | E.164 format, e.g. `+14155552671` |
| `created_at` | timestamptz | server default now() | |

**Validation**: E.164 regex at API and frontend; reject duplicates with 409.

**Gate rule**: If `enabled=true` and allowlist count > 0, only listed numbers receive agent replies. Empty allowlist = open access.

## Agno-Managed Entities (external to app migrations)

### WhatsApp Session

- **Scope**: One active session per phone number (`wa:{agent_name}:{normalized_phone}`).
- **Storage**: Agno PostgreSQL adapter tables (created/managed by Agno, not Alembic in this feature unless Agno requires explicit schema).
- **History**: Last 10 agent runs in context (`num_history_runs=10`; one run = one user message + one agent response).
- **`/new` command**: Agno creates new session with random suffix; prior session preserved.

### WhatsApp Message (logical)

Not persisted in app tables; Agno session storage holds turn history. Structured logs capture inbound/outbound for observability.

## Relationships

```text
WhatsAppSettings (1) ──< AllowedPhoneNumber (*)

WhatsApp Session (Agno) — scoped by phone, isolated from:
  UserIdentity ──< ChatSession ──< ChatMessage (REST channel)
```

## Migration

**Revision**: `002_whatsapp_settings` (Alembic)

```text
whatsapp_settings
allowed_phone_numbers
  INDEX on phone_number (unique)
  FK settings_id → whatsapp_settings.id
```

No seed data; lazy init at runtime.

## State Transitions

### WhatsAppSettings.enabled

| From | Action | To | Webhook behavior |
|------|--------|-----|------------------|
| false (default) | Profile toggle ON | true | Process messages (subject to allowlist) |
| true | Profile toggle OFF | false | Silent ignore all inbound |
| true | In-flight message | true | Complete in-flight; ignore subsequent |

### Allowlist

| State | Behavior |
|-------|----------|
| Empty + enabled | Open access — all numbers |
| Non-empty + enabled | Only listed numbers |
| Any + disabled | No processing |

## Unchanged Entities

From `specs/001-agentos-chat-search/data-model.md`: `UserIdentity`, `ChatSession`, `ChatMessage`, `AgentRun`, `SearchResult` — no schema changes. REST and WhatsApp channels remain isolated.
