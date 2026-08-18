"use client";

import { useCallback, useMemo } from "react";
import {
  type ColumnDef,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table";
import {
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  ChevronLeft,
  ChevronRight,
  Copy,
  MoreHorizontal,
  Pencil,
  RotateCcw,
  Trash2,
  Users,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
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
import { useAuthStore } from "@/stores/authStore";
import type {
  SortByField,
  SortDirection,
  UserRole,
  UserRow,
  UserStatus,
} from "@/types/user";

interface UsersTableProps {
  data: UserRow[];
  total: number;
  page: number;
  pageSize: number;
  sortBy: SortByField;
  sortDir: SortDirection;
  isLoading: boolean;
  isError: boolean;
  error?: Error | null;
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: number) => void;
  onSortChange: (sortBy: SortByField, sortDir: SortDirection) => void;
  onEditUser: (user: UserRow) => void;
  onDeleteUser: (user: UserRow) => void;
  selectedIds: string[];
  onSelectionChange: (ids: string[]) => void;
  onRetry: () => void;
  onResetFilters: () => void;
}

function formatRelativeTime(dateString: string | null): string {
  if (!dateString) return "Never";
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHours = Math.floor(diffMin / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffDays > 30) {
    return date.toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  }
  if (diffDays > 0) return `${diffDays}d ago`;
  if (diffHours > 0) return `${diffHours}h ago`;
  if (diffMin > 0) return `${diffMin}m ago`;
  return "Just now";
}

function getRoleBadge(role: UserRole) {
  switch (role) {
    case "admin":
      return (
        <span className="inline-flex items-center rounded-md bg-accent/15 px-2 py-0.5 text-xs font-medium text-accent border border-accent/25">
          Admin
        </span>
      );
    case "manager":
      return (
        <span className="inline-flex items-center rounded-md bg-accent-2/15 px-2 py-0.5 text-xs font-medium text-accent-2 border border-accent-2/25">
          Manager
        </span>
      );
    case "viewer":
      return (
        <span className="inline-flex items-center rounded-md bg-surface-2 px-2 py-0.5 text-xs font-medium text-muted border border-subtle">
          Viewer
        </span>
      );
    case "guest":
      return (
        <span className="inline-flex items-center rounded-md bg-surface-2 px-2 py-0.5 text-xs font-medium text-faint border border-subtle">
          Guest
        </span>
      );
  }
}

function getStatusBadge(status: UserStatus) {
  switch (status) {
    case "active":
      return (
        <span className="inline-flex items-center gap-1 rounded-md bg-success-soft px-2 py-0.5 text-xs font-medium text-success border border-success/20">
          <span className="size-1.5 rounded-full bg-success animate-pulse" />
          Active
        </span>
      );
    case "pending":
      return (
        <span className="inline-flex items-center gap-1 rounded-md bg-warning-soft px-2 py-0.5 text-xs font-medium text-warning border border-warning/20">
          <span className="size-1.5 rounded-full bg-warning" />
          Pending
        </span>
      );
    case "inactive":
      return (
        <span className="inline-flex items-center gap-1 rounded-md bg-danger-soft px-2 py-0.5 text-xs font-medium text-danger border border-danger/20">
          <span className="size-1.5 rounded-full bg-danger" />
          Inactive
        </span>
      );
  }
}

export function UsersTable({
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
  onEditUser,
  onDeleteUser,
  selectedIds,
  onSelectionChange,
  onRetry,
  onResetFilters,
}: UsersTableProps) {
  const currentUser = useAuthStore((s) => s.user);
  const canMutate =
    currentUser?.role === "admin" || currentUser?.role === "manager";
  const isAdmin = currentUser?.role === "admin";

  const isAllSelected =
    data.length > 0 && data.every((u) => selectedIds.includes(u.id));
  const isSomeSelected =
    data.some((u) => selectedIds.includes(u.id)) && !isAllSelected;

  const handleSelectAll = useCallback(() => {
    if (isAllSelected) {
      onSelectionChange(
        selectedIds.filter((id) => !data.some((u) => u.id === id))
      );
    } else {
      const newIds = new Set([...selectedIds, ...data.map((u) => u.id)]);
      onSelectionChange(Array.from(newIds));
    }
  }, [isAllSelected, data, selectedIds, onSelectionChange]);

  const handleToggleRow = useCallback(
    (id: string) => {
      if (selectedIds.includes(id)) {
        onSelectionChange(selectedIds.filter((i) => i !== id));
      } else {
        onSelectionChange([...selectedIds, id]);
      }
    },
    [selectedIds, onSelectionChange]
  );

  const handleHeaderSort = useCallback(
    (field: SortByField) => {
      if (sortBy === field) {
        onSortChange(field, sortDir === "asc" ? "desc" : "asc");
      } else {
        onSortChange(field, "asc");
      }
    },
    [sortBy, sortDir, onSortChange]
  );

  const renderSortIcon = useCallback(
    (field: SortByField) => {
      if (sortBy !== field) {
        return <ArrowUpDown className="size-3 text-faint" />;
      }
      return sortDir === "asc" ? (
        <ArrowUp className="size-3 text-accent" />
      ) : (
        <ArrowDown className="size-3 text-accent" />
      );
    },
    [sortBy, sortDir]
  );

  const columns = useMemo<ColumnDef<UserRow>[]>(
    () => [
      {
        id: "select",
        header: () => (
          <input
            type="checkbox"
            checked={isAllSelected}
            ref={(el) => {
              if (el) el.indeterminate = isSomeSelected;
            }}
            onChange={handleSelectAll}
            aria-label="Select all users on this page"
            className="size-4 rounded border-subtle bg-surface accent-accent cursor-pointer"
          />
        ),
        cell: ({ row }) => (
          <input
            type="checkbox"
            checked={selectedIds.includes(row.original.id)}
            onChange={() => handleToggleRow(row.original.id)}
            aria-label={`Select ${row.original.name}`}
            className="size-4 rounded border-subtle bg-surface accent-accent cursor-pointer"
          />
        ),
      },
      {
        accessorKey: "name",
        header: () => (
          <button
            type="button"
            onClick={() => handleHeaderSort("name")}
            className="flex items-center gap-1 font-semibold text-foreground hover:text-accent transition-colors"
          >
            User {renderSortIcon("name")}
          </button>
        ),
        cell: ({ row }) => {
          const user = row.original;
          const initials = user.name
            .split(" ")
            .map((n) => n[0])
            .join("")
            .slice(0, 2)
            .toUpperCase();
          return (
            <div className="flex items-center gap-2.5">
              <div className="flex size-7 shrink-0 items-center justify-center rounded-full bg-accent-soft text-accent text-xs font-semibold">
                {initials}
              </div>
              <div className="flex flex-col min-w-0">
                <span className="font-medium text-foreground truncate">
                  {user.name}
                </span>
                <span className="text-xs text-muted truncate">
                  {user.email ?? "Guest account"}
                </span>
              </div>
            </div>
          );
        },
      },
      {
        accessorKey: "role",
        header: () => (
          <button
            type="button"
            onClick={() => handleHeaderSort("role")}
            className="flex items-center gap-1 font-semibold text-foreground hover:text-accent transition-colors"
          >
            Role {renderSortIcon("role")}
          </button>
        ),
        cell: ({ row }) => getRoleBadge(row.original.role),
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
        cell: ({ row }) => getStatusBadge(row.original.status),
      },
      {
        accessorKey: "team_name",
        header: "Team",
        cell: ({ row }) => (
          <span className="text-xs text-foreground">
            {row.original.team_name ?? "—"}
          </span>
        ),
      },
      {
        accessorKey: "last_active",
        header: () => (
          <button
            type="button"
            onClick={() => handleHeaderSort("last_active")}
            className="flex items-center gap-1 font-semibold text-foreground hover:text-accent transition-colors"
          >
            Last Active {renderSortIcon("last_active")}
          </button>
        ),
        cell: ({ row }) => (
          <span className="text-xs text-muted">
            {formatRelativeTime(row.original.last_active)}
          </span>
        ),
      },
      {
        id: "actions",
        header: "",
        cell: ({ row }) => {
          const user = row.original;
          const isSelf = user.id === currentUser?.id;

          return (
            <div className="flex justify-end">
              <DropdownMenu>
                <DropdownMenuTrigger
                  className="inline-flex size-7 items-center justify-center rounded-lg p-1 text-muted hover:text-foreground hover:bg-surface-2 transition-colors outline-none cursor-pointer"
                  aria-label={`Actions for ${user.name}`}
                >
                  <MoreHorizontal className="size-4" />
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-40 bg-surface border-subtle shadow-md">
                  {user.email && (
                    <DropdownMenuItem
                      onClick={() => {
                        if (user.email && typeof navigator !== "undefined") {
                          navigator.clipboard?.writeText(user.email);
                        }
                      }}
                      className="cursor-pointer gap-2 text-xs"
                    >
                      <Copy className="size-3.5 text-muted" />
                      Copy Email
                    </DropdownMenuItem>
                  )}
                  {canMutate && (
                    <DropdownMenuItem
                      onClick={() => onEditUser(user)}
                      className="cursor-pointer gap-2 text-xs"
                    >
                      <Pencil className="size-3.5 text-muted" />
                      Edit Details
                    </DropdownMenuItem>
                  )}
                  {isAdmin && (
                    <>
                      <DropdownMenuSeparator className="my-1 border-subtle" />
                      <DropdownMenuItem
                        variant="destructive"
                        disabled={isSelf}
                        onClick={() => onDeleteUser(user)}
                        className="cursor-pointer gap-2 text-xs"
                      >
                        <Trash2 className="size-3.5" />
                        {isSelf ? "Cannot delete self" : "Delete User"}
                      </DropdownMenuItem>
                    </>
                  )}
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          );
        },
      },
    ],
    [
      selectedIds,
      isAllSelected,
      isSomeSelected,
      canMutate,
      isAdmin,
      currentUser,
      onDeleteUser,
      onEditUser,
      handleHeaderSort,
      handleSelectAll,
      handleToggleRow,
      renderSortIcon,
    ]
  );

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    manualPagination: true,
    manualSorting: true,
  });

  const totalPages = Math.ceil(total / pageSize) || 1;
  const startItem = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const endItem = Math.min(page * pageSize, total);

  // ── 1. Error State ─────────────────────────────────────
  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-danger/20 bg-surface p-12 text-center">
        <div className="flex size-12 items-center justify-center rounded-full bg-danger-soft text-danger">
          <RotateCcw className="size-6" />
        </div>
        <h3 className="mt-4 text-base font-semibold text-foreground">
          Failed to load users
        </h3>
        <p className="mt-1 text-sm text-muted max-w-sm">
          {error?.message ||
            "An unexpected error occurred while fetching user data. Please try again."}
        </p>
        <Button
          onClick={onRetry}
          variant="outline"
          size="sm"
          className="mt-4 gap-1.5 border-subtle"
        >
          <RotateCcw className="size-3.5" />
          Retry Request
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* ── Table Container ────────────────────────────── */}
      <div className="overflow-hidden rounded-xl border border-subtle bg-surface shadow-sm">
        <Table>
          <TableHeader className="bg-surface-2/60 border-b border-subtle">
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id} className="hover:bg-transparent">
                {headerGroup.headers.map((header) => (
                  <TableHead
                    key={header.id}
                    className="h-9 px-3 text-xs font-semibold text-muted"
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
            {/* ── 2. Loading State (Skeletons) ────────────── */}
            {isLoading ? (
              Array.from({ length: pageSize > 10 ? 10 : pageSize }).map(
                (_, index) => (
                  <TableRow
                    key={`skeleton-${index}`}
                    className="border-b border-subtle hover:bg-transparent"
                  >
                    <TableCell className="px-3 py-3">
                      <Skeleton className="size-4 rounded" />
                    </TableCell>
                    <TableCell className="px-3 py-3">
                      <div className="flex items-center gap-2.5">
                        <Skeleton className="size-7 rounded-full" />
                        <div className="space-y-1">
                          <Skeleton className="h-3.5 w-28" />
                          <Skeleton className="h-3 w-36" />
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="px-3 py-3">
                      <Skeleton className="h-5 w-14 rounded-md" />
                    </TableCell>
                    <TableCell className="px-3 py-3">
                      <Skeleton className="h-5 w-16 rounded-md" />
                    </TableCell>
                    <TableCell className="px-3 py-3">
                      <Skeleton className="h-4 w-20" />
                    </TableCell>
                    <TableCell className="px-3 py-3">
                      <Skeleton className="h-4 w-16" />
                    </TableCell>
                    <TableCell className="px-3 py-3 text-right">
                      <Skeleton className="size-7 rounded-lg ml-auto" />
                    </TableCell>
                  </TableRow>
                )
              )
            ) : data.length === 0 ? (
              /* ── 3. Empty State ────────────────────────── */
              <TableRow className="hover:bg-transparent">
                <TableCell
                  colSpan={columns.length}
                  className="h-64 text-center"
                >
                  <div className="flex flex-col items-center justify-center p-6 text-center">
                    <div className="flex size-12 items-center justify-center rounded-full bg-surface-2 text-muted">
                      <Users className="size-6" />
                    </div>
                    <h3 className="mt-3 text-sm font-semibold text-foreground">
                      No users found
                    </h3>
                    <p className="mt-1 text-xs text-muted max-w-xs">
                      No users match your active search and filter criteria. Try
                      clearing filters to view all users.
                    </p>
                    <Button
                      variant="outline"
                      size="xs"
                      onClick={onResetFilters}
                      className="mt-3 text-xs border-subtle"
                    >
                      Clear Filters
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              /* ── 4. Success State (Data Rows) ──────────── */
              table.getRowModel().rows.map((row) => (
                <TableRow
                  key={row.original.id}
                  data-state={
                    selectedIds.includes(row.original.id) && "selected"
                  }
                  className="border-b border-subtle/60 transition-colors hover:bg-surface-2/50 data-[state=selected]:bg-accent/5"
                >
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id} className="px-3 py-2.5 text-xs">
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext()
                      )}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* ── Pagination Controls ────────────────────────── */}
      <div className="flex flex-col items-center justify-between gap-3 px-1 sm:flex-row text-xs text-muted">
        <div>
          Showing <span className="font-medium text-foreground">{startItem}</span> to{" "}
          <span className="font-medium text-foreground">{endItem}</span> of{" "}
          <span className="font-medium text-foreground">{total}</span> users
        </div>

        <div className="flex items-center gap-3">
          {/* Page size selector */}
          <div className="flex items-center gap-1.5">
            <span>Rows per page:</span>
            <select
              value={pageSize}
              onChange={(e) => onPageSizeChange(Number(e.target.value))}
              aria-label="Rows per page"
              className="h-7 rounded-md border border-subtle bg-surface px-2 text-xs text-foreground outline-none focus-visible:ring-2 focus-visible:ring-ring"
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
