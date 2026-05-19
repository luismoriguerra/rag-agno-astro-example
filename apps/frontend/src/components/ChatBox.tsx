import { useCallback, useEffect, useRef, useState } from "react";
import type { ChatMessage, ChatSessionDetail, ChatUiState, SearchSource } from "../services/chatTypes";
import {
  createSession,
  deleteSession,
  getSession,
  restoreActiveSession,
  stopRun,
  streamRun,
  submitMessage,
} from "../services/chatApi";

function emptyAssistant(): ChatMessage {
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

export default function ChatBox() {
  const [uiState, setUiState] = useState<ChatUiState>("restoring");
  const [session, setSession] = useState<ChatSessionDetail | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [statusText, setStatusText] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const stopStreamRef = useRef<(() => void) | null>(null);
  const transcriptRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    void (async () => {
      try {
        const detail = await restoreActiveSession();
        setSession(detail);
        setMessages(detail.messages);
        setUiState(detail.messages.length ? "ready" : "empty");
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to restore chat.");
        setUiState("failed");
      }
    })();
  }, []);

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
    const userMessage: ChatMessage = {
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
      setError(e instanceof Error ? e.message : "Failed to send message.");
      setUiState("failed");
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
      setError(e instanceof Error ? e.message : "Failed to start new chat.");
      setUiState("failed");
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
      setError(e instanceof Error ? e.message : "Failed to delete session.");
      setUiState("failed");
    }
  };

  const handleStop = async () => {
    if (!activeRunId) return;
    setUiState("stopping");
    try {
      await stopRun(activeRunId);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to stop response.");
    }
  };

  const busy =
    uiState === "submitting" ||
    uiState === "thinking" ||
    uiState === "streaming" ||
    uiState === "stopping";

  return (
    <div className="chat-shell">
      <header className="chat-header">
        <h1>Chat</h1>
        <div className="chat-actions">
          <button type="button" onClick={() => void handleNewChat()} disabled={uiState === "restoring"}>
            New Chat
          </button>
          <button
            type="button"
            onClick={() => void handleStop()}
            disabled={!activeRunId || uiState === "stopping"}
          >
            Stop
          </button>
          <button
            type="button"
            onClick={() => void handleDelete()}
            disabled={!session || uiState === "restoring"}
          >
            Delete active session
          </button>
        </div>
      </header>

      {error && (
        <p role="alert" className="chat-error">
          {error}
        </p>
      )}

      <div
        ref={transcriptRef}
        className="chat-transcript"
        aria-live="polite"
        aria-relevant="additions text"
      >
        {uiState === "restoring" && <p className="chat-muted">Restoring conversation…</p>}
        {uiState === "empty" && !messages.length && (
          <p className="chat-muted">Ask a question to search the public web.</p>
        )}
        {messages.map((m) => (
          <article key={m.id} className={`chat-message chat-message-${m.role}`}>
            <strong>{m.role === "user" ? "You" : "Assistant"}</strong>
            <p>{m.content || (m.status === "streaming" ? "…" : "")}</p>
            {m.sources && m.sources.length > 0 && (
              <ul className="chat-sources">
                {m.sources.map((s) => (
                  <li key={`${s.url}-${s.rank}`}>
                    <a href={s.url} target="_blank" rel="noreferrer">
                      {s.title}
                    </a>
                  </li>
                ))}
              </ul>
            )}
          </article>
        ))}
        {statusText && <p className="chat-status">{statusText}</p>}
      </div>

      <form
        className="chat-composer"
        onSubmit={(e) => {
          e.preventDefault();
          void handleSubmit();
        }}
      >
        <label className="sr-only" htmlFor="chat-input">
          Message
        </label>
        <textarea
          id="chat-input"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Ask a question…"
          rows={3}
          disabled={uiState === "restoring" || !session}
        />
        <button type="submit" disabled={!draft.trim() || busy || !session}>
          Send
        </button>
      </form>
    </div>
  );
}
