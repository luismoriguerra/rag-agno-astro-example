import type { AgentRun, ChatMessage, ChatSession, ChatSessionDetail } from "./chatTypes";

const API_BASE =
  import.meta.env.PUBLIC_AGENTOS_API_BASE_URL ?? "http://localhost:8000";
const MOCK_IDENTITY =
  import.meta.env.PUBLIC_MOCK_IDENTITY ?? "mock|local-dev-user";

function headers(): HeadersInit {
  return {
    "Content-Type": "application/json",
    "X-Mock-Identity": MOCK_IDENTITY,
  };
}

async function parseError(response: Response): Promise<Error> {
  try {
    const body = await response.json();
    return new Error(body.message ?? `Request failed (${response.status})`);
  } catch {
    return new Error(`Request failed (${response.status})`);
  }
}

export async function listSessions(): Promise<ChatSession[]> {
  const res = await fetch(`${API_BASE}/api/chat/sessions`, { headers: headers() });
  if (!res.ok) throw await parseError(res);
  const data = (await res.json()) as { sessions: ChatSession[] };
  return data.sessions;
}

export async function createSession(): Promise<ChatSession> {
  const res = await fetch(`${API_BASE}/api/chat/sessions`, {
    method: "POST",
    headers: headers(),
  });
  if (!res.ok) throw await parseError(res);
  return res.json() as Promise<ChatSession>;
}

export async function getSession(sessionId: string): Promise<ChatSessionDetail> {
  const res = await fetch(`${API_BASE}/api/chat/sessions/${sessionId}`, {
    headers: headers(),
  });
  if (!res.ok) throw await parseError(res);
  return res.json() as Promise<ChatSessionDetail>;
}

export async function deleteSession(sessionId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/chat/sessions/${sessionId}`, {
    method: "DELETE",
    headers: headers(),
  });
  if (!res.ok && res.status !== 204) throw await parseError(res);
}

export async function restoreActiveSession(): Promise<ChatSessionDetail> {
  const sessions = await listSessions();
  const active = sessions.find((s) => s.status === "active");
  if (active) return getSession(active.id);
  const created = await createSession();
  return getSession(created.id);
}

export async function submitMessage(
  sessionId: string,
  content: string,
): Promise<{ message: ChatMessage; run: AgentRun }> {
  const res = await fetch(`${API_BASE}/api/chat/sessions/${sessionId}/messages`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({ content }),
  });
  if (!res.ok) throw await parseError(res);
  return res.json() as Promise<{ message: ChatMessage; run: AgentRun }>;
}

export async function stopRun(runId: string): Promise<AgentRun> {
  const res = await fetch(`${API_BASE}/api/chat/runs/${runId}/stop`, {
    method: "POST",
    headers: headers(),
  });
  if (!res.ok) throw await parseError(res);
  return res.json() as Promise<AgentRun>;
}

export type StreamHandlers = {
  onThinking: (message: string) => void;
  onToken: (text: string) => void;
  onSource: (source: { title: string; url: string; rank: number; snippet?: string }) => void;
  onDone: (status: string) => void;
  onError: (message: string) => void;
};

export function streamRun(runId: string, handlers: StreamHandlers): () => void {
  const controller = new AbortController();
  const url = `${API_BASE}/api/chat/runs/${runId}/stream`;

  (async () => {
    const res = await fetch(url, {
      headers: { "X-Mock-Identity": MOCK_IDENTITY },
      signal: controller.signal,
    });
    if (!res.ok || !res.body) {
      handlers.onError("Unable to open response stream.");
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
      const payload = JSON.parse(data) as Record<string, unknown>;
      if (event === "thinking") handlers.onThinking(String(payload.message ?? ""));
      if (event === "token") handlers.onToken(String(payload.text ?? ""));
      if (event === "source")
        handlers.onSource({
          title: String(payload.title ?? ""),
          url: String(payload.url ?? ""),
          rank: Number(payload.rank ?? 1),
          snippet: payload.snippet ? String(payload.snippet) : undefined,
        });
      if (event === "done") finish(String(payload.status ?? "completed"));
      if (event === "error") {
        finished = true;
        handlers.onError(String(payload.message ?? "Stream failed."));
      }
    };

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop() ?? "";
      for (const part of parts) handlePart(part);
    }
    if (buffer.trim()) handlePart(buffer);
    finish("completed");
  })().catch((err: Error) => {
    if (err.name !== "AbortError") handlers.onError(err.message);
  });

  return () => controller.abort();
}
