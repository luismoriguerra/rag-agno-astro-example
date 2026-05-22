# Mobile UI Contract

Extends [005-research-generator research-ui.md](../../005-research-generator/contracts/research-ui.md) with responsive rules for viewports below 768px. Backend API contracts are unchanged.

## Global Rules

| Rule | Value |
|------|-------|
| Mobile breakpoint | `< 768px` viewport width |
| Desktop breakpoint | `≥ 768px` (existing layouts preserved) |
| Minimum touch target | 44×44 CSS pixels for primary interactive controls |
| Horizontal page scroll | Forbidden on mobile for home and research pages |
| Auth | Unchanged — Auth0 redirect for unauthenticated users |

---

## Shared Navigation (all authenticated pages)

Applies to: `/`, `/research/{sessionId}`, `/chat`, any page using `AppLayout` + `Navbar`.

### Desktop (≥ 768px)

Unchanged from current implementation: inline Lumen logo, Home, Chat, + New Research, profile avatar with dropdown.

### Mobile (< 768px)

**Top bar** (left → right):
1. Lumen logo (links to `/`)
2. Spacer
3. Hamburger icon button (opens drawer)
4. Profile avatar button (opens account dropdown)

**Nav drawer** (slide-out from left):
- Home → `/`
- Chat → `/chat`
- + New Research → `/` (compose area)
- Close control or backdrop tap dismisses drawer
- Escape key dismisses drawer

**Profile menu** (unchanged behavior):
- Email display (if available)
- Sign out → `/api/auth/logout`

**States**:
| State | Behavior |
|-------|----------|
| Drawer closed | Only top bar visible |
| Drawer open | Backdrop overlay; page content inert until dismissed |
| Profile menu open | Dropdown below avatar; independent of drawer |

---

## Home Page (`/`)

### Desktop (≥ 768px)

Unchanged: centered `max-w-3xl` column, compose card, research list below.

### Mobile (< 768px)

**Layout**: Single column, full width with horizontal padding (`px-4` minimum).

**Compose area**:
- Heading and textarea full width
- Submit button full width or right-aligned with minimum 44px height
- "Live web sources" hint may wrap below button on narrow screens

**Research list**:
- Drafts / Published tabs remain visible
- Page size selector remains reachable (may wrap to second line)
- Session rows: title truncates; status badge visible; delete action **always visible** (not hover-only)
- Pagination controls with enlarged tap areas

**States**: Same as desktop (loading, empty, error, submitting) — see 005 research-ui contract.

---

## Research Workspace (`/research/{sessionId}`)

### Desktop (≥ 768px)

Unchanged: session title header, 40% left chat panel, 60% right article panel, article controls bar when article exists.

### Mobile (< 768px)

**Header**:
- Session title (truncated with ellipsis)
- Error message below title if present

**Workspace tabs** (directly below header):
| Tab | Label | Default |
|-----|-------|---------|
| Thread | "Thread" | Active on load |
| Article | "Article" | Shows badge when new content ready |

**Tab badge rules**:
- Show badge on Article tab when generation completes or article updates while user is on Thread tab
- Clear badge when user taps Article tab
- Do not auto-switch to Article tab on completion

**Thread tab content**:
- Full research chat thread (messages, streaming, reasoning)
- Sticky bottom area: message input + Stop generating (when active)
- Retry on error messages

**Article tab content**:
- Article controls bar (version, status toggle, download) when article exists
- Rendered markdown body with in-pane horizontal scroll for wide tables/code
- Loading placeholder when agent is running and no article yet

**Pane visibility**: Only one tab pane visible at a time; both panes remain mounted to preserve stream state.

**States** (mobile mapping):

| State | Thread tab | Article tab |
|-------|------------|-------------|
| Initial load | Messages loaded | Latest article or placeholder |
| Agent running | Streaming + Stop | Previous article or loading |
| Agent complete | Updated messages | Updated article; badge if user stayed on Thread; no badge if user already on Article |
| Agent failed | Error + Retry | Previous article or empty |
| Agent stopped | Stop confirmation | Previous article or empty |

---

## Chat Page (`/chat`)

| Area | Mobile behavior |
|------|-----------------|
| Navigation | Same hamburger contract as above |
| Chat content layout | **Out of scope** — desktop layout may overflow; not modified in this feature |

---

## Resize Behavior

| Transition | Expected behavior |
|------------|-------------------|
| Mobile → Desktop | Two-panel side-by-side appears; tab UI hidden; messages, article, and run state preserved |
| Desktop → Mobile | Single-column with tabs; default or last active tab shown; no page reload |

---

## Accessibility (implementation guidance)

- Hamburger button: `aria-expanded`, `aria-controls` pointing to drawer panel
- Drawer: focus trap while open; return focus to hamburger on close
- Workspace tabs: `role="tablist"`, `role="tab"`, `aria-selected`, `aria-controls` for panels
- Badge: `aria-label` on Article tab when update pending (e.g., "Article updated")
