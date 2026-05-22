export type WorkspaceTab = "thread" | "article";

export function shouldSetArticleBadge(activeTab: WorkspaceTab): boolean {
  return activeTab === "thread";
}

export function shouldShowArticleBadge(
  activeTab: WorkspaceTab,
  articleHasUpdate: boolean,
): boolean {
  return activeTab === "thread" && articleHasUpdate;
}
