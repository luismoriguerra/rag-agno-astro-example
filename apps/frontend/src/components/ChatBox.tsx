import { useCallback, useEffect, useRef, useState } from "react";
import type { ChatMessage as ChatMessageType, ChatSessionDetail, ChatUiState, SearchSource } from "../services/chatTypes";
import ChatMessageBubble, { ThinkingIndicator } from "./ChatMessage";
import { AuthApiError } from "../lib/auth0";
import { getUrlParam, removeUrlParam } from "../lib/urlState";
import {
  createSession,
  deleteSession,
  getSession,
  logoutRedirectUrl,
  restoreActiveSession,
  stopRun,
  streamRun,
  submitMessage,
} from "../services/chatApi";

function emptyAssistant(): ChatMessageType {
  return {
    id: crypto.randomUUID(),
    role: "assistant",
    content: "",
    status: "streaming",
    sequence_index: 0,
    created_at: new Date().toISOString(),
    sources: [],
  };
}

function readAuthErrorFromUrl(): string | null {
  const authError = getUrlParam("auth_error");
  if (!authError) return null;
  removeUrlParam("auth_error");
  return authError;
}

export default function ChatBox() {
  const [uiState, setUiState] = useState<ChatUiState>("restoring");
  const [session, setSession] = useState<ChatSessionDetail | null>(null);
  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [draft, setDraft] = useState("");
  const [statusText, setStatusText] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const stopStreamRef = useRef<(() => void) | null>(null);
  const transcriptRef = useRef<HTMLDivElement>(null);

  const handleAuthError = useCallback((err: unknown) => {
    if (err instanceof AuthApiError) {
      setError(err.message);
    } else if (err instanceof Error) {
      setError(err.message);
    } else {
      setError("Unable to access your data. Sign in again or contact support.");
    }
    setUiState("failed");
  }, []);

  useEffect(() => {
    const urlError = readAuthErrorFromUrl();
    if (urlError) {
      setError(urlError);
      setUiState("failed");
      return;
    }

    void (async () => {
      try {
        const detail = await restoreActiveSession();
        setSession(detail);
        setMessages(detail.messages);
        setUiState(detail.messages.length ? "ready" : "empty");
      } catch (e) {
        handleAuthError(e);
      }
    })();
  }, [handleAuthError]);

  useEffect(() => {
    transcriptRef.current?.scrollTo({ top: transcriptRef.current.scrollHeight });
  }, [messages, statusText]);

  const beginStream = useCallback((runId: string, assistantId: string) => {
    setActiveRunId(runId);
    setUiState("thinking");
    stopStreamRef.current?.();
    stopStreamRef.current = streamRun(runId, {
      onThinking: (message) => {
        setStatusText(message);
        setUiState("thinking");
      },
      onToken: (text) => {
        setUiState("streaming");
        setStatusText("");
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId ? { ...m, content: m.content + text, status: "streaming" } : m,
          ),
        );
      },
      onSource: (source) => {
        setMessages((prev) =>
          prev.map((m) => {
            if (m.id !== assistantId) return m;
            const sources = [...(m.sources ?? []), source as SearchSource];
            return { ...m, sources };
          }),
        );
      },
      onDone: (status) => {
        setActiveRunId(null);
        setUiState(status === "stopped" ? "stopped" : "ready");
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? { ...m, status: status === "stopped" ? "stopped" : "complete" }
              : m,
          ),
        );
        setStatusText("");
      },
      onError: (message) => {
        setActiveRunId(null);
        setError(message);
        setUiState("failed");
        setMessages((prev) =>
          prev.map((m) => (m.id === assistantId ? { ...m, status: "failed" } : m)),
        );
      },
    });
  }, []);

  const handleSubmit = async () => {
    const content = draft.trim();
    if (!content || !session) return;
    if (uiState === "submitting" || uiState === "thinking" || uiState === "streaming") return;

    setError(null);
    setUiState("submitting");
    const assistant = emptyAssistant();
    const userMessage: ChatMessageType = {
      id: crypto.randomUUID(),
      role: "user",
      content,
      status: "complete",
      sequence_index: messages.length,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage, assistant]);
    setDraft("");

    try {
      const { message, run } = await submitMessage(session.id, content);
      setMessages((prev) =>
        prev.map((m, i) =>
          i === prev.length - 2
            ? { ...m, id: message.id, sequence_index: message.sequence_index }
            : m,
        ),
      );
      beginStream(run.id, assistant.id);
      setUiState("thinking");
    } catch (e) {
      setDraft(content);
      handleAuthError(e);
    }
  };

  const handleNewChat = async () => {
    stopStreamRef.current?.();
    setActiveRunId(null);
    setError(null);
    try {
      const created = await createSession();
      const detail = await getSession(created.id);
      setSession(detail);
      setMessages([]);
      setUiState("empty");
    } catch (e) {
      handleAuthError(e);
    }
  };

  const handleDelete = async () => {
    if (!session) return;
    stopStreamRef.current?.();
    try {
      await deleteSession(session.id);
      setMessages([]);
      setUiState("deleted");
      const detail = await restoreActiveSession();
      setSession(detail);
      setMessages(detail.messages);
      setUiState(detail.messages.length ? "ready" : "empty");
    } catch (e) {
      handleAuthError(e);
    }
  };

  const handleStop = async () => {
    if (!activeRunId) return;
    setUiState("stopping");
    try {
      await stopRun(activeRunId);
    } catch (e) {
      handleAuthError(e);
    }
  };

  const handleSignOut = () => {
    window.location.href = logoutRedirectUrl();
  };

  const busy =
    uiState === "submitting" ||
    uiState === "thinking" ||
    uiState === "streaming" ||
    uiState === "stopping";

  const showSignIn =
    error &&
    (error.includes("Sign in") ||
      error.includes("session expired") ||
      error.includes("expired"));

  return (
    <div className="flex flex-col h-full bg-white">
      <header className="px-5 py-3 border-b border-[#e5e2de] shrink-0 flex items-center justify-between">
        <h1 className="text-lg font-semibold text-[#1a1a1a]">Chat</h1>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => void handleNewChat()}
            disabled={uiState === "restoring"}
            className="text-xs font-medium text-[#6b7280] border border-[#e5e2de] px-3 py-1.5 rounded-lg hover:bg-[#f3f4f6] transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            New Chat
          </button>
          <button
            type="button"
            onClick={() => void handleStop()}
            disabled={!activeRunId || uiState === "stopping"}
            className="text-xs font-medium text-[#6b7280] border border-[#e5e2de] px-3 py-1.5 rounded-lg hover:bg-[#f3f4f6] transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Stop
          </button>
          <button
            type="button"
            onClick={() => void handleDelete()}
            disabled={!session || uiState === "restoring"}
            className="text-xs font-medium text-red-500 border border-[#e5e2de] px-3 py-1.5 rounded-lg hover:bg-red-50 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Delete
          </button>
          <button
            type="button"
            onClick={handleSignOut}
            className="text-xs font-medium text-[#6b7280] border border-[#e5e2de] px-3 py-1.5 rounded-lg hover:bg-[#f3f4f6] transition-colors"
          >
            Sign out
          </button>
        </div>
      </header>

      {error && (
        <div role="alert" className="px-5 py-2 bg-red-50 border-b border-red-200 text-sm text-red-700">
          {error}
          {showSignIn && (
            <>
              {" "}
              <a href="/api/auth/login" className="underline font-medium">Sign in again</a>
            </>
          )}
        </div>
      )}

      <div
        ref={transcriptRef}
        className="flex-1 overflow-y-auto px-5 py-4 space-y-4"
        aria-live="polite"
        aria-relevant="additions text"
      >
        {uiState === "restoring" && (
          <p className="text-sm text-[#6b7280] italic text-center py-8">Restoring conversation...</p>
        )}
        {uiState === "empty" && !messages.length && (
          <p className="text-sm text-[#6b7280] italic text-center py-8">Ask a question to search the public web.</p>
        )}
        {messages.map((m) => (
          <ChatMessageBubble
            key={m.id}
            role={m.role}
            content={m.content || (m.status === "streaming" ? "..." : "")}
            agentLabel="Assistant"
            sources={m.sources}
          />
        ))}
        {(uiState === "thinking" || uiState === "streaming") && statusText && (
          <ThinkingIndicator statusText={statusText} />
        )}
      </div>

      <form
        className="px-5 py-3 border-t border-[#e5e2de] flex gap-2 shrink-0 bg-white"
        onSubmit={(e) => {
          e.preventDefault();
          void handleSubmit();
        }}
      >
        <label className="sr-only" htmlFor="chat-input">
          Message
        </label>
        <input
          id="chat-input"
          type="text"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Ask a question..."
          disabled={uiState === "restoring" || !session}
          className="flex-1 border border-[#e5e2de] rounded-xl px-3.5 py-2 text-sm bg-[#f9fafb] text-[#1a1a1a] placeholder:text-[#b0ada8] focus:outline-none focus:ring-2 focus:ring-[#10a37f]/20 focus:border-[#10a37f] focus:bg-white"
        />
        <button
          type="submit"
          disabled={!draft.trim() || busy || !session}
          className="text-sm font-medium text-white bg-[#10a37f] hover:bg-[#0d8c6d] px-4 py-2 rounded-xl transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        >
          Send
        </button>
      </form>
    </div>
  );
}
