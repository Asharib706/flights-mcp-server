"use client";

import React from "react";

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

/* ── Simple markdown-like rendering ─────────────────────────────────────── */
function renderMarkdown(rawText: any): React.ReactNode {
  let text = "";
  if (typeof rawText === "string") {
    text = rawText;
  } else if (Array.isArray(rawText)) {
    text = rawText.map(t => typeof t === "string" ? t : (t.text || JSON.stringify(t))).join("");
  } else if (rawText != null) {
    text = JSON.stringify(rawText);
  }

  const lines = text.split("\n");
  const elements: React.ReactNode[] = [];
  let listItems: string[] = [];

  const flushList = () => {
    if (listItems.length > 0) {
      elements.push(
        <ul key={`ul-${elements.length}`} className="list-disc pl-5 my-1 space-y-0.5">
          {listItems.map((item, i) => (
            <li key={i}>{processInline(item)}</li>
          ))}
        </ul>
      );
      listItems = [];
    }
  };

  const processInline = (text: string): React.ReactNode => {
    const parts = text.split(/(\*\*[^*]+\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return (
          <strong key={i} className="font-semibold" style={{ color: "var(--text)" }}>
            {part.slice(2, -2)}
          </strong>
        );
      }
      const codeParts = part.split(/(`[^`]+`)/g);
      return codeParts.map((cp, j) => {
        if (cp.startsWith("`") && cp.endsWith("`")) {
          return (
            <code
              key={`${i}-${j}`}
              className="px-1.5 py-0.5 rounded text-[0.85em]"
              style={{ background: "rgba(0,194,255,0.08)", color: "var(--sky)" }}
            >
              {cp.slice(1, -1)}
            </code>
          );
        }
        return cp;
      });
    });
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    if (trimmed.startsWith("### ")) {
      flushList();
      elements.push(
        <h3
          key={`h3-${i}`}
          className="text-sm font-bold mt-3 mb-1"
          style={{ fontFamily: "'Cabinet Grotesk', sans-serif", color: "var(--text)" }}
        >
          {processInline(trimmed.slice(4))}
        </h3>
      );
      continue;
    }
    if (trimmed.startsWith("## ")) {
      flushList();
      elements.push(
        <h2
          key={`h2-${i}`}
          className="text-base font-bold mt-3 mb-1"
          style={{ fontFamily: "'Cabinet Grotesk', sans-serif", color: "var(--text)" }}
        >
          {processInline(trimmed.slice(3))}
        </h2>
      );
      continue;
    }
    if (trimmed.startsWith("- ") || trimmed.startsWith("* ") || /^\d+\.\s/.test(trimmed)) {
      listItems.push(trimmed.replace(/^[-*]\s|^\d+\.\s/, ""));
      continue;
    }
    if (trimmed === "") { flushList(); continue; }
    flushList();
    elements.push(
      <p key={`p-${i}`} className="my-1">
        {processInline(trimmed)}
      </p>
    );
  }
  flushList();
  return elements;
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

  return (
    <div
      className={`animate-message-in flex ${isUser ? "flex-row-reverse" : "flex-row"} items-start gap-3 md:gap-4 mb-8 w-full`}
    >
      {/* Avatar */}
      <div
        className={`w-10 h-10 rounded-2xl flex items-center justify-center text-xl flex-shrink-0 shadow-lg ${
          isUser ? "animate-fade-in" : "animate-float"
        }`}
        style={{
          background: isUser 
            ? "linear-gradient(135deg, var(--horizon), var(--sun))" 
            : "linear-gradient(135deg, var(--sky), var(--success))",
          boxShadow: isUser 
            ? "0 4px 12px rgba(255,107,53,0.2)" 
            : "0 4px 12px rgba(0,194,255,0.3)",
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
              ? "rounded-[2rem] rounded-tr-none px-6 py-4 md:py-5 text-white"
              : "rounded-[2rem] rounded-tl-none px-7 py-5 md:py-6 border"
          }`}
          style={
            isUser
              ? {
                  background: "linear-gradient(135deg, var(--sky), #007ACC)",
                  boxShadow: "0 10px 30px -10px rgba(0,194,255,0.4)",
                }
              : {
                  background: "rgba(15, 23, 42, 0.6)",
                  backdropFilter: "blur(24px)",
                  borderColor: "var(--glass-border)",
                  boxShadow: "0 12px 40px -12px rgba(0,0,0,0.5)",
                }
          }
        >
          {message.content ? (
            <div className={`prose-chat ${isUser ? "text-white" : ""}`} style={isUser ? {} : { color: "var(--text)" }}>
              {isUser ? message.content : renderMarkdown(message.content)}
            </div>
          ) : (
            !isUser && message.isStreaming && <TypingIndicator />
          )}
        </div>
      </div>
    </div>
  );
}
