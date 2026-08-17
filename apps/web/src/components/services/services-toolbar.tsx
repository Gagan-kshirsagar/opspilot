"use client";

import { Search, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type {
  ServiceSortByField,
  ServiceStatus,
  SortDirection,
} from "@/types/service";

interface ServicesToolbarProps {
  search: string;
  onSearchChange: (value: string) => void;
  statusFilter: ServiceStatus | "";
  onStatusFilterChange: (status: ServiceStatus | "") => void;
  sortBy: ServiceSortByField;
  onSortByChange: (field: ServiceSortByField) => void;
  sortDir: SortDirection;
  onSortDirChange: (dir: SortDirection) => void;
  onResetFilters: () => void;
  hasActiveFilters: boolean;
}

export function ServicesToolbar({
  search,
  onSearchChange,
  statusFilter,
  onStatusFilterChange,
  sortBy,
  onSortByChange,
  sortDir,
  onSortDirChange,
  onResetFilters,
  hasActiveFilters,
}: ServicesToolbarProps) {
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
            placeholder="Search services…"
            className="h-8 pl-8 pr-8 text-xs bg-surface border-subtle"
            aria-label="Search services"
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

        {/* Status Filter */}
        <select
          value={statusFilter}
          onChange={(e) =>
            onStatusFilterChange(e.target.value as ServiceStatus | "")
          }
          aria-label="Filter by status"
          className="h-8 rounded-lg border border-subtle bg-surface px-2.5 text-xs text-foreground outline-none focus-visible:ring-2 focus-visible:ring-ring cursor-pointer"
        >
          <option value="">All Statuses</option>
          <option value="healthy">Healthy</option>
          <option value="degraded">Degraded</option>
          <option value="down">Down</option>
        </select>

        {/* Sort By */}
        <select
          value={sortBy}
          onChange={(e) => onSortByChange(e.target.value as ServiceSortByField)}
          aria-label="Sort by field"
          className="h-8 rounded-lg border border-subtle bg-surface px-2.5 text-xs text-foreground outline-none focus-visible:ring-2 focus-visible:ring-ring cursor-pointer"
        >
          <option value="name">Sort by Name</option>
          <option value="status">Sort by Status</option>
          <option value="uptime_pct">Sort by Uptime</option>
        </select>

        {/* Sort Direction Toggle */}
        <button
          type="button"
          onClick={() => onSortDirChange(sortDir === "asc" ? "desc" : "asc")}
          className="h-8 rounded-lg border border-subtle bg-surface px-2.5 text-xs font-medium text-muted hover:text-foreground outline-none focus-visible:ring-2 focus-visible:ring-ring cursor-pointer"
          aria-label="Toggle sort direction"
        >
          {sortDir.toUpperCase()}
        </button>

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
