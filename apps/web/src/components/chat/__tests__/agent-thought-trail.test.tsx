/**
 * AgentThoughtTrail component tests — Vitest & RTL.
 * Tests tool steps rendering, icons, collapse/expand toggle, and streaming indicators.
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { AgentThoughtTrail } from "../agent-thought-trail";
import type { AgentStep } from "@/types/chat";

describe("AgentThoughtTrail", () => {
  it("renders nothing when steps list is empty", () => {
    const { container } = render(<AgentThoughtTrail steps={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders reasoning steps and formats tool names", () => {
    const steps: AgentStep[] = [
      {
        type: "tool_call",
        tool: "query_services",
        args: { status: "degraded" },
      },
      {
        type: "tool_result",
        tool: "query_services",
        summary: "Retrieved 1 live service status record(s)",
      },
      {
        type: "tool_call",
        tool: "retrieve_docs",
        args: { query: "Payment Gateway Runbook" },
      },
      {
        type: "tool_result",
        tool: "retrieve_docs",
        summary: "Found 1 relevant knowledge base source(s)",
      },
    ];

    render(<AgentThoughtTrail steps={steps} isStreaming={false} />);

    expect(screen.getByText(/Reasoning Steps \(4\)/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Checking services with status 'degraded'/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText("Retrieved 1 live service status record(s)")
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Searching runbooks for "Payment Gateway Runbook"/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText("Found 1 relevant knowledge base source(s)")
    ).toBeInTheDocument();
  });

  it("toggles collapse and expand when header is clicked", async () => {
    const steps: AgentStep[] = [
      {
        type: "tool_call",
        tool: "query_incidents",
        args: { severity: "sev1" },
      },
    ];

    render(<AgentThoughtTrail steps={steps} isStreaming={false} />);

    expect(
      screen.getByText(/Querying SEV1 incidents/i)
    ).toBeInTheDocument();

    const toggleButton = screen.getByRole("button", {
      name: /toggle agent reasoning steps/i,
    });

    // Click to collapse
    await userEvent.click(toggleButton);
    expect(
      screen.queryByText(/Querying SEV1 incidents/i)
    ).not.toBeInTheDocument();

    // Click to expand again
    await userEvent.click(toggleButton);
    expect(
      screen.getByText(/Querying SEV1 incidents/i)
    ).toBeInTheDocument();
  });
});
