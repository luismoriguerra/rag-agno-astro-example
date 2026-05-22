import {
  AuthApiError,
  authErrorKind,
  getAccessToken,
  getAuthorizationHeader,
} from "../lib/auth0";
import type {
  CreateResearchSessionResponse,
  ResearchArticleEvent,
  ResearchSessionDetail,
  ResearchSessionListResponse,
} from "./researchTypes";

const API_BASE = import.meta.env.PUBLIC_AGENTOS_API_BASE_URL ?? "http://localhost:8000";

async function parseError(response: Response): Promise<Error> {
  try {
    const body = await response.json();
    const message = body.message ?? `Request failed (${response.status})`;
    if (response.status === 401 || response.status === 403) {
      return new AuthApiError(message, authErrorKind(message));
    }
    return new Error(message);
  } catch {
    return new Error(`Request failed (${response.status})`);
  }
}

async function authFetch(
  input: string,
  init: RequestInit = {},
  allowRetry = true,
): Promise<Response> {
  const authHeaders = await getAuthorizationHeader();
  const res = await fetch(input, {
    ...init,
    headers: {
      ...authHeaders,
      ...(init.headers ?? {}),
    },
  });
  if (res.status === 401 && allowRetry) {
    await getAccessToken();
    return authFetch(input, init, false);
  }
  return res;
}

export async function createResearchSession(
  idea: string,
): Promise<CreateResearchSessionResponse> {
  const res = await authFetch(`${API_BASE}/api/research/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ idea }),
  });
  if (!res.ok) throw await parseError(res);
  return res.json() as Promise<CreateResearchSessionResponse>;
}

export async function listResearchSessions(
  page = 1,
  pageSize = 10,
  status?: "draft" | "published",
): Promise<ResearchSessionListResponse> {
  const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
  if (status) params.set("status", status);
  const res = await authFetch(`${API_BASE}/api/research/sessions?${params}`);
  if (!res.ok) throw await parseError(res);
  return res.json() as Promise<ResearchSessionListResponse>;
}

export async function getResearchSession(
  sessionId: string,
): Promise<ResearchSessionDetail> {
  const res = await authFetch(`${API_BASE}/api/research/sessions/${sessionId}`);
  if (!res.ok) throw await parseError(res);
  return res.json() as Promise<ResearchSessionDetail>;
}

export async function deleteResearchSession(sessionId: string): Promise<void> {
  const res = await authFetch(`${API_BASE}/api/research/sessions/${sessionId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw await parseError(res);
}

export type ResearchStreamHandlers = {
  onThinking: (message: string) => void;
  onReasoning: (content: string) => void;
  onToken: (text: string) => void;
  onArticle: (article: ResearchArticleEvent) => void;
  onActions: (actions: string[]) => void;
  onDone: (status: string) => void;
  onError: (message: string) => void;
};

export function streamResearchRun(
  runId: string,
  handlers: ResearchStreamHandlers,
): () => void {
  const controller = new AbortController();
  const url = `${API_BASE}/api/research/runs/${runId}/stream`;

  (async () => {
    let token = await getAccessToken();
    let res = await fetch(url, {
      headers: { Authorization: `Bearer ${token}` },
      signal: controller.signal,
    });
    if (res.status === 401) {
      token = await getAccessToken();
      res = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` },
        signal: controller.signal,
      });
    }
    if (!res.ok || !res.body) {
      handlers.onError("Unable to open research stream.");
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let finished = false;

    const finish = (status: string) => {
      if (finished) return;
      finished = true;
      handlers.onDone(status);
    };

    const handlePart = (part: string) => {
      const lines = part.split("\n");
      let event = "message";
      let data = "";
      for (const line of lines) {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        if (line.startsWith("data:")) data += line.slice(5).trim();
      }
      if (!data) return;

      try {
        const payload = JSON.parse(data) as Record<string, unknown>;
        switch (event) {
          case "thinking":
            handlers.onThinking(String(payload.message ?? ""));
            break;
          case "reasoning":
            handlers.onReasoning(String(payload.content ?? ""));
            break;
          case "token":
            handlers.onToken(String(payload.text ?? ""));
            break;
          case "article_preview":
          case "article":
            handlers.onArticle({
              markdown: String(payload.markdown ?? ""),
              version: Number(payload.version ?? 1),
              title: String(payload.title ?? ""),
            });
            break;
          case "actions": {
            const actions = payload.actions;
            if (Array.isArray(actions)) {
              handlers.onActions(actions.map(String));
            }
            break;
          }
          case "done": {
            const doneActions = payload.actions;
            if (Array.isArray(doneActions) && doneActions.length > 0) {
              handlers.onActions(doneActions.map(String));
            }
            finish(String(payload.status ?? "completed"));
            break;
          }
          case "error":
            finished = true;
            handlers.onError(String(payload.message ?? "Stream failed."));
            break;
        }
      } catch {
        // skip malformed JSON
      }
    };

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop() ?? "";
      for (const p of parts) handlePart(p);
    }
    if (buffer.trim()) handlePart(buffer);
    finish("completed");
  })().catch((err: Error) => {
    if (err.name !== "AbortError") handlers.onError(err.message);
  });

  return () => controller.abort();
}

export async function sendResearchMessage(
  sessionId: string,
  content: string,
): Promise<{ message_id: string; run_id: string }> {
  const res = await authFetch(`${API_BASE}/api/research/sessions/${sessionId}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
  if (!res.ok) throw await parseError(res);
  return res.json() as Promise<{ message_id: string; run_id: string }>;
}

export async function stopResearchRun(runId: string): Promise<void> {
  const res = await authFetch(`${API_BASE}/api/research/runs/${runId}/stop`, {
    method: "POST",
  });
  if (!res.ok) throw await parseError(res);
}

export async function updateArticleStatus(
  articleId: string,
  status: "draft" | "published",
): Promise<void> {
  const res = await authFetch(`${API_BASE}/api/research/articles/${articleId}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
  if (!res.ok) throw await parseError(res);
}

export async function retryResearchSession(
  sessionId: string,
): Promise<{ run_id: string }> {
  const res = await authFetch(`${API_BASE}/api/research/sessions/${sessionId}/retry`, {
    method: "POST",
  });
  if (!res.ok) throw await parseError(res);
  return res.json() as Promise<{ run_id: string }>;
}
