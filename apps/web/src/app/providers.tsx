"use client";

/**
 * Client-side providers wrapper — QueryClientProvider.
 */

import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "@/lib/query/queryClient";
import { AuthBootstrap } from "@/components/auth/auth-bootstrap";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthBootstrap>{children}</AuthBootstrap>
    </QueryClientProvider>
  );
}

