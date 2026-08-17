/**
 * AskPanel component tests — RTL.
 * Tests multi-turn chat layout, session sidebar, suggestion clicks, and streaming message display.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { AskPanel } from "../ask-panel";
import * as chatApi from "@/lib/api/chat";

vi.mock("@/lib/api/chat");

import { useAuthStore } from "@/stores/authStore";

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
    window.HTMLElement.prototype.scrollIntoView = vi.fn();
    useAuthStore.setState({
      status: "authenticated",
      user: {
        id: "user-1",
        email: "test@test.com",
        name: "Test User",
        role: "admin",
        status: "active",
        is_guest: false,
        created_at: new Date().toISOString(),
      },
    });
    vi.spyOn(chatApi, "listChatSessions").mockResolvedValue([
      {
        id: "sess-1",
        user_id: "user-1",
        title: "Previous SLA Discussion",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    ]);
  });

  it("renders multi-turn chat interface with sidebar and input", async () => {
    renderWithClient(<AskPanel />);

    expect(screen.getByText("Conversations")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /new chat/i })).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText(/ask a question or follow up on previous turns/i)
    ).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Previous SLA Discussion")).toBeInTheDocument();
    });
  });

  it("loads existing session messages when session is clicked in sidebar", async () => {
    vi.spyOn(chatApi, "getChatSession").mockResolvedValueOnce({
      id: "sess-1",
      user_id: "user-1",
      title: "Previous SLA Discussion",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      messages: [
        {
          id: "m-1",
          session_id: "sess-1",
          role: "user",
          content: "What is the API Gateway SLA?",
          created_at: new Date().toISOString(),
        },
        {
          id: "m-2",
          session_id: "sess-1",
          role: "assistant",
          content: "The API Gateway availability SLA is 99.98%.",
          citations: [
            {
              document_title: "Service Level Agreements",
              ordinal: 0,
              snippet: "API Gateway availability SLA is 99.98%.",
              score: 0.95,
            },
          ],
          created_at: new Date().toISOString(),
        },
      ],
    });

    renderWithClient(<AskPanel />);

    await waitFor(() => {
      expect(screen.getByText("Previous SLA Discussion")).toBeInTheDocument();
    });

    await userEvent.click(screen.getByText("Previous SLA Discussion"));

    await waitFor(() => {
      expect(screen.getByText("What is the API Gateway SLA?")).toBeInTheDocument();
      expect(screen.getByText("The API Gateway availability SLA is 99.98%.")).toBeInTheDocument();
      expect(screen.getByText("Service Level Agreements")).toBeInTheDocument();
      expect(screen.getByText("95%")).toBeInTheDocument();
    });
  });

  it("populates input and sends message when suggestion prompt is clicked", async () => {
    const sseChunks = [
      'event: citations\ndata: {"citations":[],"used_context":false}\n\n',
      'event: token\ndata: {"text":"I don\'t have that in the knowledge base."}\n\n',
      'event: done\ndata: {"session_id":"sess-2","message_id":"msg-2","title":"New Chat"}\n\n',
    ];

    let chunkIndex = 0;
    const mockReadableStream = new ReadableStream({
      pull(controller) {
        if (chunkIndex < sseChunks.length) {
          const encoder = new TextEncoder();
          controller.enqueue(encoder.encode(sseChunks[chunkIndex]));
          chunkIndex++;
        } else {
          controller.close();
        }
      },
    });

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      body: mockReadableStream,
    });

    renderWithClient(<AskPanel />);

    expect(
      screen.getByText(/what is the p1 incident escalation process/i)
    ).toBeInTheDocument();

    await userEvent.click(
      screen.getByText(/what is the p1 incident escalation process/i)
    );

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/chat/stream"),
      expect.objectContaining({
        method: "POST",
      })
    );
  });
});
