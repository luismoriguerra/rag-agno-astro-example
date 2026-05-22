import { useEffect, useRef, useState } from "react";
import ChatMessage, { ThinkingIndicator } from "./ChatMessage";
import type { ResearchMessage, ResearchUiState } from "../services/researchTypes";

interface ResearchChatProps {
  messages: ResearchMessage[];
  uiState: ResearchUiState;
  statusText: string;
  suggestedActions?: string[];
  onSendMessage?: (content: string) => void | Promise<void>;
  onStop?: () => void;
  onRetry?: () => void;
}

export default function ResearchChat({
  messages,
  uiState,
  statusText,
  suggestedActions = [],
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
      <div className="px-4 py-3 border-b border-[#e5e2de] shrink-0">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-[#6b7280]">
          Research Thread
        </h2>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.length === 0 && uiState === "loading" && (
          <p className="text-sm text-[#6b7280] italic text-center py-8">Loading conversation...</p>
        )}
        {messages.length === 0 && uiState === "idle" && (
          <p className="text-sm text-[#6b7280] italic text-center py-8">No messages yet.</p>
        )}

        {messages.map((m) => (
          <ChatMessage
            key={m.id}
            role={m.role}
            content={m.content}
            reasoningContent={m.reasoning_content}
            agentLabel="Research Agent"
          />
        ))}

        {isRunning && <ThinkingIndicator statusText={statusText} />}

        {uiState === "error" && onRetry && (
          <div className="flex gap-3 items-start pl-10">
            <button
              onClick={onRetry}
              className="text-sm text-white bg-red-500 hover:bg-red-600 px-3 py-1.5 rounded-lg transition-colors"
            >
              Retry
            </button>
          </div>
        )}

        {!isRunning && suggestedActions.length > 0 && (
          <div className="flex flex-wrap gap-2 pl-10">
            {suggestedActions.map((action, i) => (
              <button
                key={i}
                onClick={() => onSendMessage?.(action)}
                className="text-xs font-medium text-[#44312a] bg-[#f5f3f0] border border-[#e5e2de] px-3 py-1.5 rounded-full hover:bg-[#ebe8e4] hover:border-[#44312a]/30 transition-colors"
              >
                {action}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="px-4 py-3 border-t border-[#e5e2de] flex gap-2 shrink-0 bg-white">
        {isRunning ? (
          <button
            onClick={onStop}
            className="w-full text-sm font-medium text-[#6b7280] border border-[#d1d5db] hover:bg-[#f3f4f6] py-2 rounded-lg transition-colors"
          >
            Stop generating
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
              className="flex-1 border border-[#e5e2de] rounded-xl px-3.5 py-2 text-sm bg-[#f9fafb] text-[#1a1a1a] placeholder:text-[#b0ada8] focus:outline-none focus:ring-2 focus:ring-[#10a37f]/20 focus:border-[#10a37f] focus:bg-white"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || isRunning}
              className="text-sm font-medium text-white bg-[#10a37f] hover:bg-[#0d8c6d] px-4 py-2 rounded-xl transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Send
            </button>
          </>
        )}
      </div>
    </div>
  );
}
