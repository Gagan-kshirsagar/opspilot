"use client";

import { Suspense } from "react";
import { Bot } from "lucide-react";

import { AskPanel } from "@/components/chat/ask-panel";

export default function ChatPage() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 space-y-6 animate-slide-up">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Bot className="size-5 text-accent" />
            <h1 className="text-xl font-bold tracking-tight text-foreground sm:text-2xl">
              Ask OpsPilot
            </h1>
          </div>
          <p className="mt-1 text-xs text-muted">
            Grounded operational intelligence synthesized directly from verified runbooks and policies.
          </p>
        </div>
      </div>

      {/* Main Q&A Panel */}
      <Suspense fallback={<div className="h-[600px] animate-pulse rounded-xl border border-subtle bg-surface/50" />}>
        <AskPanel />
      </Suspense>
    </div>
  );
}
