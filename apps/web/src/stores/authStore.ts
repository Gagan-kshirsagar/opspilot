/**
 * Auth store — UI state ONLY (user object + auth status).
 *
 * Tokens are NOT stored here. They live in the axios client module.
 * Server truth comes via TanStack Query; this store holds derived UI flags.
 */

import { create } from "zustand";
import type { AuthUser } from "@/lib/auth/types";

export type AuthStatus =
  | "loading"
  | "authenticated"
  | "guest"
  | "unauthenticated";

interface AuthState {
  user: AuthUser | null;
  status: AuthStatus;
  setUser: (user: AuthUser) => void;
  setStatus: (status: AuthStatus) => void;
  clear: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  status: "loading",

  setUser: (user) =>
    set({
      user,
      status: user.is_guest ? "guest" : "authenticated",
    }),

  setStatus: (status) => set({ status }),

  clear: () =>
    set({
      user: null,
      status: "unauthenticated",
    }),
}));
