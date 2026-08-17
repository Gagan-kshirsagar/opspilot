"use client";

import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { authProvider } from "@/lib/auth";
import { queryKeys } from "@/lib/query/keys";
import { useAuthStore } from "@/stores/authStore";

let _bootstrapPromise: Promise<void> | null = null;

export function resetBootstrapForTests() {
  _bootstrapPromise = null;
}

export function AuthBootstrap({ children }: { children: React.ReactNode }) {
  const qc = useQueryClient();

  useEffect(() => {
    if (!_bootstrapPromise) {
      _bootstrapPromise = (async () => {
        try {
          const user = await authProvider.restoreSession();
          if (user) {
            useAuthStore.getState().setUser(user);
            qc.setQueryData(queryKeys.auth.me(), user);
          } else {
            useAuthStore.getState().clear();
          }
        } catch {
          useAuthStore.getState().clear();
        }
      })();
    }
  }, [qc]);

  return <>{children}</>;
}

