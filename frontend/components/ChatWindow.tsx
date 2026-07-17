"use client";

import { useRef, useEffect } from "react";
import MessageBubble, { Message } from "./MessageBubble";

interface ChatWindowProps {
  messages: Message[];
  onSuggestionClick?: (text: string) => void;
}

export default function ChatWindow({ messages, onSuggestionClick }: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const lastMessageContent = messages[messages.length - 1]?.content;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, lastMessageContent]);

  const isEmpty = messages.length === 0;

  return (
    <div className="flex-1 overflow-y-auto scrollbar-thin px-4 md:px-8 py-6 md:py-10">
      <div
        className={`max-w-4xl mx-auto w-full ${isEmpty ? "min-h-full flex flex-col justify-center" : ""}`}
      >
        {isEmpty ? (
          <EmptyState onSuggestionClick={onSuggestionClick} />
        ) : (
          messages.map((msg) => <MessageBubble key={msg.id} message={msg} />)
        )}
        <div ref={bottomRef} className="h-4" />
      </div>
    </div>
  );
}

/* ── Welcome / Empty State ─────────────────────────────────────────────── */
const QUICK_CARDS = [
  {
    icon: "💸",
    title: "Cheapest Flights",
    desc: "Find the best deals on any route with live pricing",
    prompt: "Find the cheapest flights from Karachi to Dubai next Friday",
  },
  {
    icon: "🏨",
    title: "Hotel Search",
    desc: "Discover top-rated stays filtered by budget & amenities",
    prompt: "Best rated hotels in Istanbul under $150/night for 3 nights",
  },
  {
    icon: "📊",
    title: "Price Comparison",
    desc: "Compare dates, airlines, and routes side by side",
    prompt: "Compare flights from Lahore to London in July vs August",
  },
  {
    icon: "🗺️",
    title: "Full Trip Planner",
    desc: "Flights + hotels bundled into one seamless plan",
    prompt: "Plan a 7-day trip to Tokyo with flights from KHI and a hotel with breakfast",
  },
];

function EmptyState({
  onSuggestionClick,
}: {
  onSuggestionClick?: (text: string) => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center text-center px-4 py-8 md:py-16 animate-fade-up">
      {/* Mark */}
      <div className="relative mb-8">
        <div
          className="absolute inset-0 blur-3xl rounded-full scale-150 animate-pulse"
          style={{ background: "var(--card-glow)" }}
        />
        <span className="text-6xl md:text-8xl block animate-float relative z-10">🧭</span>
      </div>

      {/* Title */}
      <h1
        className="font-serif-italic text-5xl md:text-7xl mb-6 leading-tight tracking-tight"
        style={{ color: "var(--text)" }}
      >
        Where to next?
      </h1>

      <p className="text-sm md:text-lg max-w-lg mb-12 leading-relaxed font-medium" style={{ color: "var(--muted)" }}>
        Ask me anything about flights, hotels, or trip planning.
        <span className="block mt-1 opacity-70 font-normal">Real-time data from Google Flights & Hotels.</span>
      </p>

      {/* Quick-action grid - Responsive 1 -> 2 columns */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 md:gap-5 w-full max-w-3xl">
        {QUICK_CARDS.map((card, i) => (
          <button
            key={i}
            onClick={() => onSuggestionClick?.(card.prompt)}
            className="card flex flex-col items-center text-center p-6 md:p-8 rounded-[2rem] transition-all duration-300 cursor-pointer relative overflow-hidden group hover:-translate-y-0.5"
          >
            <div className="relative z-10 flex flex-col items-center">
              <span className="text-4xl block mb-4 group-hover:scale-110 group-hover:rotate-6 transition-transform duration-300">{card.icon}</span>
              <div className="font-display font-extrabold text-base md:text-lg mb-2" style={{ color: "var(--text)" }}>
                {card.title}
              </div>
              <div className="text-xs md:text-sm leading-relaxed line-clamp-2" style={{ color: "var(--muted)" }}>
                {card.desc}
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
