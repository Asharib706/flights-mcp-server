"use client";

import { useRef, useEffect } from "react";
import MessageBubble, { Message } from "./MessageBubble";

interface ChatWindowProps {
  messages: Message[];
  onSuggestionClick?: (text: string) => void;
}

export default function ChatWindow({ messages, onSuggestionClick }: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, messages[messages.length - 1]?.content]);

  return (
    <div className="flex-1 overflow-y-auto scrollbar-thin px-4 md:px-8 py-6 md:py-10">
      <div className="max-w-4xl mx-auto w-full">
        {messages.length === 0 ? (
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
      {/* Floating globe */}
      <div className="relative mb-8">
        <div className="absolute inset-0 bg-sky-500/20 blur-3xl rounded-full scale-150 animate-pulse" />
        <span className="text-6xl md:text-8xl block animate-float relative z-10">🌍</span>
      </div>

      {/* Title */}
      <h1
        className="text-5xl md:text-7xl mb-6 leading-tight tracking-tight font-black"
        style={{
          fontFamily: "'Instrument Serif', serif",
          fontStyle: "italic",
          background: "linear-gradient(135deg, #fff 40%, var(--sky))",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
        }}
      >
        Where to next?
      </h1>

      <p className="text-sm md:text-lg max-w-lg mb-12 leading-relaxed font-medium" style={{ color: "var(--muted)" }}>
        Ask me anything about flights, hotels, or trip planning. 
        <span className="block mt-1 opacity-60 font-normal">Real-time data from Google Flights & Hotels.</span>
      </p>

      {/* Quick-action grid - Responsive 1 -> 2 columns */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 w-full max-w-3xl">
        {QUICK_CARDS.map((card, i) => (
          <button
            key={i}
            onClick={() => onSuggestionClick?.(card.prompt)}
            className="flex flex-col items-center text-center p-6 md:p-8 rounded-[2.5rem] transition-all duration-500 cursor-pointer border relative overflow-hidden group hover:scale-[1.02] hover:shadow-2xl hover:shadow-sky-500/10"
            style={{
              background: "rgba(15, 23, 42, 0.5)",
              borderColor: "var(--glass-border)",
            }}
          >
            {/* Hover Gradient Overlay */}
            <div className="absolute inset-0 bg-gradient-to-br from-sky-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            
            <div className="relative z-10 flex flex-col items-center">
              <span className="text-4xl block mb-4 group-hover:scale-110 group-hover:rotate-12 transition-transform duration-500">{card.icon}</span>
              <div
                className="font-black text-base md:text-lg mb-2"
                style={{ fontFamily: "'Cabinet Grotesk', sans-serif", color: "var(--text)" }}
              >
                {card.title}
              </div>
              <div className="text-xs md:text-sm leading-relaxed opacity-60 line-clamp-2" style={{ color: "var(--muted)" }}>
                {card.desc}
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
