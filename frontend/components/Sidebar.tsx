"use client";

interface SidebarProps {
  onReset: () => void;
  isOpen?: boolean;
  onClose?: () => void;
}

const HISTORY_ITEMS = [
  { icon: "🗼", label: "Paris to Dubai, Jul 15" },
  { icon: "🗽", label: "NYC flights under $400" },
  { icon: "🏯", label: "Tokyo hotels with pool" },
  { icon: "🌴", label: "Maldives resorts, Aug" },
  { icon: "🏔️", label: "Zürich ski trip Jan 2026" },
  { icon: "☀️", label: "Barcelona weekend getaway" },
];

export default function Sidebar({ onReset, isOpen, onClose }: SidebarProps) {
  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          className="md:hidden fixed inset-0 z-[60] bg-black/60 backdrop-blur-sm animate-fade-in"
          onClick={onClose}
        />
      )}

      <aside
        className={`fixed md:static inset-y-0 left-0 z-[70] flex flex-col transition-all duration-300 transform 
          ${isOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"}
          overflow-hidden border-r`}
        style={{
          width: 280,
          flexShrink: 0,
          background: "rgba(10,15,30,0.92)",
          backdropFilter: "blur(32px)",
          borderColor: "var(--glass-border)",
        }}
      >
        {/* Logo & Close */}
        <div
          className="px-6 py-6 border-b flex-shrink-0 flex items-center justify-between"
          style={{ borderColor: "var(--glass-border)" }}
        >
          <div className="flex items-center gap-3">
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center text-xl font-bold flex-shrink-0"
              style={{
                background: "linear-gradient(135deg, var(--sky), var(--success))",
                boxShadow: "0 0 20px rgba(0,194,255,0.4)",
              }}
            >
              ✈️
            </div>
            <div>
              <div
                className="font-cabinet text-xl font-black tracking-tight"
                style={{
                  background: "linear-gradient(90deg, #fff, var(--sky))",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                }}
              >
                SkyMind
              </div>
              <div
                className="text-[10px] tracking-widest uppercase mt-0.5"
                style={{ color: "var(--muted)" }}
              >
                AI Travel Assistant
              </div>
            </div>
          </div>

          {/* Close for mobile */}
          <button
            onClick={onClose}
            className="md:hidden p-2 text-white/50 hover:text-white transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* New Conversation Button */}
        <div className="px-5 pt-6 pb-2 flex-shrink-0">
          <button
            onClick={() => {
              onReset();
              onClose?.();
            }}
            className="w-full flex items-center gap-2.5 px-4 py-3.5 rounded-xl text-white text-sm font-medium transition-all duration-200"
            style={{
              background: "linear-gradient(135deg, var(--sky), #007ACC)",
              boxShadow: "0 4px 20px rgba(0,194,255,0.3)",
            }}
            onMouseEnter={(e) =>
              ((e.currentTarget as HTMLButtonElement).style.boxShadow =
                "0 6px 28px rgba(0,194,255,0.45)")
            }
            onMouseLeave={(e) =>
              ((e.currentTarget as HTMLButtonElement).style.boxShadow =
                "0 4px 20px rgba(0,194,255,0.3)")
            }
          >
            <span className="text-base">✦</span>
            New Conversation
          </button>
        </div>

        {/* History Section */}
        <div
          className="px-6 pt-6 pb-2 text-[10px] tracking-[1.5px] uppercase font-bold flex-shrink-0"
          style={{ color: "var(--muted)" }}
        >
          Recent Trips
        </div>

        <nav className="flex-1 overflow-y-auto scrollbar-thin px-3 pb-4">
          {HISTORY_ITEMS.map((item, i) => (
            <div
              key={i}
              className="flex items-center gap-3 px-3 py-3 rounded-xl cursor-pointer mb-1 text-sm transition-all duration-150 group"
              style={{ color: "var(--muted)" }}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLDivElement).style.background =
                  "rgba(255,255,255,0.05)";
                (e.currentTarget as HTMLDivElement).style.color = "var(--text)";
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLDivElement).style.background = "";
                (e.currentTarget as HTMLDivElement).style.color = "var(--muted)";
              }}
              onClick={onClose}
            >
              <span className="text-lg flex-shrink-0 opacity-70 group-hover:opacity-100 transition-opacity">{item.icon}</span>
              <span className="truncate">{item.label}</span>
            </div>
          ))}
        </nav>

        {/* Status badge */}
        <div
          className="px-5 py-5 border-t flex-shrink-0"
          style={{ borderColor: "var(--glass-border)" }}
        >
        <div
          className="flex items-center gap-2.5 px-4 py-3.5 rounded-2xl text-xs font-semibold"
          style={{
            background: "rgba(16, 185, 129, 0.08)",
            border: "1px solid rgba(16, 185, 129, 0.2)",
            color: "var(--success)",
          }}
        >
          <span
            className="w-2 h-2 rounded-full flex-shrink-0 animate-pulse-dot"
            style={{ background: "var(--success)" }}
          />
          System Online · 2 MCPs
        </div>
        </div>
      </aside>
    </>
  );
}
