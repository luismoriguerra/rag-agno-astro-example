import { shouldShowArticleBadge, type WorkspaceTab } from "../lib/workspaceTabState";

interface WorkspaceTabsProps {
  activeTab: WorkspaceTab;
  articleHasUpdate: boolean;
  onTabChange: (tab: WorkspaceTab) => void;
}

export default function WorkspaceTabs({
  activeTab,
  articleHasUpdate,
  onTabChange,
}: WorkspaceTabsProps) {
  const showBadge = shouldShowArticleBadge(activeTab, articleHasUpdate);

  const tabClass = (tab: WorkspaceTab) =>
    `relative flex-1 min-h-11 px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
      activeTab === tab
        ? "bg-[#44312a] text-white"
        : "text-[#6b7280] hover:bg-[#f5f3f0]"
    }`;

  return (
    <div
      role="tablist"
      aria-label="Research workspace views"
      className="flex gap-1 px-4 py-2 border-b border-[#e5e2de] bg-white md:hidden shrink-0"
    >
      <button
        type="button"
        role="tab"
        id="workspace-tab-thread"
        aria-selected={activeTab === "thread"}
        aria-controls="workspace-panel-thread"
        className={tabClass("thread")}
        onClick={() => onTabChange("thread")}
      >
        Thread
      </button>
      <button
        type="button"
        role="tab"
        id="workspace-tab-article"
        aria-selected={activeTab === "article"}
        aria-controls="workspace-panel-article"
        aria-label={showBadge ? "Article, updated" : "Article"}
        className={tabClass("article")}
        onClick={() => onTabChange("article")}
      >
        Article
        {showBadge && (
          <span
            className="absolute top-2 right-3 w-2 h-2 rounded-full bg-[#10a37f]"
            aria-hidden="true"
          />
        )}
      </button>
    </div>
  );
}
