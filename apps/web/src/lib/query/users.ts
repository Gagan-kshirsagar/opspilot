/**
 * TanStack Query hooks for user management.
 *
 * Server truth via Query; mutations invalidate the cache automatically.
 */

import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import type { AxiosError } from "axios";

import {
  bulkDeleteUsers,
  createUser,
  deleteUser,
  fetchTeams,
  fetchUser,
  fetchUsers,
  updateUser,
} from "@/lib/api/users";
import { queryKeys } from "@/lib/query/keys";
import type {
  BulkDeleteResponse,
  CreateUserData,
  PaginatedUsersResponse,
  Team,
  UpdateUserData,
  UserDetail,
  UserListParams,
} from "@/types/user";
import type { ErrorResponse } from "@/lib/auth/types";

// ── List users (paginated) ──────────────────────────────

export function useUsers(params: UserListParams) {
  return useQuery<PaginatedUsersResponse>({
    queryKey: queryKeys.users.list(params),
    queryFn: () => fetchUsers(params),
    placeholderData: keepPreviousData,
  });
}

// ── Single user detail ──────────────────────────────────

export function useUser(id: string | null) {
  return useQuery<UserDetail>({
    queryKey: queryKeys.users.detail(id ?? ""),
    queryFn: () => fetchUser(id!),
    enabled: id !== null,
  });
}

// ── Create user ─────────────────────────────────────────

export function useCreateUser() {
  const qc = useQueryClient();

  return useMutation<
    UserDetail,
    AxiosError<ErrorResponse>,
    CreateUserData
  >({
    mutationFn: (data) => createUser(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.users.all });
    },
  });
}

// ── Update user ─────────────────────────────────────────

export function useUpdateUser() {
  const qc = useQueryClient();

  return useMutation<
    UserDetail,
    AxiosError<ErrorResponse>,
    { id: string; data: UpdateUserData }
  >({
    mutationFn: ({ id, data }) => updateUser(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.users.all });
    },
  });
}

// ── Delete user ─────────────────────────────────────────

export function useDeleteUser() {
  const qc = useQueryClient();

  return useMutation<void, AxiosError<ErrorResponse>, string>({
    mutationFn: (id) => deleteUser(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.users.all });
    },
  });
}

// ── Bulk delete ─────────────────────────────────────────

export function useBulkDeleteUsers() {
  const qc = useQueryClient();

  return useMutation<
    BulkDeleteResponse,
    AxiosError<ErrorResponse>,
    string[]
  >({
    mutationFn: (ids) => bulkDeleteUsers(ids),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.users.all });
    },
  });
}

// ── Teams list ──────────────────────────────────────────

export function useTeams() {
  return useQuery<Team[]>({
    queryKey: queryKeys.teams.list(),
    queryFn: fetchTeams,
    staleTime: 5 * 60 * 1000, // teams rarely change
  });
}
