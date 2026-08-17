"use client";

/**
 * Theme store + toggle — manages dark/light mode via class on <html>.
 *
 * No new dependencies (no next-themes). Persists preference to localStorage.
 */

import { useEffect } from "react";
import { create } from "zustand";
import { Moon, Sun } from "lucide-react";
import { cn } from "@/lib/utils";

type Theme = "light" | "dark";

interface ThemeState {
  theme: Theme;
  toggle: () => void;
  setTheme: (t: Theme) => void;
}

export const useThemeStore = create<ThemeState>((set) => ({
  theme: "dark",
  toggle: () =>
    set((s) => {
      const next = s.theme === "dark" ? "light" : "dark";
      return { theme: next };
    }),
  setTheme: (t) => set({ theme: t }),
}));

/** Sync the theme class on <html> + localStorage. */
export function useThemeSync() {
  const theme = useThemeStore((s) => s.theme);
  const setTheme = useThemeStore((s) => s.setTheme);

  // On mount, read preference.
  useEffect(() => {
    const stored = localStorage.getItem("opspilot_theme") as Theme | null;
    if (stored === "light" || stored === "dark") {
      setTheme(stored);
    } else if (
      typeof window.matchMedia === "function" &&
      window.matchMedia("(prefers-color-scheme: dark)").matches
    ) {
      setTheme("dark");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Apply the class + persist.
  useEffect(() => {
    const root = document.documentElement;
    root.classList.toggle("dark", theme === "dark");
    localStorage.setItem("opspilot_theme", theme);
  }, [theme]);
}

/** Light / dark toggle button. */
export function ThemeToggle({ className }: { className?: string }) {
  const theme = useThemeStore((s) => s.theme);
  const toggle = useThemeStore((s) => s.toggle);

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
      className={cn(
        "inline-flex items-center justify-center rounded-lg p-2",
        "text-muted hover:text-foreground hover:bg-surface-2",
        "transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        className,
      )}
    >
      {theme === "dark" ? (
        <Sun className="size-4" />
      ) : (
        <Moon className="size-4" />
      )}
    </button>
  );
}
