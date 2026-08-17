/**
 * Auth types — mirrors backend Pydantic schemas.
 *
 * Routers/services depend ONLY on the AuthProvider interface, never
 * on a concrete JWT / Firebase implementation.
 */

// ── Data types ───────────────────────────────────────────

export interface AuthUser {
  id: string;
  email: string | null;
  name: string;
  role: "admin" | "manager" | "viewer" | "guest";
  status: string;
  is_guest: boolean;
  created_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_in: number;
}

export interface AuthResponse {
  user: AuthUser;
  tokens: TokenPair;
}

export interface ErrorResponse {
  detail: string;
}

// ── Provider interface ───────────────────────────────────

export interface AuthProvider {
  login(email: string, password: string): Promise<AuthResponse>;
  register(email: string, password: string, name: string): Promise<AuthResponse>;
  loginAsGuest(): Promise<AuthResponse>;
  getCurrentUser(): Promise<AuthUser>;
  refresh(refreshToken?: string): Promise<TokenPair>;
  restoreSession(): Promise<AuthUser | null>;
  logout(): Promise<void>;
}

