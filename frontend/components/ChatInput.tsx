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
        className="flex items-center gap-3 md:gap-4 rounded-full px-6 md:px-8 py-3.5 md:py-4.5 transition-all duration-500 border shadow-2xl"
        style={{
          background: "rgba(15, 23, 42, 0.8)",
          backdropFilter: "blur(40px)",
          borderColor: "var(--glass-border)",
        }}
        onFocusCapture={(e) => {
          (e.currentTarget as HTMLDivElement).style.borderColor = "rgba(0,194,255,0.5)";
          (e.currentTarget as HTMLDivElement).style.boxShadow = "0 0 0 4px rgba(0,194,255,0.1), 0 20px 40px -12px rgba(0,0,0,0.7)";
        }}
        onBlurCapture={(e) => {
          (e.currentTarget as HTMLDivElement).style.borderColor = "var(--glass-border)";
          (e.currentTarget as HTMLDivElement).style.boxShadow = "0 15px 35px -12px rgba(0,0,0,0.5)";
        }}
      >
        {/* Left tool buttons */}
        <div className="hidden sm:flex items-center gap-2 flex-shrink-0">
          <button
            type="button"
            className="w-10 h-10 rounded-full flex items-center justify-center text-lg transition-all duration-300 border bg-white/5 border-white/10 hover:bg-white/10 hover:border-white/20 text-white/40 hover:text-white"
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
          placeholder="Where are we flying? ✈️"
          disabled={disabled}
          rows={1}
          className="flex-1 bg-transparent resize-none outline-none text-base md:text-lg max-h-[160px] py-2 scrollbar-thin placeholder:text-slate-500 font-medium"
          style={{
            color: "var(--text)",
            lineHeight: "1.5",
          }}
        />

        {/* Send button */}
        <button
          type="submit"
          disabled={disabled || !input.trim()}
          className="w-10 h-10 md:w-12 md:h-12 rounded-full flex items-center justify-center text-white flex-shrink-0 transition-all duration-500 disabled:opacity-20 disabled:scale-95 group/btn overflow-hidden"
          style={{
            background: "linear-gradient(135deg, var(--sky), #007ACC)",
            boxShadow: "0 4px 15px rgba(0,194,255,0.3)",
          }}
        >
          <div className="relative z-10 transition-transform duration-500 group-hover/btn:translate-x-0.5 group-hover/btn:-translate-y-0.5">
            <svg className="w-5 h-5 md:w-6 md:h-6" fill="none" stroke="currentColor" strokeWidth={3} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
            </svg>
          </div>
          {/* Internal Glow */}
          <div className="absolute inset-0 bg-white/20 opacity-0 group-hover/btn:opacity-100 transition-opacity" />
        </button>
      </div>

      {/* Footer row */}
      <div className="flex items-center justify-center mt-3 px-4 transition-opacity duration-300 group-focus-within/form:opacity-60 opacity-0">
        <span className="text-[10px] md:text-xs font-bold tracking-[0.1em] uppercase" style={{ color: "var(--muted)" }}>
          <span className="text-sky-400">Enter</span> to send · <span className="text-sky-400">Shift+Enter</span> for new line
        </span>
      </div>
    </form>
  );
}
