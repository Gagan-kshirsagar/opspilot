/**
 * Centralised query key factory.
 *
 * Usage:
 *   queryKeys.auth.me()         → ["auth", "me"]
 *   queryKeys.users.list(p)     → ["users", "list", p]
 *   queryKeys.services.list(p)  → ["services", "list", p]
 *   queryKeys.incidents.list(p) → ["incidents", "list", p]
 */

import type { IncidentListParams } from "@/types/incident";
import type { ServiceListParams } from "@/types/service";
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
  services: {
    all: ["services"] as const,
    list: (params?: ServiceListParams) =>
      [...queryKeys.services.all, "list", params] as const,
    detail: (id: string) =>
      [...queryKeys.services.all, "detail", id] as const,
  },
  incidents: {
    all: ["incidents"] as const,
    list: (params: IncidentListParams) =>
      [...queryKeys.incidents.all, "list", params] as const,
    detail: (id: string) =>
      [...queryKeys.incidents.all, "detail", id] as const,
  },
  chat: {
    all: ["chat"] as const,
  },
} as const;
