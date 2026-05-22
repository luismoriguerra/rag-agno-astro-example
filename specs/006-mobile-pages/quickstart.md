# Quickstart: Mobile Home and Research Pages

## Prerequisites

- Node.js 22
- Existing local dev environment from feature 005 (backend + frontend + Auth0)
- Browser devtools with responsive mode (or a physical phone on the same network)

## No New Environment Variables

Backend and frontend env files are unchanged. This feature is frontend-only.

## Local Run

```bash
make install
make dev
```

Open:

- Home: `http://localhost:4321/`
- Research session: `http://localhost:4321/research/{session_id}`
- Chat: `http://localhost:4321/chat`

## Automated Checks

```bash
cd apps/frontend && npm run check
cd apps/frontend && npm test
```

From repo root:

```bash
make check
```

## Manual Verification — Mobile Navigation

Set viewport to **375×812** (iPhone) or **320×568** (small phone).

1. Sign in if prompted.
2. Confirm top bar shows: Lumen logo, hamburger icon, profile avatar.
3. Tap hamburger → drawer opens with Home, Chat, + New Research.
4. Tap backdrop → drawer closes.
5. Open drawer → tap Chat → navigates to `/chat` with same hamburger nav.
6. Tap profile → sign-out option visible.

Repeat at **768px** width: confirm desktop inline nav returns (no hamburger).

## Manual Verification — Home Page Mobile

Viewport: **375px** width.

1. Compose card fills width; no horizontal page scroll.
2. Enter a topic → tap "Research & draft" → redirects to research workspace.
3. Return to home (via drawer or logo).
4. Confirm session list rows show title + status; delete icon visible without hover.
5. Switch Drafts / Published tabs.
6. Change page size and paginate if enough sessions exist.
7. Confirm empty state message when list is empty.

## Manual Verification — Research Workspace Mobile

Viewport: **375px** width. Open an active or completed session.

1. Confirm session title visible; **Thread** tab active by default.
2. Confirm Thread | Article tabs below title.
3. During generation: streaming visible; "Stop generating" reachable at bottom.
4. When generation completes while on Thread: **Article tab shows badge**; UI stays on Thread.
5. Tap Article tab → badge clears; article renders; controls (version, status, download) reachable.
6. Wide markdown (tables/code): scrolls horizontally inside article area only.
7. Send follow-up message from Thread tab → generation restarts; badge reappears on completion if still on Thread.
8. Tap Retry after a simulated error (if available).

## Manual Verification — Resize (SC-004)

**Research workspace (US4 scenario 1):**

1. Open research session at **375px** on Article tab during or after a run.
2. Widen viewport to **1024px** without reload.
3. Confirm side-by-side thread + article layout appears with content intact.
4. Narrow back to **375px** → tabs return; no lost messages or article content.

**Home page (US4 scenario 2):**

5. Open home page at **1024px** (desktop layout).
6. Narrow viewport to **767px** without reload.
7. Confirm compose area and research list reflow to single column with no content loss.
8. Widen back to **768px** → desktop layout returns.

## Breakpoint Spot Checks

| Width | Home | Research workspace | Nav |
|-------|------|-------------------|-----|
| 320px | No page horizontal scroll | Tabs usable | Drawer works |
| 767px | Mobile layout | Mobile tabs | Hamburger |
| 768px | Desktop layout | Side-by-side panels | Inline nav |

## Touch Target Spot Check (SC-003)

On 375px viewport, verify these controls are at least 44×44px tap area (record results in `specs/006-mobile-pages/checklists/touch-target-audit.md` for SC-003):

- Hamburger button
- Research & draft button
- Drafts / Published tab buttons
- Session list row link (full-row tap target)
- Thread / Article tabs
- Stop generating
- Pagination prev/next
- Delete session (when visible)
- Article status toggle and download (when article exists)

## Deployment

No Railway config changes. Deploy frontend service as usual:

```bash
make railway-deploy
```

Post-deploy: repeat navigation and home-page checks on production URL at 375px width.

## Troubleshooting

| Issue | Check |
|-------|-------|
| Hamburger not appearing | Viewport must be < 768px; hard refresh |
| Side-by-side still showing on phone | Tailwind `md:` classes; verify no cached CSS |
| Delete button missing on mobile | Should be always visible below `md` breakpoint |
| Badge never clears | Tap Article tab explicitly |
| Chat page layout broken | Expected — chat content layout is out of scope; nav should still work |
