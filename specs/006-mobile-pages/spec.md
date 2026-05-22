# Feature Specification: Mobile Home and Research Pages

**Feature Branch**: `006-mobile-pages`  
**Created**: 2026-05-21  
**Status**: Draft  
**Input**: User description: "let's add mobile version for home page and Research page"

## Clarifications

### Session 2026-05-21

- Q: On viewports below 768px, how should users switch between the research thread and article in the research workspace? → A: Top tabs below session title ("Thread" | "Article").
- Q: At what viewport width should the layout switch from mobile to desktop? → A: Mobile below 768px; 768px and above uses desktop layout.
- Q: On viewports below 768px, how should the shared top navigation be presented? → A: Hamburger menu — logo and profile visible; Home, Chat, and + New Research inside a slide-out drawer.
- Q: When the agent finishes generating an article on mobile, should the UI automatically switch to the Article tab? → A: Stay on Thread; show a badge/indicator on the Article tab when new content is ready.
- Q: Should the mobile hamburger navigation apply to the /chat page as well? → A: Yes — hamburger nav on all authenticated pages including /chat; chat content layout unchanged.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Use the Home Page on a Phone (Priority: P1)

A logged-in user opens the home page on a viewport below 768px. They can start a new research idea, submit it, and browse their existing research sessions without horizontal scrolling or overlapping controls.

**Why this priority**: The home page is the primary entry point for research. If it is unusable on mobile, users cannot start or return to work from their phones.

**Independent Test**: Can be fully tested by loading the home page at a narrow viewport width, submitting a new idea, and verifying the compose area and session list remain readable and actionable.

**Acceptance Scenarios**:

1. **Given** a logged-in user on a viewport below 768px, **When** the home page loads, **Then** the "New idea" compose area appears above the research list in a single vertical column with readable text and no horizontal page scroll.
2. **Given** a logged-in user on a viewport below 768px, **When** they enter a topic and tap "Research & draft", **Then** the submit action works the same as on desktop and redirects to the research workspace.
3. **Given** a logged-in user on a viewport below 768px with existing sessions, **When** they view the research list, **Then** each row shows title, status, and tap target large enough to open the session without precision tapping.
4. **Given** a logged-in user on a viewport below 768px, **When** they switch between Drafts and Published tabs or change page size or page number, **Then** list controls remain reachable and the list updates correctly.

---

### User Story 2 - Navigate the Research Workspace on a Phone (Priority: P1)

A logged-in user opens an active or completed research session on a viewport below 768px. They can follow agent progress in the research thread, stop generation when needed, and read or manage the article without the two-panel desktop layout breaking the experience.

**Why this priority**: The research workspace is where users spend most of their time during and after generation. Mobile support must preserve the full research workflow, not just viewing a static article.

**Independent Test**: Can be fully tested by opening `/research/{session_id}` on a narrow viewport, watching an active run, switching to the article view, and using stop, retry, and article controls.

**Acceptance Scenarios**:

1. **Given** a logged-in user on a viewport below 768px in an active research session, **When** the workspace loads, **Then** the session title is visible and the research thread is the default view.
2. **Given** a user viewing the research thread on a viewport below 768px, **When** the agent is generating, **Then** streaming status and reasoning remain readable, and a clearly labeled "Stop generating" control stays visible without obscuring the conversation.
3. **Given** a user on a viewport below 768px, **When** they tap the "Article" top tab below the session title, **Then** the rendered article fills the available width with readable typography, including headings, lists, code blocks, and tables without breaking the layout.
4. **Given** a user on a viewport below 768px with a completed article, **When** they use article controls (version badge, draft/published status, download), **Then** all controls remain accessible and behave the same as on desktop.
5. **Given** a user on the Thread tab while the agent completes an article update, **When** generation finishes, **Then** the UI remains on the Thread tab and the Article tab shows a visible badge/indicator that new content is ready; the indicator clears once the user opens the Article tab.
6. **Given** a user on a viewport below 768px, **When** they send a follow-up message or tap Retry after an error, **Then** chat input and recovery actions work without requiring desktop-only interactions.
7. **Given** a user on the Article tab when the agent completes an article update, **When** generation finishes, **Then** no badge appears on the Article tab and the updated content is shown in place.

---

### User Story 3 - Use Shared Navigation on Mobile (Priority: P2)

A logged-in user moves between Home, Chat, and account actions from a viewport below 768px using navigation that fits narrow widths without crowding or clipping.

**Why this priority**: Both target pages share the global navigation bar. Mobile layouts fail if users cannot reach core destinations or sign out.

**Independent Test**: Can be fully tested by loading any authenticated page on a narrow viewport and verifying all navigation destinations and the user menu are reachable.

**Acceptance Scenarios**:

1. **Given** a logged-in user on a viewport below 768px, **When** they view the top navigation, **Then** the Lumen logo and profile avatar are visible, and tapping the hamburger icon opens a slide-out drawer with Home, Chat, and + New Research without overlapping or clipping.
2. **Given** a logged-in user on a viewport below 768px with the navigation drawer open, **When** they tap outside the drawer or the close control, **Then** the drawer closes and page content remains accessible.
3. **Given** a logged-in user on a viewport below 768px, **When** they open the account menu from the profile avatar, **Then** they can sign out successfully.
4. **Given** a logged-in user on a viewport below 768px, **When** they tap "+ New Research" in the navigation drawer, **Then** they are taken to the home page compose area to start a new session.
5. **Given** a logged-in user on a viewport below 768px on the `/chat` page, **When** the page loads, **Then** the same hamburger navigation (logo, drawer, profile menu) is available even though chat content layout is unchanged.

---

### User Story 4 - Resize Between Phone and Desktop Layouts (Priority: P3)

A user rotates their device or resizes the browser window. The home and research pages adapt smoothly between mobile and desktop layouts without losing session state or trapping the user in a broken view.

**Why this priority**: Responsive behavior must remain stable across common real-world transitions, not only at fixed phone widths.

**Independent Test**: Can be tested by loading a research session, switching between thread and article on mobile width, then widening to desktop width and confirming both panels appear side by side with state preserved.

**Acceptance Scenarios**:

1. **Given** a user viewing the research workspace on a viewport below 768px with the article tab active, **When** they widen the viewport to desktop width, **Then** the layout shows the research thread and article side by side without losing messages, article content, or run state.
2. **Given** a user on a desktop-width home page, **When** they narrow the viewport to phone width, **Then** the compose area and research list reflow into a single column without content loss.

---

### Edge Cases

- What happens when a session title is very long on a narrow screen? The title truncates with ellipsis in the header while remaining readable; full title is still discoverable from the home list or article heading.
- What happens when the research thread has many messages on mobile? The thread scrolls independently; the stop control and message input remain reachable (pinned or sticky at the bottom as appropriate).
- What happens when the article contains wide elements (tables, code blocks, ASCII diagrams)? Content scrolls horizontally within the article area only; the page itself does not require horizontal scroll.
- What happens when the user switches tabs during active generation? Thread and article views stay in sync with the same session state; switching tabs does not interrupt the run.
- What happens when generation completes while the user is on the Thread tab? The UI stays on Thread; the Article tab shows a badge until the user views the updated article.
- What happens when generation completes while the user is already on the Article tab? No badge is shown; the article content updates in place on the active tab.
- What happens on the smallest common phone width (320px)? All primary actions remain usable without overlap.
- What happens when the user is not signed in on mobile? Existing authentication redirect behavior applies; no mobile-specific bypass is introduced.
- What happens when the research list is empty on mobile? The empty state message remains visible below the compose area with the same guidance as desktop.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The home page MUST provide a usable single-column layout on viewports below 768px that includes the compose area and paginated research list without horizontal page scrolling.
- **FR-002**: The home page MUST preserve all existing behaviors on mobile: submit new idea, validation on empty submit, tab filtering (drafts/published), pagination, page-size selection, session navigation, empty and loading states, and delete confirmation.
- **FR-003**: The research workspace MUST adapt to viewports below 768px so the research thread and article are not forced into unreadable side-by-side columns.
- **FR-004**: On viewports below 768px, the research workspace MUST expose top tabs labeled "Thread" and "Article" directly below the session title, letting users switch between views while sharing the same session state.
- **FR-005**: The research workspace MUST keep "Stop generating", message input, retry, and error messaging usable on viewports below 768px during all run states defined by the existing research experience.
- **FR-006**: The article panel on mobile MUST render the same markdown content as desktop, including headings, lists, code blocks, tables, blockquotes, links, and images, with graceful degradation for unparseable markdown.
- **FR-007**: Article controls (version indicator, draft/published status, markdown download) MUST remain accessible on viewports below 768px when an article exists.
- **FR-008**: Shared top navigation on viewports below 768px MUST show the Lumen logo and profile avatar inline, with Home, Chat, and + New Research accessible via a hamburger-triggered slide-out drawer; sign-out MUST remain reachable from the profile account menu.
- **FR-009**: Interactive controls on mobile layouts MUST use touch-friendly sizing so primary actions can be activated without precision tapping.
- **FR-010**: Layout MUST transition between mobile and desktop presentations at a **768px viewport breakpoint** (mobile below 768px, desktop at 768px and above) without losing in-progress research state, messages, or article content.
- **FR-011**: Mobile layouts MUST NOT change authentication requirements, API behavior, or research business rules; this feature is presentation-only for the home and research workspace pages.
- **FR-012**: The chat page (`/chat`) content layout is out of scope for this feature, but the shared hamburger navigation MUST apply on `/chat` and all other authenticated pages that use the global navbar.
- **FR-013**: On viewports below 768px, when article generation completes while the user is on the Thread tab, the UI MUST remain on Thread and MUST show a visible badge or indicator on the Article tab; the indicator MUST clear once the user opens the Article tab. When the user is already on the Article tab at completion, no badge is shown and the article updates in place.
- **FR-014**: The mobile navigation drawer and research workspace tabs MUST support basic accessibility: focus trap while the drawer is open with focus returned to the hamburger trigger on close; ARIA attributes on drawer trigger, drawer panel, and tab controls as defined in the mobile UI contract.

### Constitution Requirements *(mandatory when applicable)*

- **RAG Grounding**: N/A — no retrieval or agent knowledge changes; existing research agent behavior is unchanged.
- **Agent Behavior**: N/A — agent orchestration, tool use, and streaming semantics remain as defined by the research generator feature.
- **Auth0 Authorization**: Existing Auth0-protected access applies unchanged. Mobile layouts MUST NOT expose protected content to unauthenticated users or bypass server-side ownership checks.
- **Data and Vector Search**: N/A — no schema, persistence, or vector search changes.
- **Deployment and Observability**: No new backend services. Deployment follows existing frontend release process. Manual verification on viewports below 768px is required before release.

### Key Entities *(include if feature involves data)*

N/A — this feature adapts presentation of existing home and research session experiences; no new persistent entities are introduced.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On all viewports below 768px (validated at sample widths 320px, 375px, and 767px), 100% of primary home-page tasks (start research, browse list, open session, change tab/page) can be completed without horizontal page scrolling.
- **SC-002**: On all viewports below 768px (validated at sample widths 320px, 375px, and 767px), 100% of primary research-workspace tasks (follow generation, stop run, switch to article, read article, change status, download markdown, send follow-up) can be completed without horizontal page scrolling.
- **SC-003**: At least 95% of interactive controls on the home and research pages meet a minimum 44×44 CSS pixel touch target on viewports below 768px, verified via the quickstart touch-target spot-check inventory.
- **SC-004**: When resizing from phone width to desktop width during an active research run, session content and run state remain intact with zero required page reloads.
- **SC-005**: In moderated usability checks on real phone devices or emulators, users can start a research session and read the resulting article in under 3 minutes without assistance.

## Assumptions

- "Mobile version" means responsive layouts for viewports below 768px; tablet-specific optimizations may follow the same rules unless separately specified later.
- Viewports below **768px** use mobile layout; desktop layout behavior at 768px and above remains equivalent to the current experience.
- The research workspace uses top tabs ("Thread" | "Article") below the session title on viewports below 768px rather than side-by-side panels, because side-by-side panels are unreadable at narrow widths.
- Shared navigation on viewports below 768px uses a hamburger-triggered slide-out drawer for Home, Chat, and + New Research, with logo and profile avatar always visible in the top bar.
- Existing research UI contract behaviors (compose, list, chat thread, article preview, controls, streaming states) are the functional baseline; mobile work adapts layout and interaction affordances only.
- The chat page content layout is excluded from scope, but the shared hamburger navigation applies globally on all authenticated pages (home, research, and chat).
