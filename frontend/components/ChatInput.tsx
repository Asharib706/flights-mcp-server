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
      el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
    }
  }, [input]);

  const handleSubmit = (e?: FormEvent) => {
    e?.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setInput("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <form onSubmit={handleSubmit} className="relative z-10 max-w-4xl mx-auto w-full group/form">
      {/* Input wrapper */}
      <div
        className="flex items-center gap-2 sm:gap-3 md:gap-4 rounded-full pl-4 pr-2 sm:pl-6 sm:pr-2.5 md:pl-8 md:pr-3 py-2.5 md:py-3 transition-all duration-300 border shadow-lg"
        style={{ background: "var(--surface)", borderColor: "var(--border)" }}
        onFocusCapture={(e) => {
          (e.currentTarget as HTMLDivElement).style.borderColor = "var(--accent)";
        }}
        onBlurCapture={(e) => {
          (e.currentTarget as HTMLDivElement).style.borderColor = "var(--border)";
        }}
      >
        {/* Left tool buttons */}
        <div className="hidden sm:flex items-center gap-2 flex-shrink-0">
          <button
            type="button"
            aria-label="Attach a file"
            className="w-9 h-9 md:w-10 md:h-10 rounded-full flex items-center justify-center text-lg transition-all duration-200 border"
            style={{ background: "var(--surface-2)", borderColor: "var(--border)", color: "var(--muted)" }}
          >
            📎
          </button>
        </div>

        {/* Textarea */}
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about flights, hotels, or your next trip"
          disabled={disabled}
          rows={1}
          aria-label="Message SkyMind"
          className="flex-1 bg-transparent resize-none outline-none text-base md:text-lg max-h-[160px] py-2 scrollbar-thin font-medium min-w-0"
          style={{ color: "var(--text)", lineHeight: "1.5" }}
        />

        {/* Send button */}
        <button
          type="submit"
          disabled={disabled || !input.trim()}
          aria-label="Send message"
          className="w-10 h-10 md:w-12 md:h-12 rounded-full flex items-center justify-center flex-shrink-0 transition-all duration-300 disabled:opacity-30 disabled:scale-95 group/btn"
          style={{ background: "var(--accent)", color: "var(--on-accent)" }}
        >
          <svg
            className="w-5 h-5 md:w-6 md:h-6 transition-transform duration-300 group-hover/btn:translate-x-0.5 group-hover/btn:-translate-y-0.5"
            fill="none"
            stroke="currentColor"
            strokeWidth={3}
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
          </svg>
        </button>
      </div>

      {/* Footer row */}
      <div className="hidden sm:flex items-center justify-center mt-3 px-4 transition-opacity duration-300 group-focus-within/form:opacity-70 opacity-0">
        <span className="text-[10px] md:text-xs font-bold tracking-[0.1em] uppercase" style={{ color: "var(--muted)" }}>
          <span style={{ color: "var(--accent)" }}>Enter</span> to send · <span style={{ color: "var(--accent)" }}>Shift+Enter</span> for new line
        </span>
      </div>
    </form>
  );
}
