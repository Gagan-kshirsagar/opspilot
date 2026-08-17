/**
 * Auth provider barrel — exports the active provider based on env config.
 *
 * App code imports from here ONLY:
 *   import { authProvider } from "@/lib/auth";
 */

import type { AuthProvider } from "@/lib/auth/types";
import { firebaseProvider } from "@/lib/auth/providers/firebaseProvider";
import { jwtProvider } from "@/lib/auth/providers/jwtProvider";

const AUTH_PROVIDER_KEY =
  process.env.NEXT_PUBLIC_AUTH_PROVIDER ?? "jwt";

function resolveProvider(): AuthProvider {
  switch (AUTH_PROVIDER_KEY) {
    case "jwt":
      return jwtProvider;
    case "firebase":
      return firebaseProvider;
    default:
      throw new Error(
        `Unknown auth provider: "${AUTH_PROVIDER_KEY}". Supported: "jwt", "firebase".`,
      );
  }
}

export const authProvider: AuthProvider = resolveProvider();

// Re-export types for convenience.
export type { AuthProvider, AuthResponse, AuthUser, TokenPair } from "@/lib/auth/types";
