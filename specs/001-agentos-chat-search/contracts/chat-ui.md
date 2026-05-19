# UI Contract: Astro `/chat`

## Route

- Path: `/chat`
- Purpose: Persisted chat interface for the mocked/Auth0-compatible current identity.
- Backend dependency: `AGENTOS_API_BASE_URL`

## Required Page Regions

- Chat transcript region with user messages, assistant messages, safe status messages, and source
  links.
- Message composer with text input and submit action.
- New Chat action.
- Stop action, visible only when an agent run is active.
- Delete active session action for the active session.
- Connection/error region for retryable backend, stream, identity, and restore failures.

## State Contract

| State | Trigger | Required UI Behavior |
|-------|---------|----------------------|
| `empty` | No active messages | Show empty transcript guidance and enabled composer |
| `restoring` | Page loads active session | Show loading affordance without clearing cached UI |
| `ready` | Session restored or created | Enable composer and New Chat |
| `submitting` | User submits valid message | Add user message, disable duplicate submit, open stream |
| `thinking` | Backend emits safe progress event | Show safe status such as "Searching public web results" |
| `streaming` | Backend emits token events | Append answer text visibly as it arrives |
| `stopping` | User presses Stop | Disable Stop until cancellation result, keep prior messages |
| `stopped` | Backend confirms stopped | Stop adding answer text and mark run stopped |
| `failed` | Backend or stream fails | Show retryable error and preserve latest user question |
| `deleted` | User deletes the active session | Clear active transcript and exclude that session from future restore and agent context |

## Interaction Rules

- Empty or whitespace-only messages must not be submitted.
- New Chat creates a new persisted session and does not delete prior sessions.
- Stop cancels only the active run in the current session.
- The page must never display raw hidden reasoning, chain-of-thought, internal prompts, or secrets.
- Search result sources must be visible for answers that use public web results.
- Restored messages must belong only to the current mocked/Auth0-compatible identity.

## Streaming Event Handling

| SSE Event | Required Client Behavior |
|-----------|--------------------------|
| `thinking` | Render safe progress status from `message` |
| `token` | Append `text` to the active assistant message |
| `source` | Add source metadata to the active assistant message |
| `done` | Mark active assistant message complete |
| `error` | Mark active assistant message failed and show retryable error |

## Accessibility Requirements

- Transcript updates should be announced politely without stealing focus.
- Stop and New Chat buttons must be keyboard reachable.
- Error messages must be text, not color-only indicators.
- Streaming text must remain readable when motion or animation preferences are reduced.
