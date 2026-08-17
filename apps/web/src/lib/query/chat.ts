/**
 * TanStack Query hooks for RAG chat and sessions.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { AxiosError } from "axios";

import {
  askChat,
  deleteChatSession,
  getChatSession,
  listChatSessions,
} from "@/lib/api/chat";
import type { ErrorResponse } from "@/lib/auth/types";
import { queryKeys } from "@/lib/query/keys";
import { useAuthStore } from "@/stores/authStore";
import type {
  ChatRequest,
  ChatResponse,
  ChatSession,
  ChatSessionDetail,
} from "@/types/chat";

/**
 * Mutation hook for asking a question to the knowledge base (non-streaming).
 */
export function useAskChat() {
  return useMutation<ChatResponse, AxiosError<ErrorResponse>, ChatRequest>({
    mutationFn: (data: ChatRequest) => askChat(data),
  });
}

/**
 * Query hook for listing user's chat sessions.
 */
export function useChatSessions() {
  const status = useAuthStore((s) => s.status);
  return useQuery<ChatSession[], AxiosError<ErrorResponse>>({
    queryKey: queryKeys.chat.sessions(),
    queryFn: () => listChatSessions(),
    enabled: status === "authenticated",
  });
}

/**
 * Query hook for fetching a specific session's full message history.
 */
export function useChatSessionDetail(sessionId: string | null) {
  const status = useAuthStore((s) => s.status);
  return useQuery<ChatSessionDetail, AxiosError<ErrorResponse>>({
    queryKey: queryKeys.chat.sessionDetail(sessionId ?? ""),
    queryFn: () => getChatSession(sessionId!),
    enabled: Boolean(sessionId) && status === "authenticated",
  });
}

/**
 * Mutation hook for deleting a chat session.
 */
export function useDeleteChatSession() {
  const queryClient = useQueryClient();

  return useMutation<void, AxiosError<ErrorResponse>, string>({
    mutationFn: (sessionId: string) => deleteChatSession(sessionId),
    onSuccess: (_, deletedId) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.chat.sessions() });
      queryClient.removeQueries({
        queryKey: queryKeys.chat.sessionDetail(deletedId),
      });
    },
  });
}
