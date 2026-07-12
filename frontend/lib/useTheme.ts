"use client";

import { useCallback, useEffect, useState } from "react";

type Theme = "light" | "dark";

function getSystemTheme(): Theme {
  if (typeof window === "undefined") return "dark";
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

/**
 * Reads/writes the "skymind-theme" localStorage override that wins over the
 * OS preference (see the inline script in layout.tsx that applies it before
 * first paint). With no stored override, this stays in sync with OS changes
 * live rather than freezing a one-time snapshot.
 */
export function useTheme() {
  const [theme, setThemeState] = useState<Theme>(() => {
    if (typeof window === "undefined") return "light";
    const stored = localStorage.getItem("skymind-theme") as Theme | null;
    return stored ?? getSystemTheme();
  });

  // Only subscribes to live OS-preference changes when there's no explicit
  // stored override — the initial value is read lazily above, not here.
  useEffect(() => {
    if (typeof window === "undefined" || localStorage.getItem("skymind-theme")) return;
    const mql = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = (e: MediaQueryListEvent) => setThemeState(e.matches ? "dark" : "light");
    mql.addEventListener("change", onChange);
    return () => mql.removeEventListener("change", onChange);
  }, []);

  const setTheme = useCallback((t: Theme) => {
    setThemeState(t);
    localStorage.setItem("skymind-theme", t);
    document.documentElement.setAttribute("data-theme", t);
  }, []);

  const toggle = useCallback(() => {
    setTheme(theme === "dark" ? "light" : "dark");
  }, [theme, setTheme]);

  return { theme, setTheme, toggle };
}
