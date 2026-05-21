import { useState } from "react";

export type MessageRole = "user" | "assistant";
export type MessageStatus = "complete" | "streaming" | "stopped" | "failed";

export interface ResearchChatMessageProps {
  role: MessageRole;
  content: string;
  reasoningContent?: string | null;
  status: MessageStatus;
}

function GeneratingIndicator() {
  return (
    <span className="generating-indicator" style={{ display: "inline-flex", alignItems: "center", gap: "0.25rem" }}>
      <span style={{ animation: "pulse 1.2s ease-in-out infinite", opacity: 0.6 }}>●</span>
      <span style={{ fontSize: "0.85rem", color: "#6b7280" }}>Generating…</span>
      <style>{`@keyframes pulse { 0%,100% { opacity: 0.3; } 50% { opacity: 1; } }`}</style>
    </span>
  );
}

function ReasoningBlock({ content }: { content: string }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <details
      open={expanded}
      onToggle={(e) => setExpanded((e.target as HTMLDetailsElement).open)}
      style={{
        marginBottom: "0.5rem",
        borderLeft: "3px solid #d1d5db",
        paddingLeft: "0.75rem",
      }}
    >
      <summary
        style={{
          cursor: "pointer",
          fontSize: "0.8rem",
          color: "#6b7280",
          userSelect: "none",
        }}
      >
        {expanded ? "Hide reasoning" : "Show reasoning"}
      </summary>
      <pre
        style={{
          whiteSpace: "pre-wrap",
          fontSize: "0.8rem",
          color: "#6b7280",
          margin: "0.25rem 0 0",
          fontFamily: "inherit",
        }}
      >
        {content}
      </pre>
    </details>
  );
}

export default function ResearchChatMessage({
  role,
  content,
  reasoningContent,
  status,
}: ResearchChatMessageProps) {
  const isError = status === "failed";
  const isGenerating = status === "streaming";

  return (
    <article
      className={`research-chat-message research-chat-message-${role}`}
      style={{
        padding: "0.75rem 1rem",
        marginBottom: "0.5rem",
        borderRadius: "0.5rem",
        background: role === "user" ? "#f3f4f6" : "#fff",
        border: isError ? "1px solid #fca5a5" : "1px solid #e5e7eb",
        ...(isError && { backgroundColor: "#fef2f2" }),
      }}
    >
      <div
        style={{
          fontSize: "0.75rem",
          fontWeight: 600,
          color: isError ? "#dc2626" : "#6b7280",
          marginBottom: "0.25rem",
          display: "flex",
          alignItems: "center",
          gap: "0.35rem",
        }}
      >
        {isError && <span aria-hidden="true">⚠</span>}
        {role === "user" ? "You" : "Research Agent"}
      </div>

      {role === "assistant" && reasoningContent && (
        <ReasoningBlock content={reasoningContent} />
      )}

      {content ? (
        <div style={{ whiteSpace: "pre-wrap", lineHeight: 1.6 }}>{content}</div>
      ) : isGenerating ? (
        <GeneratingIndicator />
      ) : null}

      {isError && !content && (
        <div style={{ color: "#dc2626", fontSize: "0.85rem" }}>
          Something went wrong. Please try again.
        </div>
      )}
    </article>
  );
}
