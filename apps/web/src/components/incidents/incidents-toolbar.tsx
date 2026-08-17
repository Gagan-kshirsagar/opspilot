"use client";

import { Search, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useServices } from "@/lib/query/services";
import type {
  IncidentSeverity,
  IncidentStatus,
} from "@/types/incident";

interface IncidentsToolbarProps {
  search: string;
  onSearchChange: (value: string) => void;
  severityFilter: IncidentSeverity | "";
  onSeverityFilterChange: (severity: IncidentSeverity | "") => void;
  statusFilter: IncidentStatus | "";
  onStatusFilterChange: (status: IncidentStatus | "") => void;
  serviceFilter: string;
  onServiceFilterChange: (serviceId: string) => void;
  onResetFilters: () => void;
  hasActiveFilters: boolean;
}

export function IncidentsToolbar({
  search,
  onSearchChange,
  severityFilter,
  onSeverityFilterChange,
  statusFilter,
  onStatusFilterChange,
  serviceFilter,
  onServiceFilterChange,
  onResetFilters,
  hasActiveFilters,
}: IncidentsToolbarProps) {
  const { data: services = [] } = useServices();

  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      {/* Search & Filters */}
      <div className="flex flex-1 flex-wrap items-center gap-2">
        {/* Search */}
        <div className="relative min-w-[200px] max-w-xs flex-1">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted" />
          <Input
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search incident title…"
            className="h-8 pl-8 pr-8 text-xs bg-surface border-subtle"
            aria-label="Search incidents"
          />
          {search && (
            <button
              type="button"
              onClick={() => onSearchChange("")}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-muted hover:text-foreground"
              aria-label="Clear search"
            >
              <X className="size-3.5" />
            </button>
          )}
        </div>

        {/* Severity Filter */}
        <select
          value={severityFilter}
          onChange={(e) =>
            onSeverityFilterChange(e.target.value as IncidentSeverity | "")
          }
          aria-label="Filter by severity"
          className="h-8 rounded-lg border border-subtle bg-surface px-2.5 text-xs text-foreground outline-none focus-visible:ring-2 focus-visible:ring-ring cursor-pointer"
        >
          <option value="">All Severities</option>
          <option value="sev1">SEV-1 (Critical)</option>
          <option value="sev2">SEV-2 (High)</option>
          <option value="sev3">SEV-3 (Moderate)</option>
        </select>

        {/* Status Filter */}
        <select
          value={statusFilter}
          onChange={(e) =>
            onStatusFilterChange(e.target.value as IncidentStatus | "")
          }
          aria-label="Filter by status"
          className="h-8 rounded-lg border border-subtle bg-surface px-2.5 text-xs text-foreground outline-none focus-visible:ring-2 focus-visible:ring-ring cursor-pointer"
        >
          <option value="">All Statuses</option>
          <option value="open">Open</option>
          <option value="investigating">Investigating</option>
          <option value="resolved">Resolved</option>
        </select>

        {/* Service Filter */}
        <select
          value={serviceFilter}
          onChange={(e) => onServiceFilterChange(e.target.value)}
          aria-label="Filter by service"
          className="h-8 rounded-lg border border-subtle bg-surface px-2.5 text-xs text-foreground outline-none focus-visible:ring-2 focus-visible:ring-ring cursor-pointer"
        >
          <option value="">All Services</option>
          {services.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>

        {/* Reset Filter Button */}
        {hasActiveFilters && (
          <Button
            variant="ghost"
            size="xs"
            onClick={onResetFilters}
            className="text-xs text-muted hover:text-foreground"
          >
            Reset
          </Button>
        )}
      </div>
    </div>
  );
}
