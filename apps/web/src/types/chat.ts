/**
 * Chat and RAG Knowledge Base types — mirrors backend schemas.
 */

export interface ChatRequest {
  question: string;
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
