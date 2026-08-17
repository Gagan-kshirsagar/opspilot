/**
 * useChatStream hook tests — Vitest.
 * Tests SSE streaming parsing, token accumulation, citations, abort/stop, and error handling.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { useChatStream } from "@/hooks/useChatStream";

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  }
  Wrapper.displayName = "TestQueryClientWrapper";
  return Wrapper;
}

describe("useChatStream", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("accumulates streaming tokens and handles citations and done events", async () => {
    const sseChunks = [
      'event: citations\ndata: {"citations":[{"document_title":"SLAs","ordinal":0,"snippet":"99.98%","score":0.9}],"used_context":true}\n\n',
      'event: token\ndata: {"text":"The "}\n\n',
      'event: token\ndata: {"text":"SLA "}\n\n',
      'event: token\ndata: {"text":"is 99.98%."}\n\n',
      'event: done\ndata: {"session_id":"sess-123","message_id":"msg-456","title":"SLA Query"}\n\n',
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

    const onDoneMock = vi.fn();
    const { result } = renderHook(() => useChatStream({ onDone: onDoneMock }), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.sendMessage("What is the SLA?");
    });

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/chat/stream"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ question: "What is the SLA?" }),
      })
    );
    expect(onDoneMock).toHaveBeenCalledWith("sess-123");
    expect(result.current.isStreaming).toBe(false);
  });

  it("handles stop() and aborts stream", async () => {
    const mockReadableStream = new ReadableStream({
      start(controller) {
        const encoder = new TextEncoder();
        controller.enqueue(encoder.encode('event: token\ndata: {"text":"Partial..."}\n\n'));
      },
    });

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      body: mockReadableStream,
    });

    const { result } = renderHook(() => useChatStream(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.sendMessage("Long question");
    });

    expect(result.current.isStreaming).toBe(true);

    act(() => {
      result.current.stop();
    });

    expect(result.current.isStreaming).toBe(false);
  });

  it("handles server error response cleanly", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      json: () => Promise.resolve({ detail: "Database connection failed" }),
    });

    const onErrorMock = vi.fn();
    const { result } = renderHook(() => useChatStream({ onError: onErrorMock }), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.sendMessage("Test query");
    });

    expect(result.current.isStreaming).toBe(false);
    expect(result.current.error).toBe("Database connection failed");
    expect(onErrorMock).toHaveBeenCalledWith("Database connection failed");
  });
});
