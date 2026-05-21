import { useEffect, useRef, useState } from "react";
import type { ResearchMessage, ResearchUiState } from "../services/researchTypes";

interface ResearchChatProps {
  messages: ResearchMessage[];
  uiState: ResearchUiState;
  statusText: string;
  onSendMessage?: (content: string) => void | Promise<void>;
  onStop?: () => void;
  onRetry?: () => void;
}

export default function ResearchChat({
  messages,
  uiState,
  statusText,
  onSendMessage,
  onStop,
  onRetry,
}: ResearchChatProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [input, setInput] = useState("");
  const isRunning = uiState === "thinking" || uiState === "streaming";

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, statusText]);

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed || isRunning) return;
    onSendMessage?.(trimmed);
    setInput("");
  };

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-3 border-b border-[#e5e2de] flex-shrink-0">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-[#6b7280]">
          Research Thread
        </h2>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
        {messages.length === 0 && uiState === "loading" && (
          <p className="text-sm text-[#6b7280] italic">Loading conversation...</p>
        )}
        {messages.length === 0 && uiState === "idle" && (
          <p className="text-sm text-[#6b7280] italic">No messages yet.</p>
        )}

        {messages.map((m) => (
          <div
            key={m.id}
            className={`rounded-lg px-3 py-2.5 text-sm ${
              m.role === "user"
                ? "bg-[#f0eeeb] text-[#1a1a1a]"
                : "bg-white border border-[#e5e2de] text-[#1a1a1a]"
            }`}
          >
            <div className={`text-xs font-semibold mb-1 ${
              m.role === "user" ? "text-[#44312a]" : "text-green-700"
            }`}>
              {m.role === "user" ? "You" : "Research Agent"}
            </div>
            <div className="whitespace-pre-wrap leading-relaxed">{m.content}</div>
            {m.reasoning_content && (
              <details className="mt-2 border-t border-[#e5e2de] pt-2">
                <summary className="text-xs text-[#6b7280] cursor-pointer select-none">
                  Chain of thought
                </summary>
                <pre className="mt-1 text-xs text-[#6b7280] whitespace-pre-wrap">{m.reasoning_content}</pre>
              </details>
            )}
          </div>
        ))}

        {isRunning && (
          <div className="flex items-center gap-2 text-sm text-[#6b7280]">
            <span className="flex gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-[#44312a] animate-bounce" style={{ animationDelay: "0s" }} />
              <span className="w-1.5 h-1.5 rounded-full bg-[#44312a] animate-bounce" style={{ animationDelay: "0.15s" }} />
              <span className="w-1.5 h-1.5 rounded-full bg-[#44312a] animate-bounce" style={{ animationDelay: "0.3s" }} />
            </span>
            {statusText && <span className="italic">{statusText}</span>}
          </div>
        )}

        {uiState === "error" && onRetry && (
          <button
            onClick={onRetry}
            className="text-sm text-white bg-red-500 hover:bg-red-600 px-3 py-1.5 rounded-lg transition-colors"
          >
            Retry
          </button>
        )}
      </div>

      <div className="px-4 py-3 border-t border-[#e5e2de] flex gap-2 flex-shrink-0 bg-white">
        {isRunning ? (
          <button
            onClick={onStop}
            className="w-full text-sm font-medium text-white bg-red-500 hover:bg-red-600 py-2 rounded-lg transition-colors"
          >
            Stop
          </button>
        ) : (
          <>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
              placeholder="Refine the article..."
              disabled={isRunning}
              className="flex-1 border border-[#e5e2de] rounded-lg px-3 py-2 text-sm bg-white text-[#1a1a1a] placeholder:text-[#b0ada8] focus:outline-none focus:ring-2 focus:ring-[#44312a]/20 focus:border-[#44312a]"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || isRunning}
              className="text-sm font-medium text-white bg-[#44312a] hover:bg-[#5a4238] px-4 py-2 rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Send
            </button>
          </>
        )}
      </div>
    </div>
  );
}
