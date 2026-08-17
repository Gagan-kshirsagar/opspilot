"use client";

/**
 * Dashboard — minimal placeholder to prove the protected route works.
 */

import { useAuthStore } from "@/stores/authStore";

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user);

  return (
    <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 animate-slide-up">
      <h1 className="text-2xl font-semibold tracking-tight text-foreground">
        Welcome, {user?.name ?? "..."}
      </h1>
      <p className="mt-2 text-sm text-muted">
        You&apos;re signed in as{" "}
        <span className="font-medium text-foreground">{user?.role}</span>.
        This is a placeholder dashboard — more features coming in the next
        slice.
      </p>

      {/* ── Quick stats placeholder ────────────────────── */}
      <div className="mt-8 grid gap-4 sm:grid-cols-3">
        {["Incidents", "On-call", "Services"].map((label) => (
          <div
            key={label}
            className="rounded-xl border border-subtle bg-surface p-5 shadow-sm"
          >
            <p className="text-xs font-medium uppercase tracking-wider text-muted">
              {label}
            </p>
            <p className="mt-1 text-2xl font-semibold text-foreground">—</p>
          </div>
        ))}
      </div>
    </div>
  );
}
