"use client";

import { useEffect, useRef } from "react";
import { AlertCircle, RotateCcw, Send, Square } from "lucide-react";

import { Button } from "@/components/ui/button";

interface ChatInputBoxProps {
  input: string;
  setInput: (value: string) => void;
  onSend: (text: string) => void;
  onStop: () => void;
  onRetry?: () => void;
  isStreaming: boolean;
  error: string | null;
}

export function ChatInputBox({
  input,
  setInput,
  onSend,
  onStop,
  onRetry,
  isStreaming,
  error,
}: ChatInputBoxProps) {
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    if (!isStreaming) {
      textareaRef.current?.focus();
    }
  }, [isStreaming]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (input.trim() && !isStreaming) {
        onSend(input);
      }
    }
  };

  return (
    <div className="p-3 sm:p-4 border-t border-subtle bg-surface/90 backdrop-blur-sm space-y-2">
      {/* Stream Error Alert */}
      {error && (
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
          if (input.trim() && !isStreaming) {
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
          placeholder="Ask a question or follow up on previous turns... (Enter to send, Shift+Enter for new line)"
          aria-label="Chat input message"
          disabled={isStreaming}
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
            disabled={!input.trim()}
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
