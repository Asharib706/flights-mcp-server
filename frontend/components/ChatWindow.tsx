"use client";

import { useRef, useEffect } from "react";
import MessageBubble, { Message } from "./MessageBubble";

interface ChatWindowProps {
    messages: Message[];
    onSuggestionClick?: (text: string) => void;
}

export default function ChatWindow({ messages, onSuggestionClick }: ChatWindowProps) {
    const bottomRef = useRef<HTMLDivElement>(null);

    // Auto-scroll on new messages
    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, messages[messages.length - 1]?.content]);

    return (
        <div className="flex-1 overflow-y-auto scrollbar-thin px-4 md:px-8 py-6">
            {messages.length === 0 ? (
                <EmptyState onSuggestionClick={onSuggestionClick} />
            ) : (
                messages.map((msg) => <MessageBubble key={msg.id} message={msg} />)
            )}
            <div ref={bottomRef} />
        </div>
    );
}

/* ── Empty state / welcome screen ────────────────────────────────────────── */
function EmptyState({ onSuggestionClick }: { onSuggestionClick?: (text: string) => void }) {
    const suggestions = [
        { icon: "✈️", text: "Find flights from Karachi to Dubai on March 10" },
        { icon: "💰", text: "Cheapest flights from Islamabad to London next week" },
        { icon: "📅", text: "Compare flights to New York for March 15-20" },
        { icon: "💼", text: "Best business class flights from Lahore to Istanbul" },
    ];

    return (
        <div className="h-full flex flex-col items-center justify-center text-center px-4">
            {/* Logo / Icon */}
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center mb-6 glow-pulse shadow-xl shadow-indigo-500/20">
                <svg className="w-10 h-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
                </svg>
            </div>

            <h1
                className="text-2xl md:text-3xl font-bold text-white mb-2"
                style={{ fontFamily: "'Space Grotesk', sans-serif" }}
            >
                SkyPilot
            </h1>
            <p className="text-slate-400 text-sm max-w-md mb-8">
                Your AI-powered flight assistant. Search flights, compare prices across dates,
                and explore routes to cities with multiple airports — all in one conversation.
            </p>

            {/* Suggestion chips */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 max-w-xl w-full">
                {suggestions.map((s, i) => (
                    <button
                        key={i}
                        onClick={() => onSuggestionClick?.(s.text)}
                        className="glass-bright text-left text-xs text-slate-400 px-4 py-3 rounded-xl 
                       hover:text-slate-200 hover:border-indigo-500/40 hover:scale-[1.02]
                       transition-all duration-200 cursor-pointer
                       flex items-start gap-2.5"
                    >
                        <span className="text-base mt-[-1px]">{s.icon}</span>
                        <span className="leading-relaxed">{s.text}</span>
                    </button>
                ))}
            </div>
        </div>
    );
}
