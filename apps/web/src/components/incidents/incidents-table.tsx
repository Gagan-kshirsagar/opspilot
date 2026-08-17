"use client";

import { useMemo } from "react";
import {
  type ColumnDef,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table";
import {
  AlertCircle,
  AlertTriangle,
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Eye,
  MoreHorizontal,
  RotateCcw,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatRelativeTime } from "@/lib/utils/format";
import { useAuthStore } from "@/stores/authStore";
import type {
  IncidentItem,
  IncidentSeverity,
  IncidentSortByField,
  IncidentStatus,
  SortDirection,
} from "@/types/incident";

interface IncidentsTableProps {
  data: IncidentItem[];
  total: number;
  page: number;
  pageSize: number;
  sortBy: IncidentSortByField;
  sortDir: SortDirection;
  isLoading: boolean;
  isError: boolean;
  error?: Error | null;
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: number) => void;
  onSortChange: (sortBy: IncidentSortByField, sortDir: SortDirection) => void;
  onSelectIncident: (incident: IncidentItem) => void;
  onRetry: () => void;
  onResetFilters: () => void;
}

export function getIncidentSeverityBadge(severity: IncidentSeverity) {
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

export function getIncidentStatusBadge(status: IncidentStatus) {
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

export function IncidentsTable({
  data,
  total,
  page,
  pageSize,
  sortBy,
  sortDir,
  isLoading,
  isError,
  error,
  onPageChange,
  onPageSizeChange,
  onSortChange,
  onSelectIncident,
  onRetry,
  onResetFilters,
}: IncidentsTableProps) {
  const currentUser = useAuthStore((s) => s.user);
  const canResolve =
    currentUser?.role === "admin" || currentUser?.role === "manager";

  const handleHeaderSort = (field: IncidentSortByField) => {
    if (sortBy === field) {
      onSortChange(field, sortDir === "asc" ? "desc" : "asc");
    } else {
      onSortChange(field, "asc");
    }
  };

  const renderSortIcon = (field: IncidentSortByField) => {
    if (sortBy !== field) {
      return <ArrowUpDown className="size-3 text-faint" />;
    }
    return sortDir === "asc" ? (
      <ArrowUp className="size-3 text-accent" />
    ) : (
      <ArrowDown className="size-3 text-accent" />
    );
  };

  const columns = useMemo<ColumnDef<IncidentItem>[]>(
    () => [
      {
        accessorKey: "title",
        header: () => (
          <button
            type="button"
            onClick={() => handleHeaderSort("title")}
            className="flex items-center gap-1 font-semibold text-foreground hover:text-accent transition-colors"
          >
            Title {renderSortIcon("title")}
          </button>
        ),
        cell: ({ row }) => (
          <span className="font-medium text-foreground text-xs hover:text-accent cursor-pointer">
            {row.original.title}
          </span>
        ),
      },
      {
        accessorKey: "severity",
        header: () => (
          <button
            type="button"
            onClick={() => handleHeaderSort("severity")}
            className="flex items-center gap-1 font-semibold text-foreground hover:text-accent transition-colors"
          >
            Severity {renderSortIcon("severity")}
          </button>
        ),
        cell: ({ row }) => getIncidentSeverityBadge(row.original.severity),
      },
      {
        accessorKey: "status",
        header: () => (
          <button
            type="button"
            onClick={() => handleHeaderSort("status")}
            className="flex items-center gap-1 font-semibold text-foreground hover:text-accent transition-colors"
          >
            Status {renderSortIcon("status")}
          </button>
        ),
        cell: ({ row }) => getIncidentStatusBadge(row.original.status),
      },
      {
        accessorKey: "service_name",
        header: () => (
          <button
            type="button"
            onClick={() => handleHeaderSort("service_name")}
            className="flex items-center gap-1 font-semibold text-foreground hover:text-accent transition-colors"
          >
            Service {renderSortIcon("service_name")}
          </button>
        ),
        cell: ({ row }) => (
          <span className="text-xs text-foreground font-medium">
            {row.original.service_name}
          </span>
        ),
      },
      {
        accessorKey: "assignee_name",
        header: "Assignee",
        cell: ({ row }) => (
          <span className="text-xs text-muted">
            {row.original.assignee_name || "Unassigned"}
          </span>
        ),
      },
      {
        accessorKey: "created_at",
        header: () => (
          <button
            type="button"
            onClick={() => handleHeaderSort("created_at")}
            className="flex items-center gap-1 font-semibold text-foreground hover:text-accent transition-colors"
          >
            Created {renderSortIcon("created_at")}
          </button>
        ),
        cell: ({ row }) => (
          <span className="text-xs text-muted">
            {formatRelativeTime(row.original.created_at)}
          </span>
        ),
      },
      {
        id: "actions",
        header: "",
        cell: ({ row }) => {
          const inc = row.original;
          return (
            <div
              className="flex justify-end"
              onClick={(e) => e.stopPropagation()}
            >
              <DropdownMenu>
                <DropdownMenuTrigger
                  className="inline-flex size-7 items-center justify-center rounded-lg p-1 text-muted hover:text-foreground hover:bg-surface-2 transition-colors outline-none cursor-pointer"
                  aria-label={`Actions for ${inc.title}`}
                >
                  <MoreHorizontal className="size-4" />
                </DropdownMenuTrigger>
                <DropdownMenuContent
                  align="end"
                  className="w-40 bg-surface border-subtle shadow-md"
                >
                  <DropdownMenuItem
                    onClick={() => onSelectIncident(inc)}
                    className="gap-2 text-xs cursor-pointer"
                  >
                    <Eye className="size-3.5 text-muted" />
                    View Details
                  </DropdownMenuItem>

                  {canResolve && inc.status !== "resolved" && (
                    <DropdownMenuItem
                      onClick={() => onSelectIncident(inc)}
                      className="gap-2 text-xs text-emerald-400 focus:text-emerald-300 cursor-pointer"
                    >
                      <CheckCircle2 className="size-3.5" />
                      Resolve...
                    </DropdownMenuItem>
                  )}
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          );
        },
      },
    ],
    [sortBy, sortDir, canResolve]
  );

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    manualPagination: true,
    manualSorting: true,
    pageCount: Math.ceil(total / pageSize),
  });

  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const startItem = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const endItem = Math.min(page * pageSize, total);

  // 1. Loading Skeleton View
  if (isLoading && data.length === 0) {
    return (
      <div className="space-y-3">
        <div className="rounded-xl border border-subtle bg-surface overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="border-subtle bg-surface-2/40 hover:bg-surface-2/40">
                <TableHead className="h-10 text-xs font-semibold text-muted">Title</TableHead>
                <TableHead className="h-10 text-xs font-semibold text-muted">Severity</TableHead>
                <TableHead className="h-10 text-xs font-semibold text-muted">Status</TableHead>
                <TableHead className="h-10 text-xs font-semibold text-muted">Service</TableHead>
                <TableHead className="h-10 text-xs font-semibold text-muted">Assignee</TableHead>
                <TableHead className="h-10 text-xs font-semibold text-muted">Created</TableHead>
                <TableHead className="h-10 w-12 text-right" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {Array.from({ length: 6 }).map((_, i) => (
                <TableRow key={`skel-${i}`} className="border-subtle">
                  <TableCell className="py-3">
                    <Skeleton className="h-4 w-48" />
                  </TableCell>
                  <TableCell className="py-3">
                    <Skeleton className="h-4 w-16 rounded-md" />
                  </TableCell>
                  <TableCell className="py-3">
                    <Skeleton className="h-4 w-20 rounded-full" />
                  </TableCell>
                  <TableCell className="py-3">
                    <Skeleton className="h-4 w-28" />
                  </TableCell>
                  <TableCell className="py-3">
                    <Skeleton className="h-4 w-24" />
                  </TableCell>
                  <TableCell className="py-3">
                    <Skeleton className="h-4 w-16" />
                  </TableCell>
                  <TableCell className="py-3 text-right">
                    <Skeleton className="size-6 ml-auto rounded-md" />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>
    );
  }

  // 2. Error State View
  if (isError) {
    return (
      <div className="flex min-h-[300px] flex-col items-center justify-center rounded-xl border border-destructive/30 bg-destructive/5 p-8 text-center">
        <div className="flex size-12 items-center justify-center rounded-full bg-destructive/10 text-destructive mb-3">
          <AlertCircle className="size-6" />
        </div>
        <h3 className="text-sm font-semibold text-foreground">
          Failed to load incidents
        </h3>
        <p className="mt-1 max-w-sm text-xs text-muted">
          {error?.message || "An unexpected error occurred while fetching incidents."}
        </p>
        <Button
          variant="outline"
          size="sm"
          onClick={onRetry}
          className="mt-4 gap-1.5 border-subtle text-xs"
        >
          <RotateCcw className="size-3.5" />
          Retry
        </Button>
      </div>
    );
  }

  // 3. Empty State View
  if (data.length === 0) {
    return (
      <div className="flex min-h-[300px] flex-col items-center justify-center rounded-xl border border-dashed border-subtle bg-surface/50 p-8 text-center">
        <div className="flex size-12 items-center justify-center rounded-full bg-surface-2 text-muted mb-3">
          <AlertTriangle className="size-6" />
        </div>
        <h3 className="text-sm font-semibold text-foreground">
          No incidents found
        </h3>
        <p className="mt-1 max-w-sm text-xs text-muted">
          No incidents matching your filter criteria.
        </p>
        <Button
          variant="outline"
          size="sm"
          onClick={onResetFilters}
          className="mt-4 text-xs border-subtle"
        >
          Clear filters
        </Button>
      </div>
    );
  }

  // 4. Success State View
  return (
    <div className="space-y-3">
      <div className="rounded-xl border border-subtle bg-surface overflow-hidden">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow
                key={headerGroup.id}
                className="border-subtle bg-surface-2/40 hover:bg-surface-2/40"
              >
                {headerGroup.headers.map((header) => (
                  <TableHead
                    key={header.id}
                    className="h-10 text-xs font-semibold text-muted"
                  >
                    {header.isPlaceholder
                      ? null
                      : flexRender(
                          header.column.columnDef.header,
                          header.getContext()
                        )}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows.map((row) => (
              <TableRow
                key={row.id}
                onClick={() => onSelectIncident(row.original)}
                className="border-subtle hover:bg-surface-2/60 cursor-pointer transition-colors"
              >
                {row.getVisibleCells().map((cell) => (
                  <TableCell key={cell.id} className="py-3">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Pagination Controls */}
      <div className="flex flex-col items-center justify-between gap-3 px-1 sm:flex-row text-xs text-muted">
        <div>
          Showing <span className="font-medium text-foreground">{startItem}</span> to{" "}
          <span className="font-medium text-foreground">{endItem}</span> of{" "}
          <span className="font-medium text-foreground">{total}</span> incidents
        </div>

        <div className="flex items-center gap-3">
          {/* Page size selector */}
          <div className="flex items-center gap-1.5">
            <span>Rows per page:</span>
            <select
              value={pageSize}
              onChange={(e) => onPageSizeChange(Number(e.target.value))}
              aria-label="Rows per page"
              className="h-7 rounded-md border border-subtle bg-surface px-2 text-xs text-foreground outline-none focus-visible:ring-2 focus-visible:ring-ring cursor-pointer"
            >
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
            </select>
          </div>

          <div className="flex items-center gap-1">
            <span className="mr-1">
              Page {page} of {totalPages}
            </span>
            <Button
              variant="outline"
              size="icon-xs"
              onClick={() => onPageChange(page - 1)}
              disabled={page <= 1 || isLoading}
              aria-label="Previous page"
              className="border-subtle"
            >
              <ChevronLeft className="size-3.5" />
            </Button>
            <Button
              variant="outline"
              size="icon-xs"
              onClick={() => onPageChange(page + 1)}
              disabled={page >= totalPages || isLoading}
              aria-label="Next page"
              className="border-subtle"
            >
              <ChevronRight className="size-3.5" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
