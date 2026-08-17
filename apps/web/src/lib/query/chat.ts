/**
 * TanStack Query hooks for RAG chat.
 */

import { useMutation } from "@tanstack/react-query";
import type { AxiosError } from "axios";

import { askChat } from "@/lib/api/chat";
import type { ErrorResponse } from "@/lib/auth/types";
import type { ChatRequest, ChatResponse } from "@/types/chat";

/**
 * Mutation hook for asking a question to the knowledge base.
 */
export function useAskChat() {
  return useMutation<ChatResponse, AxiosError<ErrorResponse>, ChatRequest>({
    mutationFn: (data: ChatRequest) => askChat(data),
  });
}
