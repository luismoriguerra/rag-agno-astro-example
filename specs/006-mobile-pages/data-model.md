# Data Model: Mobile Home and Research Pages

## Overview

This feature introduces **no PostgreSQL entities, API payloads, or persistence changes**. All state is ephemeral client-side UI state in React islands. Existing research session, message, and article entities from feature 005 are consumed unchanged.

## Client UI State

### NavDrawerState (Navbar)

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `isOpen` | boolean | `false` | Whether the hamburger slide-out drawer is visible |
| `isProfileMenuOpen` | boolean | `false` | Existing profile dropdown; independent of nav drawer |

**Transitions**:
- Open drawer: hamburger tap → `isOpen = true`
- Close drawer: overlay tap, close button, Escape, or navigation link tap → `isOpen = false`
- Opening profile menu does not require closing drawer (orthogonal)

---

### WorkspaceMobileState (ResearchWorkspace)

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `activeTab` | `'thread' \| 'article'` | `'thread'` | Mobile-only tab selection below 768px |
| `articleHasUpdate` | boolean | `false` | Badge indicator on Article tab |

**Transitions**:
- User taps Article tab → `activeTab = 'article'`, `articleHasUpdate = false`
- User taps Thread tab → `activeTab = 'thread'`
- Agent emits article / run completes while `activeTab === 'thread'` → `articleHasUpdate = true`
- User already on Article tab when update arrives → `articleHasUpdate` stays `false`
- Viewport widens to ≥768px → tab UI hidden; both panels visible; `activeTab` preserved but unused until narrow again

---

### ResponsiveLayoutContext

| Signal | Source | Threshold |
|--------|--------|-----------|
| `isMobile` | `useMediaQuery('(max-width: 767px)')` | `< 768px` |

**Notes**:
- Not persisted to URL or localStorage.
- Resize across breakpoint does not reset session messages, article markdown, or active run streams (FR-010, SC-004).

## Validation Rules

- `activeTab` MUST NOT interrupt an active SSE stream when changed.
- `articleHasUpdate` MUST clear only on explicit Article tab selection, not on resize to desktop.
- Nav drawer MUST close before route navigation completes to avoid stale overlay on next page.

## Relationships to Existing Entities

| Existing entity | Mobile feature usage |
|-----------------|---------------------|
| `ResearchSession` | Title shown in workspace header (truncated on narrow screens) |
| `ResearchMessage` | Rendered in Thread tab / left panel — unchanged data |
| `ResearchArticle` | Rendered in Article tab / right panel — unchanged data |
| Auth0 user profile | Avatar in navbar — unchanged |

## Out of Scope

- No new URL query parameters for tab state.
- No server-side mobile detection or separate API responses.
- No chat page layout state (chat content remains desktop-oriented).
