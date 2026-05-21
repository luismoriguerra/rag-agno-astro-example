# Feature Specification: WhatsApp Agent Interface

**Feature Branch**: `004-whatsapp-agent-interface`  
**Created**: 2026-05-19  
**Status**: Draft  
**Input**: User description: "Allow to use WhatsApp to consume backend agent API, following the Agno WhatsApp interface guide"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Send a Question via WhatsApp (Priority: P1)

A user sends a text message to the WhatsApp bot number. The system receives the message, routes it to the existing search agent, and replies with a text answer directly in the WhatsApp conversation thread.

**Why this priority**: This is the core value proposition — exposing the existing agent capability through a new conversational channel. Without this, no other WhatsApp feature is meaningful.

**Independent Test**: Can be fully tested by sending a plain text question (e.g., "What is the capital of France?") to the WhatsApp bot and verifying a relevant text answer is returned in the same conversation.

**Acceptance Scenarios**:

1. **Given** the WhatsApp bot is running and registered with Meta, **When** a user sends a text message, **Then** the agent processes the message and sends a text reply within 60 seconds.
2. **Given** a user sends a question that requires web search, **When** the agent searches and finds results, **Then** the reply includes cited sources as inline URLs.
3. **Given** the agent encounters an error processing the message, **When** the error occurs, **Then** the user receives a friendly error message in WhatsApp (not a silent failure).

---

### User Story 2 - Conversation History within a Session (Priority: P2)

A user can send multiple messages in sequence. The bot remembers the context of previous messages within the same session, allowing follow-up questions that reference earlier parts of the conversation.

**Why this priority**: Stateless Q&A is useful but limited. Contextual conversation makes the WhatsApp bot significantly more valuable for multi-step research or complex queries.

**Independent Test**: Can be tested by sending "Who is the president of France?" followed by "What is his age?" and verifying the second answer correctly resolves "his" to the president mentioned in the first reply.

**Acceptance Scenarios**:

1. **Given** a user has an active session with prior messages, **When** they send a follow-up question referencing earlier context, **Then** the bot responds with context-aware answers.
2. **Given** a user sends `/new`, **When** the session resets, **Then** subsequent messages start with a fresh context and the prior session is preserved.

---

### User Story 3 - Webhook Security and Verification (Priority: P2)

Meta's webhook verification and message signature validation are properly configured so that only legitimate messages from Meta's infrastructure are processed, and the webhook endpoint responds correctly to Meta's verification challenge.

**Why this priority**: Without proper webhook security, the bot cannot be activated in Meta's dashboard and would be vulnerable to spoofed messages. This is a hard requirement from Meta/WhatsApp.

**Independent Test**: Can be tested by triggering Meta's webhook verification flow and confirming the endpoint returns the correct challenge response, and by sending a request with an invalid signature and verifying it is rejected.

**Acceptance Scenarios**:

1. **Given** Meta sends a webhook verification GET request with a verify token, **When** the token matches the configured value, **Then** the endpoint returns the challenge string with HTTP 200.
2. **Given** an incoming webhook POST has an `X-Hub-Signature-256` header, **When** the signature does not match the computed HMAC-SHA256, **Then** the request is rejected with HTTP 403.
3. **Given** `WHATSAPP_APP_SECRET` is not set, **When** a webhook POST arrives, **Then** the server returns HTTP 500 (unless signature validation is explicitly skipped for local development).

---

### User Story 4 - Start a New Session (Priority: P3)

A user can send the `/new` command in WhatsApp to start a fresh conversation session. The old session is preserved but the bot begins a new context.

**Why this priority**: Useful for users who want to switch topics without prior context bleeding into new queries, but not essential for initial launch.

**Independent Test**: Can be tested by sending a message, then sending `/new`, then sending a new question and verifying the bot does not reference prior conversation content.

**Acceptance Scenarios**:

1. **Given** a user has an active session, **When** they send `/new`, **Then** a new session is created and subsequent messages use fresh context.
2. **Given** a user sends `/new`, **When** the old session existed, **Then** the old session data remains in the database and is not deleted.

---

### User Story 5 - Manage WhatsApp Settings via Profile Page (Priority: P2)

A logged-in user visits a Profile page in the frontend application. The page displays the user's name and email (from Auth0) at the top, followed by a WhatsApp settings section. The WhatsApp section includes a toggle to enable or disable the WhatsApp chat interface and a list where the user can add or remove phone numbers that are allowed to interact with the bot.

**Why this priority**: Controls who can use the bot and prevents unexpected LLM costs from unauthorized users. Also provides a self-service way to manage the WhatsApp feature without redeploying or editing environment variables.

**Independent Test**: Can be tested by logging into the frontend, navigating to the Profile page (via sidebar once US6 is complete, or direct URL `/profile` during US5-only development), toggling "Enable WhatsApp chat" on, adding a phone number, and then verifying that only that number can interact with the WhatsApp bot. Sidebar visibility on Profile is validated under US6 / FR-019 (requires AppLayout wrap).

**Acceptance Scenarios**:

1. **Given** a logged-in user visits the Profile page, **When** they toggle "Enable WhatsApp chat" off, **Then** the WhatsApp webhook stops processing incoming messages and returns no response.
2. **Given** a logged-in user has WhatsApp chat enabled, **When** they add a phone number to the allowlist, **Then** only messages from allowlisted numbers receive bot responses.
3. **Given** a logged-in user removes a phone number from the allowlist, **When** that number sends a message to the bot, **Then** the bot silently ignores the message (no response, no outbound API call).
4. **Given** WhatsApp chat is enabled with an empty allowlist, **When** any user sends a message, **Then** all messages are accepted (open access when no numbers are explicitly restricted).

---

### User Story 6 - Sidebar Navigation and Home Page (Priority: P2)

The frontend application includes a persistent sidebar with links to Home (`/`), Chat (`/chat`), and Profile (`/profile`). The home page at `/` serves as a basic landing page instead of the current redirect to `/chat`.

**Why this priority**: A sidebar provides consistent navigation across all pages and makes the Profile page discoverable. The home page gives the application a proper entry point.

**Independent Test**: Can be tested by navigating to `/` and verifying a home page is displayed with sidebar links to Chat and Profile. Clicking each link navigates to the correct page.

**Acceptance Scenarios**:

1. **Given** a logged-in user visits any page, **When** the page loads, **Then** a persistent sidebar is visible with links to Home, Chat, and Profile.
2. **Given** a logged-in user visits `/`, **When** the home page loads, **Then** a basic landing page is displayed (not a redirect to `/chat`).
3. **Given** a logged-in user clicks "Chat" in the sidebar, **When** the navigation occurs, **Then** they are taken to the `/chat` page with the existing chat UI.
4. **Given** a logged-in user clicks "Profile" in the sidebar, **When** the navigation occurs, **Then** they are taken to the `/profile` page.

---

### Edge Cases

- When a user sends an empty message or only whitespace, the system silently ignores it (no agent call, no response).
- When messages exceed the agent's context window limit, the oldest messages beyond the 10-exchange window are dropped from context automatically.
- When the agent takes longer than the configured timeout (default 60 seconds), the agent call is cancelled and the user receives the timeout error message defined in FR-007.
- When a user sends multiple messages while a previous request is still processing, the system queues incoming messages and processes them sequentially per user. The user receives a "processing..." acknowledgment while waiting for the queued message to be handled.
- When Meta's servers are temporarily unreachable for sending replies, the system retries up to 3 times with exponential backoff (2s, 4s, 8s). If all retries fail, the error is logged and the response is discarded.
- When the WhatsApp access token expires or is revoked, outbound message delivery fails and the error is logged. The system continues to receive webhooks but cannot reply until the token is refreshed.
- When a user adds an invalid phone number format to the allowlist, the Profile page validates input and rejects numbers not in E.164 international format (e.g., +1234567890).
- When WhatsApp chat is toggled off while a message is currently being processed, the in-flight message completes and the response is sent. Subsequent messages are ignored.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST expose a webhook endpoint at `/whatsapp/webhook` that handles Meta's webhook verification challenge (GET) and incoming message delivery (POST). This path MUST be excluded from the existing JWT middleware (using HMAC-SHA256 signature validation instead). The full callback URL registered in Meta's dashboard is `{BASE_URL}/whatsapp/webhook`.
- **FR-002**: System MUST validate incoming webhook signatures using HMAC-SHA256 when `WHATSAPP_APP_SECRET` is configured.
- **FR-003**: System MUST receive text messages from WhatsApp users and route them to the existing search agent for processing.
- **FR-004**: System MUST send the agent's response back to the user as a WhatsApp text message.
- **FR-005**: System MUST maintain per-user conversation sessions scoped by phone number, enabling context-aware multi-turn conversations with up to 10 prior agent runs included in context (`num_history_runs=10`; one run = one user message processed and one agent response generated).
- **FR-006**: System MUST support the `/new` command to start a fresh session while preserving the prior session data.
- **FR-007**: System MUST handle agent errors and timeouts gracefully by sending a plain-text WhatsApp message instead of failing silently. Messages MUST NOT include stack traces, internal error codes, or raw exception text. Use these exact default messages unless overridden in configuration: (a) agent/processing failure — `"Sorry, I couldn't process your message. Please try again."`; (b) timeout (default 60 seconds) — `"Sorry, this is taking too long. Please try again or send /new to start fresh."`. Each message MUST be under 500 characters.
- **FR-008**: System MUST log all incoming messages and outgoing responses for observability and debugging.
- **FR-009**: System MUST support configurable environment variables for WhatsApp credentials (`WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_VERIFY_TOKEN`, `WHATSAPP_APP_SECRET`) and an optional development-only variable `WHATSAPP_SKIP_SIGNATURE_VALIDATION` (defaults to false; when true, bypasses HMAC signature checks for local development with ngrok).
- **FR-010**: System MUST coexist with the existing REST/SSE chat API without disrupting current functionality. WhatsApp routes MUST only be mounted when required credentials (`WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_VERIFY_TOKEN`) are present. If missing, the app MUST start normally without WhatsApp functionality and log a startup warning. The existing REST/SSE API is unaffected.
- **FR-011**: System MUST queue concurrent messages from the same user and process them sequentially, sending a "processing..." acknowledgment for queued messages.
- **FR-012**: System MUST persist WhatsApp sessions in the existing PostgreSQL database so that conversation context survives container restarts.
- **FR-013**: System MUST retry failed outbound message delivery up to 3 times with exponential backoff (2s, 4s, 8s) before logging the failure and discarding the response.
- **FR-014**: The frontend MUST provide a Profile page that displays the user's name and email (from Auth0) at the top, with a WhatsApp settings section below containing a toggle to enable or disable WhatsApp chat processing.
- **FR-015**: The Profile page MUST allow the user to add and remove phone numbers from a WhatsApp allowlist.
- **FR-016**: When WhatsApp chat is disabled via the Profile toggle, the system MUST stop processing incoming WhatsApp messages. The default state for a new deployment is disabled (WhatsApp settings are auto-created with enabled=false and an empty allowlist on first read).
- **FR-017**: When the allowlist is non-empty, the system MUST only respond to messages from allowlisted phone numbers and silently ignore messages from all other numbers (no response sent). When the allowlist is empty, all messages are accepted (open access).
- **FR-018**: The backend MUST expose API endpoints for reading and updating WhatsApp settings (enabled toggle and phone allowlist) as a global singleton, protected by Auth0 JWT authentication. Any authenticated user with `access:api` scope can read and update settings.
- **FR-019**: The frontend MUST include a persistent sidebar navigation with links to Home (`/`), Chat (`/chat`), and Profile (`/profile`), visible on all authenticated pages.
- **FR-020**: The frontend MUST provide a basic home page at `/` instead of the current redirect to `/chat`.

### Constitution Requirements *(mandatory when applicable)*

- **RAG Grounding**: N/A — the WhatsApp interface reuses the existing search agent which already handles web search and source citation.
- **Agent Behavior**: The existing Agno search agent is reused as-is. The WhatsApp interface is mounted into the existing FastAPI application as a sub-application or router (single deployment, single port), delegating message processing to the same agent logic that powers the REST API. No new tools, permissions, or handoff behaviors are introduced. No separate service or AgentOS process is needed.
- **Auth0 Authorization**: WhatsApp users are identified by phone number (not Auth0 JWT). The WhatsApp interface operates outside the Auth0 authentication boundary. The webhook path `/whatsapp/webhook` MUST be added to the JWT middleware's excluded paths list (alongside `/health`) so that Meta's webhook requests are not rejected with 401. The webhook authenticates via its own HMAC-SHA256 signature validation instead. Phone-number-based sessions are isolated from JWT-authenticated REST sessions. The Profile page settings endpoints (enable/disable WhatsApp, manage allowlist) are protected by Auth0 JWT and require the `access:api` scope.
- **Data and Vector Search**: WhatsApp sessions are stored in the existing PostgreSQL database using Agno's built-in PostgreSQL storage adapter. Two new tables are added: `whatsapp_settings` (global singleton for enabled toggle) and `allowed_phone_numbers` (normalized allowlist with foreign key to settings). No pgvector changes are needed. WhatsApp sessions are kept separate from the existing `ChatSession` model to maintain channel isolation. A new Alembic migration is required for the settings and allowlist tables.
- **Deployment and Observability**: New environment variables for WhatsApp credentials must be added to the Railway deployment. A new Alembic migration must run on deploy for the `whatsapp_settings` and `allowed_phone_numbers` tables (existing `start.sh` auto-runs migrations). A publicly accessible HTTPS URL is required for the webhook endpoint. Health check at `/health` remains unaffected. WhatsApp message logs should be captured by the existing structured logging.

### Key Entities *(include if feature involves data)*

- **WhatsApp Session**: A conversation context scoped to a single WhatsApp phone number. Persisted in the existing PostgreSQL database via Agno's built-in PostgreSQL storage adapter. Each phone number maps to one active session at a time. Sessions survive container restarts.
- **WhatsApp Message**: An inbound or outbound message in a WhatsApp conversation. Inbound messages are text from the user; outbound messages are agent responses routed through the Meta WhatsApp Business API.
- **Webhook Event**: An HTTP request from Meta's infrastructure containing message payloads, delivery receipts, or verification challenges.
- **WhatsApp Settings**: A global singleton configuration record storing whether WhatsApp chat is enabled. One record for the entire application — not per-user. Managed by any authenticated user via the Profile page and persisted in PostgreSQL. Auto-created with safe defaults (enabled=false) on first read if it does not exist — no migration seed or manual setup required.
- **Allowed Phone Number**: A phone number in E.164 format that is authorized to interact with the WhatsApp bot. Stored in a separate normalized table with a foreign key to the WhatsApp Settings record. Each phone number is unique within the allowlist.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users receive a response to their WhatsApp message within 60 seconds of sending it.
- **SC-002**: The bot correctly answers at least 90% of factual questions that the existing REST-based agent answers correctly (parity with existing channel). **Verification method**: use the fixed 10-question parity set in `quickstart.md` §7; send each prompt to both REST chat and WhatsApp (with WhatsApp enabled); for each question, mark pass if the WhatsApp reply contains the same core factual claim as the REST reply (manual review); pass SC-002 when ≥9/10 questions pass.
- **SC-003**: Follow-up questions that depend on prior conversation context are answered correctly within the same session.
- **SC-004**: The `/new` command successfully resets context, verified by the bot not referencing prior conversation in subsequent answers.
- **SC-005**: Invalid webhook signatures are rejected 100% of the time when `WHATSAPP_APP_SECRET` is configured.
- **SC-006**: The existing REST/SSE chat API continues to function without regressions after the WhatsApp interface is added. **Verification scope**: `GET /health` returns 200; authenticated chat session create/list/message flows work; SSE streaming delivers at least one complete assistant reply; `make test` passes for existing backend and frontend chat tests.

## Clarifications

### Session 2026-05-19

- Q: How should the system handle simultaneous messages from the same user while a previous request is still processing? → A: Queue incoming messages and process sequentially per user, with a "processing..." acknowledgment.
- Q: Which storage backend should WhatsApp sessions use? → A: PostgreSQL (existing database) via Agno's built-in PostgreSQL storage adapter, for durability across container restarts.
- Q: Should phone numbers be encrypted at rest in v1? → A: Defer. Store as-is for v1; enable Agno's `enable_encryption` as a follow-up (single flag toggle, no data migration).
- Q: What should happen when Meta's API is unreachable for sending replies? → A: Simple retry — up to 3 attempts with exponential backoff (2s, 4s, 8s). Log and discard on final failure.
- Q: Should access to the WhatsApp bot be restricted? → A: Open access by default, but add a Profile page in the frontend with a "Enable WhatsApp chat" toggle and a phone number allowlist. When the allowlist is non-empty, only listed numbers can interact. When empty, all users are accepted.
- Q: Is WhatsApp Settings a global config or per-user? → A: Global singleton. One settings record for the entire app. Any authenticated user with `access:api` scope can manage it.
- Q: How should the bot respond to messages from non-allowlisted numbers? → A: Silent ignore — no response, no outbound API call, no information leakage.
- Q: How many prior exchanges should be included in conversation context? → A: 10 prior exchanges.
- Q: What should the Profile page scope include? → A: User info (name, email from Auth0) at the top, plus WhatsApp settings section below.
- Q: How should the user navigate to the Profile page? → A: Sidebar navigation with links to Home, Chat, and Profile. Also add a basic home page at `/` instead of the current redirect to `/chat`.
- Q: How is the WhatsApp Settings singleton record initialized? → A: Lazy creation — auto-created with safe defaults (enabled=false, empty allowlist) on first read. No migration seed or manual setup required.
- Q: How should the phone number allowlist be stored? → A: Separate normalized table (`allowed_phone_numbers`) with a foreign key to the settings record. Each phone number is unique within the allowlist.
- Q: How does the WhatsApp interface coexist with the existing backend? → A: Mount into the existing FastAPI app as a sub-application or router. Single deployment, single port. No separate AgentOS process or second service.
- Q: How is the webhook endpoint authenticated given the existing JWT middleware? → A: Exclude the webhook path from JWT middleware's excluded paths list (like `/health`). The webhook uses its own HMAC-SHA256 signature validation for security.
- Q: Should `WHATSAPP_SKIP_SIGNATURE_VALIDATION` be documented? → A: Yes, add to FR-009 as an optional dev-only variable (defaults to false). Bypasses HMAC checks for local ngrok development.
- Q: What happens when WhatsApp env vars are not set? → A: Opt-in — WhatsApp routes only mount when required credentials are present. App starts normally without WhatsApp, logging a warning. Existing API unaffected.
- Q: What is the webhook URL path? → A: `/whatsapp/webhook` (Agno default prefix). Full callback URL for Meta dashboard: `{BASE_URL}/whatsapp/webhook`.

### Session 2026-05-20 (analysis remediation)

- Q: What counts as one "exchange" for the 10-message context window? → A: One agent run — one inbound user message processed and one agent response generated (`num_history_runs=10`).
- Q: What exact text should users see on agent errors and timeouts? → A: Fixed plain-text defaults in FR-007; no stack traces or internal codes; under 500 characters.
- Q: How is SC-002 (90% REST parity) measured? → A: Fixed 10-question set in `quickstart.md` §7; manual comparison of core factual claims; ≥9/10 passes.
- Q: When is US5 "complete" vs FR-019 sidebar on Profile? → A: US5 settings functionality is independently testable at `/profile`; FR-019 sidebar on Profile requires US6 AppLayout wrap (tasks T039–T040, T043).

## Assumptions

- The project already has an Agno-based search agent that can be reused without modification for WhatsApp message processing.
- A Meta Developer account and WhatsApp Business API access are available or will be set up outside this feature's scope.
- The deployment environment (Railway) supports exposing HTTPS endpoints accessible from Meta's webhook infrastructure.
- For local development, ngrok or a similar tunneling tool will be used to expose the local server to Meta's webhooks.
- Phone number encryption (Agno's `enable_encryption` feature) is desirable but not required for the initial release; it can be added as a follow-up.
- Only text messages are supported in the initial release. Media messages (images, video, audio, documents) are out of scope for v1.
- The WhatsApp interface uses Agno's built-in `Whatsapp` interface class, following the official Agno documentation pattern, rather than building a custom webhook handler from scratch.
- The WhatsApp bot will share the same Agno `Agent` configuration as the REST API but will use a separate session namespace within PostgreSQL to keep the two channels isolated.
