/**
 * API client for the FastAPI backend — auth, sessions, memory, and the
 * SSE-streamed chat endpoint. Every request sends credentials so the
 * httpOnly session cookie set by /api/auth/login (or /register) rides
 * along automatically; there's no token to manage on the client.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // response wasn't JSON — keep statusText
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

/* ── Auth ───────────────────────────────────────────────────────────────── */
export interface UserOut {
  id: string;
  email: string;
  display_name: string | null;
  onboarding_done: boolean;
}

export function register(email: string, password: string, displayName?: string): Promise<UserOut> {
  return apiFetch<UserOut>("/api/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, display_name: displayName || null }),
  });
}

export function login(email: string, password: string): Promise<UserOut> {
  return apiFetch<UserOut>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function logout(): Promise<{ status: string }> {
  return apiFetch("/api/auth/logout", { method: "POST" });
}

export function getMe(): Promise<UserOut> {
  return apiFetch<UserOut>("/api/auth/me");
}

/* ── Onboarding ─────────────────────────────────────────────────────────── */
export interface OnboardingPayload {
  home_airport?: string;
  trip_type?: string;
  budget_band?: string;
  cabin_class?: string;
  interests?: string[];
  travel_frequency?: string;
  constraints?: string;
}

export function submitOnboarding(payload: OnboardingPayload): Promise<{ status: string }> {
  return apiFetch("/api/onboarding", { method: "POST", body: JSON.stringify(payload) });
}

/* ── Memory ─────────────────────────────────────────────────────────────── */
export interface MemoryFact {
  key: string;
  value: string;
  category: string;
  source: string;
  confidence: number;
  updated_at: string;
}

export function getMemory(): Promise<MemoryFact[]> {
  return apiFetch<MemoryFact[]>("/api/memory");
}

export function forgetMemoryFact(key: string): Promise<{ status: string; key: string }> {
  return apiFetch(`/api/memory/${encodeURIComponent(key)}`, { method: "DELETE" });
}

/* ── Sessions ───────────────────────────────────────────────────────────── */
export interface SessionSummary {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface StoredToolEvent {
  type: "tool_call" | "tool_result";
  tool_name?: string;
  content?: string;
}

export interface StoredMessage {
  id: string;
  role: "user" | "ai" | "tool";
  content: string;
  tool_events: StoredToolEvent[] | null;
  created_at: string;
}

export function listSessions(): Promise<SessionSummary[]> {
  return apiFetch<SessionSummary[]>("/api/sessions");
}

export function getSessionMessages(sessionId: string): Promise<StoredMessage[]> {
  return apiFetch<StoredMessage[]>(`/api/sessions/${sessionId}/messages`);
}

/* ── Chat (SSE) ─────────────────────────────────────────────────────────── */
export interface ChatEvent {
  type: "ai_message" | "tool_call" | "tool_result" | "done" | "error";
  content?: string;
  tool_name?: string;
  session_id: string;
}

/**
 * Send a message and stream SSE events from the backend.
 * Calls `onEvent` for each parsed SSE event.
 */
export async function streamChat(
  message: string,
  sessionId: string | null,
  onEvent: (event: ChatEvent) => void,
  signal?: AbortSignal
): Promise<void> {
  const response = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      session_id: sessionId,
    }),
    signal,
  });

  if (response.status === 401) {
    throw new ApiError(401, "Not authenticated");
  }
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  const reader = response.body?.getReader();
  if (!reader) throw new Error("No response body");

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // Parse SSE lines
    const lines = buffer.split("\n");
    buffer = lines.pop() || ""; // keep incomplete line in buffer

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try {
          const data: ChatEvent = JSON.parse(line.slice(6));
          onEvent(data);
        } catch {
          // skip malformed JSON
        }
      }
    }
  }
}

/**
 * Reset a chat session.
 */
export async function resetSession(sessionId: string): Promise<void> {
  await apiFetch("/api/reset", {
    method: "POST",
    body: JSON.stringify({ message: "", session_id: sessionId }),
  });
}

/**
 * Health check.
 */
export async function healthCheck(): Promise<{
  status: string;
  llm_provider: string;
  tools_loaded: number;
}> {
  const res = await fetch(`${API_BASE}/api/health`, { credentials: "include" });
  return res.json();
}
