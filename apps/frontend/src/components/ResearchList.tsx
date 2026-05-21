import { useCallback, useEffect, useState } from "react";
import { listResearchSessions } from "../services/researchApi";
import type {
  ResearchSessionListResponse,
  ResearchSessionSummary,
} from "../services/researchTypes";

const PAGE_SIZE_OPTIONS = [5, 10, 20, 50] as const;

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

export default function ResearchList() {
  const [data, setData] = useState<ResearchSessionListResponse | null>(null);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState<number>(10);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSessions = useCallback(async (p: number, ps: number) => {
    setLoading(true);
    setError(null);
    try {
      const result = await listResearchSessions(p, ps);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load sessions.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchSessions(page, pageSize);
  }, [page, pageSize, fetchSessions]);

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;

  if (loading && !data) {
    return <p className="text-sm text-[#6b7280] italic">Loading sessions…</p>;
  }

  if (error) {
    return <p className="text-sm text-red-600">{error}</p>;
  }

  if (!data || data.sessions.length === 0) {
    return (
      <p className="text-sm text-[#6b7280] italic">
        No research sessions yet. Enter an idea above to start.
      </p>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-[#6b7280]">
          Drafts
        </h2>
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

      <ul className="space-y-1">
        {data.sessions.map((s) => (
          <li key={s.id}>
            <a
              href={`/research/${s.id}`}
              className="flex items-center justify-between px-3 py-2.5 rounded-lg hover:bg-white hover:shadow-sm transition-all group border border-transparent hover:border-[#e5e2de]"
            >
              <span className="text-sm text-[#1a1a1a] truncate max-w-[70%] group-hover:text-[#44312a]">
                {s.title}
              </span>
              <StatusBadge session={s} />
            </a>
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
