"use client";

import { useState } from "react";
import {
  AlertTriangle,
  Calendar,
  CheckCircle2,
  Clock,
  Loader2,
  Server,
  User,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useResolveIncident } from "@/lib/query/incidents";
import { formatRelativeTime } from "@/lib/utils/format";
import { useAuthStore } from "@/stores/authStore";
import type { IncidentItem, IncidentSeverity, IncidentStatus } from "@/types/incident";

function getSeverityBadge(severity: IncidentSeverity) {
  switch (severity) {
    case "sev1":
      return (
        <span className="inline-flex items-center rounded-md bg-rose-500/15 px-2.5 py-1 text-xs font-semibold text-rose-400 border border-rose-500/25 uppercase tracking-wide">
          SEV-1 Critical
        </span>
      );
    case "sev2":
      return (
        <span className="inline-flex items-center rounded-md bg-amber-500/15 px-2.5 py-1 text-xs font-semibold text-amber-400 border border-amber-500/25 uppercase tracking-wide">
          SEV-2 High
        </span>
      );
    case "sev3":
      return (
        <span className="inline-flex items-center rounded-md bg-blue-500/15 px-2.5 py-1 text-xs font-semibold text-blue-400 border border-blue-500/25 uppercase tracking-wide">
          SEV-3 Moderate
        </span>
      );
  }
}

function getStatusBadge(status: IncidentStatus) {
  switch (status) {
    case "open":
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-rose-500/10 px-3 py-1 text-xs font-medium text-rose-400 border border-rose-500/20">
          <span className="size-2 rounded-full bg-rose-400" />
          Open
        </span>
      );
    case "investigating":
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-500/10 px-3 py-1 text-xs font-medium text-amber-400 border border-amber-500/20">
          <span className="size-2 rounded-full bg-amber-400" />
          Investigating
        </span>
      );
    case "resolved":
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-400 border border-emerald-500/20">
          <span className="size-2 rounded-full bg-emerald-400" />
          Resolved
        </span>
      );
  }
}

interface IncidentDetailDialogProps {
  incident: IncidentItem | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function IncidentDetailDialog({
  incident,
  open,
  onOpenChange,
}: IncidentDetailDialogProps) {
  const currentUser = useAuthStore((s) => s.user);
  const canResolve =
    currentUser?.role === "admin" || currentUser?.role === "manager";

  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const resolveMutation = useResolveIncident();

  if (!incident) return null;

  const isResolved = incident.status === "resolved";

  const handleResolve = async () => {
    setErrorMessage(null);
    try {
      await resolveMutation.mutateAsync(incident.id);
      onOpenChange(false);
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      setErrorMessage(
        axiosErr.response?.data?.detail || "Failed to resolve incident."
      );
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg bg-surface border-subtle">
        <DialogHeader>
          <div className="flex items-center justify-between gap-2 pr-6">
            {getSeverityBadge(incident.severity)}
            {getStatusBadge(incident.status)}
          </div>
          <DialogTitle className="text-lg font-bold text-foreground mt-2 leading-snug">
            {incident.title}
          </DialogTitle>
          <DialogDescription className="text-xs text-muted">
            Incident ID: <span className="font-mono text-faint">{incident.id}</span>
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2 text-xs">
          {/* Service & Assignee Info */}
          <div className="grid grid-cols-2 gap-3 rounded-lg border border-subtle bg-surface-2/50 p-3">
            <div>
              <span className="flex items-center gap-1 text-[11px] font-medium text-faint uppercase tracking-wider">
                <Server className="size-3" />
                Impacted Service
              </span>
              <p className="mt-1 font-semibold text-foreground">
                {incident.service_name}
              </p>
            </div>

            <div>
              <span className="flex items-center gap-1 text-[11px] font-medium text-faint uppercase tracking-wider">
                <User className="size-3" />
                Assignee
              </span>
              <p className="mt-1 font-semibold text-foreground">
                {incident.assignee_name || "Unassigned"}
              </p>
            </div>
          </div>

          {/* Timestamps */}
          <div className="space-y-2 rounded-lg border border-subtle bg-surface-2/30 p-3 text-muted">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1.5 text-faint">
                <Clock className="size-3.5" />
                Created
              </span>
              <span className="font-medium text-foreground">
                {new Date(incident.created_at).toLocaleString()} (
                {formatRelativeTime(incident.created_at)})
              </span>
            </div>

            {incident.resolved_at && (
              <div className="flex items-center justify-between border-t border-subtle/50 pt-2">
                <span className="flex items-center gap-1.5 text-emerald-400">
                  <CheckCircle2 className="size-3.5" />
                  Resolved
                </span>
                <span className="font-medium text-emerald-400">
                  {new Date(incident.resolved_at).toLocaleString()} (
                  {formatRelativeTime(incident.resolved_at)})
                </span>
              </div>
            )}

            <div className="flex items-center justify-between border-t border-subtle/50 pt-2">
              <span className="flex items-center gap-1.5 text-faint">
                <Calendar className="size-3.5" />
                Last Updated
              </span>
              <span>{formatRelativeTime(incident.updated_at)}</span>
            </div>
          </div>

          {/* Error display */}
          {errorMessage && (
            <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-xs text-destructive flex items-center gap-2">
              <AlertTriangle className="size-4 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}
        </div>

        <DialogFooter className="gap-2 sm:gap-0">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => onOpenChange(false)}
            className="text-xs border-subtle"
          >
            Close
          </Button>

          {canResolve && !isResolved && (
            <Button
              type="button"
              size="sm"
              onClick={handleResolve}
              disabled={resolveMutation.isPending}
              className="gap-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium"
            >
              {resolveMutation.isPending ? (
                <>
                  <Loader2 className="size-3.5 animate-spin" />
                  Resolving...
                </>
              ) : (
                <>
                  <CheckCircle2 className="size-3.5" />
                  Resolve Incident
                </>
              )}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
