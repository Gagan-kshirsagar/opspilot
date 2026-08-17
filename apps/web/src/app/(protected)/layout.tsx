"use client";

/**
 * Protected layout — redirects to /login when unauthenticated.
 * Shows a top bar with navigation links, user info, guest badge, and theme toggle.
 */

import { useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { LayoutDashboard, LogOut, Shield, Users } from "lucide-react";

import { cn } from "@/lib/utils";
import { useMe, useLogout } from "@/lib/query/auth";
import { useAuthStore } from "@/stores/authStore";
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
  const pathname = usePathname();
  const { status, user, setUser, clear } = useAuthStore();
  const logoutMutation = useLogout();

  useThemeSync();

  const { data, isError } = useMe();

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

  // Redirect only when confirmed unauthenticated.
  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/login");
    }
  }, [status, router]);

  // Loading state (waiting for bootstrap).
  if (status === "loading" || (!user && status !== "unauthenticated")) {
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

  const navItems = [
    {
      href: "/dashboard",
      label: "Dashboard",
      icon: LayoutDashboard,
      active: pathname === "/dashboard",
    },
    {
      href: "/users",
      label: "Users",
      icon: Users,
      active: pathname.startsWith("/users"),
    },
  ];

  return (
    <div className="flex min-h-screen flex-col bg-background">
      {/* ── Top bar ──────────────────────────────────── */}
      <header className="sticky top-0 z-30 border-b border-subtle bg-surface/80 backdrop-blur-sm">
        <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6">
          <div className="flex items-center gap-6">
            <Link
              href="/dashboard"
              className="flex items-center gap-2 transition-opacity hover:opacity-80"
            >
              <Shield className="size-5 text-accent" />
              <span className="text-sm font-semibold tracking-tight text-foreground">
                OpsPilot
              </span>
            </Link>

            {/* Navigation links */}
            <nav className="flex items-center gap-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium transition-colors",
                      item.active
                        ? "bg-surface-2 text-foreground font-semibold"
                        : "text-muted hover:bg-surface-2/60 hover:text-foreground"
                    )}
                  >
                    <Icon className="size-3.5" />
                    {item.label}
                  </Link>
                );
              })}
            </nav>
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
