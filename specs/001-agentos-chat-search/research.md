# Research: AgentOS Chat Search

## Decision: Two-Service Monorepo Under `apps/`

**Decision**: Use `apps/backend` for the FastAPI/AgentOS service and `apps/frontend` for the
Astro web service, coordinated by a root `Makefile`.

**Rationale**: The spec requires separate Railway services for frontend and backend while keeping
deployment local-first. The existing repository already has an `apps/` directory, and separate
service roots keep Python and Node dependencies isolated.

**Alternatives considered**:
- Single Railway service: simpler deploy, but blurs frontend/backend logs, scaling, and service
  configuration.
- Three services with a worker: unnecessary for the first single-agent release.

## Decision: FastAPI Base App With AgentOS Mounted Routes

**Decision**: Build the backend as a FastAPI app that owns health, chat, session, stop, and delete
routes, then integrates AgentOS/Agno inside the service layer.

**Rationale**: FastAPI gives explicit typed contracts, dependency injection for mocked identity,
and direct control over streaming and stop semantics. AgentOS remains the agent runtime but does
not hide the app-specific API contract.

**Alternatives considered**:
- Pure AgentOS-generated routes: less custom code, but insufficient control for the required chat
  stream, session ownership, stop, and source contracts.
- Separate API gateway: unnecessary for two local-first services.

## Decision: Agno Agent With DuckDuckGoTools and PostgreSQL Session Context

**Decision**: Use one Agno agent with DuckDuckGoTools. Every run is given the current
Auth0-compatible identity's active chat session history, and the backend filters out deleted,
inactive, and other-identity sessions before invoking the agent.

**Rationale**: This matches the spec's single-agent scope, keeps tool permissions narrow, and uses
Agno's established pattern for history-aware agents. Filtering before invocation satisfies the
security boundary and avoids cross-user context leakage.

**Alternatives considered**:
- Multi-agent routing: more flexible but explicitly out of scope.
- Stateless agent calls: simpler, but violates the requirement that every run receives chat
  history context.

## Decision: Server-Sent Events for Streaming Chat Output

**Decision**: Stream chat responses from the backend to the Astro client using Server-Sent Events
with typed event names for `thinking`, `token`, `source`, `done`, and `error`.

**Rationale**: SSE is browser-native, works well for one-way answer streams, and maps cleanly to
safe thinking/progress events without exposing raw hidden reasoning. Stop is handled by a separate
cancel endpoint keyed by run ID.

**Alternatives considered**:
- WebSockets: useful for bidirectional collaboration, but heavier than needed for single response
  streams.
- Fetch streaming only: viable, but named SSE events make status/source/token handling clearer.
- Polling: simpler infrastructure but weaker UX and higher latency for streamed text.

## Decision: Mock Auth0-Compatible Identity First

**Decision**: Implement a backend identity dependency that returns a stable mocked Auth0-style
subject for local and first release usage, while keeping request ownership checks shaped for real
Auth0 token validation later.

**Rationale**: The feature must persist history as Auth0-owned, but the user explicitly deferred
Auth0 integration. A dependency boundary lets tests verify ownership and prevents anonymous
history shortcuts that would need rework.

**Alternatives considered**:
- Full Auth0 now: aligned with constitution, but out of current scope.
- Browser-only identity: easier but unsafe for cross-device and shared-browser ownership.

## Decision: PostgreSQL for Chat Persistence, pgvector Provisioned but Unused

**Decision**: Store user identities, sessions, messages, runs, and sources in PostgreSQL. Provision
a pgvector-capable Railway PostgreSQL service for stack alignment, but do not create embedding or
vector-search tables for this feature.

**Rationale**: Persistent history, deletion, ownership filtering, and deployable state require a
server-side database. The constitution calls for PostgreSQL/pgvector, but the spec explicitly
keeps vector search out of scope.

**Alternatives considered**:
- Local browser storage: conflicts with Auth0-owned persistence and server-side agent context.
- SQLite: acceptable locally, but diverges from Railway deployment and constitution defaults.
- Vector tables now: premature because DuckDuckGo public search is the only knowledge source.

## Decision: Astro `/chat` Page With a Client-Side Chat Component

**Decision**: Use an Astro route at `src/pages/chat.astro` and a hydrated client-side chat
component/service for session management, SSE streaming, stop, new chat, delete active session, and error
states.

**Rationale**: Astro is the required frontend, and a chat UI needs client-side interactivity.
Keeping the interactive surface localized preserves Astro's minimal-JavaScript model.

**Alternatives considered**:
- Fully static form posts: cannot support stop or token streaming well.
- SPA-only frontend: unnecessary for a single interactive page.

## Decision: Local Makefile Railway Workflow

**Decision**: Provide root Makefile targets for local backend/frontend runs, local checks, Railway
project/service setup, deploy, status, logs, smoke test, and teardown-safe diagnostics. Do not add
GitHub Actions for this release.

**Rationale**: The spec requires local-first deployment and no GHA. Make targets make the Agno PAL
Railway setup pattern repeatable while keeping commands visible and easy to run locally.

**Alternatives considered**:
- GitHub Actions: deferred by requirement.
- Ad hoc shell scripts only: works, but Makefile targets are easier to discover and compose.

## Decision: Minimum Railway CPU and Memory Settings

**Decision**: Railway setup commands must apply the minimum CPU and memory settings supported by
the active Railway environment for the frontend, backend, and database service where configurable.
Any service that rejects the minimum must be documented as an exception.

**Rationale**: This minimizes first-release cost and satisfies the spec's explicit resource
constraint while leaving room for Railway platform limitations.

**Alternatives considered**:
- Default Railway sizing: simpler but may exceed desired cost.
- Overprovisioning for latency: unnecessary until load data justifies it.
