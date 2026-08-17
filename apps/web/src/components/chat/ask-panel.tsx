"use client";

import { useState } from "react";
import {
  AlertCircle,
  BookOpen,
  ChevronDown,
  ChevronUp,
  FileText,
  HelpCircle,
  Info,
  Loader2,
  RotateCcw,
  Send,
  Sparkles,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useAskChat } from "@/lib/query/chat";
import type { ChatResponse } from "@/types/chat";

const SUGGESTED_PROMPTS = [
  "What is the P1 incident escalation process?",
  "What are the availability SLA targets for our services?",
  "How do I execute a manual rollback for a service?",
  "What are the rate limit quotas at the API Gateway?",
  "What is the procedure for rotated or leaked credentials?",
];

export function AskPanel() {
  const [question, setQuestion] = useState("");
  const [submittedQuestion, setSubmittedQuestion] = useState("");
  const [response, setResponse] = useState<ChatResponse | null>(null);
  const [expandedCitations, setExpandedCitations] = useState<Record<number, boolean>>({});

  const askMutation = useAskChat();

  const handleSend = async (qToSend?: string) => {
    const targetQ = (qToSend ?? question).trim();
    if (!targetQ) return;

    setSubmittedQuestion(targetQ);
    setQuestion(targetQ);
    setExpandedCitations({});

    try {
      const res = await askMutation.mutateAsync({ question: targetQ });
      setResponse(res);
    } catch {
      // Handled via askMutation.isError
    }
  };

  const toggleCitation = (idx: number) => {
    setExpandedCitations((prev) => ({
      ...prev,
      [idx]: !prev[idx],
    }));
  };

  const handleRetry = () => {
    if (submittedQuestion) {
      handleSend(submittedQuestion);
    }
  };

  return (
    <div className="space-y-6">
      {/* ── Search / Question Input ─────────────────────── */}
      <div className="rounded-xl border border-subtle bg-surface p-4 sm:p-5 shadow-sm space-y-4">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex flex-col gap-3 sm:flex-row sm:items-center"
        >
          <div className="relative flex-1">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask anything about OpsPilot runbooks, SLAs, policies, or troubleshooting..."
              aria-label="Ask a question"
              disabled={askMutation.isPending}
              className="w-full h-11 rounded-lg border border-subtle bg-surface-2/60 px-4 text-xs sm:text-sm text-foreground placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          <Button
            type="submit"
            disabled={!question.trim() || askMutation.isPending}
            className="h-11 px-5 gap-2 bg-accent text-accent-foreground hover:bg-accent-hover text-xs font-semibold shrink-0"
          >
            {askMutation.isPending ? (
              <>
                <Loader2 className="size-4 animate-spin" />
                Searching KB...
              </>
            ) : (
              <>
                <Sparkles className="size-4" />
                Ask OpsPilot
              </>
            )}
          </Button>
        </form>

        {/* Suggestion Chips */}
        <div className="flex flex-wrap items-center gap-1.5 pt-1">
          <span className="text-[11px] font-medium text-faint flex items-center gap-1 mr-1">
            <HelpCircle className="size-3" />
            Suggestions:
          </span>
          {SUGGESTED_PROMPTS.map((promptText) => (
            <button
              key={promptText}
              type="button"
              onClick={() => handleSend(promptText)}
              disabled={askMutation.isPending}
              className="rounded-md border border-subtle/80 bg-surface-2/40 px-2.5 py-1 text-[11px] text-muted hover:border-accent/40 hover:text-foreground hover:bg-surface-2 transition-colors cursor-pointer text-left"
            >
              {promptText}
            </button>
          ))}
        </div>
      </div>

      {/* ── Dynamic State Rendering ─────────────────────── */}

      {/* 1. Loading State */}
      {askMutation.isPending && (
        <div className="rounded-xl border border-subtle bg-surface p-6 space-y-4 animate-pulse">
          <div className="flex items-center gap-2 text-xs font-medium text-accent">
            <Loader2 className="size-4 animate-spin" />
            <span>Consulting OpsPilot Knowledge Base & Grounded Citations...</span>
          </div>
          <div className="space-y-2 pt-2">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-5/6" />
            <Skeleton className="h-4 w-4/6" />
          </div>
          <div className="pt-4 border-t border-subtle/50 space-y-2">
            <Skeleton className="h-3 w-32" />
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Skeleton className="h-16 w-full rounded-lg" />
              <Skeleton className="h-16 w-full rounded-lg" />
            </div>
          </div>
        </div>
      )}

      {/* 2. Error State */}
      {askMutation.isError && !askMutation.isPending && (
        <div className="flex min-h-[220px] flex-col items-center justify-center rounded-xl border border-destructive/30 bg-destructive/5 p-6 text-center">
          <div className="flex size-10 items-center justify-center rounded-full bg-destructive/10 text-destructive mb-2.5">
            <AlertCircle className="size-5" />
          </div>
          <h3 className="text-sm font-semibold text-foreground">
            Query Failed
          </h3>
          <p className="mt-1 max-w-sm text-xs text-muted">
            {askMutation.error?.response?.data?.detail ||
              askMutation.error?.message ||
              "Unable to complete knowledge base query."}
          </p>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRetry}
            className="mt-4 gap-1.5 border-subtle text-xs"
          >
            <RotateCcw className="size-3.5" />
            Retry
          </Button>
        </div>
      )}

      {/* 3. Empty / Initial State */}
      {!response && !askMutation.isPending && !askMutation.isError && (
        <div className="flex min-h-[240px] flex-col items-center justify-center rounded-xl border border-dashed border-subtle bg-surface/40 p-8 text-center">
          <div className="flex size-12 items-center justify-center rounded-full bg-surface-2 text-accent mb-3">
            <BookOpen className="size-6" />
          </div>
          <h3 className="text-sm font-semibold text-foreground">
            Grounded Operational Q&A
          </h3>
          <p className="mt-1 max-w-md text-xs text-muted leading-relaxed">
            OpsPilot queries 14 ingested operational runbooks, escalation policies, SLA contracts, and recovery procedures with vector embeddings. Answers are strictly grounded in documented facts.
          </p>
        </div>
      )}

      {/* 4. Success Response */}
      {response && !askMutation.isPending && (
        <div className="rounded-xl border border-subtle bg-surface p-6 space-y-6 shadow-sm">
          {/* Question Recap */}
          <div className="flex items-start justify-between gap-3 border-b border-subtle/50 pb-4">
            <div>
              <span className="text-[10px] uppercase font-semibold tracking-wider text-faint">
                Question
              </span>
              <h2 className="text-sm sm:text-base font-semibold text-foreground mt-0.5">
                {submittedQuestion}
              </h2>
            </div>
            {response.used_context ? (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-medium text-emerald-400 border border-emerald-500/20 shrink-0">
                <span className="size-1.5 rounded-full bg-emerald-400" />
                Grounded ({response.citations.length} sources)
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-500/10 px-2.5 py-0.5 text-xs font-medium text-amber-400 border border-amber-500/20 shrink-0">
                <span className="size-1.5 rounded-full bg-amber-400" />
                Out of Knowledge Base
              </span>
            )}
          </div>

          {/* Decline / Insufficient Context Notice */}
          {!response.used_context && (
            <div className="flex items-start gap-3 rounded-lg border border-amber-500/20 bg-amber-500/5 p-3.5 text-xs text-muted">
              <Info className="size-4 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-amber-300 block mb-0.5">
                  Knowledge Base Boundary Guardrail
                </span>
                The query asks for information not present in the ingested OpsPilot operational documentation. To prevent hallucinations, the model declined to answer.
              </div>
            </div>
          )}

          {/* Synthesized Answer */}
          <div className="space-y-2">
            <span className="text-[10px] uppercase font-semibold tracking-wider text-faint">
              Answer
            </span>
            <div className="text-xs sm:text-sm text-foreground leading-relaxed whitespace-pre-wrap rounded-lg bg-surface-2/40 p-4 border border-subtle/50">
              {response.answer}
            </div>
          </div>

          {/* Citations Section */}
          {response.citations.length > 0 && (
            <div className="space-y-3 pt-2 border-t border-subtle/50">
              <div className="flex items-center gap-2">
                <FileText className="size-4 text-accent" />
                <h3 className="text-xs font-semibold uppercase tracking-wider text-foreground">
                  Grounded Citations ({response.citations.length})
                </h3>
              </div>

              <div className="grid grid-cols-1 gap-2.5">
                {response.citations.map((citation, idx) => {
                  const isExpanded = Boolean(expandedCitations[idx]);
                  const scorePct = Math.round(citation.score * 100);

                  return (
                    <div
                      key={`${citation.document_title}-${citation.ordinal}`}
                      className="rounded-lg border border-subtle bg-surface-2/30 p-3 text-xs transition-colors hover:border-subtle"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <div className="flex items-center gap-2 min-w-0">
                          <span className="font-semibold text-foreground truncate">
                            {citation.document_title}
                          </span>
                          <span className="rounded bg-surface-2 px-1.5 py-0.5 text-[10px] text-faint border border-subtle">
                            Section {citation.ordinal}
                          </span>
                        </div>

                        <div className="flex items-center gap-2 shrink-0">
                          <span className="rounded-full bg-accent/10 px-2 py-0.5 text-[10px] font-medium text-accent border border-accent/20">
                            {scorePct}% match
                          </span>
                          <button
                            type="button"
                            onClick={() => toggleCitation(idx)}
                            aria-label="Toggle citation snippet"
                            className="text-muted hover:text-foreground p-0.5"
                          >
                            {isExpanded ? (
                              <ChevronUp className="size-3.5" />
                            ) : (
                              <ChevronDown className="size-3.5" />
                            )}
                          </button>
                        </div>
                      </div>

                      {/* Snippet Preview */}
                      <p className="mt-2 text-[11px] text-muted line-clamp-2 leading-relaxed">
                        {citation.snippet}
                      </p>

                      {/* Expanded View */}
                      {isExpanded && (
                        <div className="mt-2 rounded border border-subtle/60 bg-surface-2/60 p-2.5 text-[11px] text-foreground font-mono leading-relaxed whitespace-pre-wrap">
                          {citation.snippet}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
