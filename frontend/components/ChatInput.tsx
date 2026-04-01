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
    <form onSubmit={handleSubmit} className="relative z-10 max-w-4xl mx-auto w-full">
      {/* Input wrapper */}
      <div
        className="flex items-end gap-3 md:gap-4 rounded-[2rem] md:rounded-[2.5rem] px-6 md:px-8 py-4 md:py-5 transition-all duration-300 border shadow-2xl"
        style={{
          background: "rgba(15, 23, 42, 0.75)",
          backdropFilter: "blur(32px)",
          borderColor: "var(--glass-border)",
        }}
        onFocusCapture={(e) => {
          (e.currentTarget as HTMLDivElement).style.borderColor = "rgba(0,194,255,0.6)";
          (e.currentTarget as HTMLDivElement).style.boxShadow = "0 0 0 5px rgba(0,194,255,0.15), 0 25px 50px -12px rgba(0,0,0,0.6)";
        }}
        onBlurCapture={(e) => {
          (e.currentTarget as HTMLDivElement).style.borderColor = "var(--glass-border)";
          (e.currentTarget as HTMLDivElement).style.boxShadow = "0 15px 35px -12px rgba(0,0,0,0.5)";
        }}
      >
        {/* Left tool buttons (hidden on very small screens) */}
        <div className="hidden sm:flex items-center gap-2 flex-shrink-0">
          {["📎", "🎙️"].map((icon, i) => (
            <button
              key={i}
              type="button"
              className="w-10 h-10 md:w-11 md:h-11 rounded-2xl flex items-center justify-center text-lg transition-all duration-200 border bg-white/5 border-white/10 hover:bg-white/10 hover:border-white/20 text-white/50 hover:text-white"
            >
              {icon}
            </button>
          ))}
        </div>

        {/* Textarea */}
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about flights or hotels…"
          disabled={disabled}
          rows={1}
          className="flex-1 bg-transparent resize-none outline-none text-base md:text-lg max-h-[160px] py-1.5 md:py-2 scrollbar-thin"
          style={{
            color: "var(--text)",
            lineHeight: "1.6",
          }}
        />

        {/* Send button */}
        <button
          type="submit"
          disabled={disabled || !input.trim()}
          className="w-11 h-11 md:w-13 md:h-13 rounded-2xl md:rounded-3xl flex items-center justify-center text-white flex-shrink-0 transition-all duration-300 disabled:opacity-20 disabled:grayscale disabled:cursor-not-allowed group"
          style={{
            background: "linear-gradient(135deg, var(--sky), #007ACC)",
            boxShadow: "0 6px 16px rgba(0,194,255,0.35)",
          }}
          onMouseEnter={(e) => {
            if (!e.currentTarget.disabled) {
              (e.currentTarget as HTMLButtonElement).style.transform = "translateY(-2px) scale(1.05)";
              (e.currentTarget as HTMLButtonElement).style.boxShadow = "0 10px 24px rgba(0,194,255,0.5)";
            }
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLButtonElement).style.transform = "";
            (e.currentTarget as HTMLButtonElement).style.boxShadow = "0 6px 16px rgba(0,194,255,0.35)";
          }}
        >
          <svg className="w-6 h-6 md:w-7 md:h-7 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
          </svg>
        </button>
      </div>

      {/* Footer row */}
      <div className="flex items-center justify-between mt-4 px-4 opacity-40">
        <span className="text-[10px] md:text-xs font-bold tracking-widest uppercase" style={{ color: "var(--muted)" }}>
          <span className="hidden sm:inline">Press </span>Enter to send · Shift+Enter for new line
        </span>
        <span className="text-[10px] md:text-xs font-mono" style={{ color: "var(--muted)" }}>
          {input.length > 0 ? `${input.length} characters` : ""}
        </span>
      </div>
    </form>
  );
}
