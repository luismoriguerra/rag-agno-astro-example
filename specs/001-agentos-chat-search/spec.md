# Feature Specification: AgentOS Chat Search

**Feature Branch**: `001-agentos-chat-search`  
**Created**: 2026-05-18  
**Status**: Draft  
**Input**: User description: "create agentos app with simple agent that allow to search using DuckDuck go and create a new astro app with a page /chat with chatbox that call agentos app, and allow to deploy all to railway; for railway deployment reference use https://github.com/agno-agi/pal/blob/main/scripts/railway_up.sh"

## Clarifications

### Session 2026-05-18

- Q: Which Railway deployment topology should this feature use? → A: Two Railway services: Astro frontend + AgentOS backend.
- Q: How should conversation context work across chat messages? → A: Chat history is persisted across reloads and future visits.
- Q: How should persisted chat history be associated with visitors? → A: Auth0 account-owned history, using a mocked authenticated identity until Auth0 is integrated.
- Q: How long should chat history be retained? → A: Chat history is kept indefinitely until the user deletes it.
- Q: How should New Chat, Stop, thinking, and streaming behave? → A: New Chat creates a new persisted session; Stop cancels the active response and keeps prior messages; Thinking shows safe progress/tool status; answer text streams visibly.
- Q: How should deployment commands be exposed? → A: Deployment uses local Makefile commands; GitHub Actions is out of scope for now.
- Q: What chat history context should the agent receive? → A: Every agent run receives the current identity's active chat session history as context.
- Q: What Railway resource sizing should project and services use? → A: Railway project and services use minimum CPU and memory settings.

## Deployment Constraints

- The initial implementation uses a mocked authenticated identity while preserving the Auth0 ownership model for persisted history.
- Real Auth0 token validation is required before any production deployment that exposes persisted user history or agent tools.
- Local and staging deployments may use the mocked identity only when deployment configuration explicitly enables it.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ask a Search-Backed Question (Priority: P1)

A visitor opens the chat page, types a question, submits it, and receives an answer generated
from a search-capable agent using current public web results and available prior chat history.

**Why this priority**: This is the core product loop and the smallest useful end-to-end slice.

**Independent Test**: Open `/chat`, ask a current-events or documentation question, and verify
that the page shows a relevant answer with source context or a clear no-results message.

**Acceptance Scenarios**:

1. **Given** a visitor is on `/chat`, **When** they submit a valid question, **Then** the page displays the user's message, a loading state, and a final agent answer.
2. **Given** the agent uses web results to answer, **When** the answer is displayed, **Then** the answer includes the source links or source labels used to ground the response.
3. **Given** the question cannot be answered from available search results, **When** the agent completes, **Then** the page explains that it could not find enough supporting information.
4. **Given** a signed-in or mocked signed-in visitor returns to `/chat` after a reload or later visit, **When** their history is available, **Then** prior messages owned by that identity are restored and can provide context for follow-up questions.
5. **Given** a signed-in or mocked signed-in visitor deletes the active chat session, **When** they use Delete active session, **Then** prior messages in that session are no longer restored or used as context.
6. **Given** a visitor submits a question, **When** the agent begins responding, **Then** the page renders safe progress status and streams answer text as it becomes available.
7. **Given** a visitor is in an existing chat session, **When** they start a new chat, **Then** a new persisted session is created without deleting the prior session.
8. **Given** a visitor submits a question in an active chat session with prior messages, **When** the agent run starts, **Then** the agent receives that active session's chat history as context.

---

### User Story 2 - Handle Chat and Search Failures Gracefully (Priority: P2)

A visitor receives clear feedback when search, the agent service, or the chat request fails,
without losing their typed message or seeing a broken page.

**Why this priority**: Failure handling protects the user experience for a feature that depends
on external search and a backend service.

**Independent Test**: Simulate a search or service failure and verify the page shows a helpful
error state and allows the visitor to retry.

**Acceptance Scenarios**:

1. **Given** the search service is unavailable, **When** a visitor submits a question, **Then** the page shows a retryable error message and preserves the submitted question.
2. **Given** the agent response takes too long, **When** the request reaches the configured wait limit, **Then** the page stops waiting and tells the visitor to retry.
3. **Given** a visitor submits an empty message, **When** they attempt to send it, **Then** the page prevents submission and explains what is required.
4. **Given** an agent response is in progress, **When** the visitor presses Stop, **Then** the active response is canceled and prior messages remain available.

---

### User Story 3 - Publish the Chat Experience (Priority: P3)

A maintainer can deploy the chat page and agent service together so the experience is reachable
from a public deployment URL.

**Why this priority**: The feature is not complete until the end-to-end chat flow can be hosted
and verified outside a local machine.

**Independent Test**: Run the documented local Makefile deployment command from a clean
environment, open the published chat URL, and complete the primary chat flow.

**Acceptance Scenarios**:

1. **Given** required deployment credentials and environment variables are available, **When** a maintainer runs the local Makefile deployment command, **Then** the Astro frontend service and AgentOS backend service are published successfully.
2. **Given** deployment configuration is missing required values, **When** a maintainer starts deployment, **Then** the process reports the missing values before publishing an unusable service.
3. **Given** deployment finishes successfully, **When** a maintainer opens the public chat page, **Then** the page can call the agent service and show an answer.
4. **Given** maintainers have not configured CI/CD, **When** deployment is needed, **Then** they can deploy from their local machine without GitHub Actions.
5. **Given** a maintainer creates the Railway project and services, **When** resource settings are applied, **Then** the project and services use the minimum CPU and memory settings available for the deployment environment.

---

### Edge Cases

- The search provider returns no useful results for a valid question.
- The search provider rate-limits or rejects a request.
- The agent service returns malformed, empty, or overly long output.
- The visitor submits repeated messages quickly before the previous answer completes.
- The browser loses network connectivity during an active chat request.
- Persisted chat history is unavailable or cannot be restored.
- The mocked authenticated identity is missing or invalid during the pre-Auth0 implementation phase.
- A visitor deletes the active chat session while another chat response is in progress.
- A visitor starts a new chat while another response is in progress.
- A streamed response is interrupted before completion.
- Active session history cannot be loaded before an agent run starts.
- Deployment succeeds for one component but not the other.
- Required deployment secrets are absent or invalid.
- A required Makefile target is missing or fails before deployment starts.
- A maintainer expects GitHub Actions deployment even though it is out of scope for this release.
- Minimum CPU or memory settings are unavailable or rejected by Railway for a required service.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a `/chat` page where visitors can enter and submit a text question.
- **FR-002**: System MUST display the visitor's submitted messages and the agent's responses in a readable chat transcript.
- **FR-003**: System MUST connect submitted questions to a simple agent service that can search public web results through DuckDuckGo.
- **FR-004**: System MUST ground answers in returned search results when search results are used.
- **FR-005**: System MUST display source links or source labels for answers that rely on web search results.
- **FR-006**: System MUST explain when it cannot find enough supporting information to answer confidently.
- **FR-007**: System MUST show loading, empty-input, retryable-error, and timeout states on the chat page.
- **FR-008**: System MUST preserve the user's submitted question when a retryable error occurs.
- **FR-009**: System MUST persist chat history across page reloads and future visits.
- **FR-010**: System MUST restore available chat history when the visitor opens `/chat`.
- **FR-011**: System MUST provide the current identity's active chat session history as context to every agent run.
- **FR-012**: System MUST associate persisted chat history with an Auth0-compatible user identity.
- **FR-013**: System MUST support a mocked authenticated identity for the initial implementation before Auth0 is integrated.
- **FR-014**: System MUST prevent one identity from restoring another identity's chat history.
- **FR-015**: System MUST retain chat history indefinitely until the owning identity deletes it.
- **FR-016**: System MUST allow the current identity to delete the active chat session and stop restoring or using that session as context.
- **FR-017**: System MUST stop restoring or using deleted chat session history as context.
- **FR-018**: System MUST prevent deleted sessions, other identities' sessions, and inactive sessions from being included in an agent run context.
- **FR-019**: System MUST provide a New Chat action that creates a new persisted chat session for the current identity without deleting prior sessions.
- **FR-020**: System MUST provide a Stop action that cancels the active agent response while preserving prior messages in the current session.
- **FR-021**: System MUST render safe thinking/progress status while the agent is preparing, searching, or generating an answer.
- **FR-022**: System MUST NOT expose raw hidden reasoning, chain-of-thought, secrets, or internal prompts in thinking/progress status.
- **FR-023**: System MUST stream answer text visibly as it becomes available.
- **FR-024**: System MUST provide a Makefile with local commands for running the app locally, deploying the Astro frontend and AgentOS backend, checking deployment status, viewing logs, and running a smoke test.
- **FR-025**: System MUST provide deployment instructions and configuration checks for publishing the Astro frontend and AgentOS backend as separate Railway services through local Makefile commands.
- **FR-026**: System MUST document required deployment variables before deployment starts.
- **FR-027**: System MUST include a post-deployment smoke test that verifies the public chat page can reach the agent service.
- **FR-028**: System MUST follow the Railway deployment reference pattern from the Agno PAL setup script, including preflight checks, separate service creation, environment configuration, deployment, domain creation, and log guidance.
- **FR-029**: System MUST NOT require GitHub Actions for local development, deployment, or smoke-test workflows in this release.
- **FR-030**: System MUST configure the Railway project and Railway services with the minimum CPU and memory settings available for the deployment environment.
- **FR-031**: System MUST document any Railway service that cannot use minimum CPU or memory settings and explain the required exception.

### Constitution Requirements *(mandatory when applicable)*

- **RAG Grounding**: Public web search results are the knowledge source for this feature. Answers must cite or label the search results used, and insufficient search context must produce a clear fallback message instead of an unsupported answer.
- **Agent Behavior**: The agent has one responsibility: answer user chat questions by optionally searching DuckDuckGo. Its tool permissions are limited to public search for this feature, every run receives the current identity's active chat session history as context, and runs must expose enough trace information to debug prompts, search decisions, and final answers. User-facing thinking/progress status must summarize safe execution state only.
- **Auth0 Authorization**: Persisted chat history must be owned by an Auth0-compatible identity. The first implementation may use a mocked authenticated identity, but the access boundary must be replaceable by real Auth0 validation before production use.
- **Data and Vector Search**: Persistent chat history is in scope for this feature and must be partitioned by owner identity. Vector search remains out of scope, and no private content beyond visitor chat messages is retrieved.
- **Deployment and Observability**: Deployment must cover separate Astro frontend and AgentOS backend Railway services, define required environment variables, configure minimum Railway CPU and memory settings, expose a health or smoke-test path, provide Makefile targets for local deployment operations, and provide log commands for deployment troubleshooting. GitHub Actions is out of scope for this release.

### Key Entities *(include if feature involves data)*

- **Chat Message**: A visitor-submitted question or agent-produced answer shown in the chat transcript.
- **Chat Session**: A persisted sequence of chat messages owned by one Auth0-compatible identity, retained until user deletion, restored across reloads and future visits, and provided as context to every agent run while active.
- **User Identity**: An Auth0 account identifier or mocked authenticated identifier used to own and restore chat history.
- **Agent Response**: The streamed answer, safe progress status, final status, and source context returned to the chat page.
- **Search Result**: A public web result used to ground an answer, including title, URL, and snippet or summary.
- **Deployment Configuration**: Required environment values, local Makefile targets, minimum CPU and memory settings, and service settings needed to publish separate frontend and backend Railway services.
- **Knowledge Source**: Public DuckDuckGo search results available at answer time.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 90% of valid chat questions with available public search results receive a visible answer in under 10 seconds during normal operation.
- **SC-002**: 100% of answers that use search results include at least one visible source link or source label.
- **SC-003**: 100% of empty, failed, or timed-out submissions produce a user-readable message without clearing the user's latest question.
- **SC-004**: 95% of signed-in or mocked signed-in visitors with available persisted history see their latest chat transcript restored within 2 seconds of opening `/chat`.
- **SC-005**: 100% of history restore attempts return only messages owned by the current identity.
- **SC-006**: 100% of deleted active chat sessions are absent from future restores and follow-up context for that identity.
- **SC-007**: 100% of agent runs include the current identity's active chat session history when that history is available.
- **SC-008**: 100% of agent runs exclude deleted sessions, inactive sessions, and sessions owned by another identity.
- **SC-009**: 95% of successful responses begin showing streamed answer text within 3 seconds after the agent starts generating.
- **SC-010**: 100% of stopped responses preserve prior messages and stop adding new answer text after cancellation completes.
- **SC-011**: 100% of thinking/progress displays avoid raw hidden reasoning, internal prompts, secrets, and chain-of-thought.
- **SC-012**: A maintainer can complete first deployment by running documented local Makefile commands and open a working public chat page in under 15 minutes after credentials and required secrets are available.
- **SC-013**: The deployment smoke test verifies the public chat page and agent service connection through one documented Makefile command or user flow.
- **SC-014**: 100% of Railway project and service resource settings use minimum CPU and memory values unless a documented Railway constraint requires an exception.

## Assumptions

- The initial implementation uses a mocked authenticated identity while preserving the Auth0 ownership model for persisted history.
- DuckDuckGo is the only search source for the initial version.
- Deployment follows the referenced Agno PAL Railway setup approach as an implementation reference, adapted to this project's two-service frontend/backend topology, service names, and environment variables.
- Deployment automation is local-first through a Makefile; GitHub Actions can be considered later but is not part of this release.
- Railway project and service creation defaults to minimum CPU and memory settings to minimize cost for the first release.
- A single simple agent is sufficient for the first release; multi-agent routing is out of scope.
