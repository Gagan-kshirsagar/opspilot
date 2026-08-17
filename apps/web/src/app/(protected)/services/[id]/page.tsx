"use client";

import { use } from "react";
import Link from "next/link";
import {
  Activity,
  AlertTriangle,
  ArrowLeft,
  Calendar,
  CheckCircle2,
  RotateCcw,
  Server,
  ShieldCheck,
  User,
} from "lucide-react";

import { getServiceStatusBadge } from "@/components/services/service-card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useIncidents } from "@/lib/query/incidents";
import { useService } from "@/lib/query/services";
import { formatRelativeTime } from "@/lib/utils/format";
import type { IncidentSeverity, IncidentStatus } from "@/types/incident";

function getIncidentSeverityBadge(severity: IncidentSeverity) {
  switch (severity) {
    case "sev1":
      return (
        <span className="inline-flex items-center rounded-md bg-rose-500/15 px-2 py-0.5 text-xs font-semibold text-rose-400 border border-rose-500/25 uppercase tracking-wide">
          SEV-1
        </span>
      );
    case "sev2":
      return (
        <span className="inline-flex items-center rounded-md bg-amber-500/15 px-2 py-0.5 text-xs font-semibold text-amber-400 border border-amber-500/25 uppercase tracking-wide">
          SEV-2
        </span>
      );
    case "sev3":
      return (
        <span className="inline-flex items-center rounded-md bg-blue-500/15 px-2 py-0.5 text-xs font-semibold text-blue-400 border border-blue-500/25 uppercase tracking-wide">
          SEV-3
        </span>
      );
  }
}

function getIncidentStatusBadge(status: IncidentStatus) {
  switch (status) {
    case "open":
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-rose-500/10 px-2.5 py-0.5 text-xs font-medium text-rose-400 border border-rose-500/20">
          <span className="size-1.5 rounded-full bg-rose-400" />
          Open
        </span>
      );
    case "investigating":
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-500/10 px-2.5 py-0.5 text-xs font-medium text-amber-400 border border-amber-500/20">
          <span className="size-1.5 rounded-full bg-amber-400" />
          Investigating
        </span>
      );
    case "resolved":
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-medium text-emerald-400 border border-emerald-500/20">
          <span className="size-1.5 rounded-full bg-emerald-400" />
          Resolved
        </span>
      );
  }
}

interface ServiceDetailPageProps {
  params: Promise<{ id: string }>;
}

export default function ServiceDetailPage({ params }: ServiceDetailPageProps) {
  const { id } = use(params);

  const {
    data: service,
    isLoading: isServiceLoading,
    isError: isServiceError,
    error: serviceError,
    refetch: refetchService,
  } = useService(id);

  const {
    data: incidentsData,
    isLoading: isIncidentsLoading,
  } = useIncidents({
    service_id: id,
    page: 1,
    page_size: 20,
    sort_by: "created_at",
    sort_dir: "desc",
  });

  if (isServiceLoading) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 space-y-6 animate-slide-up">
        <div className="flex items-center gap-3">
          <Skeleton className="size-8 rounded-lg" />
          <Skeleton className="h-6 w-48" />
        </div>
        <div className="rounded-xl border border-subtle bg-surface p-6 space-y-4">
          <Skeleton className="h-6 w-1/3" />
          <Skeleton className="h-4 w-full" />
          <div className="grid grid-cols-3 gap-4 pt-4">
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
          </div>
        </div>
      </div>
    );
  }

  if (isServiceError || !service) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 animate-slide-up">
        <div className="flex min-h-[350px] flex-col items-center justify-center rounded-xl border border-destructive/30 bg-destructive/5 p-8 text-center">
          <div className="flex size-12 items-center justify-center rounded-full bg-destructive/10 text-destructive mb-3">
            <AlertTriangle className="size-6" />
          </div>
          <h3 className="text-sm font-semibold text-foreground">
            Failed to load service details
          </h3>
          <p className="mt-1 max-w-sm text-xs text-muted">
            {serviceError?.message || "Service could not be found."}
          </p>
          <div className="mt-4 flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetchService()}
              className="gap-1.5 text-xs border-subtle"
            >
              <RotateCcw className="size-3.5" />
              Retry
            </Button>
            <Link href="/services">
              <Button variant="ghost" size="sm" className="text-xs">
                Back to Services
              </Button>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const incidents = incidentsData?.items || [];
  const activeIncidents = incidents.filter(
    (i) => i.status === "open" || i.status === "investigating"
  );
  const resolvedIncidents = incidents.filter((i) => i.status === "resolved");

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 space-y-6 animate-slide-up">
      {/* Top navigation */}
      <div>
        <Link
          href="/services"
          className="inline-flex items-center gap-1.5 text-xs text-muted hover:text-foreground transition-colors mb-2"
        >
          <ArrowLeft className="size-3.5" />
          Back to services
        </Link>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-xl bg-surface-2 border border-subtle">
              <Server className="size-5 text-accent" />
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h1 className="text-xl font-bold tracking-tight text-foreground sm:text-2xl">
                  {service.name}
                </h1>
                {getServiceStatusBadge(service.status)}
              </div>
              <p className="text-xs text-muted mt-0.5">
                Service ID: <span className="font-mono text-faint">{service.id}</span>
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-subtle bg-surface p-4">
          <div className="flex items-center gap-2 text-faint text-xs font-medium uppercase tracking-wider">
            <Activity className="size-4" />
            Uptime SLA
          </div>
          <p className="mt-2 text-2xl font-bold text-foreground">
            {service.uptime_pct.toFixed(2)}%
          </p>
          <p className="mt-1 text-[11px] text-muted">Rolling 30-day availability</p>
        </div>

        <div className="rounded-xl border border-subtle bg-surface p-4">
          <div className="flex items-center gap-2 text-faint text-xs font-medium uppercase tracking-wider">
            <User className="size-4" />
            Service Owner
          </div>
          <p className="mt-2 text-base font-semibold text-foreground truncate">
            {service.owner_name}
          </p>
          <p className="mt-1 text-[11px] text-muted">Responsible on-call point of contact</p>
        </div>

        <div className="rounded-xl border border-subtle bg-surface p-4">
          <div className="flex items-center gap-2 text-faint text-xs font-medium uppercase tracking-wider">
            <AlertTriangle className="size-4" />
            Active Incidents
          </div>
          <p className={`mt-2 text-2xl font-bold ${service.open_incident_count > 0 ? "text-amber-400" : "text-emerald-400"}`}>
            {service.open_incident_count}
          </p>
          <p className="mt-1 text-[11px] text-muted">Open or currently investigating</p>
        </div>
      </div>

      {/* Service Details & Notes */}
      <div className="rounded-xl border border-subtle bg-surface p-5 space-y-3">
        <h2 className="text-sm font-semibold text-foreground">System Description</h2>
        <p className="text-xs text-muted leading-relaxed">
          {service.note || "No additional documentation provided for this service."}
        </p>
        <div className="flex flex-wrap gap-4 border-t border-subtle/50 pt-3 text-xs text-faint">
          <span className="flex items-center gap-1.5">
            <Calendar className="size-3.5" />
            Created {new Date(service.created_at).toLocaleDateString()}
          </span>
          <span className="flex items-center gap-1.5">
            <ShieldCheck className="size-3.5" />
            Last updated {formatRelativeTime(service.updated_at)}
          </span>
        </div>
      </div>

      {/* Associated Incidents Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-foreground">
              Incident History
            </h2>
            <p className="text-xs text-muted">
              Recent operational events and outages associated with {service.name}.
            </p>
          </div>
          <Link href="/incidents">
            <Button variant="outline" size="xs" className="text-xs border-subtle">
              View All Incidents
            </Button>
          </Link>
        </div>

        {isIncidentsLoading ? (
          <div className="space-y-2">
            <Skeleton className="h-14 w-full rounded-lg" />
            <Skeleton className="h-14 w-full rounded-lg" />
          </div>
        ) : incidents.length === 0 ? (
          <div className="flex min-h-[140px] flex-col items-center justify-center rounded-xl border border-dashed border-subtle bg-surface/50 p-6 text-center">
            <CheckCircle2 className="size-6 text-emerald-400 mb-2" />
            <p className="text-xs font-medium text-foreground">No incidents reported</p>
            <p className="text-[11px] text-muted">This service has a clean incident record.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {activeIncidents.length > 0 && (
              <div className="space-y-2">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-amber-400">
                  Active ({activeIncidents.length})
                </h3>
                <div className="space-y-2">
                  {activeIncidents.map((inc) => (
                    <div
                      key={inc.id}
                      className="flex items-center justify-between rounded-lg border border-amber-500/20 bg-surface p-3 text-xs"
                    >
                      <div className="flex items-center gap-3">
                        {getIncidentSeverityBadge(inc.severity)}
                        <span className="font-medium text-foreground">{inc.title}</span>
                      </div>
                      <div className="flex items-center gap-3 text-muted">
                        <span>{formatRelativeTime(inc.created_at)}</span>
                        {getIncidentStatusBadge(inc.status)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {resolvedIncidents.length > 0 && (
              <div className="space-y-2 pt-2">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-faint">
                  Resolved History ({resolvedIncidents.length})
                </h3>
                <div className="space-y-2">
                  {resolvedIncidents.slice(0, 5).map((inc) => (
                    <div
                      key={inc.id}
                      className="flex items-center justify-between rounded-lg border border-subtle bg-surface/60 p-3 text-xs"
                    >
                      <div className="flex items-center gap-3">
                        {getIncidentSeverityBadge(inc.severity)}
                        <span className="text-foreground">{inc.title}</span>
                      </div>
                      <div className="flex items-center gap-3 text-muted">
                        <span>Resolved {formatRelativeTime(inc.resolved_at)}</span>
                        {getIncidentStatusBadge(inc.status)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
