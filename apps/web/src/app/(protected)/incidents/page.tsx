"use client";

import { useMemo, useState } from "react";
import { AlertTriangle } from "lucide-react";

import { IncidentDetailDialog } from "@/components/incidents/incident-detail-drawer";
import { IncidentsTable } from "@/components/incidents/incidents-table";
import { IncidentsToolbar } from "@/components/incidents/incidents-toolbar";
import { useDebounce } from "@/hooks/use-debounce";
import { useIncidents } from "@/lib/query/incidents";
import type {
  IncidentItem,
  IncidentSeverity,
  IncidentSortByField,
  IncidentStatus,
  SortDirection,
} from "@/types/incident";

export default function IncidentsPage() {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [sortBy, setSortBy] = useState<IncidentSortByField>("created_at");
  const [sortDir, setSortDir] = useState<SortDirection>("desc");
  const [search, setSearch] = useState("");
  const [severityFilter, setSeverityFilter] = useState<IncidentSeverity | "">("");
  const [statusFilter, setStatusFilter] = useState<IncidentStatus | "">("");
  const [serviceFilter, setServiceFilter] = useState("");

  const [selectedIncident, setSelectedIncident] = useState<IncidentItem | null>(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);

  const debouncedSearch = useDebounce(search, 300);

  const queryParams = useMemo(() => {
    return {
      page,
      page_size: pageSize,
      sort_by: sortBy,
      sort_dir: sortDir,
      search: debouncedSearch.trim() || undefined,
      severity: severityFilter ? [severityFilter] : undefined,
      status: statusFilter ? [statusFilter] : undefined,
      service_id: serviceFilter || undefined,
    };
  }, [
    page,
    pageSize,
    sortBy,
    sortDir,
    debouncedSearch,
    severityFilter,
    statusFilter,
    serviceFilter,
  ]);

  const {
    data: incidentsData,
    isLoading,
    isError,
    error,
    refetch,
  } = useIncidents(queryParams);

  const hasActiveFilters = Boolean(
    search.trim() || severityFilter || statusFilter || serviceFilter
  );

  const handleResetFilters = () => {
    setSearch("");
    setSeverityFilter("");
    setStatusFilter("");
    setServiceFilter("");
    setPage(1);
  };

  const handleSortChange = (
    newSortBy: IncidentSortByField,
    newSortDir: SortDirection
  ) => {
    setSortBy(newSortBy);
    setSortDir(newSortDir);
    setPage(1);
  };

  const handleSelectIncident = (incident: IncidentItem) => {
    setSelectedIncident(incident);
    setIsDetailOpen(true);
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 space-y-6 animate-slide-up">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <AlertTriangle className="size-5 text-accent" />
            <h1 className="text-xl font-bold tracking-tight text-foreground sm:text-2xl">
              Incidents
            </h1>
          </div>
          <p className="mt-1 text-xs text-muted">
            Track, triage, and resolve active service disruptions and historical incidents.
          </p>
        </div>
      </div>

      {/* Toolbar */}
      <IncidentsToolbar
        search={search}
        onSearchChange={(v) => {
          setSearch(v);
          setPage(1);
        }}
        severityFilter={severityFilter}
        onSeverityFilterChange={(s) => {
          setSeverityFilter(s);
          setPage(1);
        }}
        statusFilter={statusFilter}
        onStatusFilterChange={(st) => {
          setStatusFilter(st);
          setPage(1);
        }}
        serviceFilter={serviceFilter}
        onServiceFilterChange={(srv) => {
          setServiceFilter(srv);
          setPage(1);
        }}
        onResetFilters={handleResetFilters}
        hasActiveFilters={hasActiveFilters}
      />

      {/* Table */}
      <IncidentsTable
        data={incidentsData?.items || []}
        total={incidentsData?.total || 0}
        page={page}
        pageSize={pageSize}
        sortBy={sortBy}
        sortDir={sortDir}
        isLoading={isLoading}
        isError={isError}
        error={error}
        onPageChange={setPage}
        onPageSizeChange={(ps) => {
          setPageSize(ps);
          setPage(1);
        }}
        onSortChange={handleSortChange}
        onSelectIncident={handleSelectIncident}
        onRetry={() => refetch()}
        onResetFilters={handleResetFilters}
      />

      {/* Incident Detail Drawer/Modal */}
      <IncidentDetailDialog
        incident={selectedIncident}
        open={isDetailOpen}
        onOpenChange={setIsDetailOpen}
      />
    </div>
  );
}
