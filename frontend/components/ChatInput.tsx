"use client";

import { useState, useRef, useEffect, FormEvent, KeyboardEvent } from "react";

interface ChatInputProps {
    onSend: (message: string) => void;
    disabled?: boolean;
}

export default function ChatInput({ onSend, disabled }: ChatInputProps) {
    const [input, setInput] = useState("");
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    // Auto-resize textarea
    useEffect(() => {
        const el = textareaRef.current;
        if (el) {
            el.style.height = "auto";
            el.style.height = `${Math.min(el.scrollHeight, 150)}px`;
        }
    }, [input]);

    const handleSubmit = (e?: FormEvent) => {
        e?.preventDefault();
        const trimmed = input.trim();
        if (!trimmed || disabled) return;
        onSend(trimmed);
        setInput("");
        // Reset height
        if (textareaRef.current) {
            textareaRef.current.style.height = "auto";
        }
    };

    const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
        }
    };

    return (
        <form onSubmit={handleSubmit} className="relative">
            <div className="glass-bright rounded-2xl flex items-end gap-2 p-2 transition-all focus-within:border-indigo-500/40">
                <textarea
                    ref={textareaRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Ask about flights…"
                    disabled={disabled}
                    rows={1}
                    className="flex-1 bg-transparent text-slate-200 placeholder-slate-500 resize-none outline-none px-3 py-2.5 text-sm max-h-[150px] scrollbar-thin"
                />
                <button
                    type="submit"
                    disabled={disabled || !input.trim()}
                    className="flex-shrink-0 w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center 
                     text-white transition-all duration-200    
                     hover:shadow-lg hover:shadow-indigo-500/30 hover:scale-105
                     disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:scale-100 disabled:hover:shadow-none"
                >
                    <svg
                        className="w-5 h-5"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth={2}
                        viewBox="0 0 24 24"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5"
                        />
                    </svg>
                </button>
            </div>
            <p className="text-center text-[11px] text-slate-600 mt-2">
                SkyPilot can make mistakes. Verify important flight details.
            </p>
        </form>
    );
}
