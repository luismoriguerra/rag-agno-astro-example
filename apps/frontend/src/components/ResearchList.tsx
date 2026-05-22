import { useCallback, useEffect, useState } from "react";
import { deleteResearchSession, listResearchSessions } from "../services/researchApi";
import { getUrlParam, setUrlParam } from "../lib/urlState";
import type {
  ArticleStatus,
  ResearchSessionListResponse,
  ResearchSessionSummary,
} from "../services/researchTypes";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

const PAGE_SIZE_OPTIONS = [5, 10, 20, 50] as const;

function TrashIcon() {
  return (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2m3 0v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6h14z" />
      <path d="M10 11v6M14 11v6" />
    </svg>
  );
}

function StatusBadge({ session }: { session: ResearchSessionSummary }) {
  if (session.is_generating) {
    return (
      <span className="inline-flex items-center gap-1 text-xs font-medium text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full">
        <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
        generating
      </span>
    );
  }
  if (session.status === "published") {
    return (
      <span className="text-xs font-medium text-green-700 bg-green-50 px-2 py-0.5 rounded-full">
        published
      </span>
    );
  }
  return (
    <span className="text-xs font-medium text-[#9aa8b8] bg-gray-100 px-2 py-0.5 rounded-full">
      draft
    </span>
  );
}

const TABS: { key: ArticleStatus; label: string }[] = [
  { key: "draft", label: "Drafts" },
  { key: "published", label: "Published" },
];

export default function ResearchList() {
  const [data, setData] = useState<ResearchSessionListResponse | null>(null);
  const [tab, setTab] = useState<ArticleStatus>(() => {
    const t = getUrlParam("tab");
    return t === "published" ? "published" : "draft";
  });
  const [page, setPage] = useState(() => {
    const p = Number(getUrlParam("page"));
    return p > 0 ? p : 1;
  });
  const [pageSize, setPageSize] = useState<number>(() => {
    const ps = Number(getUrlParam("page_size"));
    return PAGE_SIZE_OPTIONS.includes(ps as (typeof PAGE_SIZE_OPTIONS)[number]) ? ps : 10;
  });
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchSessions = useCallback(async (p: number, ps: number, status: ArticleStatus) => {
    setLoading(true);
    setError(null);
    try {
      const result = await listResearchSessions(p, ps, status);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load sessions.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    setUrlParam("tab", tab === "draft" ? null : tab);
    setUrlParam("page", page === 1 ? null : String(page));
    setUrlParam("page_size", pageSize === 10 ? null : String(pageSize));
    void fetchSessions(page, pageSize, tab);
  }, [page, pageSize, tab, fetchSessions]);

  const switchTab = (next: ArticleStatus) => {
    if (next === tab) return;
    setTab(next);
    setPage(1);
  };

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;

  const executeDelete = async (session: ResearchSessionSummary) => {
    setDeletingId(session.id);
    setError(null);
    try {
      await deleteResearchSession(session.id);
      const remainingOnPage = (data?.sessions.length ?? 1) - 1;
      if (remainingOnPage === 0 && page > 1) {
        setPage((p) => p - 1);
      } else {
        await fetchSessions(page, pageSize, tab);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete session.");
    } finally {
      setDeletingId(null);
    }
  };

  const emptyMessage =
    tab === "draft"
      ? "No drafts yet. Enter an idea above to start."
      : "No published articles yet.";

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <div className="flex gap-1" role="tablist">
          {TABS.map((t) => (
            <button
              key={t.key}
              role="tab"
              aria-selected={tab === t.key}
              data-testid={`tab-${t.key}`}
              onClick={() => switchTab(t.key)}
              className={`text-xs font-semibold uppercase tracking-wider px-3 py-1.5 rounded-md transition-colors ${
                tab === t.key
                  ? "bg-[#44312a] text-white"
                  : "text-[#6b7280] hover:bg-gray-100"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
        <label className="flex items-center gap-2 text-xs text-[#6b7280]">
          Show
          <select
            value={pageSize}
            onChange={(e) => { setPageSize(Number(e.target.value)); setPage(1); }}
            className="border border-[#e5e2de] rounded-md px-2 py-1 text-xs bg-white focus:outline-none focus:ring-1 focus:ring-[#44312a]/20"
          >
            {PAGE_SIZE_OPTIONS.map((opt) => (
              <option key={opt} value={opt}>{opt}</option>
            ))}
          </select>
        </label>
      </div>

      {error && (
        <p role="alert" className="mb-3 text-sm text-red-600">{error}</p>
      )}

      {loading && !data && (
        <p className="text-sm text-[#6b7280] italic">Loading sessions…</p>
      )}

      {!loading && error && !data && (
        <p className="text-sm text-red-600">{error}</p>
      )}

      {data && data.sessions.length === 0 && (
        <p className="text-sm text-[#6b7280] italic">{emptyMessage}</p>
      )}

      <ul className="space-y-1" data-testid="session-list">
        {data && data.sessions.map((s) => (
          <li key={s.id} data-testid={`session-row-${s.id}`}>
            <div className="flex items-center gap-2 px-3 py-2.5 rounded-lg hover:bg-white hover:shadow-sm transition-all group border border-transparent hover:border-[#e5e2de]">
              <a
                href={`/research/${s.id}`}
                className="flex-1 min-w-0 text-sm text-[#1a1a1a] truncate group-hover:text-[#44312a]"
              >
                {s.title}
              </a>
              <div className="flex items-center gap-2 shrink-0">
                <StatusBadge session={s} />
                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <button
                      type="button"
                      aria-label={`Delete ${s.title}`}
                      data-testid={`delete-session-${s.id}`}
                      disabled={deletingId === s.id || s.is_generating}
                      title={s.is_generating ? "Cannot delete while generating" : "Delete draft"}
                      className="p-1 rounded-md text-[#9aa8b8] hover:text-red-600 hover:bg-red-50 opacity-0 group-hover:opacity-100 focus:opacity-100 transition-all disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:text-[#9aa8b8] disabled:hover:bg-transparent"
                    >
                      <TrashIcon />
                    </button>
                  </AlertDialogTrigger>
                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle>Delete &ldquo;{s.title}&rdquo;?</AlertDialogTitle>
                      <AlertDialogDescription>
                        This will permanently remove the draft and cannot be undone.
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel>Cancel</AlertDialogCancel>
                      <AlertDialogAction
                        className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                        onClick={() => void executeDelete(s)}
                      >
                        Delete
                      </AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              </div>
            </div>
          </li>
        ))}
      </ul>

      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-4 pt-3 border-t border-[#e5e2de]">
          <button
            type="button"
            disabled={page <= 1 || loading}
            onClick={() => setPage((p) => p - 1)}
            className="text-xs text-[#6b7280] hover:text-[#1a1a1a] disabled:opacity-40 disabled:cursor-not-allowed"
          >
            ← Previous
          </button>
          <span className="text-xs text-[#6b7280]">
            Page {page} of {totalPages}
          </span>
          <button
            type="button"
            disabled={page >= totalPages || loading}
            onClick={() => setPage((p) => p + 1)}
            className="text-xs text-[#6b7280] hover:text-[#1a1a1a] disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}
