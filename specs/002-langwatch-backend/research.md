# Research: LangWatch Backend Observability

## Decision: Agno OpenInference Instrumentation via LangWatch SDK

**Decision**: Follow the [Agno LangWatch guide](https://docs.agno.com/observability/langwatch):
install `langwatch` and `openinference-instrumentation-agno`, call
`langwatch.setup(instrumentors=[AgnoInstrumentor()])` once at backend startup when
`LANGWATCH_API_KEY` is set.

**Rationale**: Official Agno integration; automatic capture of model calls and tool spans without
manual OpenTelemetry configuration. Matches FR-001 and FR-002 (full prompt/response content via
OpenInference defaults).

**Alternatives considered**:
- Manual OpenTelemetry exporter setup: more boilerplate; LangWatch SDK handles OTEL wiring.
- Langfuse/LangSmith: out of scope; user requested LangWatch specifically.

## Decision: Conditional Startup Initialization

**Decision**: Add `configure_langwatch()` invoked from FastAPI `lifespan` after `configure_logging()`.
Skip setup entirely when `LANGWATCH_API_KEY` is empty or whitespace.

**Rationale**: Satisfies FR-005 (no key → no LangWatch requirement) and FR-006 (chat must not
depend on tracing). Invalid keys are handled by SDK/export path; chat errors are not raised to
users.

**Alternatives considered**:
- Always call `langwatch.setup()` and rely on SDK no-op without key: less explicit; harder to
  document and test the disabled path.
- Lazy init on first agent run: works but delays first-run trace completeness; startup init is
  clearer for maintainers.

## Decision: Trace Metadata via LangWatch Trace Context Around Agent Execution

**Decision**: Wrap `agent.run(...)` inside `agent_service._execute_run` with a LangWatch trace
context (e.g. `langwatch.trace(...)`) that sets required metadata:
`run_id`, `session_id`, `auth_subject`, and `environment`.

**Rationale**: AgnoInstrumentor captures model/tool spans automatically; an outer trace ties them
to chat-system identifiers (FR-009, SC-007). Auth subject is available in `_execute_run`; run and
session IDs are already logged via structured `trace_agent_run_start`.

**Alternatives considered**:
- Metadata only in structured logs: does not satisfy LangWatch search/filter requirements.
- Post-hoc trace patching: fragile and race-prone with async export.

## Decision: Environment Tag from `APP_ENVIRONMENT` Setting

**Decision**: Add `app_environment: str` to backend settings with allowed values `local`, `staging`,
`production` (default `local`). Map to LangWatch trace metadata key `environment`. Document
Railway values in deployment docs (`production` for prod service, `staging` if a staging service
exists).

**Rationale**: Clarification session chose single LangWatch project with environment tags (FR-011,
SC-008). Explicit env var avoids inferring environment from `DATABASE_URL` or hostnames.

**Alternatives considered**:
- Derive from `RAILWAY_ENVIRONMENT`: Railway-specific; weak for local-only runs.
- Hardcode `production` on Railway: breaks staging distinction.

## Decision: Preserve `AGNO_TELEMETRY` Independently

**Decision**: Do not modify existing `agno_telemetry` settings wiring when LangWatch is enabled
(FR-012). `build_search_agent()` continues to respect `Settings.agno_telemetry` as today.

**Rationale**: Clarification: LangWatch is additive; Agno product telemetry remains opt-in via its
own flag.

## Decision: Python Dependencies in `pyproject.toml`

**Decision**: Add runtime dependencies:

- `langwatch` (current stable)
- `openinference-instrumentation-agno`

Pin with lower bounds in `pyproject.toml`; lock via project install workflow (`make install`).

**Rationale**: Matches Agno documentation install line; keeps backend self-contained.

## Decision: No HTTP API or Database Changes

**Decision**: No new REST endpoints, OpenAPI changes, or migrations. Observability is internal to
the backend process.

**Rationale**: Spec limits scope to backend tracing; chat contracts unchanged (constitution III).

## Decision: Verification Strategy

**Decision**:

- Unit test: `configure_langwatch()` no-ops without API key; calls setup when key present (mock
  `langwatch.setup`).
- Manual verification: set `LANGWATCH_API_KEY`, submit chat message, confirm trace in LangWatch UI
  with metadata filters documented in quickstart.
- Optional: `langwatch trace search --limit 5` CLI after a run (documented in quickstart).

**Rationale**: Third-party export is hard to assert in CI without secrets; proportional testing per
constitution V.

## Environment Variables (Consolidated)

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `LANGWATCH_API_KEY` | No | empty | Enables LangWatch export when set |
| `LANGWATCH_ENDPOINT` | No | SaaS default | Self-hosted LangWatch base URL |
| `APP_ENVIRONMENT` | No | `local` | Trace tag: `local`, `staging`, or `production` |

Existing variables unchanged: `AGNO_TELEMETRY`, `OPENROUTER_API_KEY`, etc.
