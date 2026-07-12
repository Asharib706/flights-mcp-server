"use client";

import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

/* ── Types ──────────────────────────────────────────────────────────────── */
export interface ToolEvent {
  type: "tool_call" | "tool_result";
  tool_name?: string;
  content?: string;
}

export interface Message {
  id: string;
  role: "user" | "ai";
  content: string;
  toolEvents?: ToolEvent[];
  isStreaming?: boolean;
}

/** Content from the backend is always plain text (see server.py's stringify_ai_content),
 * but stay defensive here in case a raw LangChain content-block list ever slips through. */
function toPlainText(raw: unknown): string {
  if (typeof raw === "string") return raw;
  if (Array.isArray(raw)) {
    return raw
      .map((t) => (typeof t === "string" ? t : (t as { text?: string })?.text || ""))
      .join("");
  }
  return raw == null ? "" : JSON.stringify(raw);
}

/* ── Tool Event Badge ────────────────────────────────────────────────────── */
function ToolEventBadge({ event, isComplete }: { event: ToolEvent; isComplete: boolean }) {
  if (event.type !== "tool_call") return null;
  return (
    <div className="animate-fade-in my-1">
      <span className="tool-badge">
        {isComplete ? (
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3} style={{ color: "var(--success)" }}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
        ) : (
          <svg className="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        )}
        {isComplete
          ? `Used ${event.tool_name?.replace(/_/g, " ")}`
          : `Searching ${event.tool_name?.replace(/_/g, " ")}…`}
      </span>
    </div>
  );
}

/* ── Typing Indicator ────────────────────────────────────────────────────── */
function TypingIndicator() {
  return (
    <div className="flex items-center gap-3 px-4 py-3">
      <div className="flex gap-1">
        <span className="typing-dot" />
        <span className="typing-dot" />
        <span className="typing-dot" />
      </div>
      <span className="text-xs" style={{ color: "var(--muted)" }}>Searching…</span>
    </div>
  );
}

/* ── Message Bubble ──────────────────────────────────────────────────────── */
export default function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  const isDone = !message.isStreaming;
  const text = toPlainText(message.content);

  return (
    <div
      className={`animate-message-in flex ${isUser ? "flex-row-reverse" : "flex-row"} items-start gap-3 md:gap-4 mb-8 w-full`}
    >
      {/* Avatar */}
      <div
        className={`w-9 h-9 md:w-10 md:h-10 rounded-2xl flex items-center justify-center text-lg md:text-xl flex-shrink-0 shadow-lg ${
          isUser ? "animate-fade-in" : "animate-float"
        }`}
        style={{
          background: isUser
            ? "linear-gradient(135deg, var(--accent-2), var(--accent))"
            : "linear-gradient(135deg, var(--accent), var(--accent-2))",
        }}
      >
        {isUser ? "👤" : "🤖"}
      </div>

      {/* Bubble container */}
      <div
        className={`flex flex-col ${isUser ? "items-end" : "items-start"} max-w-[85%] sm:max-w-[75%]`}
      >
        {/* Tool events (AI only) */}
        {!isUser && message.toolEvents && message.toolEvents.length > 0 && (
          <div className="mb-2.5 flex flex-wrap gap-1.5 px-1">
            {message.toolEvents.map((ev, i) => (
              <ToolEventBadge key={i} event={ev} isComplete={isDone} />
            ))}
          </div>
        )}

        {/* The Bubble */}
        <div
          className={`${
            isUser
              ? "rounded-[1.75rem] rounded-tr-md px-5 py-3.5 md:px-6 md:py-4"
              : "rounded-[1.75rem] rounded-tl-md px-5 py-4 md:px-6 md:py-5 border"
          }`}
          style={
            isUser
              ? { background: "var(--accent)", color: "var(--on-accent)" }
              : { background: "var(--surface)", borderColor: "var(--border)", color: "var(--text)" }
          }
        >
          {text ? (
            <div className="prose-chat">
              {isUser ? (
                <p className="whitespace-pre-wrap m-0">{text}</p>
              ) : (
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{text}</ReactMarkdown>
              )}
            </div>
          ) : (
            !isUser && message.isStreaming && <TypingIndicator />
          )}
        </div>
      </div>
    </div>
  );
}
