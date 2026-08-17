/**
 * ServicesList component tests — RTL.
 * Tests all 4 UI states: loading, empty, error, success.
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ServicesList } from "../services-list";
import type { ServiceItem } from "@/types/service";

const mockServices: ServiceItem[] = [
  {
    id: "srv-1",
    name: "API Gateway",
    status: "healthy",
    uptime_pct: 99.98,
    owner_user_id: "user-1",
    owner_name: "Admin User",
    note: "Edge routing proxy",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: "srv-2",
    name: "Search Index",
    status: "down",
    uptime_pct: 84.5,
    owner_user_id: "user-2",
    owner_name: "Manager User",
    note: "Elasticsearch cluster",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

const defaultProps = {
  services: mockServices,
  isLoading: false,
  isError: false,
  error: null,
  onRetry: vi.fn(),
  onResetFilters: vi.fn(),
  hasActiveFilters: false,
};

describe("ServicesList", () => {
  it("renders success state with service cards", () => {
    render(<ServicesList {...defaultProps} />);

    expect(screen.getByText("API Gateway")).toBeInTheDocument();
    expect(screen.getByText("99.98%")).toBeInTheDocument();
    expect(screen.getByText("Search Index")).toBeInTheDocument();
    expect(screen.getByText("84.50%")).toBeInTheDocument();
    expect(screen.getByText("Admin User")).toBeInTheDocument();
    expect(screen.getByText("Manager User")).toBeInTheDocument();
  });

  it("renders loading state", () => {
    render(<ServicesList {...defaultProps} isLoading={true} services={[]} />);

    expect(screen.queryByText("API Gateway")).not.toBeInTheDocument();
  });

  it("renders empty state when no services are available", () => {
    render(<ServicesList {...defaultProps} services={[]} />);

    expect(screen.getByText("No services found")).toBeInTheDocument();
  });

  it("renders error state with retry button", async () => {
    const handleRetry = vi.fn();
    render(
      <ServicesList
        {...defaultProps}
        isError={true}
        error={new Error("Service unavailable")}
        onRetry={handleRetry}
      />
    );

    expect(screen.getByText("Failed to load services")).toBeInTheDocument();
    expect(screen.getByText("Service unavailable")).toBeInTheDocument();

    const retryButton = screen.getByRole("button", { name: /retry/i });
    await userEvent.click(retryButton);
    expect(handleRetry).toHaveBeenCalledTimes(1);
  });
});
