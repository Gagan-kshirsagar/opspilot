import {
  apiClient,
  clearTokens,
  getRefreshToken,
  setAccessToken,
  setRefreshToken,
} from "@/lib/api/client";
import type {
  AuthProvider,
  AuthResponse,
  AuthUser,
  TokenPair,
} from "@/lib/auth/types";

export const jwtProvider: AuthProvider = {
  async login(email: string, password: string): Promise<AuthResponse> {
    const { data } = await apiClient.post<AuthResponse>("/api/v1/auth/login", {
      email,
      password,
    });
    setAccessToken(data.tokens.access_token);
    setRefreshToken(data.tokens.refresh_token);
    return data;
  },

  async register(
    email: string,
    password: string,
    name: string,
  ): Promise<AuthResponse> {
    const { data } = await apiClient.post<AuthResponse>(
      "/api/v1/auth/register",
      { email, password, name },
    );
    setAccessToken(data.tokens.access_token);
    setRefreshToken(data.tokens.refresh_token);
    return data;
  },

  async loginAsGuest(): Promise<AuthResponse> {
    const { data } = await apiClient.post<AuthResponse>("/api/v1/auth/guest");
    setAccessToken(data.tokens.access_token);
    setRefreshToken(data.tokens.refresh_token);
    return data;
  },

  async getCurrentUser(): Promise<AuthUser> {
    const { data } = await apiClient.get<AuthUser>("/api/v1/auth/me");
    return data;
  },

  async refresh(refreshToken?: string): Promise<TokenPair> {
    const token = refreshToken ?? getRefreshToken();
    const { data } = await apiClient.post<TokenPair>(
      "/api/v1/auth/refresh",
      token ? { refresh_token: token } : {},
    );
    setAccessToken(data.access_token);
    if (data.refresh_token) {
      setRefreshToken(data.refresh_token);
    }
    return data;
  },

  async restoreSession(): Promise<AuthUser | null> {
    try {
      const refreshToken = getRefreshToken();
      const { data } = await apiClient.post<TokenPair>(
        "/api/v1/auth/refresh",
        refreshToken ? { refresh_token: refreshToken } : {},
      );
      setAccessToken(data.access_token);
      if (data.refresh_token) {
        setRefreshToken(data.refresh_token);
      }
      const user = await jwtProvider.getCurrentUser();
      return user;
    } catch {
      clearTokens();
      return null;
    }
  },

  async logout(): Promise<void> {
    try {
      await apiClient.post("/api/v1/auth/logout");
    } finally {
      clearTokens();
    }
  },
};

