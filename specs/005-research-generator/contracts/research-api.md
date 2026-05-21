# Research API Contract

## Authentication

All endpoints require Auth0 Bearer JWT. Unauthenticated requests return `401`.

## Endpoints

### POST /api/research/sessions

Create a new research session and trigger the research agent.

**Request**:
```json
{ "idea": "The state of WebAssembly in 2026" }
```

**Response** `201`:
```json
{
  "session_id": "uuid",
  "title": "The state of WebAssembly in 2026",
  "status": "draft",
  "created_at": "2026-05-20T22:00:00Z",
  "run_id": "uuid"
}
```

**Errors**:
- `400` — `idea` is empty or missing
- `401` — unauthenticated

---

### GET /api/research/sessions

List the authenticated user's research sessions, paginated.

**Query parameters**:
| Param | Type | Default | Notes |
|-------|------|---------|-------|
| `page` | int | 1 | 1-based page number |
| `page_size` | int | 10 | Options: 5, 10, 20, 50 |

**Response** `200`:
```json
{
  "sessions": [
    {
      "id": "uuid",
      "title": "The state of WebAssembly in 2026",
      "idea": "The state of WebAssembly in 2026",
      "status": "draft",
      "is_generating": false,
      "current_version": 2,
      "created_at": "2026-05-20T22:00:00Z",
      "updated_at": "2026-05-20T22:05:00Z"
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 10
}
```

**Notes**:
- `status` is derived from the latest article version (`draft` or `published`); `draft` if no article exists.
- `is_generating` is `true` if an agent run is currently `running` or `queued`.
- Ordered by `updated_at DESC`.

---

### GET /api/research/sessions/{session_id}

Get a single research session with article and messages.

**Response** `200`:
```json
{
  "session": {
    "id": "uuid",
    "title": "WebAssembly in 2026",
    "idea": "The state of WebAssembly in 2026",
    "status": "draft",
    "is_generating": false,
    "current_version": 2,
    "created_at": "2026-05-20T22:00:00Z",
    "updated_at": "2026-05-20T22:05:00Z"
  },
  "article": {
    "id": "uuid",
    "current_version": 2,
    "latest_version": {
      "id": "uuid",
      "version_number": 2,
      "markdown_content": "# WebAssembly in 2026\n\n## TL;DR\n...",
      "status": "draft",
      "change_source": "agent",
      "created_at": "2026-05-20T22:05:00Z"
    }
  },
  "messages": [
    {
      "id": "uuid",
      "role": "user",
      "content": "The state of WebAssembly in 2026",
      "reasoning_content": null,
      "status": "complete",
      "sequence_index": 0,
      "created_at": "2026-05-20T22:00:00Z"
    },
    {
      "id": "uuid",
      "role": "assistant",
      "content": "I'll research WebAssembly...",
      "reasoning_content": "Planning article structure...",
      "status": "complete",
      "sequence_index": 1,
      "created_at": "2026-05-20T22:00:05Z"
    }
  ]
}
```

**Errors**:
- `404` — session not found or not owned by current user

---

### POST /api/research/sessions/{session_id}/messages

Send a follow-up prompt to refine the article.

**Request**:
```json
{ "content": "Add a section about performance benchmarks" }
```

**Response** `201`:
```json
{
  "message_id": "uuid",
  "run_id": "uuid"
}
```

**Errors**:
- `400` — content is empty
- `409` — an agent run is already in progress for this session
- `404` — session not found or not owned

---

### GET /api/research/runs/{run_id}/stream

SSE stream for a research agent run.

**Event types**:

| Event | Data | Notes |
|-------|------|-------|
| `thinking` | `{"status": "searching", "message": "Researching section 1..."}` | Agent progress |
| `reasoning` | `{"content": "..."}` | Chain-of-thought chunk (visible in research chat) |
| `token` | `{"text": "..."}` | Agent chat response token |
| `article` | `{"markdown": "# Full Article...", "version": 2, "title": "..."}` | Complete article on run finish |
| `done` | `{"run_id": "uuid", "status": "completed"}` | Terminal success |
| `error` | `{"code": "agent_error", "message": "..."}` | Terminal failure |

---

### POST /api/research/runs/{run_id}/stop

Cancel an in-progress research agent run.

**Response** `200`:
```json
{ "run_id": "uuid", "status": "stopped" }
```

**Errors**:
- `404` — run not found or not owned
- `409` — run already terminal

---

### PATCH /api/research/articles/{article_id}/status

Update the status of the latest article version.

**Request**:
```json
{ "status": "published" }
```

**Response** `200`:
```json
{
  "article_id": "uuid",
  "version_number": 2,
  "status": "published"
}
```

**Errors**:
- `400` — invalid status (must be `draft` or `published`)
- `404` — article not found or not owned

---

### POST /api/research/sessions/{session_id}/retry

Retry a failed research agent run.

**Response** `201`:
```json
{ "run_id": "uuid" }
```

**Errors**:
- `404` — session not found or not owned
- `409` — a run is already in progress
