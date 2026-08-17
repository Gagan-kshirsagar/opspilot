/**
 * AskPanel component tests — RTL.
 * Tests all 4 UI states: initial, loading, error, and answer with citations.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { AskPanel } from "../ask-panel";
import * as chatApi from "@/lib/api/chat";
import type { ChatResponse } from "@/types/chat";

vi.mock("@/lib/api/chat");

function renderWithClient(ui: React.ReactElement) {
  const testQueryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return render(
    <QueryClientProvider client={testQueryClient}>{ui}</QueryClientProvider>
  );
}

describe("AskPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders initial state with input and suggestions", () => {
    renderWithClient(<AskPanel />);

    expect(screen.getByPlaceholderText(/ask anything about opspilot/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /ask opspilot/i })).toBeInTheDocument();
    expect(screen.getByText(/what is the p1 incident escalation process/i)).toBeInTheDocument();
  });

  it("submits question and renders grounded answer with citations", async () => {
    const mockResponse: ChatResponse = {
      answer: "For P1 critical incidents, page on-call immediately and open war room.",
      citations: [
        {
          document_title: "Incident Response Runbook",
          ordinal: 0,
          snippet: "SEV-1 is critical customer-facing outage. Escalation steps require paging on-call.",
          score: 0.88,
        },
      ],
      used_context: true,
    };

    vi.spyOn(chatApi, "askChat").mockResolvedValueOnce(mockResponse);

    renderWithClient(<AskPanel />);

    const input = screen.getByPlaceholderText(/ask anything about opspilot/i);
    await userEvent.type(input, "What is the P1 process?");
    const sendButton = screen.getByRole("button", { name: /ask opspilot/i });
    await userEvent.click(sendButton);

    await waitFor(() => {
      expect(screen.getByText("For P1 critical incidents, page on-call immediately and open war room.")).toBeInTheDocument();
    });

    expect(screen.getByText("Grounded (1 sources)")).toBeInTheDocument();
    expect(screen.getByText("Incident Response Runbook")).toBeInTheDocument();
    expect(screen.getByText("88% match")).toBeInTheDocument();
  });

  it("renders decline guardrail banner when out of knowledge base", async () => {
    const mockResponse: ChatResponse = {
      answer: "I don't have that in the knowledge base.",
      citations: [],
      used_context: false,
    };

    vi.spyOn(chatApi, "askChat").mockResolvedValueOnce(mockResponse);

    renderWithClient(<AskPanel />);

    const input = screen.getByPlaceholderText(/ask anything about opspilot/i);
    await userEvent.type(input, "What is the capital of France?");
    await userEvent.click(screen.getByRole("button", { name: /ask opspilot/i }));

    await waitFor(() => {
      expect(screen.getByText("Knowledge Base Boundary Guardrail")).toBeInTheDocument();
    });

    expect(screen.getByText("Out of Knowledge Base")).toBeInTheDocument();
    expect(screen.getByText("I don't have that in the knowledge base.")).toBeInTheDocument();
  });

  it("renders error state when API request fails", async () => {
    vi.spyOn(chatApi, "askChat").mockRejectedValueOnce(new Error("Connection timeout"));

    renderWithClient(<AskPanel />);

    const input = screen.getByPlaceholderText(/ask anything about opspilot/i);
    await userEvent.type(input, "Test query");
    await userEvent.click(screen.getByRole("button", { name: /ask opspilot/i }));

    await waitFor(() => {
      expect(screen.getByText("Query Failed")).toBeInTheDocument();
    });

    expect(screen.getByText("Connection timeout")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /retry/i })).toBeInTheDocument();
  });
});
