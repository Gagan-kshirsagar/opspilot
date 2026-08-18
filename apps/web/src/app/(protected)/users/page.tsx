"use client";

import { useState } from "react";

import { DeleteUserDialog } from "@/components/users/delete-user-dialog";
import { UserFormDialog } from "@/components/users/user-form-dialog";
import { UsersTable } from "@/components/users/users-table";
import { UsersToolbar } from "@/components/users/users-toolbar";
import { useDebounce } from "@/hooks/use-debounce";
import { useUsers } from "@/lib/query/users";
import { useAuthStore } from "@/stores/authStore";
import type {
  SortByField,
  SortDirection,
  UserListParams,
  UserRole,
  UserRow,
  UserStatus,
} from "@/types/user";

export default function UsersPage() {
  const currentUser = useAuthStore((s) => s.user);
  const canMutate =
    currentUser?.role === "admin" || currentUser?.role === "manager";

  // Filter & pagination state
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [searchInput, setSearchInput] = useState("");
  const debouncedSearch = useDebounce(searchInput, 300);

  const [roleFilter, setRoleFilter] = useState<UserRole | "">("");
  const [statusFilter, setStatusFilter] = useState<UserStatus | "">("");
  const [teamFilter, setTeamFilter] = useState("");

  const [sortBy, setSortBy] = useState<SortByField>("created_at");
  const [sortDir, setSortDir] = useState<SortDirection>("desc");

  // Selection state
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  // Dialog state
  const [formOpen, setFormOpen] = useState(false);
  const [userToEdit, setUserToEdit] = useState<UserRow | null>(null);

  const [deleteOpen, setDeleteOpen] = useState(false);
  const [userToDelete, setUserToDelete] = useState<UserRow | null>(null);

  const handleSearchChange = (val: string) => {
    setSearchInput(val);
    setPage(1);
  };
  const handleRoleChange = (val: UserRole | "") => {
    setRoleFilter(val);
    setPage(1);
  };
  const handleStatusChange = (val: UserStatus | "") => {
    setStatusFilter(val);
    setPage(1);
  };
  const handleTeamChange = (val: string) => {
    setTeamFilter(val);
    setPage(1);
  };

  // Construct query params
  const queryParams: UserListParams = {
    page,
    page_size: pageSize,
    sort_by: sortBy,
    sort_dir: sortDir,
    search: debouncedSearch || undefined,
    role: roleFilter ? [roleFilter] : undefined,
    status: statusFilter ? [statusFilter] : undefined,
    team_id: teamFilter || undefined,
  };

  const { data, isLoading, isError, error, refetch } = useUsers(queryParams);

  const hasActiveFilters = Boolean(
    searchInput || roleFilter || statusFilter || teamFilter
  );

  const handleResetFilters = () => {
    setSearchInput("");
    setRoleFilter("");
    setStatusFilter("");
    setTeamFilter("");
    setPage(1);
  };

  const handleAddUser = () => {
    setUserToEdit(null);
    setFormOpen(true);
  };

  const handleEditUser = (user: UserRow) => {
    setUserToEdit(user);
    setFormOpen(true);
  };

  const handleDeleteSingle = (user: UserRow) => {
    setUserToDelete(user);
    setDeleteOpen(true);
  };

  const handleBulkDelete = () => {
    setUserToDelete(null);
    setDeleteOpen(true);
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 space-y-6 animate-slide-up">
      {/* Header section */}
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            User Management
          </h1>
          <p className="text-sm text-muted">
            Manage organization members, team assignments, and security roles.
          </p>
        </div>
      </div>

      {/* Toolbar (Search, Filter, Actions) */}
      <UsersToolbar
        search={searchInput}
        onSearchChange={handleSearchChange}
        roleFilter={roleFilter}
        onRoleFilterChange={handleRoleChange}
        statusFilter={statusFilter}
        onStatusFilterChange={handleStatusChange}
        teamFilter={teamFilter}
        onTeamFilterChange={handleTeamChange}
        onResetFilters={handleResetFilters}
        hasActiveFilters={hasActiveFilters}
        canMutate={canMutate}
        onAddUserClick={handleAddUser}
        selectedCount={selectedIds.length}
        onBulkDeleteClick={handleBulkDelete}
      />

      {/* Data Table */}
      <UsersTable
        data={data?.items ?? []}
        total={data?.total ?? 0}
        page={page}
        pageSize={pageSize}
        sortBy={sortBy}
        sortDir={sortDir}
        isLoading={isLoading}
        isError={isError}
        error={error}
        onPageChange={setPage}
        onPageSizeChange={(size) => {
          setPageSize(size);
          setPage(1);
        }}
        onSortChange={(field, dir) => {
          setSortBy(field);
          setSortDir(dir);
        }}
        onEditUser={handleEditUser}
        onDeleteUser={handleDeleteSingle}
        selectedIds={selectedIds}
        onSelectionChange={setSelectedIds}
        onRetry={() => refetch()}
        onResetFilters={handleResetFilters}
      />

      {/* Create / Edit Dialog */}
      <UserFormDialog
        open={formOpen}
        onOpenChange={setFormOpen}
        userToEdit={userToEdit}
      />

      {/* Delete Confirmation Dialog */}
      <DeleteUserDialog
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        userToDelete={userToDelete}
        selectedIds={selectedIds}
        onDeleted={() => setSelectedIds([])}
      />
    </div>
  );
}
