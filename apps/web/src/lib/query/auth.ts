/**
 * Auth TanStack Query hooks.
 *
 * Server truth via Query; mutations sync results to the Zustand auth store.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { AxiosError } from "axios";

import { authProvider } from "@/lib/auth";
import type { AuthResponse, AuthUser, ErrorResponse } from "@/lib/auth/types";
import { clearTokens, getAccessToken } from "@/lib/api/client";
import { queryKeys } from "@/lib/query/keys";
import { useAuthStore } from "@/stores/authStore";

// ── useMe — fetch current user ──────────────────────────

export function useMe() {
  const { setUser, clear } = useAuthStore();

  return useQuery<AuthUser>({
    queryKey: queryKeys.auth.me(),
    queryFn: () => authProvider.getCurrentUser(),
    enabled: getAccessToken() !== null,
    retry: false,
    meta: {
      onSuccess: (data: AuthUser) => {
        setUser(data);
      },
      onError: () => {
        clear();
      },
    },
    // We use the select/onSuccess pattern via manual sync below:
  });
}

// ── useLogin ─────────────────────────────────────────────

export function useLogin() {
  const qc = useQueryClient();
  const { setUser } = useAuthStore();
  const router = useRouter();

  return useMutation<
    AuthResponse,
    AxiosError<ErrorResponse>,
    { email: string; password: string }
  >({
    mutationFn: ({ email, password }) => authProvider.login(email, password),
    onSuccess: (data) => {
      setUser(data.user);
      qc.setQueryData(queryKeys.auth.me(), data.user);
      router.push("/dashboard");
    },
  });
}

// ── useRegister ──────────────────────────────────────────

export function useRegister() {
  const qc = useQueryClient();
  const { setUser } = useAuthStore();
  const router = useRouter();

  return useMutation<
    AuthResponse,
    AxiosError<ErrorResponse>,
    { email: string; password: string; name: string }
  >({
    mutationFn: ({ email, password, name }) =>
      authProvider.register(email, password, name),
    onSuccess: (data) => {
      setUser(data.user);
      qc.setQueryData(queryKeys.auth.me(), data.user);
      router.push("/dashboard");
    },
  });
}

// ── useGuestLogin ────────────────────────────────────────

export function useGuestLogin() {
  const qc = useQueryClient();
  const { setUser } = useAuthStore();
  const router = useRouter();

  return useMutation<AuthResponse, AxiosError<ErrorResponse>>({
    mutationFn: () => authProvider.loginAsGuest(),
    onSuccess: (data) => {
      setUser(data.user);
      qc.setQueryData(queryKeys.auth.me(), data.user);
      router.push("/dashboard");
    },
  });
}

// ── useLogout ────────────────────────────────────────────

export function useLogout() {
  const qc = useQueryClient();
  const { clear } = useAuthStore();
  const router = useRouter();

  return useMutation<void, AxiosError<ErrorResponse>>({
    mutationFn: () => authProvider.logout(),
    onSettled: () => {
      clear();
      clearTokens();
      qc.removeQueries({ queryKey: queryKeys.auth.all });
      router.push("/login");
    },
  });
}
