<!--
Sync Impact Report
Version change: template -> 1.0.0
Modified principles:
- Placeholder principle 1 -> I. Grounded RAG and Agent Behavior
- Placeholder principle 2 -> II. Auth0-Centered Security Boundaries
- Placeholder principle 3 -> III. Typed API and UI Contracts
- Placeholder principle 4 -> IV. PostgreSQL and pgvector Integrity
- Placeholder principle 5 -> V. Railway-Ready Delivery and Observability
Added sections:
- Technology Standards
- Development Workflow
Removed sections:
- Placeholder section names and template examples
Templates requiring updates:
- Updated: .specify/templates/plan-template.md
- Updated: .specify/templates/spec-template.md
- Updated: .specify/templates/tasks-template.md
- Updated: .specify/templates/commands/*.md (no command templates present)
Follow-up TODOs:
- None
-->
# web0personal-vector Constitution

## Core Principles

### I. Grounded RAG and Agent Behavior
Every AI feature MUST be grounded in retrievable project or user-owned knowledge before it
answers with factual confidence. Retrieval behavior MUST define source selection, embedding
model assumptions, chunking strategy, ranking method, and fallback behavior when context is
insufficient. Agno/AgentOS agents MUST have explicit tool permissions, deterministic handoff
boundaries, and observable execution traces for prompts, retrieval decisions, tool calls, and
final responses. The rationale is that a RAG product is only trustworthy when users can
understand which knowledge shaped an answer and when the system declined unsupported claims.

### II. Auth0-Centered Security Boundaries
Authentication and authorization MUST be enforced through Auth0-backed identity, roles,
permissions, and token validation at the FastAPI boundary before protected data or agent tools
are reached. Backend code MUST treat client-provided identity, role, tenant, and ownership
claims as untrusted unless verified from validated tokens or server-side records. Secrets MUST
be stored in deployment environment variables or managed secret stores, never in source code.
The rationale is that the app combines private knowledge, vector search, and agentic actions,
so identity and authorization failures have direct data exposure risk.

### III. Typed API and UI Contracts
FastAPI MUST be the backend HTTP API boundary, and Astro MUST be the frontend application
boundary. Shared request, response, and error contracts MUST be explicit, validated, and kept
compatible across backend and frontend changes. Backend endpoints MUST expose predictable
status codes and structured errors; frontend code MUST handle loading, empty, unauthorized,
and failure states for user-facing flows. The rationale is that typed, documented contracts
keep the RAG, auth, and UI layers independently testable and deployable.

### IV. PostgreSQL and pgvector Integrity
PostgreSQL is the system of record and pgvector is the vector similarity layer. Schema changes
MUST use migrations, define ownership and retention expectations for user data, and include
indexes appropriate to query and similarity-search access patterns. Embeddings MUST be
versioned by model and generation strategy so re-indexing and quality comparisons are possible.
Queries that retrieve private content MUST include authorization-aware filters before ranking
or returning records. The rationale is that vector search quality and data security both depend
on disciplined relational modeling, migration safety, and filtered retrieval.

### V. Railway-Ready Delivery and Observability
Each deployable backend, frontend, worker, and database-dependent component MUST be runnable
with documented local commands and deployable to Railway using environment-specific
configuration. Production-facing paths MUST emit structured logs for requests, auth failures,
agent runs, retrieval quality signals, database errors, and deployment health checks. Changes
MUST include tests or a documented manual verification plan proportional to their risk. The
rationale is that Railway deployments are repeatable only when failures in AI, auth, or data
paths are diagnosable without guessing.

## Technology Standards

The default architecture is a RAG web application with a FastAPI backend, Astro frontend,
Agno/AgentOS runtime for agent orchestration, Auth0 for authentication and authorization,
PostgreSQL with pgvector for persistence and vector search, and Railway for deployment.
Alternative frameworks or hosted services require an explicit plan-time justification that
explains why the default stack cannot satisfy the feature.

Backend work MUST prefer FastAPI dependency injection, Pydantic validation, explicit service
boundaries, and migration-backed database access. Frontend work MUST prefer Astro pages and
components with minimal client-side JavaScript unless interactivity requires an island. Agent
work MUST isolate prompts, tools, retrieval, and model configuration so each can be tested and
reviewed separately. Database work MUST avoid ad hoc schema drift and MUST account for
pgvector index choice, recall, latency, and access filtering when similarity search is involved.

## Development Workflow

Specs MUST describe user value, security expectations, data ownership, RAG grounding needs,
and measurable success criteria before implementation planning. Plans MUST record constitution
checks for RAG quality, Auth0 authorization, API contracts, PostgreSQL/pgvector design,
observability, and Railway deployment impact before tasks are generated.

Tasks MUST be organized into independently deliverable user stories with foundational work
blocked before story implementation. Backend, auth, database, RAG, and deployment changes
MUST include automated tests where practical; when automation is not practical, the task list
MUST include a manual verification step with exact commands or user flows. Pull requests MUST
call out any constitution deviations, migration risks, secret/configuration changes, and
deployment impacts.

## Governance

This constitution supersedes conflicting repository guidance for feature specifications,
implementation plans, task generation, and code review. Amendments MUST be made by updating
this file, documenting the Sync Impact Report, and propagating any affected guidance to Spec Kit
templates or runtime docs in the same change.

Versioning follows semantic versioning. MAJOR changes remove or redefine principles in a way
that invalidates prior plans, MINOR changes add principles or materially expand governance,
and PATCH changes clarify wording without changing obligations. Compliance is reviewed during
planning and again before delivery; unresolved violations MUST be documented in the plan's
complexity or risk section with a rationale and mitigation.

**Version**: 1.0.0 | **Ratified**: 2026-05-18 | **Last Amended**: 2026-05-18
