"use client";

import { useMemo, useState } from "react";
import { Server } from "lucide-react";

import { ServicesList } from "@/components/services/services-list";
import { ServicesToolbar } from "@/components/services/services-toolbar";
import { useDebounce } from "@/hooks/use-debounce";
import { useServices } from "@/lib/query/services";
import type {
  ServiceSortByField,
  ServiceStatus,
  SortDirection,
} from "@/types/service";

export default function ServicesPage() {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<ServiceStatus | "">("");
  const [sortBy, setSortBy] = useState<ServiceSortByField>("name");
  const [sortDir, setSortDir] = useState<SortDirection>("asc");

  const debouncedSearch = useDebounce(search, 300);

  const queryParams = useMemo(() => {
    return {
      search: debouncedSearch.trim() || undefined,
      status: statusFilter ? [statusFilter] : undefined,
      sort_by: sortBy,
      sort_dir: sortDir,
    };
  }, [debouncedSearch, statusFilter, sortBy, sortDir]);

  const {
    data: services = [],
    isLoading,
    isError,
    error,
    refetch,
  } = useServices(queryParams);

  const hasActiveFilters = Boolean(
    search.trim() || statusFilter || sortBy !== "name" || sortDir !== "asc"
  );

  const handleResetFilters = () => {
    setSearch("");
    setStatusFilter("");
    setSortBy("name");
    setSortDir("asc");
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 space-y-6 animate-slide-up">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Server className="size-5 text-accent" />
            <h1 className="text-xl font-bold tracking-tight text-foreground sm:text-2xl">
              Services
            </h1>
          </div>
          <p className="mt-1 text-xs text-muted">
            Monitor health, uptime SLAs, and operational status across internal services.
          </p>
        </div>
      </div>

      {/* Toolbar */}
      <ServicesToolbar
        search={search}
        onSearchChange={setSearch}
        statusFilter={statusFilter}
        onStatusFilterChange={setStatusFilter}
        sortBy={sortBy}
        onSortByChange={setSortBy}
        sortDir={sortDir}
        onSortDirChange={setSortDir}
        onResetFilters={handleResetFilters}
        hasActiveFilters={hasActiveFilters}
      />

      {/* Services Grid */}
      <ServicesList
        services={services}
        isLoading={isLoading}
        isError={isError}
        error={error}
        onRetry={() => refetch()}
        onResetFilters={handleResetFilters}
        hasActiveFilters={hasActiveFilters}
      />
    </div>
  );
}
