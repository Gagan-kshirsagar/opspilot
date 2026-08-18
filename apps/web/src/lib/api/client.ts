/**
 * Typed Axios client with auth interceptors.
 *
 * - Request interceptor: attaches Bearer token from in-memory storage.
 * - Response interceptor: on 401, attempts a single refresh, retries,
 *   then clears auth and redirects to /login on failure.
 *
 * Token storage: access token in a module-scoped closure (never in
 * React state or localStorage). Refresh token in localStorage
 * (pragmatic trade-off documented in DECISIONS.md).
 */

import axios, {
  type AxiosError,
  type AxiosRequestConfig,
  type InternalAxiosRequestConfig,
} from "axios";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ── Token storage (module-scoped, NOT React state) ───────

let _accessToken: string | null = null;

export function setAccessToken(token: string | null): void {
  _accessToken = token;
}

export function getAccessToken(): string | null {
  return _accessToken;
}

export function setRefreshToken(token: string | null): void {
  if (typeof window === "undefined") return;
  if (token) {
    localStorage.setItem("opspilot_refresh_token", token);
  } else {
    localStorage.removeItem("opspilot_refresh_token");
  }
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("opspilot_refresh_token");
}

export function clearTokens(): void {
  setAccessToken(null);
  setRefreshToken(null);
}

// ── Axios instance ───────────────────────────────────────

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
  withCredentials: true,
  timeout: 15_000,
  paramsSerializer: {
    indexes: null,
  },
});

// ── Request interceptor: attach Bearer ───────────────────

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getAccessToken();
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── Response interceptor: 401 → refresh once → retry ────

let _isRefreshing = false;
let _failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (err: unknown) => void;
}> = [];

function processQueue(error: unknown, token: string | null = null): void {
  for (const promise of _failedQueue) {
    if (token) {
      promise.resolve(token);
    } else {
      promise.reject(error);
    }
  }
  _failedQueue = [];
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as
      | (AxiosRequestConfig & { _retry?: boolean })
      | undefined;

    // Only retry on 401 and if we haven't already retried.
    if (error.response?.status !== 401 || !originalRequest || originalRequest._retry) {
      return Promise.reject(error);
    }

    // Don't retry auth endpoints themselves.
    const url = originalRequest.url ?? "";
    if (url.includes("/auth/login") || url.includes("/auth/refresh")) {
      return Promise.reject(error);
    }

    if (_isRefreshing) {
      // Queue this request until the refresh completes.
      return new Promise<string>((resolve, reject) => {
        _failedQueue.push({ resolve, reject });
      }).then((token) => {
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${token}`;
        }
        return apiClient(originalRequest);
      });
    }

    originalRequest._retry = true;
    _isRefreshing = true;

    const refreshToken = getRefreshToken();

    try {
      const { data } = await axios.post(
        `${BASE_URL}/api/v1/auth/refresh`,
        refreshToken ? { refresh_token: refreshToken } : {},
        { withCredentials: true },
      );

      const newAccessToken = data.access_token as string;
      const newRefreshToken = data.refresh_token as string | undefined;

      setAccessToken(newAccessToken);
      if (newRefreshToken) {
        setRefreshToken(newRefreshToken);
      }
      processQueue(null, newAccessToken);

      if (originalRequest.headers) {
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
      }
      return apiClient(originalRequest);
    } catch (refreshError) {
      processQueue(refreshError, null);
      clearTokens();
      if (typeof window !== "undefined") {
        // eslint-disable-next-line @next/next/no-location-assign-relative-destination
        window.location.href = "/login";
      }
      return Promise.reject(refreshError);
    } finally {
      _isRefreshing = false;
    }
  },
);
