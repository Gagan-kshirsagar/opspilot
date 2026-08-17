"use client";

import { Plus, Search, Trash2, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useTeams } from "@/lib/query/users";
import type { Team, UserRole, UserStatus } from "@/types/user";

interface UsersToolbarProps {
  search: string;
  onSearchChange: (value: string) => void;
  roleFilter: UserRole | "";
  onRoleFilterChange: (role: UserRole | "") => void;
  statusFilter: UserStatus | "";
  onStatusFilterChange: (status: UserStatus | "") => void;
  teamFilter: string;
  onTeamFilterChange: (teamId: string) => void;
  onResetFilters: () => void;
  hasActiveFilters: boolean;
  canMutate: boolean;
  onAddUserClick: () => void;
  selectedCount: number;
  onBulkDeleteClick: () => void;
}

export function UsersToolbar({
  search,
  onSearchChange,
  roleFilter,
  onRoleFilterChange,
  statusFilter,
  onStatusFilterChange,
  teamFilter,
  onTeamFilterChange,
  onResetFilters,
  hasActiveFilters,
  canMutate,
  onAddUserClick,
  selectedCount,
  onBulkDeleteClick,
}: UsersToolbarProps) {
  const { data: teams = [] } = useTeams();

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
            placeholder="Search by name or email…"
            className="h-8 pl-8 pr-8 text-xs bg-surface border-subtle"
            aria-label="Search users"
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

        {/* Role Filter */}
        <select
          value={roleFilter}
          onChange={(e) => onRoleFilterChange(e.target.value as UserRole | "")}
          aria-label="Filter by role"
          className="h-8 rounded-lg border border-subtle bg-surface px-2.5 text-xs text-foreground outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          <option value="">All Roles</option>
          <option value="admin">Admin</option>
          <option value="manager">Manager</option>
          <option value="viewer">Viewer</option>
          <option value="guest">Guest</option>
        </select>

        {/* Status Filter */}
        <select
          value={statusFilter}
          onChange={(e) =>
            onStatusFilterChange(e.target.value as UserStatus | "")
          }
          aria-label="Filter by status"
          className="h-8 rounded-lg border border-subtle bg-surface px-2.5 text-xs text-foreground outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          <option value="">All Statuses</option>
          <option value="active">Active</option>
          <option value="pending">Pending</option>
          <option value="inactive">Inactive</option>
        </select>

        {/* Team Filter */}
        <select
          value={teamFilter}
          onChange={(e) => onTeamFilterChange(e.target.value)}
          aria-label="Filter by team"
          className="h-8 rounded-lg border border-subtle bg-surface px-2.5 text-xs text-foreground outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          <option value="">All Teams</option>
          {teams.map((t: Team) => (
            <option key={t.id} value={t.id}>
              {t.name}
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

      {/* Action Buttons */}
      <div className="flex items-center gap-2">
        {selectedCount > 0 && canMutate && (
          <Button
            variant="destructive"
            size="sm"
            onClick={onBulkDeleteClick}
            className="gap-1.5 text-xs"
          >
            <Trash2 className="size-3.5" />
            Delete ({selectedCount})
          </Button>
        )}

        {canMutate && (
          <Button
            size="sm"
            onClick={onAddUserClick}
            className="gap-1.5 bg-accent text-accent-foreground hover:bg-accent-hover text-xs font-medium"
          >
            <Plus className="size-3.5" />
            Add User
          </Button>
        )}
      </div>
    </div>
  );
}
