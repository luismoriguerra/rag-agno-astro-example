# Feature Specification: Backend Agentic Architecture Refactor

**Feature Branch**: `007-backend-agentic-refactor`  
**Created**: 2026-05-25  
**Status**: Draft  
**Input**: User description: "refactor to a well structured and well constructed backend agentic app"

## Clarifications

### Session 2026-05-25

- Q: When a user submits a second chat message while a chat run is still in progress, what should happen? → A: Reject the second message with a conflict response (one active run per chat session, same as research).
- Q: When a user stops an in-progress run mid-stream, what happens to the partial assistant response already delivered? → A: Keep partial content — save whatever was streamed so far as the assistant message with a "stopped" status.
- Q: After the refactor, which store is the authoritative source of truth for chat conversation history? → A: Agent session store becomes authoritative; domain tables are a read projection for API/UI restore.
- Q: How should the refactor be rolled out to production? → A: Big bang — chat and research refactored together in a single release.
- Q: Should there be a per-user limit on concurrent active agent runs across all sessions? → A: Max 10 concurrent active runs per user.
- Q: What may be exposed to end users from model reasoning during research runs? → A: Never raw chain-of-thought. User-visible SSE uses safe `thinking` messages during execution; the optional research `reasoning` event carries a **redacted phase summary** only (e.g., delegation steps, tool-use counts). Full reasoning deltas go to LangWatch traces and optional operator-only DB fields — not client SSE.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Real-Time Agent Responses (Priority: P1)

When a user sends a message in chat or research, they see the agent's response appear progressively as it is generated — including visible progress while the agent searches the web or delegates work — rather than waiting for the entire answer to finish before anything appears.

**Why this priority**: Perceived responsiveness is the core UX of an agentic product. Artificial delays or silent waits make the app feel broken even when answers are correct.

**Independent Test**: Send a chat message and a research prompt; verify tokens or progress events appear within 3 seconds of submission and continue until completion, without a long silent gap followed by a bulk dump.

**Acceptance Scenarios**:

1. **Given** a logged-in user submits a chat question, **When** the agent begins working, **Then** the user sees a safe progress indicator (e.g., "Searching…") within 3 seconds, followed by streamed answer text as it becomes available.
2. **Given** a logged-in user starts a research session, **When** the research team delegates to a writer or runs a web search, **Then** the user sees status updates reflecting the current phase (researching, delegating, writing) without exposing raw chain-of-thought.
3. **Given** a user is watching a streamed response, **When** the agent completes, **Then** the user receives a definitive completion signal and the final message is persisted and restorable on session reload.

---

### User Story 2 - Reliable Research Output Structure (Priority: P1)

When the research agent creates or updates an article, the system consistently produces a chat summary, an optional article body, and optional follow-up action suggestions — without requiring fragile text parsing that fails when the model deviates from a custom format.

**Why this priority**: The research feature's value depends on reliably separating conversational feedback from article content. Format drift currently causes empty articles, missing actions, or chat text leaking into the article panel.

**Independent Test**: Run five research sessions with varied prompts (new article, summary-only, Q&A-only, refinement); verify each response type maps correctly to chat panel, article panel, and action chips.

**Acceptance Scenarios**:

1. **Given** a user requests a new research article, **When** the agent completes, **Then** the chat panel shows a conversational summary, the article panel shows full markdown with title, TL;DR, body sections, and sources, and the user sees 3–5 suggested follow-up actions.
2. **Given** a user asks a question about an existing article without requesting changes, **When** the agent responds, **Then** the chat panel updates with the answer and the article panel remains unchanged.
3. **Given** the agent cannot produce structured output, **When** a fallback is needed, **Then** the user receives a clear chat message explaining the limitation rather than a blank or corrupted article panel.

---

### User Story 3 - Conversation Continuity Across Turns (Priority: P1)

When a user continues an existing chat or research session, the agent remembers prior turns in that session and responds in context — without the user needing to repeat earlier information.

**Why this priority**: Multi-turn refinement is essential for both chat search and research workflows. Manual history stitching is error-prone and does not scale as sessions grow.

**Independent Test**: In chat, ask a follow-up question that references a prior answer without restating context; verify the agent responds coherently. In research, refine an article twice and verify each turn builds on the previous draft.

**Acceptance Scenarios**:

1. **Given** a chat session with at least three prior messages, **When** the user asks "Can you elaborate on the second point?", **Then** the agent's answer references the correct prior content without the user restating it.
2. **Given** a research session with an existing article draft, **When** the user sends "Add a benchmarks section", **Then** the agent updates the article while preserving prior sections and sources where still valid.
3. **Given** a user reloads a session page, **When** they send a new message, **Then** the agent still has access to the full prior conversation for that session via the agent session store, and the UI restore API reflects the same history through the domain projection.

---

### User Story 4 - Accurate Source Citations (Priority: P2)

When the search agent answers a question using web search, the user sees cited sources with meaningful titles and snippets — not just bare URLs extracted from the answer text.

**Why this priority**: Grounded answers require trustworthy citations. URL-only sources with missing titles reduce confidence and make verification harder.

**Independent Test**: Ask a factual question requiring web search; verify at least one source includes a human-readable title distinct from the URL and, when available, a snippet.

**Acceptance Scenarios**:

1. **Given** a chat answer grounded in web search, **When** sources are displayed, **Then** each source includes a title and URL, and a snippet when the search provider returned one.
2. **Given** the agent cites multiple sources, **When** the response completes, **Then** sources are deduplicated, ranked, and capped at a reasonable maximum (e.g., 10) for display.
3. **Given** search returns insufficient results, **When** the agent responds, **Then** the user is told clearly that confidence is limited and sources may be sparse or absent.

---

### User Story 5 - Stop and Recover from Agent Runs (Priority: P2)

When a user stops an in-progress agent run or the run fails, the system transitions to a clear terminal state — the user is not left with a permanently "running" session, and they can start a new message afterward.

**Why this priority**: Long-running research and search calls can exceed user patience. Without reliable stop and failure handling, sessions become unusable until manual intervention.

**Independent Test**: Start a research run, click stop mid-flight, verify status becomes stopped and a new message can be sent. Simulate a timeout and verify failed status with a user-friendly message.

**Acceptance Scenarios**:

1. **Given** an agent run is in progress, **When** the user requests stop, **Then** the run transitions to a stopped state within 10 seconds, the UI receives a completion signal, and any assistant text already streamed is persisted with a stopped status.
2. **Given** an agent run exceeds the configured time limit, **When** the timeout triggers, **Then** the run is marked failed with a clear user-facing message and the session accepts new input.
3. **Given** a run failed or was stopped, **When** the user sends a new message, **Then** the system accepts it without requiring session recreation.
4. **Given** a chat run is already in progress, **When** the user submits another message to the same chat session, **Then** the system rejects the submission with a conflict response and does not start a second run.

---

### User Story 6 - Operator Visibility into Agent Activity (Priority: P2)

When agent runs execute in any environment, operators can trace a run end-to-end — including tool usage and model calls — to diagnose latency, cost, and failure patterns without reproducing the issue locally.

**Why this priority**: Agentic systems fail opaquely without traces. Both chat and research workloads need consistent observability, especially research which is multi-step and cost-heavy.

**Independent Test**: Execute one chat run and one research run with tracing enabled; verify both appear in the observability dashboard with session and run identifiers, tool spans, and token usage where applicable.

**Acceptance Scenarios**:

1. **Given** tracing is configured for an environment, **When** a chat agent run completes, **Then** a trace exists linking run ID, session ID, and authenticated user subject.
2. **Given** tracing is configured, **When** a research team run completes, **Then** a trace exists showing coordinator and writer phases with token usage captured per model call.
3. **Given** tracing is not configured, **When** agent runs execute, **Then** chat and research continue to function normally with structured application logs still emitted.

---

### User Story 7 - Preserved Product Behavior During Refactor (Priority: P1)

Existing authenticated users continue to use chat search and research features without breaking changes to session management, message submission, streaming endpoints, or article versioning. Chat and research are refactored together and released in a single deployment — no partial rollout where one workflow runs on the old architecture while the other runs on the new.

**Why this priority**: This is a structural improvement, not a product pivot. Regression would block deployment regardless of internal quality gains.

**Independent Test**: Run the existing contract and integration test suite against the refactored backend; all current API contracts pass without frontend changes.

**Acceptance Scenarios**:

1. **Given** the refactored backend is deployed, **When** the frontend performs existing chat flows (create session, send message, stream run, stop run, restore history), **Then** all flows succeed with equivalent user-visible behavior.
2. **Given** the refactored backend is deployed, **When** the frontend performs existing research flows (create session, stream run, refine article, download markdown, change draft/published status), **Then** all flows succeed with equivalent user-visible behavior.
3. **Given** a user has data in existing sessions, **When** the refactor is deployed, **Then** prior messages, articles, versions, and costs remain accessible.

---

### Edge Cases

- What happens when the user opens an SSE stream after partially missing events (reconnect)? The client receives replayed events from the run's history buffer or persisted state so it can catch up.
- What happens when two messages are submitted rapidly to the same chat or research session? The second submission is rejected with a conflict response while the first run is active; the user must wait for completion, stop, or failure before sending again.
- What happens when a user exceeds the per-user concurrent run limit? Additional run submissions are rejected with a conflict response until an active run completes, stops, or fails; the user sees a clear message indicating the limit (max 10 concurrent active runs).
- What happens when web search credentials are missing or invalid? The agent responds with a clear error and does not hang indefinitely.
- What happens when a user stops a run after partial content has streamed? The partial assistant text delivered so far is persisted with a stopped status and remains visible on session reload; no article version is created for research unless a complete structured outcome was produced.
- What happens when the model returns empty content? The user receives a helpful fallback message rather than a blank assistant bubble.
- What happens on application restart while runs are in progress? Runs transition to a recoverable failed or stopped state rather than remaining stuck in "running" forever.
- What happens when Auth0 signing keys rotate? Token validation continues to work without requiring a full application redeploy.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST stream agent output to connected clients as it is generated, including safe progress indicators during tool use and delegation.
- **FR-002**: System MUST NOT introduce artificial delays that simulate streaming after the full response is already available.
- **FR-003**: System MUST produce research responses as structured outcomes separating chat text, optional article markdown, optional title, and optional suggested actions.
- **FR-004**: System MUST support chat-only research responses (summary, Q&A) that do not modify the article panel.
- **FR-005**: System MUST maintain per-session conversation history for chat and research agents across multiple user turns within a session; the agent session store is authoritative for agent context, with domain tables maintained as a read projection for API and UI restore.
- **FR-006**: System MUST extract search sources from tool results with title, URL, optional snippet, and rank — not solely by parsing URLs from free text.
- **FR-007**: System MUST allow users to stop in-progress agent runs and reach a terminal stopped state; any assistant content already streamed MUST be persisted with a stopped status rather than discarded.
- **FR-008**: System MUST enforce configurable timeouts on agent runs and surface user-friendly failure messages on timeout.
- **FR-009**: System MUST prevent concurrent active runs on the same session (chat and research); a second message submission while a run is active MUST be rejected with a conflict response.
- **FR-009a**: System MUST cap concurrent active agent runs at 10 per authenticated user across **all chat and research sessions combined**; submissions beyond this limit MUST be rejected with a conflict response and a user-facing limit message. Active-run counts MUST query both `agent_runs` (chat) and `research_agent_runs` (research) tables.
- **FR-010**: System MUST preserve existing authenticated API contracts for chat and research so the current frontend works without modification; chat and research MUST be cut over together in one release (no mixed old/new architecture across workflows).
- **FR-011**: System MUST preserve owner-scoped access: users can only read, stream, or stop runs belonging to their sessions.
- **FR-012**: System MUST emit structured logs for run lifecycle events (start, complete, stop, fail) without logging secrets or raw tokens.
- **FR-013**: System MUST trace chat and research agent runs in configured observability environments with run and session correlation metadata.
- **FR-014**: System MUST capture and persist token usage for research runs for cost visibility.
- **FR-015**: System MUST initialize agent credentials from configuration at startup rather than mutating process environment on each request.
- **FR-016**: System MUST reuse agent instances across requests within a process where session identity is passed per run.
- **FR-017**: System MUST transition orphaned in-progress runs to a terminal state after application restart or unrecoverable worker failure.
- **FR-018**: System MUST refresh authentication signing keys during runtime so token validation survives provider key rotation.
- **FR-019**: System MUST dispose shared resources cleanly on application shutdown.
- **FR-020**: System MUST honor the existing telemetry opt-out setting independently of optional third-party tracing.

### Constitution Requirements *(mandatory when applicable)*

- **RAG Grounding**: Chat and research agents MUST ground factual claims in web search tool results. Sources MUST be surfaced to users with title and URL. When search results are insufficient, agents MUST state limitations explicitly rather than invent citations. Quality is measured by source accuracy (title matches URL content) and citation coverage on factual answers.
- **Agent Behavior**: Chat uses a single search-capable agent; research uses a coordinator-plus-writer team pattern with explicit delegation boundaries. Agents MUST NOT expose raw chain-of-thought to end users via SSE or REST. User-visible progress uses safe `thinking` messages only. The optional research `reasoning` SSE event MUST carry a redacted phase summary (delegation/tool milestones), not model reasoning tokens. Operator-only fields (`reasoning_content` in DB, LangWatch spans) MAY retain fuller detail for debugging. Tool permissions are limited to configured web search. All runs MUST be traceable with run ID, session ID, and authenticated subject.
- **Auth0 Authorization**: All protected routes MUST require validated Auth0 tokens with the baseline API scope. Owner filtering MUST apply before returning sessions, messages, runs, or articles. JWT validation MUST support key rotation. Research routes MUST receive the same scope enforcement as chat routes.
- **Data and Vector Search**: N/A for this refactor — no new vector search or embedding changes. Existing PostgreSQL entities (chat sessions, messages, runs, research sessions, articles, versions, costs) remain for owner filtering, run tracking, and UI/API restore as projections of agent session state. The agent session store is authoritative for conversation history; domain message tables MUST stay consistent with it for restore endpoints.
- **Deployment and Observability**: Refactor MUST deploy to Railway without new mandatory services for v1. Environment variables for model keys, search keys, Auth0, and optional tracing remain configuration-driven. Health check endpoint MUST continue to respond. Structured logs and optional traces MUST cover both chat and research run paths.

### Key Entities

- **Agent Run**: A single execution of an agent or team triggered by a user message; has status (queued, running, stopping, stopped, completed, failed), timestamps, optional error details, and links to user and assistant messages.
- **Chat Session**: A user's conversational thread for search-backed Q&A; owns ordered messages and runs; scoped to authenticated identity. Conversation history is authoritative in the agent session store; domain message rows are a projection for API restore.
- **Research Session**: A user's research workspace tied to an initial idea; owns messages, article versions, runs, and cost records.
- **Research Article Version**: An immutable snapshot of article markdown produced or updated by the agent; numbered sequentially with draft/published status.
- **Search Source**: A ranked citation from a web search tool result attached to a chat run; includes title, URL, optional snippet.
- **Run Event Stream**: A sequence of typed events (progress, token, source, article, actions, done, error) delivered to the client during an active run. Research may optionally emit a `reasoning` event containing a redacted phase summary — never raw chain-of-thought.
- **Cost Record**: Token usage attributed to a research run and model call for session-level cost summaries.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users see the first streamed content or safe progress indicator within 3 seconds of submitting a chat or research message in 95% of runs under normal load.
- **SC-002**: Research article-producing runs deliver correctly structured outcomes (chat + article + actions when applicable) in at least 90% of test scenarios without manual delimiter repair.
- **SC-003**: Follow-up messages in existing sessions receive contextually relevant answers in at least 90% of multi-turn test scenarios without users restating prior context.
- **SC-004**: At least 80% of chat answers grounded in web search include at least one source with a human-readable title distinct from the raw URL.
- **SC-005**: User-initiated stop requests reach a terminal stopped state within 10 seconds in 95% of attempts.
- **SC-006**: Zero runs remain permanently stuck in "running" status 5 minutes after application restart in integration tests.
- **SC-007**: 100% of existing contract and integration tests for chat and research APIs pass without frontend changes.
- **SC-008**: Both chat and research runs produce correlated traces (when tracing is enabled) in 100% of sampled test runs.
- **SC-009**: Median time-to-first-token improves by at least 30% compared to the pre-refactor baseline that waits for full completion before streaming.
- **SC-010**: Adding a third agent-powered workflow (beyond chat and research) requires no new bespoke streaming or run-status implementation — the same execution pattern is reused end-to-end.
- **SC-011**: Users with 10 active runs across sessions receive a conflict response on an 11th submission in 100% of tested attempts, with a message explaining the concurrent run limit.

## Assumptions

- The refactor is incremental internally but releases as a single deployment: chat and research switch to the new architecture together; existing REST and SSE API shapes remain stable and do not require a frontend release for v1. Additive 409 responses (`run_in_progress`, `concurrent_run_limit`) are backward-compatible at the HTTP layer; clients that do not handle 409 SHOULD be updated in a follow-up to show user-friendly limit messages.
- Auth0 remains the identity provider; scope model (`access:api`) is unchanged.
- OpenRouter remains the model provider; Tavily remains the web search provider for both chat and research agents.
- Single-instance deployment on Railway is acceptable for v1; multi-replica SSE fan-out via external pub/sub is out of scope unless needed to meet SC-005/SC-006 under load testing.
- Per-user concurrency is capped at 10 active agent runs across all sessions; no per-minute rate limiting is in scope for v1.
- Research agent structured output replaces delimiter-based parsing; the user-visible behavior (chat panel, article panel, action chips) stays the same.
- Chat session history adopts agent session storage as the authoritative source; existing domain message tables become a read projection for API/UI restore and owner-scoped queries. A one-time or background sync MAY run at deploy to align pre-existing rows.
- LangWatch tracing remains optional; structured application logs are always emitted.
- No new user-facing features (new pages, WhatsApp channel, vector RAG) are in scope — this is architecture and reliability only.
- Performance targets assume configured API keys are valid and external providers respond within normal latency envelopes.
