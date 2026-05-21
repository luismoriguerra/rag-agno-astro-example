import { useCallback, useEffect, useRef, useState } from "react";
import ResearchChat from "./ResearchChat";
import ArticlePreview from "./ArticlePreview";
import ArticleControls from "./ArticleControls";
import {
  getResearchSession,
  streamResearchRun,
  sendResearchMessage,
  retryResearchSession,
} from "../services/researchApi";
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
  const stopStreamRef = useRef<(() => void) | null>(null);

  const connectToStream = useCallback((runId: string) => {
    setUiState("thinking");
    stopStreamRef.current?.();
    stopStreamRef.current = streamResearchRun(runId, {
      onThinking: (message) => {
        setStatusText(message);
        setUiState("thinking");
      },
      onReasoning: () => { setUiState("streaming"); },
      onToken: () => { setUiState("streaming"); setStatusText(""); },
      onArticle: (article) => {
        setArticleMarkdown(article.markdown);
        setTitle(article.title);
        setVersionNumber(article.version);
        setArticleStatus("draft");
      },
      onDone: () => { setUiState("done"); setStatusText(""); },
      onError: (message) => { setError(message); setUiState("error"); setStatusText(""); },
    });
  }, []);

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
        const runIdFromUrl = new URLSearchParams(window.location.search).get("run_id");
        if (runIdFromUrl) {
          connectToStream(runIdFromUrl);
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

  return (
    <div className="flex flex-col h-full">
      <div className="px-5 py-3 border-b border-[#e5e2de] bg-white flex-shrink-0">
        <h1 className="text-lg font-semibold text-[#1a1a1a] truncate">{title}</h1>
        {error && <p className="text-sm text-red-600 mt-1">{error}</p>}
      </div>

      <div className="flex flex-1 overflow-hidden">
        <div className="w-[40%] min-w-[280px] border-r border-[#e5e2de] flex flex-col overflow-hidden bg-white">
          <ResearchChat
            messages={messages}
            uiState={uiState}
            statusText={statusText}
            onSendMessage={async (content) => {
              try {
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
            onStop={() => stopStreamRef.current?.()}
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

        <div className="flex-1 flex flex-col overflow-hidden bg-[#faf9f7]">
          {articleMarkdown && articleId && (
            <div className="px-5 py-2 border-b border-[#e5e2de] bg-white flex-shrink-0">
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
          <div className="flex-1 overflow-y-auto">
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
