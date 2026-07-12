"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { listSessions, resetSession as deleteSession, SessionSummary } from "../lib/api";
import { useAuth } from "./AuthProvider";
import { LogoBadge } from "./Logo";

interface SidebarProps {
  onReset: () => void;
  onSelectSession: (sessionId: string) => void;
  onSessionDeleted?: (sessionId: string) => void;
  currentSessionId: string | null;
  refreshKey: number;
  isOpen?: boolean;
  onClose?: () => void;
}

function groupSessions(sessions: SessionSummary[]) {
  const now = new Date();
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const startOfWeek = new Date(startOfToday);
  startOfWeek.setDate(startOfWeek.getDate() - 7);

  const groups: { label: string; items: SessionSummary[] }[] = [
    { label: "Today", items: [] },
    { label: "This week", items: [] },
    { label: "Older", items: [] },
  ];

  for (const s of sessions) {
    const updated = new Date(s.updated_at);
    if (updated >= startOfToday) groups[0].items.push(s);
    else if (updated >= startOfWeek) groups[1].items.push(s);
    else groups[2].items.push(s);
  }

  return groups.filter((g) => g.items.length > 0);
}

export default function Sidebar({
  onReset,
  onSelectSession,
  onSessionDeleted,
  currentSessionId,
  refreshKey,
  isOpen,
  onClose,
}: SidebarProps) {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    listSessions()
      .then(setSessions)
      .catch(() => setSessions([]));
  }, [refreshKey]);

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteSession(id);
      setSessions((prev) => prev.filter((s) => s.id !== id));
      onSessionDeleted?.(id);
    } catch {
      // best-effort — leave the list as-is on failure
    }
  };

  const groups = groupSessions(sessions);

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          className="md:hidden fixed inset-0 z-[60] backdrop-blur-sm animate-fade-in"
          style={{ background: "rgba(20,17,12,0.5)" }}
          onClick={onClose}
        />
      )}

      <aside
        className={`fixed md:static inset-y-0 left-0 z-[70] flex flex-col transition-all duration-300 transform
          ${isOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"}
          overflow-hidden border-r`}
        style={{
          width: 272,
          flexShrink: 0,
          background: "var(--bg-side)",
          borderColor: "var(--border)",
        }}
      >
        {/* Logo & Close */}
        <div
          className="px-5 py-5 border-b flex-shrink-0 flex items-center justify-between"
          style={{ borderColor: "var(--border)" }}
        >
          <div className="flex items-center gap-3">
            <LogoBadge size={38} className="rounded-xl flex-shrink-0" />
            <div>
              <div className="font-display text-lg font-extrabold tracking-tight" style={{ color: "var(--text)" }}>
                SkyMind
              </div>
              <div className="text-[10px] tracking-widest uppercase mt-0.5" style={{ color: "var(--muted)" }}>
                Travel, planned
              </div>
            </div>
          </div>

          <button
            onClick={onClose}
            aria-label="Close sidebar"
            className="md:hidden p-2 -mr-2"
            style={{ color: "var(--muted)" }}
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* New Conversation Button */}
        <div className="px-4 pt-5 pb-2 flex-shrink-0">
          <button
            onClick={() => {
              onReset();
              onClose?.();
            }}
            className="w-full flex items-center justify-center gap-2.5 px-4 py-3 rounded-xl text-sm font-semibold transition-all duration-200 hover:opacity-90"
            style={{ background: "var(--accent)", color: "var(--on-accent)" }}
          >
            <span className="text-base">✦</span>
            New trip
          </button>
        </div>

        {/* History */}
        <nav className="flex-1 overflow-y-auto scrollbar-thin px-3 pb-4 pt-3">
          {groups.length === 0 && (
            <div className="px-3 py-6 text-xs text-center" style={{ color: "var(--muted)" }}>
              Your conversations will show up here.
            </div>
          )}
          {groups.map((group) => (
            <div key={group.label} className="mb-4">
              <div
                className="px-3 pb-2 text-[10px] tracking-[1.5px] uppercase font-bold"
                style={{ color: "var(--muted)" }}
              >
                {group.label}
              </div>
              {group.items.map((s) => {
                const active = s.id === currentSessionId;
                return (
                  <div key={s.id} className="group relative mb-1">
                    <button
                      onClick={() => {
                        onSelectSession(s.id);
                        onClose?.();
                      }}
                      className="w-full flex items-center gap-2.5 px-3 py-2.5 pr-9 rounded-xl text-left text-sm transition-colors duration-150"
                      style={{
                        background: active ? "var(--surface)" : "transparent",
                        color: active ? "var(--text)" : "var(--muted)",
                        fontWeight: active ? 600 : 400,
                      }}
                    >
                      <span className="truncate block">{s.title}</span>
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(s.id);
                      }}
                      aria-label={`Delete "${s.title}"`}
                      className="absolute right-1.5 top-1/2 -translate-y-1/2 p-1.5 rounded-lg opacity-60 md:opacity-0 md:group-hover:opacity-100 transition-opacity duration-150"
                      style={{ color: "var(--muted)" }}
                    >
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                );
              })}
            </div>
          ))}
        </nav>

        {/* User menu */}
        <div className="relative px-3 py-3 border-t flex-shrink-0" style={{ borderColor: "var(--border)" }}>
          {menuOpen && (
            <div
              className="absolute bottom-full left-3 right-3 mb-2 rounded-xl border overflow-hidden shadow-lg animate-fade-in"
              style={{ background: "var(--surface)", borderColor: "var(--border)" }}
            >
              <button
                onClick={handleLogout}
                className="w-full text-left px-4 py-3 text-sm font-medium transition-colors"
                style={{ color: "var(--text)" }}
              >
                Sign out
              </button>
            </div>
          )}
          <button
            onClick={() => setMenuOpen((v) => !v)}
            className="w-full flex items-center gap-2.5 px-2 py-2 rounded-xl transition-colors duration-150"
            style={{ color: "var(--text)" }}
          >
            <div
              className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0"
              style={{ background: "var(--accent)", color: "var(--on-accent)" }}
            >
              {(user?.display_name || user?.email || "?").charAt(0).toUpperCase()}
            </div>
            <div className="flex-1 min-w-0 text-left">
              <div className="text-sm font-semibold truncate">{user?.display_name || "Traveler"}</div>
              <div className="text-xs truncate" style={{ color: "var(--muted)" }}>{user?.email}</div>
            </div>
          </button>
        </div>
      </aside>
    </>
  );
}
