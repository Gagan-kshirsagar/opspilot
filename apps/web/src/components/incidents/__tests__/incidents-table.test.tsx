/**
 * IncidentsTable component tests — RTL.
 * Tests all 4 UI states: loading, empty, error, success.
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { IncidentsTable } from "../incidents-table";
import type { IncidentItem } from "@/types/incident";

const mockIncidents: IncidentItem[] = [
  {
    id: "inc-1",
    title: "Elasticsearch node crash",
    severity: "sev1",
    status: "open",
    service_id: "srv-1",
    service_name: "Search Index",
    assignee_id: "usr-1",
    assignee_name: "Manager User",
    resolved_at: null,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: "inc-2",
    title: "SMS provider quota warning",
    severity: "sev3",
    status: "resolved",
    service_id: "srv-2",
    service_name: "Notification Service",
    assignee_id: null,
    assignee_name: null,
    resolved_at: new Date().toISOString(),
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

const defaultProps = {
  data: mockIncidents,
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
  onSelectIncident: vi.fn(),
  onRetry: vi.fn(),
  onResetFilters: vi.fn(),
};

describe("IncidentsTable", () => {
  it("renders success state with incidents table rows", () => {
    render(<IncidentsTable {...defaultProps} />);

    expect(screen.getByText("Elasticsearch node crash")).toBeInTheDocument();
    expect(screen.getByText("Search Index")).toBeInTheDocument();
    expect(screen.getByText("Manager User")).toBeInTheDocument();
    expect(screen.getByText("SEV-1")).toBeInTheDocument();
    expect(screen.getByText("Open")).toBeInTheDocument();

    expect(screen.getByText("SMS provider quota warning")).toBeInTheDocument();
    expect(screen.getByText("Notification Service")).toBeInTheDocument();
    expect(screen.getByText("Unassigned")).toBeInTheDocument();
    expect(screen.getByText("SEV-3")).toBeInTheDocument();
    expect(screen.getByText("Resolved")).toBeInTheDocument();
  });

  it("renders loading state with skeleton rows", () => {
    render(<IncidentsTable {...defaultProps} isLoading={true} data={[]} />);

    expect(screen.queryByText("Elasticsearch node crash")).not.toBeInTheDocument();
    expect(screen.getByRole("table")).toBeInTheDocument();
  });

  it("renders empty state when no incidents match", () => {
    render(<IncidentsTable {...defaultProps} data={[]} total={0} />);

    expect(screen.getByText("No incidents found")).toBeInTheDocument();
  });

  it("renders error state with retry button", async () => {
    const handleRetry = vi.fn();
    render(
      <IncidentsTable
        {...defaultProps}
        isError={true}
        error={new Error("Failed to load")}
        onRetry={handleRetry}
      />
    );

    expect(screen.getByText("Failed to load incidents")).toBeInTheDocument();
    expect(screen.getByText("Failed to load")).toBeInTheDocument();

    const retryButton = screen.getByRole("button", { name: /retry/i });
    await userEvent.click(retryButton);
    expect(handleRetry).toHaveBeenCalledTimes(1);
  });
});
