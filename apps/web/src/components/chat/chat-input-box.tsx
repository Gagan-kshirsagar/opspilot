"use client";

import { useEffect, useRef, useState } from "react";
import { AlertCircle, Clock, Info, RotateCcw, Send, Sparkles, Square } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { LimitInfo } from "@/hooks/useChatStream";

interface ChatInputBoxProps {
  input: string;
  setInput: (value: string) => void;
  onSend: (text: string) => void;
  onStop: () => void;
  onRetry?: () => void;
  isStreaming: boolean;
  error: string | null;
  limitInfo?: LimitInfo | null;
}

export function ChatInputBox({
  input,
  setInput,
  onSend,
  onStop,
  onRetry,
  isStreaming,
  error,
  limitInfo,
}: ChatInputBoxProps) {
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const [countdown, setCountdown] = useState(0);

  useEffect(() => {
    if (limitInfo?.type === "rate_limit" && limitInfo.retryAfter > 0) {
      setCountdown(limitInfo.retryAfter);
    } else {
      setCountdown(0);
    }
  }, [limitInfo]);

  useEffect(() => {
    if (countdown <= 0) return;
    const timer = setInterval(() => {
      setCountdown((prev) => (prev <= 1 ? 0 : prev - 1));
    }, 1000);
    return () => clearInterval(timer);
  }, [countdown]);

  const isRateLimited = countdown > 0;
  const isDailyLimited = limitInfo?.type === "daily_limit";

  useEffect(() => {
    if (!isStreaming && !isRateLimited && !isDailyLimited) {
      textareaRef.current?.focus();
    }
  }, [isStreaming, isRateLimited, isDailyLimited]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (input.trim() && !isStreaming && !isRateLimited && !isDailyLimited) {
        onSend(input);
      }
    }
  };

  return (
    <div className="p-3 sm:p-4 border-t border-subtle bg-surface/90 backdrop-blur-sm space-y-2">
      {/* Rate Limit Countdown Banner */}
      {isRateLimited && (
        <div className="flex items-center justify-between gap-2 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-500 animate-fade-in">
          <div className="flex items-center gap-1.5 min-w-0">
            <Clock className="size-3.5 shrink-0" />
            <span className="font-medium">
              Rate limit reached (10 msg / 10 min). Unlocking in {countdown}s...
            </span>
          </div>
        </div>
      )}

      {/* Daily Demo Budget Reached Banner */}
      {isDailyLimited && (
        <div className="flex items-center justify-between gap-2 rounded-lg border border-blue-500/30 bg-blue-500/10 px-3 py-2 text-xs text-blue-400 animate-fade-in">
          <div className="flex items-center gap-1.5 min-w-0">
            <Sparkles className="size-3.5 shrink-0" />
            <span>
              Daily demo limit reached. Resets at 00:00 UTC. Live service dashboards remain fully accessible.
            </span>
          </div>
        </div>
      )}

      {/* Generic Stream Error Alert (when not rate/daily limited) */}
      {error && !isRateLimited && !isDailyLimited && (
        <div className="flex items-center justify-between gap-2 rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-xs text-destructive">
          <div className="flex items-center gap-1.5 min-w-0">
            <AlertCircle className="size-3.5 shrink-0" />
            <span className="truncate">{error}</span>
          </div>
          {onRetry && (
            <Button
              variant="outline"
              size="sm"
              onClick={onRetry}
              className="h-6 px-2 text-[11px] gap-1 border-destructive/40 text-destructive hover:bg-destructive/10"
            >
              <RotateCcw className="size-3" />
              Retry
            </Button>
          )}
        </div>
      )}

      {/* Input Box */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (input.trim() && !isStreaming && !isRateLimited && !isDailyLimited) {
            onSend(input);
          }
        }}
        className="relative flex items-end gap-2 rounded-xl border border-subtle bg-surface-2/60 p-2 shadow-inner focus-within:border-accent/50 focus-within:ring-1 focus-within:ring-accent/50"
      >
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            isRateLimited
              ? `Rate limited — please wait ${countdown}s...`
              : isDailyLimited
              ? "Daily demo limit reached — resets at 00:00 UTC"
              : "Ask a question or follow up on previous turns... (Enter to send, Shift+Enter for new line)"
          }
          aria-label="Chat input message"
          disabled={isStreaming || isRateLimited || isDailyLimited}
          rows={1}
          className="flex-1 max-h-32 min-h-[40px] resize-none bg-transparent px-2.5 py-2 text-xs sm:text-sm text-foreground placeholder:text-muted focus:outline-none disabled:opacity-60"
        />

        {isStreaming ? (
          <Button
            type="button"
            onClick={onStop}
            className="size-9 p-0 rounded-lg bg-destructive/10 text-destructive hover:bg-destructive/20 border border-destructive/20 shrink-0"
            aria-label="Stop streaming response"
          >
            <Square className="size-4 fill-current" />
          </Button>
        ) : (
          <Button
            type="submit"
            disabled={!input.trim() || isRateLimited || isDailyLimited}
            className="size-9 p-0 rounded-lg bg-accent text-accent-foreground hover:bg-accent-hover shrink-0 disabled:opacity-40"
            aria-label="Send question"
          >
            <Send className="size-4" />
          </Button>
        )}
      </form>
    </div>
  );
}
