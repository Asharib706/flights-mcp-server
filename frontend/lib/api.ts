/**
 * SSE streaming client for the FastAPI chat backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            message,
            session_id: sessionId,
        }),
        signal,
    });

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
    await fetch(`${API_BASE}/api/reset`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId }),
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
    const res = await fetch(`${API_BASE}/api/health`);
    return res.json();
}
