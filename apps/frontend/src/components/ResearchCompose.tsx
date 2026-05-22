import { useState } from "react";
import { createResearchSession } from "../services/researchApi";

export default function ResearchCompose() {
  const [idea, setIdea] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = idea.trim();
    if (!trimmed || submitting) return;

    setError(null);
    setSubmitting(true);

    try {
      const result = await createResearchSession(trimmed);
      window.location.href = `/research/${result.session_id}?run_id=${result.run_id}`;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
      setSubmitting(false);
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-[#e5e2de] p-5 md:p-8 shadow-sm">
      <h1 className="font-serif text-3xl font-normal text-[#1a1a1a] mb-2">
        Turn an idea into a researched draft.
      </h1>
      <p className="text-[#6b7280] text-sm mb-6 max-w-lg">
        Describe what you want to write about. Lumen searches the web, synthesizes
        the findings, and hands you a draft you can edit or refine with prompts.
      </p>

      <form onSubmit={(e) => void handleSubmit(e)}>
        <textarea
          value={idea}
          onChange={(e) => setIdea(e.target.value)}
          placeholder="e.g. The state of small modular reactors in 2026 — who's building, what's shipped, what's blocked."
          rows={3}
          disabled={submitting}
          className="w-full rounded-xl border border-[#e5e2de] bg-white px-4 py-3 text-sm text-[#1a1a1a] placeholder:text-[#b0ada8] focus:outline-none focus:ring-2 focus:ring-[#44312a]/20 focus:border-[#44312a] resize-none disabled:opacity-50"
        />

        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mt-4">
          <span className="text-xs text-[#b0ada8] flex items-center gap-1 order-2 sm:order-1">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <circle cx="12" cy="12" r="10" />
              <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
            </svg>
            Live web sources via AI
          </span>

          <button
            type="submit"
            disabled={!idea.trim() || submitting}
            className="order-1 sm:order-2 w-full sm:w-auto inline-flex items-center justify-center gap-2 min-h-11 bg-[#44312a] text-white text-sm font-medium px-5 py-2.5 rounded-xl hover:bg-[#5a4238] transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <circle cx="11" cy="11" r="8" />
              <path d="m21 21-4.35-4.35" />
            </svg>
            {submitting ? "Starting…" : "Research & draft"}
          </button>
        </div>

        {error && (
          <p role="alert" className="mt-3 text-sm text-red-600">
            {error}
          </p>
        )}
      </form>
    </div>
  );
}
