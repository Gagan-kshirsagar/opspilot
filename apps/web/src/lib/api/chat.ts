/**
 * Typed API functions for RAG chat.
 */

import { apiClient } from "@/lib/api/client";
import type { ChatRequest, ChatResponse } from "@/types/chat";

/**
 * Send a question to the grounded OpsPilot knowledge base chat endpoint.
 */
export async function askChat(payload: ChatRequest): Promise<ChatResponse> {
  const { data } = await apiClient.post<ChatResponse>("/api/v1/chat", payload);
  return data;
}
