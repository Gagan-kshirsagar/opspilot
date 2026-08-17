/**
 * LoginForm tests — Vitest + RTL, query by role.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { LoginForm } from "../login-form";

// ── Mocks ────────────────────────────────────────────────

// Mock next/navigation.
const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

// Mock auth provider.
const mockLogin = vi.fn();
const mockRegister = vi.fn();
const mockLoginAsGuest = vi.fn();
const mockGetCurrentUser = vi.fn();
const mockRefresh = vi.fn();
const mockLogout = vi.fn();

vi.mock("@/lib/auth", () => ({
  authProvider: {
    login: (...args: unknown[]) => mockLogin(...args),
    register: (...args: unknown[]) => mockRegister(...args),
    loginAsGuest: () => mockLoginAsGuest(),
    getCurrentUser: () => mockGetCurrentUser(),
    refresh: (...args: unknown[]) => mockRefresh(...args),
    logout: () => mockLogout(),
  },
}));

// Mock the token helpers (they're imported by jwtProvider & auth hooks).
vi.mock("@/lib/api/client", () => ({
  apiClient: { post: vi.fn(), get: vi.fn() },
  setAccessToken: vi.fn(),
  getAccessToken: () => null,
  setRefreshToken: vi.fn(),
  getRefreshToken: () => null,
  clearTokens: vi.fn(),
}));

// ── Helpers ──────────────────────────────────────────────

function renderForm() {
  const qc = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return render(
    <QueryClientProvider client={qc}>
      <LoginForm />
    </QueryClientProvider>,
  );
}

// ── Tests ────────────────────────────────────────────────

describe("LoginForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows validation error for empty email", async () => {
    const user = userEvent.setup();
    renderForm();

    const submitBtn = screen.getByRole("button", { name: /sign in/i });
    await user.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText(/email is required/i)).toBeInTheDocument();
    });
  });

  it("shows validation error for short password", async () => {
    const user = userEvent.setup();
    renderForm();

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);

    await user.type(emailInput, "test@example.com");
    await user.type(passwordInput, "short");

    const submitBtn = screen.getByRole("button", { name: /sign in/i });
    await user.click(submitBtn);

    await waitFor(() => {
      expect(
        screen.getByText(/password must be at least 8 characters/i),
      ).toBeInTheDocument();
    });
  });

  it("calls login mutation and shows form error on 401", async () => {
    const user = userEvent.setup();

    // Simulate a 401 from the API.
    const axiosError = {
      response: { data: { detail: "Invalid email or password." }, status: 401 },
      isAxiosError: true,
    };
    mockLogin.mockRejectedValueOnce(axiosError);

    renderForm();

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);

    await user.type(emailInput, "test@example.com");
    await user.type(passwordInput, "strongpass123");

    const submitBtn = screen.getByRole("button", { name: /sign in/i });
    await user.click(submitBtn);

    await waitFor(() => {
      // The form-level error banner should appear.
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
  });

  it("triggers guest mutation when clicking 'Continue as demo guest'", async () => {
    const user = userEvent.setup();

    mockLoginAsGuest.mockResolvedValueOnce({
      user: {
        id: "test-id",
        email: null,
        name: "Guest-1234",
        role: "guest",
        status: "active",
        is_guest: true,
        created_at: new Date().toISOString(),
      },
      tokens: {
        access_token: "at",
        refresh_token: "rt",
        token_type: "bearer",
        expires_in: 1800,
      },
    });

    renderForm();

    const guestBtn = screen.getByRole("button", {
      name: /continue as demo guest/i,
    });
    await user.click(guestBtn);

    await waitFor(() => {
      expect(mockLoginAsGuest).toHaveBeenCalledOnce();
    });
  });
});
