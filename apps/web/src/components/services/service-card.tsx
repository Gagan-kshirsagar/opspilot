"use client";

import Link from "next/link";
import { Activity, ArrowRight, ShieldCheck, User } from "lucide-react";

import { formatRelativeTime } from "@/lib/utils/format";
import type { ServiceItem, ServiceStatus } from "@/types/service";

export function getServiceStatusBadge(status: ServiceStatus) {
  switch (status) {
    case "healthy":
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-medium text-emerald-400 border border-emerald-500/20">
          <span className="size-1.5 rounded-full bg-emerald-400 animate-pulse" />
          Healthy
        </span>
      );
    case "degraded":
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-500/10 px-2.5 py-0.5 text-xs font-medium text-amber-400 border border-amber-500/20">
          <span className="size-1.5 rounded-full bg-amber-400" />
          Degraded
        </span>
      );
    case "down":
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-rose-500/10 px-2.5 py-0.5 text-xs font-medium text-rose-400 border border-rose-500/20">
          <span className="size-1.5 rounded-full bg-rose-400" />
          Down
        </span>
      );
  }
}

interface ServiceCardProps {
  service: ServiceItem;
}

export function ServiceCard({ service }: ServiceCardProps) {
  const uptimeColor =
    service.uptime_pct >= 99.5
      ? "text-emerald-400"
      : service.uptime_pct >= 95
        ? "text-amber-400"
        : "text-rose-400";

  return (
    <Link
      href={`/services/${service.id}`}
      className="group relative flex flex-col justify-between rounded-xl border border-subtle bg-surface p-5 transition-all duration-200 hover:border-accent/40 hover:bg-surface-2 hover:shadow-lg hover:shadow-accent/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
    >
      <div>
        {/* Header: Name + Status */}
        <div className="flex items-start justify-between gap-2">
          <h3 className="font-semibold text-foreground text-base tracking-tight group-hover:text-accent transition-colors">
            {service.name}
          </h3>
          {getServiceStatusBadge(service.status)}
        </div>

        {/* Note / Description */}
        <p className="mt-2 text-xs text-muted line-clamp-2 min-h-[2rem]">
          {service.note || "No description provided."}
        </p>

        {/* Metrics Grid */}
        <div className="mt-4 grid grid-cols-2 gap-3 border-t border-subtle/50 pt-3">
          <div className="flex items-center gap-2">
            <Activity className="size-4 text-faint" />
            <div>
              <span className="block text-[10px] uppercase tracking-wider text-faint font-medium">
                Uptime
              </span>
              <span className={`text-sm font-semibold ${uptimeColor}`}>
                {service.uptime_pct.toFixed(2)}%
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <User className="size-4 text-faint" />
            <div>
              <span className="block text-[10px] uppercase tracking-wider text-faint font-medium">
                Owner
              </span>
              <span className="text-xs font-medium text-foreground truncate max-w-[110px] block">
                {service.owner_name}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Footer: Updated at + Action */}
      <div className="mt-4 flex items-center justify-between border-t border-subtle/50 pt-3 text-[11px] text-muted">
        <span className="flex items-center gap-1">
          <ShieldCheck className="size-3 text-faint" />
          Updated {formatRelativeTime(service.updated_at)}
        </span>
        <span className="flex items-center gap-1 font-medium text-accent opacity-0 group-hover:opacity-100 transition-opacity">
          View details
          <ArrowRight className="size-3 transition-transform group-hover:translate-x-0.5" />
        </span>
      </div>
    </Link>
  );
}
