import { useState } from "react";
import { updateArticleStatus } from "../services/researchApi";

interface ArticleControlsProps {
  articleId: string;
  versionNumber: number;
  status: "draft" | "published";
  markdownContent: string;
  title: string;
  onStatusChange: (status: "draft" | "published") => void;
}

function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .substring(0, 80) || "article";
}

export default function ArticleControls({
  articleId,
  versionNumber,
  status,
  markdownContent,
  title,
  onStatusChange,
}: ArticleControlsProps) {
  const [updating, setUpdating] = useState(false);

  const handleToggleStatus = async () => {
    const newStatus = status === "draft" ? "published" : "draft";
    setUpdating(true);
    try {
      await updateArticleStatus(articleId, newStatus);
      onStatusChange(newStatus);
    } catch {
      // silently fail
    } finally {
      setUpdating(false);
    }
  };

  const handleDownload = () => {
    const blob = new Blob([markdownContent], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${slugify(title)}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-wrap items-center gap-2 md:gap-3">
      <span className="text-xs font-semibold text-[#6b7280] bg-[#f5f3f0] px-2 py-1 rounded min-h-11 flex items-center">
        v{versionNumber}
      </span>

      <button
        onClick={() => void handleToggleStatus()}
        disabled={updating}
        className={`min-h-11 text-xs font-medium px-3 py-1 rounded-lg transition-colors disabled:opacity-50 ${
          status === "published"
            ? "bg-green-50 text-green-700 hover:bg-green-100"
            : "bg-[#44312a] text-white hover:bg-[#5a4238]"
        }`}
      >
        {status === "published" ? "Published" : "Publish"}
      </button>

      <button
        onClick={handleDownload}
        className="min-h-11 text-xs font-medium text-[#6b7280] border border-[#e5e2de] px-3 py-1 rounded-lg hover:bg-[#f5f3f0] transition-colors flex items-center gap-1"
      >
        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3" />
        </svg>
        .md
      </button>
    </div>
  );
}
