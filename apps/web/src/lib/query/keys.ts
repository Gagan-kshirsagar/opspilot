/**
 * Centralised query key factory.
 *
 * Usage:
 *   queryKeys.auth.me()      → ["auth", "me"]
 *   queryKeys.auth.all       → ["auth"]
 */

export const queryKeys = {
  auth: {
    all: ["auth"] as const,
    me: () => [...queryKeys.auth.all, "me"] as const,
  },
} as const;
