"use client";

import { useEffect, useRef, useState } from "react";
import {
  Bot,
  ChevronDown,
  ChevronUp,
  FileText,
  HelpCircle,
  Info,
  Sparkles,
  User,
} from "lucide-react";

import { Skeleton } from "@/components/ui/skeleton";
import { AgentThoughtTrail } from "@/components/chat/agent-thought-trail";
import type { AgentStep, ChatMessage, Citation } from "@/types/chat";

interface ChatMessageListProps {
  messages: ChatMessage[];
  streamingUserMessage: string | null;
  streamingSteps?: AgentStep[];
  streamingContent: string;
  streamingCitations: Citation[] | null;
  streamingUsedContext: boolean | null;
  isStreaming: boolean;
  isLoadingSession: boolean;
  onSelectPrompt: (prompt: string) => void;
}

const SUGGESTED_PROMPTS = [
  "What is the P1 incident escalation process?",
  "What are the availability SLA targets for our services?",
  "How do I execute a manual rollback for a service?",
  "What are the rate limit quotas at the API Gateway?",
  "What is the procedure for database point-in-time recovery?",
];

export function ChatMessageList({
  messages,
  streamingUserMessage,
  streamingSteps = [],
  streamingContent,
  streamingCitations,
  streamingUsedContext,
  isStreaming,
  isLoadingSession,
  onSelectPrompt,
}: ChatMessageListProps) {
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const [expandedCitations, setExpandedCitations] = useState<Record<string, boolean>>({});

  // Auto-scroll to latest message or stream update
  useEffect(() => {
    bottomRef.current?.scrollIntoView?.({ behavior: "smooth" });
  }, [messages, streamingUserMessage, streamingContent]);

  const toggleCitation = (key: string) => {
    setExpandedCitations((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  const hasMessages = messages.length > 0 || Boolean(streamingUserMessage);

  return (
    <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
      {/* Loading Skeleton */}
      {isLoadingSession && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <Skeleton className="h-12 w-2/3 rounded-xl" />
          </div>
          <div className="flex justify-start">
            <Skeleton className="h-24 w-3/4 rounded-xl" />
          </div>
        </div>
      )}

      {/* Empty State with Suggestions */}
      {!isLoadingSession && !hasMessages && (
        <div className="flex flex-col items-center justify-center min-h-[360px] text-center p-6 space-y-5">
          <div className="size-12 rounded-2xl bg-surface-2 border border-subtle flex items-center justify-center text-accent shadow-sm">
            <Sparkles className="size-6" />
          </div>
          <div className="max-w-md space-y-1.5">
            <h3 className="text-base font-semibold text-foreground">
              Ask OpsPilot Knowledge Base
            </h3>
            <p className="text-xs text-muted leading-relaxed">
              Ask multi-turn questions grounded in 14 verified operational runbooks, SLAs, and troubleshooting guides.
            </p>
          </div>

          <div className="w-full max-w-lg space-y-2 pt-2 text-left">
            <span className="text-[11px] font-medium text-faint flex items-center gap-1.5 px-1">
              <HelpCircle className="size-3 text-accent" />
              Suggested Queries:
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {SUGGESTED_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  type="button"
                  onClick={() => onSelectPrompt(prompt)}
                  className="rounded-lg border border-subtle bg-surface-2/40 p-2.5 text-xs text-muted hover:border-accent/40 hover:text-foreground hover:bg-surface-2 transition-colors cursor-pointer text-left leading-snug"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Persisted Messages */}
      {!isLoadingSession &&
        messages.map((msg) => {
          const isUser = msg.role === "user";

          return (
            <div
              key={msg.id}
              className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}
            >
              {!isUser && (
                <div className="size-8 rounded-lg bg-accent/10 border border-accent/20 flex items-center justify-center text-accent shrink-0 mt-0.5">
                  <Bot className="size-4" />
                </div>
              )}

              <div
                className={`max-w-[85%] sm:max-w-[80%] rounded-2xl p-4 text-xs sm:text-sm leading-relaxed ${
                  isUser
                    ? "bg-accent text-accent-foreground rounded-br-none shadow-sm"
                    : "bg-surface-2/60 border border-subtle text-foreground rounded-bl-none shadow-sm space-y-3"
                }`}
              >
                <div className="whitespace-pre-wrap">{msg.content}</div>

                {/* Persisted Citations */}
                {!isUser && msg.citations && msg.citations.length > 0 && (
                  <div className="pt-2 border-t border-subtle/40 space-y-2">
                    <div className="flex items-center gap-1.5 text-[11px] font-semibold text-faint uppercase tracking-wider">
                      <FileText className="size-3.5 text-accent" />
                      Sources ({msg.citations.length})
                    </div>
                    <div className="space-y-1.5">
                      {msg.citations.map((c, i) => {
                        const citeKey = `${msg.id}-${i}`;
                        const isExpanded = Boolean(expandedCitations[citeKey]);

                        return (
                          <div
                            key={citeKey}
                            className="rounded-lg border border-subtle/80 bg-surface/50 p-2 text-xs"
                          >
                            <div className="flex items-center justify-between gap-2">
                              <div className="flex items-center gap-1.5 truncate">
                                <span className="font-medium text-foreground truncate">
                                  {c.document_title}
                                </span>
                                <span className="text-[10px] text-faint">
                                  §{c.ordinal}
                                </span>
                              </div>
                              <div className="flex items-center gap-1.5 shrink-0">
                                <span className="rounded-full bg-accent/10 px-1.5 py-0.2 text-[10px] font-medium text-accent">
                                  {Math.round(c.score * 100)}%
                                </span>
                                <button
                                  type="button"
                                  onClick={() => toggleCitation(citeKey)}
                                  className="text-muted hover:text-foreground cursor-pointer"
                                >
                                  {isExpanded ? (
                                    <ChevronUp className="size-3" />
                                  ) : (
                                    <ChevronDown className="size-3" />
                                  )}
                                </button>
                              </div>
                            </div>
                            {isExpanded && (
                              <p className="mt-1.5 text-[11px] text-muted border-t border-subtle/40 pt-1.5 font-mono">
                                {c.snippet}
                              </p>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>

              {isUser && (
                <div className="size-8 rounded-lg bg-surface-2 border border-subtle flex items-center justify-center text-foreground shrink-0 mt-0.5">
                  <User className="size-4" />
                </div>
              )}
            </div>
          );
        })}

      {/* Active Streaming Turn */}
      {isStreaming && (
        <>
          {/* User question bubble */}
          {streamingUserMessage && (
            <div className="flex justify-end gap-3">
              <div className="max-w-[85%] sm:max-w-[80%] rounded-2xl rounded-br-none bg-accent text-accent-foreground p-4 text-xs sm:text-sm leading-relaxed shadow-sm">
                {streamingUserMessage}
              </div>
              <div className="size-8 rounded-lg bg-surface-2 border border-subtle flex items-center justify-center text-foreground shrink-0 mt-0.5">
                <User className="size-4" />
              </div>
            </div>
          )}

          {/* Assistant streaming token bubble */}
          <div className="flex justify-start gap-3">
            <div className="size-8 rounded-lg bg-accent/10 border border-accent/20 flex items-center justify-center text-accent shrink-0 mt-0.5">
              <Bot className="size-4" />
            </div>
            <div
              className="max-w-[85%] sm:max-w-[80%] rounded-2xl rounded-bl-none bg-surface-2/60 border border-subtle p-4 text-xs sm:text-sm text-foreground leading-relaxed shadow-sm space-y-3"
              aria-live="polite"
            >
              {/* Agent Thought / Tool Steps Trail */}
              {streamingSteps.length > 0 && (
                <AgentThoughtTrail steps={streamingSteps} isStreaming={isStreaming} />
              )}

              {streamingUsedContext === false && (
                <div className="flex items-start gap-2 rounded-lg border border-amber-500/20 bg-amber-500/5 p-2.5 text-xs text-amber-300">
                  <Info className="size-4 shrink-0 mt-0.5" />
                  <span>Out of Knowledge Base Boundary</span>
                </div>
              )}

              <div className="whitespace-pre-wrap">
                {streamingContent || (
                  <span className="text-muted italic flex items-center gap-1.5">
                    <span className="size-2 rounded-full bg-accent animate-ping" />
                    Consulting runbooks & knowledge base...
                  </span>
                )}
                {streamingContent && (
                  <span className="inline-block w-1.5 h-3.5 ml-0.5 bg-accent animate-pulse align-middle" />
                )}
              </div>

              {/* Streaming Citations */}
              {streamingCitations && streamingCitations.length > 0 && (
                <div className="pt-2 border-t border-subtle/40 space-y-1.5">
                  <div className="flex items-center gap-1.5 text-[11px] font-semibold text-faint uppercase tracking-wider">
                    <FileText className="size-3.5 text-accent" />
                    Sources ({streamingCitations.length})
                  </div>
                  <div className="space-y-1">
                    {streamingCitations.map((c, i) => (
                      <div
                        key={`stream-cite-${i}`}
                        className="rounded-lg border border-subtle/80 bg-surface/50 p-2 text-xs flex items-center justify-between"
                      >
                        <span className="font-medium text-foreground truncate">
                          {c.document_title}
                        </span>
                        <span className="rounded-full bg-accent/10 px-1.5 py-0.2 text-[10px] font-medium text-accent">
                          {Math.round(c.score * 100)}%
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </>
      )}

      <div ref={bottomRef} />
    </div>
  );
}
