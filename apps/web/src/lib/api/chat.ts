/**
 * Typed API functions for RAG chat and sessions.
 */

import { apiClient } from "@/lib/api/client";
import type {
  ChatRequest,
  ChatResponse,
  ChatSession,
  ChatSessionDetail,
} from "@/types/chat";

/**
 * Send a question to the grounded OpsPilot knowledge base chat endpoint (non-streaming).
 */
export async function askChat(payload: ChatRequest): Promise<ChatResponse> {
  const { data } = await apiClient.post<ChatResponse>("/api/v1/chat", payload);
  return data;
}

/**
 * List all chat sessions for the current authenticated user.
 */
export async function listChatSessions(): Promise<ChatSession[]> {
  const { data } = await apiClient.get<ChatSession[]>("/api/v1/chat/sessions");
  return data;
}

/**
 * Fetch full session detail including message history.
 */
export async function getChatSession(sessionId: string): Promise<ChatSessionDetail> {
  const { data } = await apiClient.get<ChatSessionDetail>(
    `/api/v1/chat/sessions/${sessionId}`
  );
  return data;
}

/**
 * Delete a chat session.
 */
export async function deleteChatSession(sessionId: string): Promise<void> {
  await apiClient.delete(`/api/v1/chat/sessions/${sessionId}`);
}
