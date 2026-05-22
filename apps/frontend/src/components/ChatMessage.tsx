import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface ChatMessageProps {
  role: "user" | "assistant" | "system_status";
  content: string;
  reasoningContent?: string | null;
  agentLabel?: string;
  sources?: { title: string; url: string; rank: number }[];
}

function AgentAvatar() {
  return (
    <div className="w-7 h-7 rounded-full bg-[#10a37f] flex items-center justify-center shrink-0">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 2L2 7l10 5 10-5-10-5z" />
        <path d="M2 17l10 5 10-5" />
        <path d="M2 12l10 5 10-5" />
      </svg>
    </div>
  );
}

export function ReasoningTimeline({ content }: { content: string }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const lines = content.split("\n").filter((l) => l.trim());
  const preview = lines[0] ?? "";

  return (
    <div className="flex gap-3 mb-1">
      <div className="flex flex-col items-center w-7 shrink-0">
        <div className="w-px flex-1 bg-[#d1d5db]" />
      </div>
      <div className="flex-1 min-w-0">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-1.5 text-xs text-[#6b7280] hover:text-[#374151] transition-colors cursor-pointer select-none"
        >
          <svg
            width="12"
            height="12"
            viewBox="0 0 16 16"
            fill="currentColor"
            className={`transition-transform ${isExpanded ? "rotate-90" : ""}`}
          >
            <path d="M6 3l5 5-5 5V3z" />
          </svg>
          <span className="font-medium">Chain of thought</span>
          {!isExpanded && (
            <span className="text-[#9ca3af]">
              — {preview.substring(0, 60)}{preview.length > 60 ? "..." : ""}
            </span>
          )}
        </button>
        {isExpanded && (
          <div className="mt-2 ml-0.5 pl-3 border-l-2 border-[#e5e7eb]">
            {lines.map((line, i) => (
              <p key={i} className="text-xs text-[#6b7280] leading-relaxed py-0.5">
                {line}
              </p>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export function ThinkingIndicator({ statusText }: { statusText?: string }) {
  return (
    <div className="flex gap-3 items-start">
      <AgentAvatar />
      <div className="flex items-center gap-2 text-sm text-[#6b7280] pt-1">
        <span className="flex gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-[#10a37f] animate-bounce" style={{ animationDelay: "0s" }} />
          <span className="w-1.5 h-1.5 rounded-full bg-[#10a37f] animate-bounce" style={{ animationDelay: "0.15s" }} />
          <span className="w-1.5 h-1.5 rounded-full bg-[#10a37f] animate-bounce" style={{ animationDelay: "0.3s" }} />
        </span>
        {statusText && <span className="italic">{statusText}</span>}
      </div>
    </div>
  );
}

export default function ChatMessage({
  role,
  content,
  reasoningContent,
  agentLabel = "Assistant",
  sources,
}: ChatMessageProps) {
  if (role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] rounded-2xl rounded-br-md px-3.5 py-2.5 text-sm bg-[#44312a] text-white">
          <div className="whitespace-pre-wrap leading-relaxed">{content}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-0">
      {reasoningContent && <ReasoningTimeline content={reasoningContent} />}
      <div className="flex gap-3 items-start">
        <AgentAvatar />
        <div className="flex-1 min-w-0 text-sm text-[#1a1a1a]">
          <div className="text-xs font-medium text-[#10a37f] mb-1">{agentLabel}</div>
          <div className="chat-markdown">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {content || "..."}
            </ReactMarkdown>
          </div>
          {sources && sources.length > 0 && (
            <div className="mt-2 pt-2 border-t border-[#e5e7eb]">
              <p className="text-xs font-medium text-[#6b7280] mb-1">Sources</p>
              <ul className="space-y-0.5">
                {sources.map((s) => (
                  <li key={`${s.url}-${s.rank}`} className="text-xs">
                    <a
                      href={s.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-[#10a37f] hover:text-[#0d8c6d] underline underline-offset-2"
                    >
                      {s.title}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
