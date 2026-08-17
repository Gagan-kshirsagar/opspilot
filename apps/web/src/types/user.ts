/**
 * User management types — mirrors backend Pydantic schemas.
 */

// ── Enums ────────────────────────────────────────────────

export type UserRole = "admin" | "manager" | "viewer" | "guest";
export type UserStatus = "active" | "pending" | "inactive";

export type SortByField =
  | "name"
  | "email"
  | "role"
  | "status"
  | "created_at"
  | "last_active";

export type SortDirection = "asc" | "desc";

// ── Query params ─────────────────────────────────────────

export interface UserListParams {
  page?: number;
  page_size?: number;
  sort_by?: SortByField;
  sort_dir?: SortDirection;
  search?: string;
  role?: UserRole[];
  status?: UserStatus[];
  team_id?: string;
}

// ── Response types ───────────────────────────────────────

export interface UserRow {
  id: string;
  name: string;
  email: string | null;
  role: UserRole;
  status: UserStatus;
  team_name: string | null;
  team_id: string | null;
  is_guest: boolean;
  last_active: string | null;
  created_at: string;
}

export interface PaginatedUsersResponse {
  items: UserRow[];
  total: number;
  page: number;
  page_size: number;
}

export interface UserDetail extends UserRow {
  updated_at: string;
}

// ── Request types ────────────────────────────────────────

export interface CreateUserData {
  name: string;
  email: string;
  role?: string;
  status?: string;
  team_id?: string | null;
  password?: string;
}

export interface UpdateUserData {
  name?: string;
  email?: string;
  role?: string;
  status?: string;
  team_id?: string | null;
  password?: string;
}

export interface BulkDeleteResponse {
  deleted: number;
}

// ── Team ─────────────────────────────────────────────────

export interface Team {
  id: string;
  name: string;
  created_at: string;
}
