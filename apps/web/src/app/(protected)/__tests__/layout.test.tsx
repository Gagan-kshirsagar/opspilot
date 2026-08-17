/**
 * ProtectedLayout and session restoration tests — Vitest + RTL.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import ProtectedLayout from "../layout";
import {
  AuthBootstrap,
  resetBootstrapForTests,
} from "@/components/auth/auth-bootstrap";
import { useAuthStore } from "@/stores/authStore";
import { queryKeys } from "@/lib/query/keys";


// ── Mocks ────────────────────────────────────────────────

const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
  usePathname: () => "/dashboard",
}));

const mockRestoreSession = vi.fn();
const mockGetCurrentUser = vi.fn();
const mockLogout = vi.fn();

vi.mock("@/lib/auth", () => ({
  authProvider: {
    restoreSession: () => mockRestoreSession(),
    getCurrentUser: () => mockGetCurrentUser(),
    logout: () => mockLogout(),
  },
}));

vi.mock("@/lib/api/client", () => ({
  apiClient: { post: vi.fn(), get: vi.fn() },
  setAccessToken: vi.fn(),
  getAccessToken: () => null,
  setRefreshToken: vi.fn(),
  getRefreshToken: () => null,
  clearTokens: vi.fn(),
}));

function renderWithClient(ui: React.ReactNode, queryClient?: QueryClient) {
  const qc =
    queryClient ??
    new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>);
}

describe("ProtectedLayout", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAuthStore.setState({ user: null, status: "loading" });
  });

  it("shows loading screen and does not redirect while status is loading", () => {
    useAuthStore.setState({ user: null, status: "loading" });

    renderWithClient(
      <ProtectedLayout>
        <div>Protected Content</div>
      </ProtectedLayout>,
    );

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
    expect(screen.queryByText("Protected Content")).not.toBeInTheDocument();
    expect(mockPush).not.toHaveBeenCalled();
  });

  it("renders protected children when authenticated", () => {
    useAuthStore.setState({
      user: {
        id: "user-123",
        email: "alice@example.com",
        name: "Alice",
        role: "viewer",
        status: "active",
        is_guest: false,
        created_at: new Date().toISOString(),
      },
      status: "authenticated",
    });

    renderWithClient(
      <ProtectedLayout>
        <div>Protected Content</div>
      </ProtectedLayout>,
    );

    expect(screen.getByText("Protected Content")).toBeInTheDocument();
    expect(screen.getByText("Alice")).toBeInTheDocument();
    expect(mockPush).not.toHaveBeenCalled();
  });

  it("redirects to /login when unauthenticated", async () => {
    useAuthStore.setState({ user: null, status: "unauthenticated" });

    renderWithClient(
      <ProtectedLayout>
        <div>Protected Content</div>
      </ProtectedLayout>,
    );

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/login");
    });
    expect(screen.queryByText("Protected Content")).not.toBeInTheDocument();
  });
});

describe("AuthBootstrap", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    resetBootstrapForTests();
    useAuthStore.setState({ user: null, status: "loading" });
  });

  it("rehydrates session and updates store and query cache when valid session exists", async () => {
    const mockUser = {
      id: "user-456",
      email: "bob@example.com",
      name: "Bob",
      role: "viewer" as const,
      status: "active",
      is_guest: false,
      created_at: new Date().toISOString(),
    };

    mockRestoreSession.mockResolvedValueOnce(mockUser);

    const qc = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });

    render(
      <QueryClientProvider client={qc}>
        <AuthBootstrap>
          <div>App Root</div>
        </AuthBootstrap>
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(useAuthStore.getState().status).toBe("authenticated");
      expect(useAuthStore.getState().user?.name).toBe("Bob");
    });

    const cachedData = qc.getQueryData(queryKeys.auth.me());
    expect(cachedData).toEqual(mockUser);
  });

  it("sets unauthenticated status when no valid session can be restored", async () => {
    mockRestoreSession.mockResolvedValueOnce(null);

    const qc = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });

    render(
      <QueryClientProvider client={qc}>
        <AuthBootstrap>
          <div>App Root</div>
        </AuthBootstrap>
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(useAuthStore.getState().status).toBe("unauthenticated");
      expect(useAuthStore.getState().user).toBeNull();
    });
  });
});
