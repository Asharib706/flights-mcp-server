"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import ChatWindow from "../components/ChatWindow";
import ChatInput from "../components/ChatInput";
import Sidebar from "../components/Sidebar";
import OnboardingModal from "../components/OnboardingModal";
import ThemeToggle from "../components/ThemeToggle";
import { LogoFull, LogoIcon } from "../components/Logo";
import { useAuth } from "../components/AuthProvider";
import { Message, ToolEvent } from "../components/MessageBubble";
import {
  streamChat,
  listSessions,
  getSessionMessages,
  StoredMessage,
  ChatEvent,
} from "../lib/api";

function storedToUIMessages(rows: StoredMessage[]): Message[] {
  return rows
    .filter((m): m is StoredMessage & { role: "user" | "ai" } => m.role === "user" || m.role === "ai")
    .map((m) => ({
      id: m.id,
      role: m.role,
      content: m.content,
      toolEvents: m.tool_events || undefined,
      isStreaming: false,
    }));
}

export default function Home() {
  const { user, loading: authLoading, refresh: refreshAuth } = useAuth();
  const router = useRouter();

  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [connected, setConnected] = useState<boolean | null>(null);
  const [statsFlights, setStatsFlights] = useState(0);
  const [statsHotels, setStatsHotels] = useState(0);
  const [statsTools, setStatsTools] = useState(0);
  const [statsTime, setStatsTime] = useState<string>("—");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  const [historyLoaded, setHistoryLoaded] = useState(false);
  const startTimeRef = useRef<number>(0);
  const abortRef = useRef<AbortController | null>(null);

  // Redirect unauthenticated visitors to /login.
  useEffect(() => {
    if (!authLoading && !user) router.replace("/login");
  }, [authLoading, user, router]);

  // Show the onboarding questionnaire once, right after it's needed.
  useEffect(() => {
    if (user && !user.onboarding_done) setShowOnboarding(true);
  }, [user]);

  // On first load, restore the most recently active session instead of always starting blank.
  useEffect(() => {
    if (!user || historyLoaded) return;
    setHistoryLoaded(true);
    listSessions()
      .then(async (sessions) => {
        if (sessions.length === 0) return;
        const rows = await getSessionMessages(sessions[0].id);
        setMessages(storedToUIMessages(rows));
        setSessionId(sessions[0].id);
      })
      .catch(() => {});
  }, [user, historyLoaded]);

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
        const toolEvents: ToolEvent[] = [];

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
                } else if (event.tool_name?.includes("hotel")) {
                  setStatsHotels((h) => h + 1);
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
                setRefreshKey((k) => k + 1);
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
        const isAuthError = (err as { status?: number })?.status === 401;
        setMessages((prev) =>
          prev.map((m) =>
            m.id === aiId
              ? {
                  ...m,
                  content: isAuthError
                    ? "⚠️ Your session expired — please sign in again."
                    : "⚠️ Could not connect to the server.",
                  isStreaming: false,
                }
              : m
          )
        );
        setConnected(false);
        if (isAuthError) {
          await refreshAuth();
          router.replace("/login");
        }
      } finally {
        setIsStreaming(false);
        setMessages((prev) =>
          prev.map((m) => (m.id === aiId ? { ...m, isStreaming: false } : m))
        );
        abortRef.current = null;
      }
    },
    [isStreaming, sessionId, refreshAuth, router]
  );

  const handleReset = useCallback(() => {
    // Starting a new trip just clears local state — it must NOT delete the
    // previous conversation, since it's still visible (and reopenable) in
    // the sidebar's history. A fresh session is created lazily on the next
    // message (see get_or_create_chat_session on the backend).
    abortRef.current?.abort();
    setMessages([]);
    setSessionId(null);
    setStatsFlights(0);
    setStatsHotels(0);
    setStatsTools(0);
    setStatsTime("—");
  }, []);

  const handleSelectSession = useCallback(
    async (id: string) => {
      if (id === sessionId) return;
      abortRef.current?.abort();
      setIsStreaming(false);
      try {
        const rows = await getSessionMessages(id);
        setMessages(storedToUIMessages(rows));
        setSessionId(id);
      } catch {
        // ignore — session may have been deleted from another tab
      }
    },
    [sessionId]
  );

  const handleSessionDeleted = useCallback(
    (id: string) => {
      if (id !== sessionId) return;
      setMessages([]);
      setSessionId(null);
    },
    [sessionId]
  );

  if (authLoading || !user) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <LogoFull height={48} className="animate-pulse-dot" />
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden relative">
      {showOnboarding && (
        <OnboardingModal
          onComplete={async () => {
            setShowOnboarding(false);
            await refreshAuth();
          }}
        />
      )}

      <Sidebar
        onReset={handleReset}
        onSelectSession={handleSelectSession}
        onSessionDeleted={handleSessionDeleted}
        currentSessionId={sessionId}
        refreshKey={refreshKey}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      {/* Main column */}
      <div className="flex flex-col flex-1 overflow-hidden">
        {/* ── Top Bar ── */}
        <header className="chrome w-full border-b flex-shrink-0 z-50">
          <div className="max-w-4xl mx-auto w-full flex items-center justify-between px-4 sm:px-6 md:px-8 py-3 md:py-4">
            <div className="flex items-center gap-3">
              {/* Hamburger Toggle */}
              <button
                onClick={() => setSidebarOpen(true)}
                aria-label="Open sidebar"
                className="md:hidden p-2 -ml-2 transition-colors"
                style={{ color: "var(--muted)" }}
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>

              <LogoIcon height={30} className="flex-shrink-0 hidden sm:block" />

              <div className="flex flex-col">
                <div className="font-display text-base md:text-lg font-extrabold tracking-tight" style={{ color: "var(--text)" }}>
                  SkyMind
                </div>
                <div className="text-[10px] md:text-xs mt-0.5" style={{ color: "var(--muted)" }}>
                  <span className="hidden xs:inline">Flights + Hotels, live</span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2 sm:gap-3">
              {/* Connection status */}
              {connected !== null && (
                <div
                  className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full text-[10px] md:text-xs border"
                  style={{
                    background: "var(--surface-2)",
                    borderColor: "var(--border)",
                    color: connected ? "var(--success)" : "var(--danger)",
                  }}
                >
                  <span
                    className="w-1.5 h-1.5 rounded-full animate-pulse-dot"
                    style={{ background: connected ? "var(--success)" : "var(--danger)" }}
                  />
                  <span className="font-semibold">{connected ? "Online" : "Offline"}</span>
                </div>
              )}

              <ThemeToggle />
            </div>
          </div>
        </header>

        {/* ── Chat Area ── */}
        <main className="flex-1 flex flex-col overflow-hidden relative">
          <ChatWindow messages={messages} onSuggestionClick={handleSend} />

          {/* ── Stats Strip ── */}
          {messages.length > 0 && (
            <div
              className="flex gap-2 px-3 sm:px-4 md:px-8 py-2 flex-shrink-0 overflow-x-auto scrollbar-thin border-t"
              style={{ borderColor: "var(--border)" }}
            >
              {[
                { icon: "✈️", label: "Flights", val: statsFlights },
                { icon: "🏨", label: "Hotels", val: statsHotels },
                { icon: "⚡", label: "Response", val: statsTime },
                { icon: "🔧", label: "Tools", val: statsTools },
              ].map((s, i) => (
                <div
                  key={i}
                  className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[10px] md:text-xs whitespace-nowrap border flex-shrink-0"
                  style={{ background: "var(--surface-2)", borderColor: "var(--border)", color: "var(--muted)" }}
                >
                  <span className="opacity-80">{s.icon}</span>
                  <span className="hidden xs:inline">{s.label}:</span>
                  <span className="font-bold" style={{ color: "var(--text)" }}>{s.val}</span>
                </div>
              ))}
            </div>
          )}

          {/* ── Input Area ── */}
          <div className="chrome flex-shrink-0 px-3 sm:px-4 md:px-8 pb-4 md:pb-8 pt-3 md:pt-4">
            <div className="max-w-4xl mx-auto w-full">
              <ChatInput onSend={handleSend} disabled={isStreaming} />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
