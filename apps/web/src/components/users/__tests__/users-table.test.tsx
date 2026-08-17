/**
 * UsersTable component tests — RTL.
 * Tests all 4 UI states: loading, empty, error, success.
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { UsersTable } from "../users-table";
import type { UserRow } from "@/types/user";

const mockUsers: UserRow[] = [
  {
    id: "user-1",
    name: "Alice Admin",
    email: "alice@opspilot.dev",
    role: "admin",
    status: "active",
    team_name: "Engineering",
    team_id: "team-1",
    is_guest: false,
    last_active: new Date().toISOString(),
    created_at: new Date().toISOString(),
  },
  {
    id: "user-2",
    name: "Bob Viewer",
    email: "bob@opspilot.dev",
    role: "viewer",
    status: "pending",
    team_name: "Product",
    team_id: "team-2",
    is_guest: false,
    last_active: null,
    created_at: new Date().toISOString(),
  },
];

const defaultProps = {
  data: mockUsers,
  total: 2,
  page: 1,
  pageSize: 20,
  sortBy: "created_at" as const,
  sortDir: "desc" as const,
  isLoading: false,
  isError: false,
  error: null,
  onPageChange: vi.fn(),
  onPageSizeChange: vi.fn(),
  onSortChange: vi.fn(),
  onEditUser: vi.fn(),
  onDeleteUser: vi.fn(),
  selectedIds: [],
  onSelectionChange: vi.fn(),
  onRetry: vi.fn(),
  onResetFilters: vi.fn(),
};

describe("UsersTable", () => {
  it("renders success state with users table data", () => {
    render(<UsersTable {...defaultProps} />);

    expect(screen.getByText("Alice Admin")).toBeInTheDocument();
    expect(screen.getByText("alice@opspilot.dev")).toBeInTheDocument();
    expect(screen.getByText("Bob Viewer")).toBeInTheDocument();
    expect(screen.getByText("bob@opspilot.dev")).toBeInTheDocument();
    expect(screen.getByText("Engineering")).toBeInTheDocument();
    expect(screen.getByText("Product")).toBeInTheDocument();
  });

  it("renders loading state with skeleton loaders", () => {
    render(<UsersTable {...defaultProps} isLoading={true} data={[]} />);

    expect(screen.queryByText("Alice Admin")).not.toBeInTheDocument();
    const table = screen.getByRole("table");
    expect(table).toBeInTheDocument();
  });

  it("renders empty state when no users are returned", () => {
    render(<UsersTable {...defaultProps} data={[]} total={0} />);

    expect(screen.getByText("No users found")).toBeInTheDocument();
    expect(
      screen.getByText(/no users match your active search/i)
    ).toBeInTheDocument();
  });

  it("renders error state with retry button", async () => {
    const handleRetry = vi.fn();
    render(
      <UsersTable
        {...defaultProps}
        isError={true}
        error={new Error("Network connection error")}
        onRetry={handleRetry}
      />
    );

    expect(screen.getByText("Failed to load users")).toBeInTheDocument();
    expect(screen.getByText("Network connection error")).toBeInTheDocument();

    const retryButton = screen.getByRole("button", { name: /retry request/i });
    await userEvent.click(retryButton);
    expect(handleRetry).toHaveBeenCalledTimes(1);
  });
});
