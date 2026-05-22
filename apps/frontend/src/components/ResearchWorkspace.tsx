import { useCallback, useEffect, useRef, useState } from "react";
import ResearchChat from "./ResearchChat";
import ArticlePreview from "./ArticlePreview";
import ArticleControls from "./ArticleControls";
import WorkspaceTabs from "./WorkspaceTabs";
import {
  getResearchSession,
  streamResearchRun,
  sendResearchMessage,
  retryResearchSession,
  stopResearchRun,
} from "../services/researchApi";
import { setUrlParam, getUrlParam, removeUrlParam } from "../lib/urlState";
import { shouldSetArticleBadge, type WorkspaceTab } from "../lib/workspaceTabState";
import type { ResearchMessage, ResearchUiState } from "../services/researchTypes";

interface ResearchWorkspaceProps {
  sessionId: string;
}

export default function ResearchWorkspace({ sessionId }: ResearchWorkspaceProps) {
  const [uiState, setUiState] = useState<ResearchUiState>("loading");
  const [messages, setMessages] = useState<ResearchMessage[]>([]);
  const [articleMarkdown, setArticleMarkdown] = useState<string | null>(null);
  const [title, setTitle] = useState<string>("Research");
  const [statusText, setStatusText] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [articleId, setArticleId] = useState<string | null>(null);
  const [versionNumber, setVersionNumber] = useState(0);
  const [articleStatus, setArticleStatus] = useState<"draft" | "published">("draft");
  const [suggestedActions, setSuggestedActions] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState<WorkspaceTab>("thread");
  const [articleHasUpdate, setArticleHasUpdate] = useState(false);
  const activeTabRef = useRef<WorkspaceTab>("thread");
  const stopStreamRef = useRef<(() => void) | null>(null);
  const activeRunIdRef = useRef<string | null>(null);

  useEffect(() => {
    activeTabRef.current = activeTab;
  }, [activeTab]);

  const markArticleUpdated = useCallback(() => {
    if (shouldSetArticleBadge(activeTabRef.current)) {
      setArticleHasUpdate(true);
    }
  }, []);

  const handleTabChange = (tab: WorkspaceTab) => {
    setActiveTab(tab);
    if (tab === "article") {
      setArticleHasUpdate(false);
    }
  };

  const connectToStream = useCallback((runId: string) => {
    setUiState("thinking");
    stopStreamRef.current?.();
    activeRunIdRef.current = runId;
    setUrlParam("run_id", runId);

    stopStreamRef.current = streamResearchRun(runId, {
      onThinking: (message) => {
        setStatusText(message);
        setUiState("thinking");
      },
      onReasoning: () => { setUiState("streaming"); },
      onToken: () => { setUiState("streaming"); setStatusText(""); },
      onArticle: async (article) => {
        setArticleMarkdown(article.markdown);
        setTitle(article.title);
        setVersionNumber(article.version);
        setArticleStatus("draft");
        markArticleUpdated();
        if (!articleId) {
          try {
            const detail = await getResearchSession(sessionId);
            if (detail.article) setArticleId(detail.article.id);
          } catch { /* will get it on next load */ }
        }
      },
      onActions: (actions) => {
        setSuggestedActions(actions);
      },
      onDone: async () => {
        setUiState("done");
        setStatusText("");
        removeUrlParam("run_id");
        markArticleUpdated();
        try {
          const detail = await getResearchSession(sessionId);
          setMessages(detail.messages);
          if (detail.article) {
            setArticleId(detail.article.id);
            setVersionNumber(detail.article.current_version);
            if (detail.article.latest_version) {
              setArticleMarkdown(detail.article.latest_version.markdown_content);
              setArticleStatus(detail.article.latest_version.status);
            }
          }
          setTitle(detail.session.title);
        } catch { /* messages will load on next page visit */ }
      },
      onError: (message) => { setError(message); setUiState("error"); setStatusText(""); },
    });
  }, [sessionId, articleId, markArticleUpdated]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const detail = await getResearchSession(sessionId);
        if (cancelled) return;
        setTitle(detail.session.title);
        setMessages(detail.messages);
        if (detail.article) {
          setArticleId(detail.article.id);
          setVersionNumber(detail.article.current_version);
          if (detail.article.latest_version) {
            setArticleMarkdown(detail.article.latest_version.markdown_content);
            setArticleStatus(detail.article.latest_version.status);
          }
        }
        const activeRunId = getUrlParam("run_id") || detail.session.active_run_id;
        if (activeRunId) {
          connectToStream(activeRunId);
        } else if (detail.session.is_generating) {
          setUiState("thinking");
          setStatusText("Research in progress...");
        } else {
          setUiState(detail.messages.length > 0 ? "done" : "idle");
        }
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Failed to load session.");
        setUiState("error");
      }
    })();
    return () => { cancelled = true; stopStreamRef.current?.(); };
  }, [sessionId, connectToStream]);

  const threadPanelClass =
    activeTab === "thread" ? "flex flex-col overflow-hidden" : "hidden md:flex md:flex-col md:overflow-hidden";
  const articlePanelClass =
    activeTab === "article" ? "flex flex-col overflow-hidden" : "hidden md:flex md:flex-col md:overflow-hidden";

  return (
    <div className="flex flex-col h-full min-h-0">
      <div className="px-4 md:px-5 py-3 border-b border-[#e5e2de] bg-white flex-shrink-0">
        <h1 className="text-lg font-semibold text-[#1a1a1a] truncate">{title}</h1>
        {error && <p className="text-sm text-red-600 mt-1">{error}</p>}
      </div>

      <WorkspaceTabs
        activeTab={activeTab}
        articleHasUpdate={articleHasUpdate}
        onTabChange={handleTabChange}
      />

      <div className="flex flex-1 min-h-0 overflow-hidden flex-col md:flex-row">
        <div
          id="workspace-panel-thread"
          role="tabpanel"
          aria-labelledby="workspace-tab-thread"
          className={`${threadPanelClass} w-full md:w-[40%] md:min-w-[280px] md:max-w-none border-r border-[#e5e2de] bg-white min-h-0`}
        >
          <ResearchChat
            messages={messages}
            uiState={uiState}
            statusText={statusText}
            suggestedActions={suggestedActions}
            hideSectionHeader
            onSendMessage={async (content) => {
              try {
                setSuggestedActions([]);
                const res = await sendResearchMessage(sessionId, content);
                setMessages((prev) => [
                  ...prev,
                  {
                    id: crypto.randomUUID(),
                    role: "user",
                    content,
                    status: "complete",
                    sequence_index: prev.length,
                    created_at: new Date().toISOString(),
                  },
                ]);
                connectToStream(res.run_id);
              } catch (err) {
                setError(err instanceof Error ? err.message : "Failed to send message.");
              }
            }}
            onStop={async () => {
              stopStreamRef.current?.();
              if (activeRunIdRef.current) {
                try { await stopResearchRun(activeRunIdRef.current); } catch { /* best-effort */ }
              }
              removeUrlParam("run_id");
              setUiState("done");
              setStatusText("");
            }}
            onRetry={async () => {
              try {
                const res = await retryResearchSession(sessionId);
                connectToStream(res.run_id);
              } catch (err) {
                setError(err instanceof Error ? err.message : "Retry failed.");
              }
            }}
          />
        </div>

        <div
          id="workspace-panel-article"
          role="tabpanel"
          aria-labelledby="workspace-tab-article"
          className={`${articlePanelClass} flex-1 bg-[#faf9f7] min-h-0`}
        >
          {articleMarkdown && articleId && (
            <div className="px-4 md:px-5 py-2 border-b border-[#e5e2de] bg-white flex-shrink-0">
              <ArticleControls
                articleId={articleId}
                versionNumber={versionNumber}
                status={articleStatus}
                markdownContent={articleMarkdown}
                title={title}
                onStatusChange={(newStatus) => setArticleStatus(newStatus)}
              />
            </div>
          )}
          <div className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden">
            <ArticlePreview
              markdown={articleMarkdown}
              isLoading={uiState === "thinking" || uiState === "streaming"}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
