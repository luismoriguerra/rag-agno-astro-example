export type ResearchUiState =
  | "loading"
  | "idle"
  | "thinking"
  | "streaming"
  | "done"
  | "error";

export type ResearchMessageRole = "user" | "assistant";
export type ResearchMessageStatus = "complete" | "streaming" | "stopped" | "failed";
export type ArticleStatus = "draft" | "published";
export type ChangeSource = "agent";

export interface ResearchMessage {
  id: string;
  role: ResearchMessageRole;
  content: string;
  reasoning_content?: string | null;
  status: ResearchMessageStatus;
  sequence_index: number;
  created_at: string;
}

export interface ArticleVersion {
  id: string;
  version_number: number;
  markdown_content: string;
  status: ArticleStatus;
  change_source: ChangeSource;
  created_at: string;
}

export interface Article {
  id: string;
  current_version: number;
  latest_version?: ArticleVersion | null;
}

export interface ResearchSessionSummary {
  id: string;
  title: string;
  idea: string;
  status: ArticleStatus;
  is_generating: boolean;
  current_version: number | null;
  created_at: string;
  updated_at: string;
}

export interface ResearchSessionDetail {
  session: ResearchSessionSummary;
  article: Article | null;
  messages: ResearchMessage[];
}

export interface CreateResearchSessionResponse {
  session_id: string;
  title: string;
  status: ArticleStatus;
  created_at: string;
  run_id: string;
}

export interface ResearchSessionListResponse {
  sessions: ResearchSessionSummary[];
  total: number;
  page: number;
  page_size: number;
}

export interface ResearchArticleEvent {
  markdown: string;
  version: number;
  title: string;
}
