# Feature Specification: LangWatch Backend Observability

**Feature Branch**: `002-langwatch-backend`  
**Created**: 2026-05-18  
**Status**: Draft  
**Input**: User description: "Add langwatch to apps/backend follow this https://docs.agno.com/observability/langwatch"

## Clarifications

### Session 2026-05-18

- Q: For LangWatch traces, how much chat content should be exported? → A: Full content in all environments (prompts, responses, and search snippets).
- Q: Should Railway production deployment require a configured LangWatch API key? → A: Optional everywhere — tracing enabled only when configured; no deploy gate.
- Q: Which identifiers must every trace include? → A: run_id, session_id, and auth subject identifier.
- Q: How should traces from different environments be organized in LangWatch? → A: Single LangWatch project with an environment tag on every trace (local, staging, production).
- Q: When LangWatch is enabled, what should happen to Agno built-in telemetry? → A: Keep both — agno_telemetry unchanged; LangWatch is additive.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Trace Agent Runs in LangWatch (Priority: P1)

A maintainer runs the chat backend with LangWatch configured and submits chat questions through
the existing agent flow. Each agent run (model calls, tool usage such as web search, and
completion) appears as a trace in the LangWatch dashboard so the maintainer can inspect latency,
errors, and execution steps without reading raw server logs.

**Why this priority**: Automatic tracing is the core value of the integration and the minimum
useful deliverable.

**Independent Test**: Configure a valid LangWatch API key, start the backend, submit one chat
message that triggers an agent run, and confirm a corresponding trace appears in LangWatch
within 60 seconds of run completion (SC-001).

**Acceptance Scenarios**:

1. **Given** the backend is started with a valid LangWatch API key configured, **When** a chat
   message triggers an agent run, **Then** LangWatch receives a trace that reflects that run.
2. **Given** a completed agent run trace in LangWatch, **When** the maintainer opens it, **Then**
   they can see enough structure to distinguish model activity from tool activity (e.g., search).
3. **Given** an agent run that fails or times out, **When** the run ends, **Then** the trace
   reflects failure or incomplete status so the maintainer can diagnose the issue.

---

### User Story 2 - Operate Without LangWatch in Development (Priority: P2)

A developer runs the backend locally without a LangWatch account or API key. The chat backend
continues to start and serve requests normally; observability export is simply inactive until
credentials are provided.

**Why this priority**: Local development should not be blocked by a third-party observability
account, while production and staging can opt in explicitly.

**Independent Test**: Start the backend with no LangWatch API key, submit a chat message, and
verify the chat flow completes with no startup failure and no requirement to configure LangWatch.

**Acceptance Scenarios**:

1. **Given** no LangWatch API key is configured, **When** the backend starts, **Then** it starts
   successfully and chat requests still work.
2. **Given** no LangWatch API key is configured, **When** agent runs execute, **Then** no traces
   are sent to LangWatch and no error is shown to end users on the chat page.
3. **Given** a LangWatch API key is added later, **When** the backend is restarted, **Then**
   subsequent agent runs begin appearing in LangWatch without code changes beyond configuration.

---

### User Story 3 - Deploy Observability to Railway (Priority: P3)

A maintainer deploys the backend to Railway with LangWatch credentials set in the deployment
environment. Staging or production agent activity is visible in LangWatch for the deployed
environment, and deployment documentation lists the new configuration requirement.

**Why this priority**: Hosted environments are where tracing pays off for incidents and quality
monitoring; this completes the operational story.

**Independent Test**: Deploy the backend with `LANGWATCH_API_KEY` (or equivalent documented
variable) set on Railway, run the smoke test or a single chat request, and confirm a trace in
LangWatch with `environment` set to `staging` or `production` (not `local`).

**Acceptance Scenarios**:

1. **Given** Railway deployment variables include a valid LangWatch API key, **When** the
   backend service is healthy and a chat agent run occurs, **Then** traces appear in LangWatch
   from that deployment.
2. **Given** a maintainer follows updated deployment documentation, **When** they configure
   optional LangWatch variables before deploy (when tracing is desired), **Then** they can verify
   LangWatch connectivity as part of post-deploy checks.
3. **Given** the LangWatch API key is missing on Railway, **When** the backend starts, **Then**
   the service still starts and chat remains available (same graceful behavior as local).

---

### Edge Cases

- What happens when the LangWatch API key is invalid or revoked? The backend must remain
  available for chat; trace export failures must not break user-facing responses. Maintainers
  should see a clear signal in logs that export failed.
- What happens when LangWatch is unreachable (network outage)? Agent runs complete for users;
  trace data may be dropped or retried according to SDK behavior without blocking chat.
- What happens when multiple concurrent agent runs execute? Each run produces a separate trace
  with distinct `run_id`, `session_id`, and auth subject metadata.
- What sensitive data must not appear in traces? User prompts, agent responses, and search
  snippets ARE included in traces in all environments (local and deployed) to maximize
  debugging value. Secrets (API keys, tokens, Auth0 credentials) must never be logged or
  exported via trace attributes. LangWatch access is limited to trusted maintainers only.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The chat backend MUST send execution traces for Agno-based agent runs to LangWatch
  when a valid LangWatch API key is configured, following the Agno LangWatch integration pattern
  (automatic instrumentation of agent activity).
- **FR-002**: Traces MUST capture agent execution sufficient for debugging, including model
  interactions and tool invocations (e.g., DuckDuckGo search) associated with a chat agent run,
  including full user prompts, agent responses, and search snippets in all environments.
- **FR-003**: LangWatch initialization MUST occur during backend startup (or equivalent
  application lifecycle hook) so all agent runs after startup are eligible for tracing.
- **FR-004**: The backend MUST read LangWatch credentials from environment configuration (not
  from source code), consistent with existing secret handling for the backend service.
- **FR-005**: When no LangWatch API key is configured, the backend MUST start and serve chat
  without requiring LangWatch.
- **FR-006**: LangWatch export failures MUST NOT cause chat API requests to fail or return
  errors to end users solely because tracing failed.
- **FR-007**: Deployment documentation for the backend MUST list LangWatch as an optional
  observability dependency and document the environment variable(s) and how to verify traces
  after deploy. LangWatch MUST NOT be a hard prerequisite for Railway deploy; missing API key
  must not block service startup or deployment completion.
- **FR-008**: Example environment templates for the backend MUST include a placeholder for the
  LangWatch API key without committing real secrets.
- **FR-009**: Every trace MUST include the chat system's `run_id`, `session_id`, and auth
  subject identifier (mocked or real Auth0-compatible subject) as searchable metadata so
  maintainers can correlate LangWatch traces to a specific agent run, session, and identity.
- **FR-011**: Every trace MUST include an `environment` tag with value `local`, `staging`, or
  `production`, using a single LangWatch project and API key across environments.
- **FR-012**: Enabling LangWatch MUST NOT change existing `agno_telemetry` behavior; both may run
  concurrently. LangWatch is additive observability, not a replacement for Agno telemetry.
- **FR-010**: The feature scope is limited to the chat backend service; the Astro frontend and
  Playwright E2E apps are out of scope unless a future feature requires client-side tracing.

### Constitution Requirements *(mandatory when applicable)*

- **RAG Grounding**: N/A — this feature does not change retrieval or answer grounding; traces
  may optionally reflect search tool usage for debugging only.
- **Agent Behavior**: Agent responsibilities and tool permissions are unchanged. This feature
  adds observable execution traces for existing Agno agent runs (prompts, tool calls, completions)
  to support debugging and quality review, aligned with constitution expectations for traceability.
- **Auth0 Authorization**: No change to identity or ownership rules at the API layer. Traces
  include full message content and may include session or run identifiers for correlation;
  LangWatch project access must be restricted to trusted maintainers. Traces must not weaken
  chat authorization or allow cross-identity session access through the product API.
- **Data and Vector Search**: N/A — no database or vector schema changes.
- **Deployment and Observability**: Railway backend deployment MUST document the LangWatch API
  key as an optional environment variable (never required for deploy). Post-deploy verification
  SHOULD include confirming at least one trace after a smoke-test chat message when the key is
  set. Existing Makefile deploy and log workflows remain the primary operational path; LangWatch
  complements structured logs.

### Key Entities *(include if feature involves data)*

- **Agent Run Trace**: A LangWatch record representing one backend agent execution, including
  timing, status, nested spans for model and tool activity, and required metadata: `run_id`,
  `session_id`, and auth subject identifier.
- **LangWatch Configuration**: Deployment-time settings (API key presence, `environment` tag
  value, optional endpoint override for self-hosted LangWatch) that control whether and where
  traces are sent. All environments share one LangWatch project; traces are filtered by
  `environment` metadata.
- **Observability Signal**: Combined structured logs (existing) plus LangWatch traces (new) used
  by maintainers to diagnose agent failures, latency, and tool behavior.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: When LangWatch is configured, 100% of successful chat agent runs initiated through
  the normal API produce a visible trace in LangWatch within 60 seconds of run completion.
- **SC-002**: When LangWatch is not configured, 100% of chat agent runs complete with the same
  user-visible success rate as before the feature (no regression attributable to tracing).
- **SC-003**: Maintainers can identify model versus tool activity in at least 90% of sampled
  traces for search-backed chat runs without access to raw server log files.
- **SC-007**: 100% of traces for chat agent runs include `run_id`, `session_id`, and auth
  subject identifier metadata that matches the corresponding chat system records.
- **SC-008**: 100% of traces include an `environment` tag with the correct value for the
  running deployment (`local`, `staging`, or `production`).
- **SC-004**: A maintainer with a LangWatch account can go from zero to first visible trace in
  under 15 minutes using documented setup steps (account key, env var, one chat message).
- **SC-005**: Invalid or missing LangWatch credentials never increase chat API error rates
  compared to the pre-integration baseline in manual testing.
- **SC-006**: Deployment documentation lists LangWatch configuration and verification steps so
  a new maintainer can enable tracing on Railway without undocumented steps.

## Assumptions

- Integration follows the official Agno LangWatch guide: LangWatch SDK setup with Agno
  OpenInference instrumentation so agent activity is captured automatically.
- LangWatch SaaS (langwatch.ai) is the default target; self-hosted LangWatch is supported only
  if the standard endpoint environment variable is documented, without custom infrastructure in
  this feature.
- Tracing is maintainer-facing; end users of `/chat` do not see LangWatch UI or trace IDs unless
  a future feature adds that explicitly.
- Full trace content (prompts, responses, search snippets) is exported in every environment;
  maintainers accept LangWatch as a trusted store for this data.
- LangWatch free-tier limits may apply; hitting limits affects trace ingestion only, not chat
  availability.
- LangWatch is optional in every environment including Railway production; no deployment gate
  depends on LangWatch being configured.
- A single LangWatch project and API key are used across environments; `environment` trace
  metadata distinguishes local, staging, and production traffic.
- Existing `agno_telemetry` and application logging remain unchanged when LangWatch is enabled;
  LangWatch is additive observability and does not disable or replace Agno telemetry.
- Only the `apps/backend` service is in scope per the user request.

## Dependencies

- Existing AgentOS chat backend with Agno search agent (feature `001-agentos-chat-search`).
- LangWatch account and API key for environments where tracing is desired.
- Agno LangWatch integration packages as documented at
  https://docs.agno.com/observability/langwatch.

## Out of Scope

- LangWatch prompt management, evaluation experiments, and scenario simulation tests (covered by
  separate LangWatch product workflows, not required for initial tracing).
- Frontend or browser-side LangWatch instrumentation.
- Changing chat UX, auth, persistence, or search behavior.
- Replacing existing structured application logs with LangWatch exclusively.
