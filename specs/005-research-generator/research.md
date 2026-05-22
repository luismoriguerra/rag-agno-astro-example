# Research: Research Generator

## Decision: Separate Research Data Model

**Decision**: Create dedicated PostgreSQL tables for research sessions, research messages, articles, and article versions — fully independent from existing chat tables.

**Rationale**: The spec explicitly requires separate storage (FR-018). Research sessions have a different lifecycle (article versioning, status, display title from H1) than chat sessions (active/inactive/deleted). Sharing tables would require schema compromises and complicate queries for both features.

**Alternatives considered**:
- Shared chat_sessions + chat_messages tables with a `type` discriminator: simpler schema but muddies chat and research lifecycles, complicates pagination for home page vs `/chat`.
- Hybrid with shared messages but separate articles: partial reuse, but creates confusing ownership split.

## Decision: Research Agent as Separate Agno Agent Instance

**Decision**: Create a `build_research_agent()` factory in `agents/research_agent.py` using `OpenRouter(id=settings.research_agent_model)` (default `deepseek/deepseek-v4-pro:nitro`) with DuckDuckGoTools, research-specific system prompt, and `show_tool_calls=True`.

**Rationale**: The research agent has fundamentally different behavior from the chat agent: different model, different system prompt (article generation with plan/TL;DR/sources structure), full chain-of-thought visibility, and multi-search per article. A separate factory keeps both agents independently configurable and testable.

**Alternatives considered**:
- Shared agent factory with mode parameter: adds conditional complexity to a simple factory.
- Single model for both: research requires long-context DeepSeek; chat uses Gemini Flash.

## Decision: SSE Streaming for Research Chat (Same Pattern as Chat)

**Decision**: Reuse the SSE event pattern (`event: thinking`, `event: token`, `event: source`, `event: done`, `event: error`) from the chat feature for research chat streaming. Add a new event type `event: article` to deliver the complete article markdown when the agent finishes.

**Rationale**: SSE is already proven in the codebase. The `article` event is the key addition — it delivers the full markdown body after each agent run completes, keeping the right panel's "update on completion" behavior simple. No partial article streaming needed (spec clarification).

**Alternatives considered**:
- WebSockets: unnecessary for unidirectional article delivery.
- Separate REST poll for article: adds latency and complexity vs piggybacking on the SSE stream.

## Decision: Article Content Extraction via Agent Structured Output

**Decision**: The research agent returns a structured response with two parts: (1) the chat messages (reasoning, plan, progress) streamed to the left panel, and (2) a final `article_markdown` field containing the complete article. The backend extracts the article from the agent's final response, creates an ArticleVersion record, and emits the `article` SSE event.

**Rationale**: Structured output lets the backend reliably separate "chat content" from "article content" without parsing agent prose. The agent's system prompt instructs it to output the article in a clearly delimited format.

**Alternatives considered**:
- Regex parsing of agent output: fragile and error-prone with markdown content.
- Two separate agent calls (plan + write): doubles latency and doesn't leverage context continuity.

## Decision: Home Page Replaces Index Redirect

**Decision**: Update `apps/frontend/src/pages/index.astro` from its current redirect-to-chat behavior to serve the Research Hub: compose area (textarea + submit) above a paginated research session list. The `/chat` route remains accessible independently.

**Rationale**: The spec removed `/research/new` and made the home page the research entry point (FR-001, FR-014). The current `index.astro` is a one-line redirect — replacing it has zero migration cost.

**Alternatives considered**:
- Keep home as redirect, add `/research` route: contradicts spec decision to make home the research hub.
- Dashboard page with both chat and research: overengineered for v1.

## Decision: Paginated API for Research Sessions

**Decision**: Create `GET /api/research/sessions?page=1&page_size=10&sort=updated_at:desc` returning `{ sessions: [...], total: N, page: N, page_size: N }`. The backend handles pagination with SQL `LIMIT/OFFSET` on the owner-filtered query.

**Rationale**: Server-side pagination keeps the frontend simple (no client-side sorting of all data), and `LIMIT/OFFSET` is sufficient for the expected scale (SC-008: 500 sessions per user in <1s).

**Alternatives considered**:
- Cursor-based pagination: better for infinite scroll, but the spec uses page numbers + page size dropdown.
- Client-side pagination: requires fetching all sessions up front, doesn't scale.

## Decision: Markdown Rendering with react-markdown + rehype

**Decision**: Use `react-markdown` with `rehype-highlight` (syntax highlighting), `remark-gfm` (tables, strikethrough), and `rehype-raw` (HTML passthrough for ASCII art) in the `ArticlePreview.tsx` component.

**Rationale**: The frontend already uses React islands for interactive components (ChatBox.tsx). `react-markdown` is the standard React markdown renderer, and rehype/remark plugins cover all FR-013 requirements (code blocks, tables, blockquotes, etc.).

**Alternatives considered**:
- `marked` + manual DOM: works but less composable in React components.
- Custom parser: unnecessary when a battle-tested library exists.

## Decision: Article Download as Client-Side Blob

**Decision**: The `.md` download button creates a `Blob` from the article markdown content already in the frontend state, generates a download link with a filename derived from the display title, and triggers a browser download. No backend endpoint needed.

**Rationale**: The article content is already loaded in the right panel. Client-side download avoids an unnecessary API roundtrip and works offline after initial load.

**Alternatives considered**:
- Backend `/api/research/articles/{id}/download` endpoint: works but adds unnecessary server load for data already on the client.

## Decision: Display Title Update via Backend Trigger

**Decision**: After the research agent generates the first article version, the backend extracts the first H1 heading from the markdown, updates the `ResearchSession.title` field, and includes the updated title in the `article` SSE event payload.

**Rationale**: Title derivation belongs in the backend because the agent output is processed there. The frontend receives the updated title and can update the UI without a separate API call.

**Alternatives considered**:
- Frontend parses H1 from markdown: duplicates logic and requires a separate session update call.
- Agent generates title separately: adds prompt complexity for a simple extraction.
