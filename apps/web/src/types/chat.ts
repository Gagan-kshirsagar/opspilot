/**
 * Chat and RAG Knowledge Base types — mirrors backend schemas.
 */

export interface ChatRequest {
  question: string;
}

export interface ChatStreamRequest {
  question: string;
  session_id?: string;
}

export interface Citation {
  document_title: string;
  ordinal: number;
  snippet: string;
  score: number;
}

export interface ChatResponse {
  answer: string;
  citations: Citation[];
  used_context: boolean;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[] | null;
  created_at: string;
}

export interface ChatSession {
  id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ChatSessionDetail extends ChatSession {
  messages: ChatMessage[];
}

export interface StreamTokenPayload {
  text: string;
}

export interface StreamCitationsPayload {
  citations: Citation[];
  used_context: boolean;
}

export interface StreamDonePayload {
  session_id: string;
  message_id: string;
  title: string;
}

export interface StreamErrorPayload {
  message: string;
}
