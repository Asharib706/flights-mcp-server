"use client";

import { useState, useCallback, useRef } from "react";
import ChatWindow from "../components/ChatWindow";
import ChatInput from "../components/ChatInput";
import { Message, ToolEvent } from "../components/MessageBubble";
import { streamChat, resetSession, ChatEvent } from "../lib/api";

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [connected, setConnected] = useState<boolean | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const handleSend = useCallback(
    async (text: string) => {
      if (isStreaming) return;

      // Add user message
      const userMsg: Message = {
        id: `user-${Date.now()}`,
        role: "user",
        content: text,
      };

      // Create placeholder AI message
      const aiId = `ai-${Date.now()}`;
      const aiMsg: Message = {
        id: aiId,
        role: "ai",
        content: "",
        toolEvents: [],
        isStreaming: true,
      };

      setMessages((prev) => [...prev, userMsg, aiMsg]);
      setIsStreaming(true);

      const controller = new AbortController();
      abortRef.current = controller;

      try {
        let currentSessionId = sessionId;
        let latestContent = "";
        let toolEvents: ToolEvent[] = [];

        await streamChat(
          text,
          sessionId,
          (event: ChatEvent) => {
            // Capture session_id from first event
            if (!currentSessionId && event.session_id) {
              currentSessionId = event.session_id;
              setSessionId(event.session_id);
            }

            switch (event.type) {
              case "ai_message":
                latestContent = event.content || "";
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === aiId
                      ? { ...m, content: latestContent, toolEvents: [...toolEvents] }
                      : m
                  )
                );
                break;

              case "tool_call":
                toolEvents.push({
                  type: "tool_call",
                  tool_name: event.tool_name,
                });
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === aiId
                      ? { ...m, toolEvents: [...toolEvents] }
                      : m
                  )
                );
                break;

              case "tool_result":
                toolEvents.push({
                  type: "tool_result",
                  content: event.content,
                });
                break;

              case "done":
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === aiId ? { ...m, isStreaming: false } : m
                  )
                );
                setConnected(true);
                break;

              case "error":
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === aiId
                      ? {
                        ...m,
                        content: `⚠️ Error: ${event.content}`,
                        isStreaming: false,
                      }
                      : m
                  )
                );
                break;
            }
          },
          controller.signal
        );
      } catch (err: unknown) {
        if (err instanceof Error && err.name === "AbortError") return;
        setMessages((prev) =>
          prev.map((m) =>
            m.id === aiId
              ? {
                ...m,
                content: `⚠️ Could not connect to the server. Make sure the backend is running on http://localhost:8000`,
                isStreaming: false,
              }
              : m
          )
        );
        setConnected(false);
      } finally {
        setIsStreaming(false);
        // Safety net: always mark the AI message as done when the stream ends
        setMessages((prev) =>
          prev.map((m) =>
            m.id === aiId ? { ...m, isStreaming: false } : m
          )
        );
        abortRef.current = null;
      }
    },
    [isStreaming, sessionId]
  );

  const handleReset = useCallback(async () => {
    if (sessionId) {
      await resetSession(sessionId);
    }
    setMessages([]);
    setSessionId(null);
  }, [sessionId]);

  return (
    <>
      {/* Header */}
      <header className="flex-shrink-0 glass border-b border-white/5">
        <div className="max-w-4xl mx-auto px-4 md:px-8 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <svg
                className="w-4 h-4 text-white"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5"
                />
              </svg>
            </div>
            <span
              className="text-sm font-semibold text-white tracking-tight"
              style={{ fontFamily: "'Space Grotesk', sans-serif" }}
            >
              SkyPilot
            </span>
            {connected !== null && (
              <span
                className={`w-2 h-2 rounded-full ${connected ? "bg-emerald-400" : "bg-red-400"
                  }`}
                title={connected ? "Connected" : "Disconnected"}
              />
            )}
          </div>

          {messages.length > 0 && (
            <button
              onClick={handleReset}
              className="text-xs text-slate-500 hover:text-slate-300 transition-colors flex items-center gap-1.5"
            >
              <svg
                className="w-3.5 h-3.5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182"
                />
              </svg>
              New Chat
            </button>
          )}
        </div>
      </header>

      {/* Chat area */}
      <main className="flex-1 flex flex-col max-w-6xl w-full mx-auto overflow-hidden">
        <ChatWindow messages={messages} onSuggestionClick={handleSend} />

        {/* Input area */}
        <div className="flex-shrink-0 px-4 md:px-8 pb-4 pt-2">
          <ChatInput onSend={handleSend} disabled={isStreaming} />
        </div>
      </main>
    </>
  );
}
