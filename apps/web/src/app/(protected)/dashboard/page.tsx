"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Activity,
  AlertOctagon,
  AlertTriangle,
  ArrowRight,
  Bot,
  CheckCircle2,
  Clock,
  Radio,
  RefreshCw,
  Search,
  Server,
  ShieldCheck,
  Sparkles,
  Zap,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useIncidents } from "@/lib/query/incidents";
import { useServices } from "@/lib/query/services";
import { useAuthStore } from "@/stores/authStore";
import type { IncidentItem } from "@/types/incident";
import type { ServiceItem } from "@/types/service";

export default function DashboardPage() {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const [searchQuery, setSearchQuery] = useState("");

  // Fetch incidents & services
  const {
    data: incidentsData,
    isLoading: isLoadingIncidents,
    refetch: refetchIncidents,
    isFetching: isFetchingIncidents,
  } = useIncidents({ page: 1, page_size: 50 });

  const {
    data: services = [],
    isLoading: isLoadingServices,
    refetch: refetchServices,
  } = useServices();

  const incidents = useMemo(
    () => incidentsData?.items ?? [],
    [incidentsData?.items]
  );

  // Metrics computation
  const activeIncidents = useMemo(
    () => incidents.filter((inc) => inc.status !== "resolved"),
    [incidents]
  );

  const p1Count = useMemo(
    () => activeIncidents.filter((inc) => inc.severity === "sev1").length,
    [activeIncidents]
  );
  const p2Count = useMemo(
    () => activeIncidents.filter((inc) => inc.severity === "sev2").length,
    [activeIncidents]
  );
  const p3Count = useMemo(
    () => activeIncidents.filter((inc) => inc.severity === "sev3").length,
    [activeIncidents]
  );

  const healthyServicesCount = useMemo(
    () => services.filter((s) => s.status === "healthy").length,
    [services]
  );

  const healthPercentage = useMemo(() => {
    if (services.length === 0) return 100;
    return Math.round((healthyServicesCount / services.length) * 100);
  }, [services, healthyServicesCount]);

  const handleAskAI = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    router.push(`/chat?q=${encodeURIComponent(searchQuery.trim())}`);
  };

  const handleQuickPrompt = (promptText: string) => {
    router.push(`/chat?q=${encodeURIComponent(promptText)}`);
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 space-y-8 animate-slide-up">
      {/* ── Top Hero & Mission Control Bar ──────────────── */}
      <div className="relative overflow-hidden rounded-2xl border border-subtle bg-gradient-to-b from-surface via-surface to-surface-2 p-6 sm:p-8 shadow-sm">
        <div className="absolute right-0 top-0 -mr-16 -mt-16 size-64 rounded-full bg-accent/10 blur-3xl pointer-events-none" />
        <div className="absolute left-1/3 bottom-0 -mb-12 size-48 rounded-full bg-accent-2/10 blur-2xl pointer-events-none" />

        <div className="relative flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div className="space-y-2">
            <div className="flex items-center gap-2.5">
              <span className="relative flex size-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex rounded-full size-2.5 bg-emerald-500" />
              </span>
              <span className="text-xs font-semibold uppercase tracking-wider text-muted">
                Mission Control Live
              </span>
              <Badge variant="outline" className="text-[11px] font-mono border-subtle">
                v0.1.0-prod
              </Badge>
            </div>

            <h1 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
              Welcome back, {user?.name ?? "Engineer"}
            </h1>
            <p className="text-sm text-muted max-w-xl">
              OpsPilot AI is actively monitoring your services, runbooks, and telemetry.
              {activeIncidents.length > 0 ? (
                <span className="text-rose-400 font-medium ml-1">
                  {activeIncidents.length} active incident{activeIncidents.length > 1 ? "s" : ""} require attention.
                </span>
              ) : (
                <span className="text-emerald-400 font-medium ml-1">
                  All systems operating within normal parameters.
                </span>
              )}
            </p>
          </div>

          {/* Quick Action Buttons */}
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                refetchIncidents();
                refetchServices();
              }}
              disabled={isFetchingIncidents}
              className="gap-2 border-subtle hover:bg-surface-2 transition-all"
            >
              <RefreshCw className={`size-3.5 ${isFetchingIncidents ? "animate-spin" : ""}`} />
              Sync Telemetry
            </Button>
            <Link href="/chat">
              <Button size="sm" className="gap-2 bg-accent text-accent-foreground hover:bg-accent-hover font-medium">
                <Bot className="size-4" />
                Launch AI
              </Button>
            </Link>
          </div>
        </div>

        {/* ── AI Quick Prompt Input ────────────────────── */}
        <form onSubmit={handleAskAI} className="relative mt-6">
          <div className="relative flex items-center rounded-xl border border-subtle bg-surface/90 shadow-inner backdrop-blur-md focus-within:border-accent focus-within:ring-2 focus-within:ring-accent/20 transition-all">
            <div className="pl-4 text-muted">
              <Search className="size-4 text-accent" />
            </div>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Ask OpsPilot anything... (e.g., 'What caused the payment latency spike?', 'Show runbook for redis-cluster')"
              className="w-full bg-transparent px-3 py-3 text-sm text-foreground placeholder:text-muted focus:outline-none"
            />
            <div className="pr-2">
              <Button type="submit" size="sm" disabled={!searchQuery.trim()} className="gap-1.5 h-8">
                <Sparkles className="size-3.5" />
                Ask AI
              </Button>
            </div>
          </div>

          {/* Quick chip suggestions */}
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <span className="text-[11px] font-medium text-faint uppercase tracking-wider">
              Suggestions:
            </span>
            {[
              "Investigate recent database connection errors",
              "Check checkout service rollback procedure",
              "Summarize all Sev1 critical incidents",
            ].map((chip) => (
              <button
                key={chip}
                type="button"
                onClick={() => handleQuickPrompt(chip)}
                className="inline-flex items-center gap-1 rounded-full border border-subtle bg-surface/60 px-2.5 py-1 text-xs text-muted hover:border-accent/40 hover:text-foreground hover:bg-surface transition-all cursor-pointer"
              >
                <Zap className="size-2.5 text-accent" />
                {chip}
              </button>
            ))}
          </div>
        </form>
      </div>

      {/* ── KPI Stat Cards Grid ─────────────────────────── */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* 1. Active Incidents Card */}
        <div className="rounded-xl border border-subtle bg-surface p-5 shadow-sm transition-all hover:border-subtle/80 hover:shadow-md">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-muted">
              Active Incidents
            </span>
            <div className={`p-2 rounded-lg ${activeIncidents.length > 0 ? "bg-rose-500/10 text-rose-400" : "bg-emerald-500/10 text-emerald-400"}`}>
              {activeIncidents.length > 0 ? <AlertOctagon className="size-4" /> : <CheckCircle2 className="size-4" />}
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold tracking-tight text-foreground">
              {isLoadingIncidents ? "..." : activeIncidents.length}
            </span>
            <span className="text-xs text-muted">
              {activeIncidents.length === 0 ? "All clear" : "under triage"}
            </span>
          </div>
          <div className="mt-4 flex items-center gap-2 pt-3 border-t border-subtle text-xs text-muted">
            <span className="inline-flex items-center gap-1 text-rose-400 font-medium">
              <span className="size-1.5 rounded-full bg-rose-400" />
              {p1Count} Sev1
            </span>
            <span>·</span>
            <span className="inline-flex items-center gap-1 text-amber-400 font-medium">
              <span className="size-1.5 rounded-full bg-amber-400" />
              {p2Count} Sev2
            </span>
            <span>·</span>
            <span className="inline-flex items-center gap-1 text-muted font-medium">
              {p3Count} Sev3
            </span>
          </div>
        </div>

        {/* 2. Service Health Card */}
        <div className="rounded-xl border border-subtle bg-surface p-5 shadow-sm transition-all hover:border-subtle/80 hover:shadow-md">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-muted">
              System Ecosystem
            </span>
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
              <Server className="size-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold tracking-tight text-foreground">
              {isLoadingServices ? "..." : `${healthPercentage}%`}
            </span>
            <span className="text-xs text-emerald-400 font-medium">
              Operational
            </span>
          </div>
          <div className="mt-4 flex items-center justify-between pt-3 border-t border-subtle text-xs text-muted">
            <span>{healthyServicesCount} / {services.length} services healthy</span>
            <Link href="/services" className="text-accent hover:underline inline-flex items-center gap-1">
              View <ArrowRight className="size-3" />
            </Link>
          </div>
        </div>

        {/* 3. AI Copilot Status Card */}
        <div className="rounded-xl border border-subtle bg-surface p-5 shadow-sm transition-all hover:border-subtle/80 hover:shadow-md">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-muted">
              AI Agent Status
            </span>
            <div className="p-2 rounded-lg bg-accent/10 text-accent">
              <Bot className="size-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold tracking-tight text-foreground">
              Ready
            </span>
            <span className="text-xs text-accent font-medium">
              Gemini 2.5 Flash
            </span>
          </div>
          <div className="mt-4 flex items-center justify-between pt-3 border-t border-subtle text-xs text-muted">
            <span className="inline-flex items-center gap-1 text-emerald-400">
              <Radio className="size-3 animate-pulse" /> RAG & Vectors Active
            </span>
            <Link href="/chat" className="text-accent hover:underline">
              Ask
            </Link>
          </div>
        </div>

        {/* 4. Security & Role Card */}
        <div className="rounded-xl border border-subtle bg-surface p-5 shadow-sm transition-all hover:border-subtle/80 hover:shadow-md">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-muted">
              Security & Auth
            </span>
            <div className="p-2 rounded-lg bg-accent-2/10 text-accent-2">
              <ShieldCheck className="size-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold tracking-tight text-foreground capitalize">
              {user?.role ?? "Guest"}
            </span>
            <span className="text-xs text-muted">access level</span>
          </div>
          <div className="mt-4 flex items-center justify-between pt-3 border-t border-subtle text-xs text-muted">
            <span className="truncate max-w-[140px]">{user?.email}</span>
            <Link href="/users" className="text-accent hover:underline inline-flex items-center gap-1">
              Users <ArrowRight className="size-3" />
            </Link>
          </div>
        </div>
      </div>

      {/* ── Main Content Split (Active Incidents & Service Health) ── */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left 2 Cols: Live Incidents Stream */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity className="size-4 text-accent" />
              <h2 className="text-base font-semibold text-foreground">
                Active Incident Queue
              </h2>
            </div>
            <Link
              href="/incidents"
              className="text-xs font-medium text-accent hover:text-accent-hover inline-flex items-center gap-1"
            >
              View all ({incidents.length}) <ArrowRight className="size-3" />
            </Link>
          </div>

          {isLoadingIncidents ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-24 animate-pulse rounded-xl border border-subtle bg-surface" />
              ))}
            </div>
          ) : activeIncidents.length === 0 ? (
            <div className="rounded-xl border border-dashed border-subtle bg-surface/40 p-8 text-center">
              <CheckCircle2 className="mx-auto size-8 text-emerald-400" />
              <h3 className="mt-2 text-sm font-semibold text-foreground">
                No active incidents!
              </h3>
              <p className="mt-1 text-xs text-muted">
                All production services and endpoints are operating within normal SLO thresholds.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {activeIncidents.slice(0, 4).map((inc) => (
                <IncidentCard key={inc.id} incident={inc} onTriage={() => handleQuickPrompt(`Triage and diagnose incident: "${inc.title}". Severity: ${inc.severity}. Status: ${inc.status}. Service: ${inc.service_name}`)} />
              ))}
            </div>
          )}
        </div>

        {/* Right 1 Col: Infrastructure Health & Quick Actions */}
        <div className="space-y-6">
          {/* Service Matrix */}
          <div className="rounded-xl border border-subtle bg-surface p-5 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-foreground">
                Service Telemetry
              </h3>
              <Link href="/services" className="text-xs text-accent hover:underline">
                Manage
              </Link>
            </div>

            {isLoadingServices ? (
              <div className="space-y-2">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="h-10 animate-pulse rounded-lg bg-surface-2" />
                ))}
              </div>
            ) : services.length === 0 ? (
              <p className="text-xs text-muted py-2">No services registered.</p>
            ) : (
              <div className="space-y-2.5">
                {services.slice(0, 5).map((service) => (
                  <ServiceRow key={service.id} service={service} />
                ))}
              </div>
            )}
          </div>

          {/* Quick Ops Shortcuts */}
          <div className="rounded-xl border border-subtle bg-surface p-5 shadow-sm space-y-3">
            <h3 className="text-sm font-semibold text-foreground">
              Operational Shortcuts
            </h3>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <Link
                href="/incidents"
                className="flex flex-col gap-1 p-3 rounded-lg border border-subtle hover:bg-surface-2 transition-all text-muted hover:text-foreground"
              >
                <AlertTriangle className="size-4 text-amber-400" />
                <span className="font-medium text-foreground">Incidents</span>
                <span className="text-[11px]">Triage board</span>
              </Link>
              <Link
                href="/chat"
                className="flex flex-col gap-1 p-3 rounded-lg border border-subtle hover:bg-surface-2 transition-all text-muted hover:text-foreground"
              >
                <Bot className="size-4 text-accent" />
                <span className="font-medium text-foreground">AI Copilot</span>
                <span className="text-[11px]">Runbook RAG</span>
              </Link>
              <Link
                href="/services"
                className="flex flex-col gap-1 p-3 rounded-lg border border-subtle hover:bg-surface-2 transition-all text-muted hover:text-foreground"
              >
                <Server className="size-4 text-emerald-400" />
                <span className="font-medium text-foreground">Services</span>
                <span className="text-[11px]">Architecture</span>
              </Link>
              <Link
                href="/users"
                className="flex flex-col gap-1 p-3 rounded-lg border border-subtle hover:bg-surface-2 transition-all text-muted hover:text-foreground"
              >
                <ShieldCheck className="size-4 text-accent-2" />
                <span className="font-medium text-foreground">Team</span>
                <span className="text-[11px]">RBAC roles</span>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Subcomponents ──────────────────────────────────────────

function IncidentCard({
  incident,
  onTriage,
}: {
  incident: IncidentItem;
  onTriage: () => void;
}) {
  const isSev1 = incident.severity === "sev1";
  const isSev2 = incident.severity === "sev2";

  return (
    <div className="rounded-xl border border-subtle bg-surface p-4 shadow-sm hover:border-subtle/80 transition-all space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span
              className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold uppercase tracking-wider ${isSev1
                  ? "bg-rose-500/15 text-rose-400 border border-rose-500/20"
                  : isSev2
                    ? "bg-amber-500/15 text-amber-400 border border-amber-500/20"
                    : "bg-surface-2 text-muted border border-subtle"
                }`}
            >
              {incident.severity}
            </span>
            <span className="text-xs font-semibold text-foreground truncate max-w-sm sm:max-w-md">
              {incident.title}
            </span>
          </div>
          <div className="flex items-center gap-3 text-xs text-muted">
            <span className="inline-flex items-center gap-1">
              <Clock className="size-3" />
              {new Date(incident.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
            </span>
            {incident.service_name && (
              <span>
                Service: <span className="font-mono text-foreground">{incident.service_name}</span>
              </span>
            )}
          </div>
        </div>

        <Button
          size="sm"
          variant="outline"
          onClick={onTriage}
          className="gap-1.5 h-7 text-xs border-accent/30 text-accent hover:bg-accent/10 hover:text-accent shrink-0"
        >
          <Bot className="size-3" />
          Triage with AI
        </Button>
      </div>
    </div>
  );
}

function ServiceRow({ service }: { service: ServiceItem }) {
  const isOperational = service.status === "healthy";

  return (
    <Link
      href={`/services/${service.id}`}
      className="flex items-center justify-between p-2 rounded-lg hover:bg-surface-2 transition-all text-xs"
    >
      <div className="flex items-center gap-2">
        <span
          className={`size-2 rounded-full ${isOperational ? "bg-emerald-400" : "bg-rose-400 animate-pulse"
            }`}
        />
        <span className="font-medium text-foreground">{service.name}</span>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-[11px] font-mono text-muted">
          {service.uptime_pct}%
        </span>
        <Badge
          variant="outline"
          className={`text-[10px] py-0 px-1.5 capitalize ${isOperational
              ? "text-emerald-400 border-emerald-500/20 bg-emerald-500/10"
              : "text-rose-400 border-rose-500/20 bg-rose-500/10"
            }`}
        >
          {service.status}
        </Badge>
      </div>
    </Link>
  );
}
