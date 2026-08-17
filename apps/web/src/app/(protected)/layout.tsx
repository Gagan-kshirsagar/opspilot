"use client";

/**
 * Protected layout — redirects to /login when unauthenticated.
 * Shows a top bar with user info, guest badge, and theme toggle.
 */

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { LogOut, Shield } from "lucide-react";

import { cn } from "@/lib/utils";
import { useMe, useLogout } from "@/lib/query/auth";
import { useAuthStore } from "@/stores/authStore";
import { getAccessToken } from "@/lib/api/client";
import { GuestBadge } from "@/components/auth/guest-badge";
import {
  ThemeToggle,
  useThemeSync,
} from "@/components/auth/theme-toggle";

export default function ProtectedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { status, user, setUser, setStatus, clear } = useAuthStore();
  const logoutMutation = useLogout();

  useThemeSync();

  const { data, isLoading, isError } = useMe();

  // Sync query data → Zustand.
  useEffect(() => {
    if (data) {
      setUser(data);
    }
  }, [data, setUser]);

  useEffect(() => {
    if (isError) {
      clear();
    }
  }, [isError, clear]);

  // Redirect when unauthenticated.
  useEffect(() => {
    // If no token at all, redirect immediately.
    if (!getAccessToken() && status === "idle") {
      setStatus("unauthenticated");
    }
  }, [status, setStatus]);

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/login");
    }
  }, [status, router]);

  // Loading state.
  if (isLoading || status === "idle" || status === "loading") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3 animate-fade-in">
          <div className="size-8 animate-spin rounded-full border-2 border-subtle border-t-accent" />
          <p className="text-sm text-muted">Loading…</p>
        </div>
      </div>
    );
  }

  // Unauthenticated — will redirect (avoid flash).
  if (status === "unauthenticated" || !user) {
    return null;
  }

  return (
    <div className="flex min-h-screen flex-col bg-background">
      {/* ── Top bar ──────────────────────────────────── */}
      <header className="sticky top-0 z-30 border-b border-subtle bg-surface/80 backdrop-blur-sm">
        <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <Shield className="size-5 text-accent" />
              <span className="text-sm font-semibold tracking-tight text-foreground">
                OpsPilot
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {user.is_guest && <GuestBadge />}

            <span className="text-sm text-muted">
              {user.name}
            </span>

            <ThemeToggle />

            <button
              type="button"
              onClick={() => logoutMutation.mutate()}
              disabled={logoutMutation.isPending}
              aria-label="Log out"
              className={cn(
                "inline-flex items-center justify-center rounded-lg p-2",
                "text-muted hover:text-foreground hover:bg-surface-2",
                "transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
              )}
            >
              <LogOut className="size-4" />
            </button>
          </div>
        </div>
      </header>

      {/* ── Page content ─────────────────────────────── */}
      <main className="flex-1">{children}</main>
    </div>
  );
}
