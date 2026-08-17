/**
 * Centralised query key factory.
 *
 * Usage:
 *   queryKeys.auth.me()      → ["auth", "me"]
 *   queryKeys.auth.all       → ["auth"]
 *   queryKeys.users.list(p)  → ["users", "list", p]
 *   queryKeys.users.detail(id) → ["users", "detail", id]
 *   queryKeys.teams.all      → ["teams"]
 */

import type { UserListParams } from "@/types/user";

export const queryKeys = {
  auth: {
    all: ["auth"] as const,
    me: () => [...queryKeys.auth.all, "me"] as const,
  },
  users: {
    all: ["users"] as const,
    list: (params: UserListParams) =>
      [...queryKeys.users.all, "list", params] as const,
    detail: (id: string) =>
      [...queryKeys.users.all, "detail", id] as const,
  },
  teams: {
    all: ["teams"] as const,
    list: () => [...queryKeys.teams.all, "list"] as const,
  },
} as const;
