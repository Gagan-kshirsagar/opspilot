/**
 * Typed API functions for user management.
 */

import { apiClient } from "@/lib/api/client";
import type {
  BulkDeleteResponse,
  CreateUserData,
  PaginatedUsersResponse,
  Team,
  UpdateUserData,
  UserDetail,
  UserListParams,
} from "@/types/user";

/**
 * Fetch paginated users with optional filters.
 */
export async function fetchUsers(
  params: UserListParams
): Promise<PaginatedUsersResponse> {
  const { data } = await apiClient.get<PaginatedUsersResponse>(
    "/api/v1/users",
    {
      params: {
        page: params.page,
        page_size: params.page_size,
        sort_by: params.sort_by,
        sort_dir: params.sort_dir,
        search: params.search || undefined,
        role: params.role,
        status: params.status,
        team_id: params.team_id || undefined,
      },
    }
  );
  return data;
}

/**
 * Fetch a single user by ID.
 */
export async function fetchUser(id: string): Promise<UserDetail> {
  const { data } = await apiClient.get<UserDetail>(`/api/v1/users/${id}`);
  return data;
}

/**
 * Create a new user.
 */
export async function createUser(
  payload: CreateUserData
): Promise<UserDetail> {
  const { data } = await apiClient.post<UserDetail>(
    "/api/v1/users",
    payload
  );
  return data;
}

/**
 * Partially update a user.
 */
export async function updateUser(
  id: string,
  payload: UpdateUserData
): Promise<UserDetail> {
  const { data } = await apiClient.patch<UserDetail>(
    `/api/v1/users/${id}`,
    payload
  );
  return data;
}

/**
 * Delete a single user.
 */
export async function deleteUser(id: string): Promise<void> {
  await apiClient.delete(`/api/v1/users/${id}`);
}

/**
 * Bulk-delete users by IDs.
 */
export async function bulkDeleteUsers(
  ids: string[]
): Promise<BulkDeleteResponse> {
  const { data } = await apiClient.post<BulkDeleteResponse>(
    "/api/v1/users/bulk-delete",
    { ids }
  );
  return data;
}

/**
 * Fetch all teams (for dropdowns).
 */
export async function fetchTeams(): Promise<Team[]> {
  const { data } = await apiClient.get<Team[]>("/api/v1/teams");
  return data;
}
