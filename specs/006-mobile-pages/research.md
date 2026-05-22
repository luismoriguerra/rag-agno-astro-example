# Research: Mobile Home and Research Pages

**Feature**: 006-mobile-pages | **Date**: 2026-05-21

## R1 — Responsive breakpoint strategy

**Decision**: Use Tailwind CSS 4 `md:` prefix (min-width **768px**) as the single mobile/desktop boundary. JavaScript layout switching uses `matchMedia('(max-width: 767px)')` via a shared `useMediaQuery` hook.

**Rationale**: Matches clarified spec (FR-010). Aligns with Tailwind defaults already available in the project without custom config. `767px` max-width and `768px` min-width are complementary and avoid off-by-one gaps.

**Alternatives considered**:
- CSS-only tab visibility without JS — rejected because article-ready badge and default Thread tab need React state tied to generation events.
- Separate tablet breakpoint at 1024px — rejected; spec treats sub-768px as mobile only.

---

## R2 — Mobile research workspace layout

**Decision**: Below 768px, render **top tabs** ("Thread" | "Article") directly under the session title header. Only one pane visible at a time; both panes stay mounted to preserve streaming state.

**Rationale**: Clarified in spec Q1. Side-by-side at 40%/60% (current `w-[40%] min-w-[280px]`) overflows on phones. Top tabs keep chat input at bottom of Thread view without competing with bottom navigation.

**Alternatives considered**:
- Bottom tabs — rejected in clarification; conflicts with sticky chat input.
- Vertical stack — rejected; article pushes thread too far down during active runs.
- Swipe panes — rejected; higher implementation cost, weaker discoverability.

---

## R3 — Article-ready indicator behavior

**Decision**: When generation completes (`onDone`) or a new article chunk arrives (`onArticle`) while the user is on the Thread tab, set `articleHasUpdate = true` and show a visible dot/badge on the Article tab. Clear the badge when the user taps Article. Do **not** auto-switch tabs.

**Rationale**: Clarified in spec Q4. Preserves streaming visibility while signaling readiness.

**Alternatives considered**:
- Auto-switch to Article — rejected in clarification.
- Toast banner — rejected; adds transient UI noise during iterative refinements.

---

## R4 — Mobile navigation pattern

**Decision**: Refactor `Navbar.tsx` to show hamburger + logo + profile on `< md`. Links (Home, Chat, + New Research) move into a left slide-out drawer with backdrop overlay. Apply via `AppLayout` so `/`, `/research/*`, and `/chat` all inherit it.

**Rationale**: Clarified in spec Q3 and Q5. Current navbar crams five items inline (`gap-6`), which clips on 375px widths.

**Alternatives considered**:
- Icon-only inline bar — rejected in clarification; still crowded with + New Research label.
- Bottom nav — rejected; inconsistent with existing top-nav brand pattern.
- New npm drawer library — rejected; simple fixed-position panel sufficient; project already uses Radix for dialogs.

---

## R5 — Touch targets and hover-dependent controls

**Decision**: Primary buttons and nav controls use `min-h-11 min-w-11` (44px) on mobile. Delete action in `ResearchList` uses `max-md:opacity-100` so touch users can reach it without hover.

**Rationale**: SC-003 requires 44×44px targets. Current delete button is `opacity-0 group-hover:opacity-100`, which fails on touch devices today.

**Alternatives considered**:
- Swipe-to-delete — rejected; out of scope, changes interaction model.
- Long-press menu — rejected; unnecessary complexity.

---

## R6 — Wide markdown on narrow screens

**Decision**: Keep `.article-prose pre` and `table` with `overflow-x: auto` on a container scoped to the article pane. Page-level `overflow-x: hidden` on workspace root prevents horizontal page scroll (SC-001, SC-002).

**Rationale**: Spec edge case requires in-pane scroll only. Existing `.article-prose pre` already has `overflow-x: auto`.

**Alternatives considered**:
- Responsive table stacking — rejected; changes markdown rendering semantics.
- Font-size reduction — rejected; hurts readability without solving wide code lines.

---

## R7 — Testing approach

**Decision**:
- **Unit**: Vitest tests for `useMediaQuery` (mock `matchMedia`) and workspace badge clear logic.
- **Manual**: Quickstart checklist at 320px, 375px, 767px, 768px using browser devtools and one real device if available.
- **Automated E2E**: Optional Playwright viewport tests — not blocking for v1; document in quickstart.

**Rationale**: Constitution requires tests proportional to risk. Frontend-only CSS/layout changes have limited backend contract surface; manual viewport verification is the highest-signal check for this feature.

**Alternatives considered**:
- Visual regression (Percy/Chromatic) — rejected; not in project toolchain today.
- Astro component snapshot tests — rejected; poor signal for responsive layout.
