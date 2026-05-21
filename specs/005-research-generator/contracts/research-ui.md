# Research UI Contract

## Pages

### Home Page (`/` — `index.astro`)

**Layout**: Full-width, authenticated-only.

**Sections** (top to bottom):
1. **Compose area** — always visible
   - "New idea" label
   - Textarea (placeholder: research topic example)
   - "Research & draft" submit button (disabled when empty)
2. **Research list** — paginated table/list
   - Columns: display title, status badge (draft/published/generating)
   - Rows link to `/research/{session_id}`
   - Page size dropdown: 5, 10, 20, 50 (default 10)
   - Page navigation controls
   - Empty state: message when no sessions exist

**States**:
| State | Behavior |
|-------|----------|
| Loading | Skeleton/spinner while session list loads |
| Empty list | "No research sessions yet. Enter an idea above to start." |
| Submitting | Button shows loading, disabled until API responds |
| Error on submit | Inline error message above the button |
| Unauthenticated | Redirect to Auth0 sign-in (middleware) |

---

### Research Workspace (`/research/[sessionId]` — `[sessionId].astro`)

**Layout**: Full-width two-panel, no sidebar.

**Left Panel — Research Chat**:
- Message thread (user + agent messages)
- Agent messages include full reasoning/chain-of-thought
- Streaming indicator during active run
- Input area at bottom (disabled during active run, with Stop button)
- Retry button on error messages
- Messages ordered by `sequence_index`

**Right Panel — Article Preview**:
- **Header controls**:
  - Version badge (e.g., "v3")
  - Status toggle (draft ↔ published)
  - Download `.md` button
- **Body**: rendered markdown (read-only)
- Loading/placeholder state until first article exists

**States**:
| State | Left Panel | Right Panel |
|-------|------------|-------------|
| Initial load | Existing messages loaded | Latest article version or loading placeholder |
| Agent running | Streaming reasoning + tokens | Loading (first run) or previous article (refinement) |
| Agent complete | New messages appended | Article updated to latest version |
| Agent failed | Error message + Retry button | Previous article or empty |
| Agent stopped | Stop confirmation | Previous article or empty |
| No article yet | Messages only | Loading/placeholder text |

**Article Panel Controls**:
| Control | Behavior |
|---------|----------|
| Version badge | Read-only "v{N}" showing `current_version` |
| Status toggle | Switches between draft/published via `PATCH /api/research/articles/{id}/status` |
| Download `.md` | Client-side Blob download; filename = `{title-slug}.md` |

**Markdown Rendering** (FR-013):
- Headings (h1–h6)
- Code blocks with syntax highlighting
- Tables (GFM)
- Lists (ordered + unordered)
- Blockquotes
- Inline code
- Links (open in new tab)
- ASCII art/diagrams (rendered in `<pre>` blocks)
- Images (if present in markdown)
