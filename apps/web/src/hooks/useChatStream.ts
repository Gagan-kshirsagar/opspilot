"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { getAccessToken } from "@/lib/api/client";
import { queryKeys } from "@/lib/query/keys";
import type {
  AgentStep,
  Citation,
  StreamCitationsPayload,
  StreamDonePayload,
  StreamErrorPayload,
  StreamStepPayload,
  StreamTokenPayload,
} from "@/types/chat";

interface UseChatStreamOptions {
  onDone?: (sessionId: string) => void;
  onError?: (error: string) => void;
}

export function useChatStream(options?: UseChatStreamOptions) {
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingUserMessage, setStreamingUserMessage] = useState<string | null>(null);
  const [streamingSteps, setStreamingSteps] = useState<AgentStep[]>([]);
  const [streamingContent, setStreamingContent] = useState("");
  const [streamingCitations, setStreamingCitations] = useState<Citation[] | null>(null);
  const [streamingUsedContext, setStreamingUsedContext] = useState<boolean | null>(null);
  const [error, setError] = useState<string | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);
  const queryClient = useQueryClient();

  // Cleanup active stream on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const stop = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsStreaming(false);
  }, []);

  const reset = useCallback(() => {
    stop();
    setStreamingUserMessage(null);
    setStreamingSteps([]);
    setStreamingContent("");
    setStreamingCitations(null);
    setStreamingUsedContext(null);
    setError(null);
  }, [stop]);

  const sendMessage = useCallback(
    async (question: string, sessionId?: string | null) => {
      const trimmed = question.trim();
      if (!trimmed || isStreaming) return;

      // Abort any existing stream
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      const controller = new AbortController();
      abortControllerRef.current = controller;

      setIsStreaming(true);
      setError(null);
      setStreamingUserMessage(trimmed);
      setStreamingSteps([]);
      setStreamingContent("");
      setStreamingCitations(null);
      setStreamingUsedContext(null);

      const token = getAccessToken();
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      try {
        const payload: { question: string; session_id?: string } = {
          question: trimmed,
        };
        if (sessionId) {
          payload.session_id = sessionId;
        }

        const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
        const response = await fetch(`${baseUrl}/api/v1/chat/stream`, {
          method: "POST",
          headers,
          body: JSON.stringify(payload),
          signal: controller.signal,
          credentials: "include",
        });

        if (!response.ok) {
          let errorMsg = `Server error (${response.status})`;
          try {
            const errJson = await response.json();
            if (errJson?.detail) {
              errorMsg = errJson.detail;
            }
          } catch {
            // Ignore non-json error body
          }
          throw new Error(errorMsg);
        }

        if (!response.body) {
          throw new Error("No readable response body received.");
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = "";

        while (true) {
          const { value, done } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const blocks = buffer.split("\n\n");
          buffer = blocks.pop() ?? "";

          for (const block of blocks) {
            const lines = block.split("\n");
            let eventType = "message";
            let dataStr = "";

            for (const line of lines) {
              if (line.startsWith("event: ")) {
                eventType = line.slice(7).trim();
              } else if (line.startsWith("data: ")) {
                dataStr = line.slice(6).trim();
              }
            }

            if (!dataStr) continue;

            try {
              const parsed = JSON.parse(dataStr);

              if (eventType === "step") {
                const stepData = parsed as StreamStepPayload;
                setStreamingSteps((prev) => [...prev, stepData]);
              } else if (eventType === "token") {
                const tokenData = parsed as StreamTokenPayload;
                if (tokenData.text) {
                  setStreamingContent((prev) => prev + tokenData.text);
                }
              } else if (eventType === "citations") {
                const citationsData = parsed as StreamCitationsPayload;
                setStreamingCitations(citationsData.citations || []);
                setStreamingUsedContext(citationsData.used_context);
              } else if (eventType === "done") {
                const doneData = parsed as StreamDonePayload;
                setIsStreaming(false);
                abortControllerRef.current = null;

                // Invalidate query cache for sessions & active session messages
                queryClient.invalidateQueries({ queryKey: queryKeys.chat.sessions() });
                queryClient.invalidateQueries({
                  queryKey: queryKeys.chat.sessionDetail(doneData.session_id),
                });

                // Clear live ephemeral stream buffer
                setStreamingUserMessage(null);
                setStreamingSteps([]);
                setStreamingContent("");
                setStreamingCitations(null);
                setStreamingUsedContext(null);

                options?.onDone?.(doneData.session_id);
                return;
              } else if (eventType === "error") {
                const errorData = parsed as StreamErrorPayload;
                const msg = errorData.message || "Streaming error occurred.";
                setError(msg);
                setIsStreaming(false);
                options?.onError?.(msg);
                return;
              }
            } catch (err) {
              console.error("Failed to parse SSE event payload:", dataStr, err);
            }
          }
        }
      } catch (err: unknown) {
        if ((err as Error)?.name === "AbortError") {
          setIsStreaming(false);
          return;
        }

        const msg = (err as Error)?.message || "Failed to stream chat answer.";
        setError(msg);
        setIsStreaming(false);
        options?.onError?.(msg);
      } finally {
        if (abortControllerRef.current === controller) {
          abortControllerRef.current = null;
        }
      }
    },
    [isStreaming, options, queryClient]
  );

  return {
    isStreaming,
    streamingUserMessage,
    streamingSteps,
    streamingContent,
    streamingCitations,
    streamingUsedContext,
    error,
    sendMessage,
    stop,
    reset,
  };
}
