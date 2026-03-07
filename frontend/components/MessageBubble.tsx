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
function renderMarkdown(text: string): React.ReactNode {
    // Split by lines and process
    const lines = text.split("\n");
    const elements: React.ReactNode[] = [];

    let inList = false;
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
            inList = false;
        }
    };

    const processInline = (text: string): React.ReactNode => {
        // Bold: **text**
        const parts = text.split(/(\*\*[^*]+\*\*)/g);
        return parts.map((part, i) => {
            if (part.startsWith("**") && part.endsWith("**")) {
                return (
                    <strong key={i} className="font-semibold text-slate-100">
                        {part.slice(2, -2)}
                    </strong>
                );
            }
            // Inline code: `text`
            const codeParts = part.split(/(`[^`]+`)/g);
            return codeParts.map((cp, j) => {
                if (cp.startsWith("`") && cp.endsWith("`")) {
                    return (
                        <code
                            key={`${i}-${j}`}
                            className="bg-indigo-500/10 px-1.5 py-0.5 rounded text-[0.85em] text-indigo-300"
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

        // Headers
        if (trimmed.startsWith("### ")) {
            flushList();
            elements.push(
                <h3
                    key={`h3-${i}`}
                    className="text-sm font-semibold text-slate-200 mt-3 mb-1"
                    style={{ fontFamily: "'Space Grotesk', sans-serif" }}
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
                    className="text-base font-semibold text-slate-100 mt-3 mb-1"
                    style={{ fontFamily: "'Space Grotesk', sans-serif" }}
                >
                    {processInline(trimmed.slice(3))}
                </h2>
            );
            continue;
        }

        // List items
        if (trimmed.startsWith("- ") || trimmed.startsWith("* ") || /^\d+\.\s/.test(trimmed)) {
            inList = true;
            const content = trimmed.replace(/^[-*]\s|^\d+\.\s/, "");
            listItems.push(content);
            continue;
        }

        // Empty line
        if (trimmed === "") {
            flushList();
            continue;
        }

        // Normal paragraph
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

/* ── Tool Event Display ─────────────────────────────────────────────────── */
function ToolEventBadge({ event, isComplete }: { event: ToolEvent; isComplete: boolean }) {
    if (event.type === "tool_call") {
        return (
            <div className="animate-fade-in my-1">
                <span className="tool-badge">
                    {isComplete ? (
                        <svg className="w-3.5 h-3.5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
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
    return null;
}

/* ── Typing Indicator ───────────────────────────────────────────────────── */
function TypingIndicator() {
    return (
        <div className="flex items-center gap-2 px-4 py-3">
            <div className="flex gap-1">
                <span className="typing-dot" />
                <span className="typing-dot" />
                <span className="typing-dot" />
            </div>
            <span className="text-xs text-slate-500">Thinking…</span>
        </div>
    );
}

/* ── Message Bubble ─────────────────────────────────────────────────────── */
export default function MessageBubble({ message }: { message: Message }) {
    const isUser = message.role === "user";
    const isDone = !message.isStreaming;

    return (
        <div
            className={`animate-message-in flex ${isUser ? "justify-end" : "justify-start"
                } mb-3`}
        >
            <div
                className={`${isUser
                        ? "max-w-[85%] md:max-w-[70%] bg-gradient-to-br from-indigo-500 to-purple-600 text-white rounded-2xl rounded-br-md px-4 py-3 shadow-lg shadow-indigo-500/10"
                        : "w-full glass-bright rounded-2xl rounded-bl-md px-5 py-4"
                    }`}
            >
                {/* Tool events (AI only) */}
                {!isUser && message.toolEvents && message.toolEvents.length > 0 && (
                    <div className="mb-2 flex flex-wrap gap-1">
                        {message.toolEvents.map((ev, i) => (
                            <ToolEventBadge key={i} event={ev} isComplete={isDone} />
                        ))}
                    </div>
                )}

                {/* Message content */}
                {message.content ? (
                    <div className={`prose-chat ${isUser ? "" : "text-slate-300"}`}>
                        {isUser ? message.content : renderMarkdown(message.content)}
                    </div>
                ) : (
                    !isUser && message.isStreaming && <TypingIndicator />
                )}
            </div>
        </div>
    );
}
