"use client";

/**
 * Guest badge — small pill shown when the current user has role=guest.
 */

import { cn } from "@/lib/utils";

interface GuestBadgeProps {
  className?: string;
}

export function GuestBadge({ className }: GuestBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5",
        "bg-warning-soft text-warning text-xs font-medium",
        "border border-warning/20",
        className,
      )}
    >
      <span className="size-1.5 rounded-full bg-warning" aria-hidden="true" />
      Demo guest
    </span>
  );
}
