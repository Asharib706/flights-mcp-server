"use client";

import { useState, useCallback, useRef } from "react";
import ChatWindow from "../components/ChatWindow";
import ChatInput from "../components/ChatInput";
import Sidebar from "../components/Sidebar";
import { Message, ToolEvent } from "../components/MessageBubble";
import { streamChat, resetSession, ChatEvent } from "../lib/api";

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [connected, setConnected] = useState<boolean | null>(null);
  const [statsFlights, setStatsFlights] = useState(0);
  const [statsTools, setStatsTools] = useState(0);
  const [statsTime, setStatsTime] = useState<string>("—");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const startTimeRef = useRef<number>(0);
  const abortRef = useRef<AbortController | null>(null);

  const handleSend = useCallback(
    async (text: string) => {
      if (isStreaming) return;

      const userMsg: Message = {
        id: `user-${Date.now()}`,
        role: "user",
        content: text,
      };

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
      startTimeRef.current = Date.now();

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
                    m.id === aiId ? { ...m, toolEvents: [...toolEvents] } : m
                  )
                );
                setStatsTools((t) => t + 1);

                if (
                  event.tool_name?.includes("flight") ||
                  event.tool_name?.includes("airport")
                ) {
                  setStatsFlights((f) => f + 1);
                }
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
                setStatsTime(
                  ((Date.now() - startTimeRef.current) / 1000).toFixed(1) + "s"
                );
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
                  content: `⚠️ Could not connect to the server.`,
                  isStreaming: false,
                }
              : m
          )
        );
        setConnected(false);
      } finally {
        setIsStreaming(false);
        setMessages((prev) =>
          prev.map((m) => (m.id === aiId ? { ...m, isStreaming: false } : m))
        );
        abortRef.current = null;
      }
    },
    [isStreaming, sessionId]
  );

  const handleReset = useCallback(async () => {
    if (sessionId) await resetSession(sessionId);
    setMessages([]);
    setSessionId(null);
    setStatsFlights(0);
    setStatsTools(0);
    setStatsTime("—");
  }, [sessionId]);

  return (
    <div className="flex h-screen overflow-hidden relative">
      <Sidebar 
        onReset={handleReset} 
        isOpen={sidebarOpen} 
        onClose={() => setSidebarOpen(false)} 
      />

      {/* Main column */}
      <div className="flex flex-col flex-1 overflow-hidden">

        {/* ── Top Bar ── */}
        <div
          className="flex items-center justify-between px-4 md:px-8 py-4 md:py-5 border-b flex-shrink-0"
          style={{
            background: "rgba(6,11,24,0.75)",
            backdropFilter: "blur(20px)",
            borderColor: "var(--glass-border)",
          }}
        >
          <div className="flex items-center gap-3">
            {/* Hamburger Toggle */}
            <button
              onClick={() => setSidebarOpen(true)}
              className="md:hidden p-2 -ml-2 text-white/70 hover:text-white transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            
            <div>
              <div
                className="text-base md:text-lg font-black tracking-tight flex items-center gap-2"
                style={{ fontFamily: "'Cabinet Grotesk', sans-serif" }}
              >
                <span className="md:hidden">✈️</span> SkyMind
                <span className="hidden md:inline">Travel Assistant</span>
              </div>
              <div className="text-[10px] md:text-xs mt-0.5 opacity-60" style={{ color: "var(--muted)" }}>
                <span className="hidden sm:inline">Powered by </span>Google Flights + Hotels Live
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Connection status (mobile simplified) */}
            {connected !== null && (
              <div
                className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-full text-[10px] md:text-xs border"
                style={{
                  background: "var(--glass)",
                  borderColor: "var(--glass-border)",
                  color: connected ? "var(--success)" : "#ef4444",
                }}
              >
                <span className="w-1.5 h-1.5 rounded-full animate-pulse-dot" style={{ background: connected ? "var(--success)" : "#ef4444" }} />
                <span className="hidden xs:inline">{connected ? "Connected" : "Offline"}</span>
              </div>
            )}

            <div
              className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs border"
              style={{
                background: "var(--glass)",
                borderColor: "var(--glass-border)",
                color: "var(--muted)",
              }}
            >
              🔍 Live
            </div>
          </div>
        </div>

        {/* ── Chat Area ── */}
        <main className="flex-1 flex flex-col overflow-hidden relative">
          <ChatWindow messages={messages} onSuggestionClick={handleSend} />

          {/* ── Stats Strip ── */}
          {messages.length > 0 && (
            <div
              className="flex gap-2.5 px-4 md:px-8 py-2.5 flex-shrink-0 overflow-x-auto scrollbar-thin"
              style={{ 
                background: "rgba(10,15,30,0.4)",
                borderTop: "1px solid var(--glass-border)" 
              }}
            >
              {[
                { icon: "✈️", label: "Flights", val: statsFlights },
                { icon: "⚡", label: "Response", val: statsTime },
                { icon: "🔧", label: "Tools", val: statsTools },
              ].map((s, i) => (
                <div
                  key={i}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-[10px] md:text-xs whitespace-nowrap border flex-shrink-0"
                  style={{
                    background: "var(--glass)",
                    borderColor: "var(--glass-border)",
                    color: "var(--muted)",
                  }}
                >
                  <span className="opacity-80">{s.icon}</span>
                  <span className="hidden xs:inline">{s.label}:</span>
                  <span className="font-bold" style={{ color: "var(--text)" }}>{s.val}</span>
                </div>
              ))}
            </div>
          )}

          {/* ── Input Area ── */}
          <div
            className="flex-shrink-0 px-4 md:px-8 pb-4 md:pb-8 pt-4"
            style={{
              background: "rgba(6,11,24,0.85)",
              backdropFilter: "blur(24px)",
              borderTop: messages.length > 0 ? "none" : "1px solid var(--glass-border)",
            }}
          >
            <div className="max-w-4xl mx-auto w-full">
              <ChatInput onSend={handleSend} disabled={isStreaming} />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
