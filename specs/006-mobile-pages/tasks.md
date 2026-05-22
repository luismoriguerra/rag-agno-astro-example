# Tasks: Mobile Home and Research Pages

**Input**: Design documents from `/specs/006-mobile-pages/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/mobile-ui.md, quickstart.md

**Tests**: Plan specifies Vitest unit tests for `useMediaQuery` and article-badge logic; manual viewport verification per quickstart.md. No backend tests required.

**Organization**: Tasks grouped by user story. Shared responsive infrastructure and navigation (US3) are in Foundational phase because they block all mobile page work.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Maps to spec user stories (US1–US4)
- Include exact file paths in descriptions

## Path Conventions

- **Frontend**: `apps/frontend/src/`
- **Frontend tests**: `apps/frontend/tests/`
- **Specs**: `specs/006-mobile-pages/`

---

## Phase 1: Setup

**Purpose**: Shared constants and project baseline for responsive work

- [x] T001 [P] Add `MOBILE_MAX_WIDTH_PX` (767) and `MOBILE_MEDIA_QUERY` (`(max-width: 767px)`) constants to `apps/frontend/src/lib/breakpoints.ts`

---

## Phase 2: Foundational — Shared Navigation (US3)

**Purpose**: Breakpoint hook and hamburger nav that ALL authenticated pages depend on

**⚠️ CRITICAL**: No home or research mobile work should ship without this phase complete

- [x] T002 [P] Implement SSR-safe `useMediaQuery(query: string)` hook with subscribe/cleanup in `apps/frontend/src/hooks/useMediaQuery.ts` using `MOBILE_MEDIA_QUERY` from `apps/frontend/src/lib/breakpoints.ts`
- [x] T003 [P] [US3] Create `NavDrawer.tsx` slide-out panel in `apps/frontend/src/components/NavDrawer.tsx` with backdrop overlay, Home/Chat/+ New Research links, close button, dismiss on overlay tap and Escape key, focus trap while open with focus returned to hamburger trigger on close, `aria-expanded`/`aria-controls` on trigger (FR-014)
- [x] T004 [US3] Refactor `apps/frontend/src/components/Navbar.tsx` so `md:` and up keeps current inline nav; below 768px shows logo, hamburger (opens NavDrawer), and profile avatar dropdown with sign-out unchanged
- [x] T005 [US3] Verify mobile nav renders on `/chat` via existing `AppLayout` in `apps/frontend/src/layouts/AppLayout.astro` — chat content layout unchanged, drawer links work at 375px viewport

**Checkpoint**: Hamburger nav works on `/`, `/research/{id}`, and `/chat` at viewports below 768px

---

## Phase 3: User Story 1 — Home Page on a Phone (Priority: P1) 🎯 MVP

**Goal**: Logged-in users can compose a new research idea and browse paginated sessions on phone-sized screens without horizontal page scroll.

**Independent Test**: Load `/` at 375px width, submit an idea, browse list tabs/pagination, open a session — no horizontal scroll, all controls reachable.

### Implementation for User Story 1

- [x] T006 [P] [US1] Update responsive page wrapper padding in `apps/frontend/src/pages/index.astro` (`px-4 py-6` default, `md:px-6 md:py-12`, keep `max-w-3xl mx-auto`)
- [x] T007 [P] [US1] Update `apps/frontend/src/components/ResearchCompose.tsx` for mobile: stack submit row vertically on narrow screens, `min-h-11` on "Research & draft" button, preserve empty validation and error states
- [x] T008 [US1] Update `apps/frontend/src/components/ResearchList.tsx` for mobile: show delete button always visible below `md` (`max-md:opacity-100`), enlarge pagination prev/next tap targets to `min-h-11`, make session row links full-row tap targets with `min-h-11`, allow tab/page-size row to wrap on narrow screens

**Checkpoint**: Home page fully usable at 320px–767px; desktop layout unchanged at 768px+

---

## Phase 4: User Story 2 — Research Workspace on a Phone (Priority: P1)

**Goal**: Users can follow agent progress, stop generation, switch Thread/Article tabs, read markdown, and use article controls on phone-sized screens.

**Independent Test**: Open `/research/{session_id}` at 375px, watch generation on Thread tab, see Article badge on completion, switch to Article tab (badge clears), use stop/retry/download/status controls.

### Implementation for User Story 2

- [x] T009 [P] [US2] Create `WorkspaceTabs.tsx` in `apps/frontend/src/components/WorkspaceTabs.tsx` with "Thread" | "Article" top tabs, optional badge dot on Article tab, `role="tablist"`/`role="tab"`/`aria-selected`, 44px min touch height
- [x] T010 [US2] Update `apps/frontend/src/components/ResearchWorkspace.tsx` to render mobile layout below 768px: header + WorkspaceTabs + single visible pane; at `md:` keep side-by-side flex layout; track `activeTab` and `articleHasUpdate`; set badge on `onDone`/`onArticle` only when `activeTab === 'thread'`; do not show badge when user is already on Article tab; clear badge when Article tab selected; keep both panes mounted across resize (covers T015 pane persistence)
- [x] T011 [P] [US2] Update `apps/frontend/src/components/ResearchChat.tsx` for mobile sticky footer (message input + "Stop generating") and `flex-1 overflow-y-auto` thread scroll area
- [x] T012 [P] [US2] Update `apps/frontend/src/components/ArticlePreview.tsx` to scope wide markdown (`pre`, `table`) with in-pane `overflow-x-auto` and prevent page-level horizontal scroll
- [x] T013 [P] [US2] Update `apps/frontend/src/components/ArticleControls.tsx` to wrap version/status/download controls on narrow widths with touch-friendly sizing
- [x] T014 [US2] Update full-height layout in `apps/frontend/src/pages/research/[sessionId].astro` for mobile browser chrome using `min-h-0 flex-1` or `dvh` pattern instead of brittle fixed viewport calc

**Checkpoint**: Full research workflow works on mobile; desktop two-panel layout preserved at 768px+

---

## Phase 5: User Story 4 — Resize Between Layouts (Priority: P3)

**Goal**: Rotating or resizing the viewport transitions smoothly between mobile and desktop layouts without losing session state.

**Independent Test**: Start on 375px Article tab during/after a run, widen to 1024px — side-by-side panels appear with content intact; narrow back to 375px — tabs return without reload.

### Implementation for User Story 4

- [x] T015 [US4] Verify pane mount persistence and stream continuity across breakpoint changes in `apps/frontend/src/components/ResearchWorkspace.tsx` per T010 — confirm no unmount of ResearchChat or ArticlePreview when toggling mobile/desktop
- [x] T016 [US4] Manual resize smoke test per `specs/006-mobile-pages/quickstart.md` "Manual Verification — Resize" section: research workspace at 767px↔768px (US4 scenario 1) and home page compose/list reflow at 767px↔768px (US4 scenario 2) without content loss or page reload

**Checkpoint**: SC-004 satisfied — no page reload required on viewport transition

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Unit tests, CSS polish, and end-to-end manual validation

- [x] T017 [P] Add Vitest tests for `useMediaQuery` matchMedia subscribe/cleanup and SSR default in `apps/frontend/tests/useMediaQuery.test.ts`
- [x] T018 [P] Add Vitest tests for article badge set/clear logic (extract pure helper in `apps/frontend/src/lib/workspaceTabState.ts` if needed) in `apps/frontend/tests/workspace-tabs.test.ts`
- [x] T019 [P] Add mobile overflow safeguards for `.article-prose` wide elements in `apps/frontend/src/styles/global.css` if not fully covered by component classes
- [x] T020 Run `make check` and complete full mobile quickstart checklist in `specs/006-mobile-pages/quickstart.md` at 320px, 375px, and 767px viewports, including the "Touch Target Spot Check (SC-003)" section
- [x] T021 [US1] [US2] Document SC-003 touch-target audit results in `specs/006-mobile-pages/checklists/touch-target-audit.md`: inventory all primary interactive controls on home and research pages at 375px, record pass/fail against 44×44px minimum, confirm ≥95% pass rate

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational / US3)**: Depends on T001 — **BLOCKS** all page-specific mobile work
- **Phase 3 (US1)**: Depends on Phase 2 completion
- **Phase 4 (US2)**: Depends on T002 (useMediaQuery) from Phase 2; independent of US1
- **Phase 5 (US4)**: Depends on Phase 4 (ResearchWorkspace responsive layout)
- **Phase 6 (Polish)**: Depends on Phases 3–5

### User Story Dependencies

| Story | Priority | Depends on | Can parallel with |
|-------|----------|------------|-------------------|
| US3 (Nav) | P2 | T001 | — (foundational, first) |
| US1 (Home) | P1 | Phase 2 | US2 after T002 done |
| US2 (Research) | P1 | T002 | US1 after Phase 2 |
| US4 (Resize) | P3 | US2 | — |

### Within Each User Story

- Constants/hook before components that consume them
- NavDrawer before Navbar refactor
- WorkspaceTabs before ResearchWorkspace integration
- Component updates before page layout updates
- Manual verification after implementation tasks in each checkpoint

### Parallel Opportunities

- **Phase 1**: T001 standalone
- **Phase 2**: T002 and T003 in parallel after T001
- **Phase 3**: T006 and T007 in parallel; then T008
- **Phase 4**: T009, T011, T012, T013 in parallel; then T010; then T014
- **Phase 6**: T017, T018, T019 in parallel; then T020, T021

---

## Parallel Example: User Story 2

```bash
# After T002 completes, launch independent component work:
Task T009: "Create WorkspaceTabs.tsx in apps/frontend/src/components/WorkspaceTabs.tsx"
Task T011: "Update ResearchChat.tsx sticky footer"
Task T012: "Update ArticlePreview.tsx overflow-x"
Task T013: "Update ArticleControls.tsx wrap controls"

# Then integrate:
Task T010: "Update ResearchWorkspace.tsx mobile tab layout"
Task T014: "Update [sessionId].astro height layout"
```

---

## Parallel Example: User Story 1 + User Story 2

```bash
# After Phase 2 completes, two developers can split:
Developer A: T006 → T007 → T008 (home page)
Developer B: T009 → T011/T012/T013 → T010 → T014 (research workspace)
```

---

## Implementation Strategy

### MVP First (US3 + US1)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: Foundational nav (T002–T005)
3. Complete Phase 3: US1 home page mobile (T006–T008)
4. **STOP and VALIDATE**: Home page usable on phone; nav works globally
5. Demo/submit PR for home + nav slice

### Full Feature Delivery

1. Setup + Foundational → mobile nav everywhere
2. US1 home page → validate at 375px
3. US2 research workspace → validate thread/article tabs + badge
4. US4 resize → validate 767↔768px transition
5. Polish → Vitest + quickstart checklist

### Suggested MVP Scope

**Minimum shippable increment**: Phase 1 + Phase 2 + Phase 3 (T001–T008) — mobile nav + home page. Research workspace mobile (US2) is the next increment.

---

## Notes

- No backend, migration, or API tasks — frontend-only feature
- Chat page (`/chat`) receives nav only; content layout overflow is a known out-of-scope limitation
- Delete button hover-only behavior is a pre-existing touch bug; T008 fixes it on mobile
- Use Tailwind `md:` (768px) consistently; JS hook uses 767px max-width per research.md R1
- `[P]` tasks touch different files — safe to parallelize
- Commit after each phase checkpoint
