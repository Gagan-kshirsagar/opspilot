/**
 * Firebase auth provider STUB — proves the pluggable seam.
 *
 * Setting NEXT_PUBLIC_AUTH_PROVIDER=firebase will hit this file,
 * proving that nothing else in the app is coupled to JWT.
 */

import type { AuthProvider } from "@/lib/auth/types";

const MSG = "Firebase auth provider is not yet implemented";

export const firebaseProvider: AuthProvider = {
  login() {
    throw new Error(MSG);
  },
  register() {
    throw new Error(MSG);
  },
  loginAsGuest() {
    throw new Error(MSG);
  },
  getCurrentUser() {
    throw new Error(MSG);
  },
  refresh() {
    throw new Error(MSG);
  },
  restoreSession() {
    throw new Error(MSG);
  },
  logout() {
    throw new Error(MSG);
  },
};

