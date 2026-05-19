export type ChatUiState =
  | "empty"
  | "restoring"
  | "ready"
  | "submitting"
  | "thinking"
  | "streaming"
  | "stopping"
  | "stopped"
  | "failed"
  | "deleted";

export type MessageRole = "user" | "assistant" | "system_status";
export type MessageStatus = "complete" | "streaming" | "stopped" | "failed";

export interface SearchSource {
  title: string;
  url: string;
  snippet?: string;
  rank: number;
}

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  status: MessageStatus;
  sequence_index: number;
  created_at: string;
  sources?: SearchSource[];
}

export interface ChatSession {
  id: string;
  title: string;
  status: "active" | "inactive";
  created_at: string;
  updated_at: string;
}

export interface ChatSessionDetail extends ChatSession {
  messages: ChatMessage[];
}

export interface AgentRun {
  id: string;
  status: string;
}
