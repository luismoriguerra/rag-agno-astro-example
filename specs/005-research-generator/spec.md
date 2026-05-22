# Feature Specification: Research Generator

**Feature Branch**: `005-research-generator`  
**Created**: 2026-05-20  
**Status**: Draft  
**Input**: User description: "Research Generator on the home page: a New idea button and textarea above a paginated recent research list (title and status). No separate /research/new page. Submitting an idea creates a session and redirects to /research/{session_id} (chat + article panels). Users refine via chat prompts (manual edit deferred). Backend research agent with versioning (draft/published label only). Rich markdown preview and .md download."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Start a New Research (Priority: P1)

On the home page, the user uses a "New idea" control and textarea (above the recent research list), enters a topic, and clicks "Research & draft." The system creates a new research session and redirects to the session workspace where the agent begins working.

**Why this priority**: This is the entry point for the entire feature. Without the ability to initiate a research session, no other functionality is usable.

**Independent Test**: Can be fully tested from the home page by entering a topic, clicking submit, and verifying redirect to `/research/{session_id}` with a new session in the database.

**Acceptance Scenarios**:

1. **Given** a logged-in user on the home page, **When** they enter "The state of WebAssembly in 2026" in the research textarea and click "Research & draft", **Then** a new research session is created and the user is redirected to `/research/{session_id}`.
2. **Given** a logged-in user on the home page, **When** they submit an empty textarea, **Then** the system shows a validation message and does not create a session.
3. **Given** a logged-in user submits a new idea, **When** they return to the home page later, **Then** the new session appears in the paginated recent research list with truncated title and draft status.

---

### User Story 2 - Agent Researches and Generates Article (Priority: P1)

After the user submits a research idea, the backend agent searches the internet, infers a potential article structure, and generates a full markdown article. The user sees the agent's thinking/reasoning in the left chat panel; the right panel shows a loading state until the first complete draft is ready, then displays the full article (updated after each refinement run completes).

**Why this priority**: The core value proposition — turning an idea into a researched draft — depends on the agent doing its work and surfacing results to the user.

**Independent Test**: Can be tested by creating a session and verifying the agent produces chat messages with reasoning steps in the left panel and a complete markdown article in the right panel.

**Acceptance Scenarios**:

1. **Given** a newly created research session, **When** the agent begins processing, **Then** the left panel shows streaming chat messages including full agent reasoning/chain-of-thought, the proposed plan (sections, audience, style), and progress, and the agent proceeds to write the article without waiting for explicit approval unless the user interrupts with changes.
2. **Given** the agent has completed its research, **When** the article is generated, **Then** the right panel displays the full markdown article including TL;DR, "What you will learn here", body sections, code examples, ASCII diagrams (when relevant), and a source list at the end, and the session display title updates to the article's first H1 heading on the home page list.
3. **Given** the agent encounters insufficient information, **When** it cannot produce a section, **Then** it flags the gap in the chat and asks the user for clarification or direction.

---

### User Story 3 - Refine Article via Chat Prompts (Priority: P2)

The user continues the conversation in the left chat panel to request changes, additions, or restructuring of the article. The agent updates the article in the right panel based on the new instructions.

**Why this priority**: Iterative refinement is what makes this tool powerful beyond a one-shot generator. Users will want to adjust tone, add sections, or correct facts.

**Independent Test**: Can be tested by sending a follow-up message like "Add a section about performance benchmarks" and verifying the article in the right panel updates to include the new section.

**Acceptance Scenarios**:

1. **Given** a generated article in the right panel, **When** the user types "Make the introduction shorter and more direct" in the chat, **Then** the agent updates the article and the right panel re-renders with the revised introduction.
2. **Given** an ongoing chat thread, **When** the user asks "Add a comparison table between X and Y", **Then** the agent adds a markdown table to the article and the source list is updated if new sources were consulted.

---

### User Story 4 - Download Article as Markdown (Priority: P3)

The user clicks a download button (`.md` icon) and receives the article as a `.md` file on their local machine.

**Why this priority**: Export is essential for using the article outside the platform but is not blocking during the research/writing workflow.

**Independent Test**: Can be tested by clicking the `.md` download button and verifying a valid markdown file is downloaded with the correct content.

**Acceptance Scenarios**:

1. **Given** a generated or edited article, **When** the user clicks the `.md` download button, **Then** a markdown file is downloaded with the article content and a filename derived from the research topic.

---

### User Story 5 - Article Versioning and Status (Priority: P2)

Each article has a status (draft or published). Every agent update creates a new version. Users see a version counter and can change status via a control on the article panel, which updates the status on the latest version.

**Why this priority**: Versioning provides safety for iterative work. Status tracking lets users distinguish work-in-progress from finalized articles.

**Independent Test**: Can be tested by making multiple edits and verifying version history grows, then changing status from "draft" to "published" and verifying the status label updates.

**Acceptance Scenarios**:

1. **Given** a newly generated article, **When** the session is created, **Then** the article status is "draft" by default.
2. **Given** an article with multiple agent updates, **When** the user views the article, **Then** the latest version is displayed with a version counter badge (e.g., "v3").
3. **Given** an article on the session page, **When** the user uses the status control to set "published" or back to "draft", **Then** the latest version status updates accordingly and is reflected in the article view and home page list.
4. **Given** a published article, **When** the agent saves a new version after a refinement prompt, **Then** the latest version status automatically reverts to "draft" until the user publishes again.

---

### User Story 6 - Home Page Research Hub (Priority: P1)

The home page is the single entry point for research: at the top, a "New idea" button and textarea to start research; below, a paginated list of the user's research sessions with title and status (draft or published). The list defaults to 10 items per page with a page size dropdown (5, 10, 20, 50).

**Why this priority**: Combines starting new research and discovering past work on one page; replaces a separate `/research/new` route.

**Independent Test**: Can be tested on the home page by verifying the compose area appears above the list, pagination works, and selecting a row opens the correct session.

**Acceptance Scenarios**:

1. **Given** a logged-in user on the home page, **When** the page loads, **Then** they see the "New idea" control, an always-visible textarea, and "Research & draft" above the paginated research list.
2. **Given** the user has research sessions (including those still generating), **When** they view the list, **Then** each row shows display title and status, ordered by most recent activity, with 10 items on the first page by default. Sessions without an article yet show truncated idea title, draft status, and a "generating" indicator while the agent runs.
3. **Given** the list has more items than the current page size, **When** the user changes page size or page number, **Then** the list updates without losing sort order.
4. **Given** the list shows a session, **When** the user selects it, **Then** they are navigated to `/research/{session_id}`.

---

### Edge Cases

- What happens when the user's internet research returns no relevant results? The agent should communicate this clearly and suggest refining the topic.
- What happens when DuckDuckGo rate-limits or returns empty results for a section? The agent flags the gap in chat, cites what it found for other sections, and recommends the user retry or refine that section later.
- What happens if the user navigates away mid-generation? The session persists in the database and the user can return to see whatever was generated.
- What happens in the article panel while the agent is still writing the first draft? A loading/placeholder is shown until the first complete article is available; reasoning streams only in the chat panel.
- What happens when the markdown contains malformed syntax? The renderer should degrade gracefully, showing raw text for unparseable sections rather than breaking the page.
- What happens if the agent fails entirely (timeout, crash, or web search unavailable)? The chat panel shows a clear error message and a "Retry" button. The session and original prompt are preserved; retry re-triggers the agent on the same session.
- What happens if the downloaded `.md` file is very large? The download should still work; there is no practical size limit for text files.
- What happens if reasoning content includes sensitive data from a source? The system must still redact secrets and internal prompts even when showing full chain-of-thought.
- What happens if the user tries to send a message while the agent is running? Send is disabled; the user must wait for completion or use Stop to cancel the active run.
- What happens when a session has no article yet? It still appears on the home page list with truncated idea title, draft status, and a mandatory "generating" indicator while the agent is running.
- What happens when a visitor is not signed in? They cannot access any page (including home or research routes) until authenticated.

## Clarifications

### Session 2026-05-20

- Q: What should users see while the research agent works (thinking/reasoning display)? → A: Full agent reasoning and chain-of-thought are visible in the research chat panel. This intentionally differs from the general chat feature's safe-progress-only policy.
- Q: Should research reuse general chat sessions or be separate? → A: Separate research sessions with dedicated storage, API routes, and UI. Independent from `/chat` sessions and message history.
- Q: Should the drafts/session sidebar appear on the session page? → A: Sidebar only on `/research/new`. The `/research/{session_id}` page uses full-width two panels (chat + article) with no session sidebar.
- Q: How should the `/research/new` sidebar list behave? → A: No separate `/research/new` page. Home page only: "New idea" button and textarea above the paginated recent research list (title + status). Session page remains full-width chat + article.
- Q: Should sessions appear in the home list before the first article exists? → A: Yes, list all sessions immediately with truncated idea title; show draft status, with an optional "generating" indicator while the agent is running.
- Q: Can the user send chat messages while the agent is running? → A: Send is disabled while the agent is running. User may use Stop to cancel the active run (same pattern as general chat).
- Q: What happens to published status when the agent creates a new version? → A: Status automatically reverts to draft when a new agent-produced version is saved.

- Q: How should the agent handle conflicts between manual edits and follow-up prompts? → A: Manual editing is deferred from v1. The right panel is read-only (Preview mode only). Users refine articles exclusively via chat prompts.
- Q: How should article version history be exposed to the user? → A: Version counter badge displayed on the article panel (e.g., "v3"). User always sees the latest version. Version history is stored in the database but no browse/diff UI in v1.
- Q: What should happen if the agent fails entirely during research? → A: Show an error message in the chat panel with a "Retry" button. The session is preserved so the user can re-trigger the agent without starting over.
- Q: Should the agent pause for user approval before writing the full article? → A: Agent posts a research plan (sections, audience, style) in chat and proceeds to write automatically unless the user replies with changes.
- Q: What should "published" mean in v1? → A: Status label only (no public URL or blog export). A control on the article panel lets the user set the latest article version to "draft" or "published". The home page lists recent research articles with title and status.

### Session 2026-05-23

- Q: Which LLM should power research generation and long-context runs? → A: OpenRouter model `deepseek/deepseek-v4-pro:nitro`, used only for the research agent (not general `/chat`).
- Q: What context is sent to the research agent on each run? → A: Full session chat history, latest article markdown body, and original idea.
- Q: Is DuckDuckGo sufficient as the web search provider for v1? → A: Yes. v1 uses DuckDuckGo only with multi-search per article (one search per section/theme), minimum 3 cited source URLs, and gap audit when snippets are weak. No second provider or paid API for v1.

### Session 2026-05-22

- Q: What should unauthenticated visitors see on the home page research hub? → A: All pages remain private. Unauthenticated users cannot access the home page, research compose area, or session pages; authentication is required first.
- Q: How should the right article panel behave during initial generation? → A: Loading/placeholder until the first full article exists; after refinements, replace with the latest complete version when each agent run finishes (no partial markdown streaming in the article panel).
- Q: Can users delete research sessions in v1? → A: Yes. Each row in the home page list exposes a delete icon that requires confirmation before permanently removing the session and all related data. Delete is blocked while an agent run is active.
- Q: Can the status control switch both draft and published? → A: Yes. User can set draft or published on the latest version at any time (bidirectional).
- Q: How should the "New idea" control relate to the textarea? → A: Textarea and "Research & draft" are always visible above the paginated list (no expand/collapse).

### Session 2026-05-21

- Q: How many research items should the home page recent list show? → A: Paginated list with default page size of 10, ordered by most recent activity. User can change page size via a dropdown and navigate pages.
- Q: Which page size choices should the dropdown offer? → A: 5, 10, 20, and 50 (default 10).
- Q: What title should each list row show? → A: Truncated original idea (max 60 characters) until an article exists, then the article's first H1 heading.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The home page MUST provide a research compose area above the recent list: a "New idea" label/button, a always-visible textarea, and a "Research & draft" submit button (clean, minimal layout per reference screenshots; no expand/collapse for compose).
- **FR-002**: System MUST create a new research session record in the database upon form submission, storing the original idea/prompt, the owner user, creation timestamp, and initial status of "draft".
- **FR-003**: System MUST redirect the user to `/research/{session_id}` after session creation.
- **FR-004**: The `/research/{session_id}` page MUST display a full-width two-panel layout (no session sidebar): left panel for the chat thread (including agent reasoning/thinking steps) and right panel for the article content.
- **FR-005**: The backend MUST include a research agent that receives the user's idea, searches the internet for relevant information, plans the article structure, and generates a full markdown article. The research agent MUST use OpenRouter model `deepseek/deepseek-v4-pro:nitro` (separate from the general chat agent model).
- **FR-021**: Every research agent run MUST receive as context the full research session chat history, the latest article markdown body (if any), and the original idea/prompt.
- **FR-006**: The research agent MUST follow the prescribed system prompt structure: post a research plan (sections, audience, style) in chat, then write the article with TL;DR, "What you will learn here", body sections with code examples and ASCII flows where relevant, and a source list. The agent proceeds after posting the plan unless the user replies with adjustments.
- **FR-022**: The research agent MUST perform multiple web searches per article (at least one search per planned section/theme) using Tavily Search API (`TavilyTools` with `search_depth="advanced"`). Each article MUST cite a minimum of 3 source URLs in the source list. When search results are insufficient, the agent MUST flag the gap in chat (FR-015) rather than fabricating content.
- **FR-007**: The agent's full reasoning and chain-of-thought MUST be visible in the left research chat panel as streaming messages (intentional exception to the general chat safe-progress-only policy; secrets and internal prompts must still be redacted).
- **FR-008**: Users MUST be able to send follow-up prompts in the chat to refine, extend, or restructure the generated article when no agent run is active. While an agent run is in progress, the send action is disabled and a Stop action cancels the active run without deleting prior messages.
- **FR-009**: The right panel MUST display the article in read-only rendered markdown (Preview mode). Manual editing is deferred to a future release. During the first agent run, the panel MUST show a loading/placeholder until the first complete article exists. On refinements, the panel updates when the agent run completes (no partial markdown streaming in the article panel).
- **FR-010**: The right panel MUST include a download button that exports the article as a `.md` file.
- **FR-011**: The system MUST store article versions; each agent update creates a new version.
- **FR-012**: Each article's latest version MUST have a status of "draft" or "published", defaulting to "draft". The session page MUST provide a bidirectional control on the article panel to set the latest version to draft or published at any time (no public URL or external publishing in v1). When the agent creates a new version, status MUST automatically revert to "draft".
- **FR-013**: The frontend MUST render enriched markdown correctly, including headings, code blocks with syntax highlighting, tables, lists, blockquotes, inline code, links, and ASCII art/diagrams.
- **FR-014**: A dedicated `/research/new` route MUST NOT exist in v1. All session discovery and the compose area live on the home page. The session page (`/research/{session_id}`) has no session list sidebar.
- **FR-015**: The research agent MUST identify and communicate gaps in the article after generation, recommending additional sections or changes.
- **FR-016**: When the agent fails entirely during research or generation, the system MUST show an error in the chat panel with a "Retry" action that re-triggers the agent on the same session without losing the user's original prompt.
- **FR-017**: The home page MUST list all of the user's research sessions immediately after creation (including before the first article exists), showing display title and status (draft or published; a "generating" indicator MUST be shown while an agent run is active), ordered by most recent activity, with navigation to the corresponding research session. The list MUST be paginated (default page size 10) and MUST provide page navigation plus a page size dropdown with options 5, 10, 20, and 50.
- **FR-018**: Research sessions, messages, articles, and versions MUST be stored and served via dedicated research APIs and data model, separate from general `/chat` sessions and chat message storage.
- **FR-019**: All research-related pages and APIs MUST require authentication; unauthenticated access is not supported in v1.
- **FR-020**: The home page list MUST expose a delete control on each session row. Deleting MUST require user confirmation before proceeding. Delete MUST be owner-scoped and MUST NOT succeed while an agent run is active (409 Conflict). Deleted sessions, messages, articles, and versions MUST be permanently removed and MUST NOT appear in future list or detail queries.

### Constitution Requirements *(mandatory when applicable)*

- **Agent Behavior**: The research agent operates under a defined system prompt and uses OpenRouter `deepseek/deepseek-v4-flash:nitro` for long-context research generation and refinements (general `/chat` keeps its existing model). Each run receives the full research chat history, latest article markdown, and original idea. It performs multi-search via Tavily Search API (`TavilyTools`, `search_depth="advanced"`; one search per section/theme; min 3 cited source URLs per article). It produces markdown articles and streams full reasoning/chain-of-thought in the research chat panel (unlike general chat). Secrets and internal system prompts must not be exposed. All agent actions are traced for observability. The agent should not perform destructive operations outside of article generation.
- **Auth0 Authorization**: All application pages remain private in v1 (including home and `/research/{session_id}`). Unauthenticated requests are redirected to sign-in. Research sessions are owned by the authenticated user; users can only view and edit their own sessions.
- **Data and Vector Search**: Research sessions, chat messages, article versions, and article metadata are stored in PostgreSQL. No vector search is required for this feature.
- **Deployment and Observability**: The feature requires new API routes and a dedicated research agent configuration. Environment variables must include OpenRouter API access, `RESEARCH_AGENT_MODEL=deepseek/deepseek-v4-flash:nitro`, and `TAVILY_API_KEY` for web search. Health checks should cover the new endpoints. Agent traces should be captured via existing LangWatch integration with model id recorded per run.

### Key Entities *(include if feature involves data)*

- **Research Session**: Represents a single research endeavor. Key attributes: unique identifier, owner user, original idea/prompt, display title (truncated idea up to 60 characters until an article exists, then the article's first H1 heading), creation timestamp, last updated timestamp. Display status is derived from the article's latest version.
- **Research Message**: A message in the research session's chat thread. Key attributes: unique identifier, session reference, role (user/agent), content, reasoning/thinking content (for agent messages), timestamp, ordering.
- **Article**: The generated research article for a session. Key attributes: unique identifier, session reference, current version number, creation timestamp.
- **Article Version**: A snapshot of the article at a point in time. Key attributes: unique identifier, article reference, version number, markdown content, status (draft/published; user-updatable on latest version; agent-created versions default to draft), change source (agent), timestamp.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can go from typing a research idea to seeing a generated article draft in under 3 minutes (measured from form submission to `article` SSE event; DuckDuckGo API wall-clock time is included in the budget).
- **SC-002**: 90% of generated articles contain all required structural elements: TL;DR, "What you will learn here", at least 3 body sections, and a source list with at least 3 sources.
- **SC-003**: Users can successfully refine an article through at least 5 consecutive chat prompts without loss of context or article state (agent receives full session history and latest article on each run).
- **SC-007**: Research chat displays agent reasoning/chain-of-thought during runs while redacting 100% of detected secrets and internal system prompts from visible output.
- **SC-004**: The article preview panel updates within 2 seconds after the agent finishes processing a refinement prompt.
- **SC-005**: Downloaded `.md` files are valid markdown that renders correctly in standard markdown viewers (GitHub, VS Code, etc.).
- **SC-006**: Article version history preserves all changes in the database, and the latest version is always displayed with a version counter badge.
- **SC-008**: Home page research list pagination returns the correct page of results within 1 second for lists up to 500 sessions per user.

## Assumptions

- Users have a stable internet connection (required for the agent's web research capabilities).
- The existing authentication system (Auth0) will be used to identify session owners.
- Research uses separate sessions, APIs, and storage from general `/chat`. UI patterns (streaming, message list) may reuse frontend components, but data and routes remain independent.
- v1 uses Tavily Search API (`TavilyTools` with `search_depth="advanced"`) for web research (multi-search per article, cited URLs, gap flagging). Requires `TAVILY_API_KEY` environment variable. General `/chat` still uses DuckDuckGoTools.
- The research agent uses OpenRouter `deepseek/deepseek-v4-flash:nitro` for long-context article generation; the general chat agent continues using the existing configured model.
- Mobile-responsive layout is desirable but not a hard requirement for v1; desktop is the primary target.
- "Published" is an in-app status label only in v1; it does not create a public shareable URL or publish to an external blog.
- The home page is the research hub: compose area (New idea + textarea) above a paginated research list (titles and status; default 10 per page; page size 5/10/20/50). No `/research/new` page.
- The agent does not literally create git branches or PRs for articles — the system prompt's mention of "create a new branch and PR" is interpreted as the agent generating the article content within the platform, with version control handled by the article versioning system.
- The existing LangWatch integration will capture agent traces without additional setup.
- Markdown rendering will use an existing library (the frontend already uses a markdown renderer for chat messages).
- Session delete is supported in v1 (hard delete with user confirmation). Archive/undo is out of scope.
