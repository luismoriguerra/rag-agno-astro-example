# Implementation Plan: Mobile Home and Research Pages

**Branch**: `006-mobile-pages` | **Date**: 2026-05-21 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/006-mobile-pages/spec.md`

## Summary

Make the home page (`/`) and research workspace (`/research/{sessionId}`) fully usable on viewports below 768px by adding responsive Tailwind layouts, a hamburger navigation drawer on all authenticated pages (including `/chat`), and a mobile research workspace with top tabs ("Thread" | "Article") plus an article-ready badge. No backend, API, or database changes. Desktop behavior at 768px and above remains unchanged.

## Technical Context

**Language/Version**: Node.js 22 and TypeScript 5.x for frontend only; Python backend unchanged
**Primary Dependencies**: Astro 5, React 19 (islands), Tailwind CSS 4 (`@tailwindcss/vite`), existing Radix Alert Dialog; no new npm packages required for v1
**Storage**: N/A — presentation-only; no PostgreSQL or API changes
**Testing**: Vitest for unit tests (media-query hook, tab/badge logic); manual viewport smoke tests at 375px and 320px; optional Playwright via MCP for regression
**Target Platform**: Mobile browsers (iOS Safari, Android Chrome) and narrow desktop windows; Railway-deployed Astro SSR frontend unchanged in infrastructure
**Project Type**: Frontend responsive extension to existing RAG web application
**Performance Goals**: Layout reflow on resize without page reload (SC-004); no perceptible lag when switching Thread/Article tabs
**Constraints**: 768px breakpoint; 44×44px minimum touch targets (SC-003); Auth0 flows unchanged; chat page content layout out of scope
**Scale/Scope**: ~6 frontend files updated, ~3 new small modules (hook, drawer, workspace tabs), 0 backend files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Grounded RAG and Agent Behavior**: N/A. No agent, retrieval, or model changes. Research streaming semantics unchanged; mobile only changes how thread and article are displayed.
- **Auth0-Centered Security Boundaries**: PASS. Auth0-protected routes unchanged. Mobile nav drawer exposes the same destinations as desktop; no new endpoints or client-side auth bypass. Profile menu and sign-out remain on the verified `/api/auth/me` path.
- **Typed API and UI Contracts**: PASS. No API contract changes. New UI contract document (`contracts/mobile-ui.md`) extends the existing research UI contract with breakpoint-specific layout rules, tab behavior, nav drawer, and article-ready badge semantics.
- **PostgreSQL and pgvector Integrity**: N/A. No schema, migration, or query changes.
- **Railway-Ready Delivery and Observability**: PASS. Frontend-only deploy via existing Railway frontend service. Manual verification checklist in `quickstart.md` covers 320px–767px viewports. No new env vars or health checks.

**Post-Design Recheck**: PASS. Research, data model (client UI state only), contracts, and quickstart preserve all constitution gates. No violations.

## Project Structure

### Documentation (this feature)

```text
specs/006-mobile-pages/
├── plan.md              # This file
├── research.md          # Phase 0 — responsive patterns and decisions
├── data-model.md        # Phase 1 — client UI state (no DB entities)
├── quickstart.md        # Phase 1 — local verification at mobile widths
├── contracts/
│   └── mobile-ui.md     # Phase 1 — mobile layout UI contract
└── tasks.md             # Phase 2 (/speckit.tasks — not created here)
```

### Source Code (repository root)

```text
apps/frontend/
├── src/
│   ├── components/
│   │   ├── Navbar.tsx                 # UPDATE: hamburger drawer below md
│   │   ├── NavDrawer.tsx              # NEW: slide-out nav panel
│   │   ├── ResearchCompose.tsx        # UPDATE: mobile padding, touch targets
│   │   ├── ResearchList.tsx           # UPDATE: mobile row layout, delete always reachable
│   │   ├── ResearchWorkspace.tsx      # UPDATE: responsive tabs vs side-by-side
│   │   ├── WorkspaceTabs.tsx          # NEW: Thread | Article tabs + badge
│   │   ├── ResearchChat.tsx           # UPDATE: sticky input/stop on mobile
│   │   ├── ArticlePreview.tsx         # UPDATE: overflow-x for wide markdown
│   │   └── ArticleControls.tsx        # UPDATE: wrap controls on narrow widths
│   ├── hooks/
│   │   └── useMediaQuery.ts           # NEW: (max-width: 767px) helper
│   ├── lib/
│   │   └── breakpoints.ts             # NEW: MOBILE_MAX_WIDTH = 767
│   ├── pages/
│   │   ├── index.astro                # UPDATE: responsive page padding
│   │   └── research/
│   │       └── [sessionId].astro      # UPDATE: mobile-friendly height calc
│   └── styles/
│       └── global.css                 # UPDATE: mobile article-prose tweaks if needed
└── tests/
    ├── useMediaQuery.test.ts          # NEW
    └── workspace-tabs.test.ts         # NEW (badge clear logic)
```

**Structure Decision**: Extend the existing `apps/frontend` Astro/React app only. Shared `Navbar` in `AppLayout.astro` delivers hamburger nav globally. `ResearchWorkspace` owns mobile tab state and article-ready badge; child panels (`ResearchChat`, `ArticlePreview`) receive layout classes but no API changes.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

## Implementation Phases (for `/speckit.tasks`)

### Phase A — Foundation (P2 nav, enables all pages)

1. Add `breakpoints.ts` and `useMediaQuery` hook (`max-width: 767px`).
2. Extract `NavDrawer.tsx`; refactor `Navbar.tsx`:
   - Desktop (`md:` and up): current inline nav unchanged.
   - Mobile: logo left, hamburger + profile right; drawer holds Home, Chat, + New Research.
   - Drawer dismiss: overlay tap, close button, Escape key.
   - Profile dropdown unchanged on avatar tap.

### Phase B — Home page mobile (P1)

3. `index.astro`: reduce padding (`px-4 py-6` on mobile, keep `px-6 py-12` on `md+`).
4. `ResearchCompose.tsx`: stack submit row vertically on mobile; ensure button `min-h-11`.
5. `ResearchList.tsx`: stack tab row on very narrow screens if needed; make delete button always visible on mobile (not hover-only); enlarge pagination tap targets.

### Phase C — Research workspace mobile (P1)

6. `WorkspaceTabs.tsx`: Thread | Article tabs with optional badge dot on Article.
7. `ResearchWorkspace.tsx`:
   - Below 768px: render header + tabs + single active pane.
   - 768px+: keep existing `flex` two-panel layout.
   - Track `activeTab: 'thread' | 'article'` and `articleHasUpdate: boolean`.
   - On `onDone` / `onArticle`: if `activeTab === 'thread'`, set `articleHasUpdate = true`; clear when user selects Article tab.
8. `ResearchChat.tsx`: sticky footer for input + Stop on mobile; ensure thread scroll area uses `flex-1 overflow-y-auto`.
9. `ArticlePreview.tsx` / `ArticleControls.tsx`: horizontal scroll for tables/code; wrap control row on mobile.

### Phase D — Verification

10. Add Vitest tests for hook and badge logic.
11. Run manual quickstart checklist at 375px, 320px, and resize 767→768px.

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Hover-only delete hidden on touch devices | Show delete icon always on mobile (`md:opacity-0 md:group-hover:opacity-100`) |
| Fixed viewport height breaks mobile browser chrome | Use `dvh` or `min-h-0 flex-1` pattern in workspace; test iOS Safari |
| Tab state lost on resize | Keep both panels mounted; toggle visibility with CSS/`hidden` rather than unmounting |
| Chat page nav breaks while content stays desktop | Scope limited to Navbar only; document in quickstart |
