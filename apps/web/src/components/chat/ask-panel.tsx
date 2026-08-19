"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Bot, MessageSquarePlus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { ChatInputBox } from "@/components/chat/chat-input-box";
import { ChatMessageList } from "@/components/chat/chat-message-list";
import { ChatSidebar } from "@/components/chat/chat-sidebar";
import { useChatStream } from "@/hooks/useChatStream";
import { useChatSessionDetail } from "@/lib/query/chat";

export function AskPanel() {
  const searchParams = useSearchParams();
  const initialQuery = searchParams ? searchParams.get("q") : null;
  const hasAutoSentRef = useRef(false);

  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [lastSentQuestion, setLastSentQuestion] = useState("");

  const {
    isStreaming,
    streamingUserMessage,
    streamingSteps,
    streamingContent,
    streamingCitations,
    streamingUsedContext,
    error,
    limitInfo,
    sendMessage,
    stop,
    reset,
  } = useChatStream({
    onDone: (newSessionId) => {
      setActiveSessionId(newSessionId);
    },
  });

  const { data: sessionDetail, isLoading: isLoadingSession } =
    useChatSessionDetail(activeSessionId);

  const handleSend = useCallback(
    (textToSend: string) => {
      const q = textToSend.trim();
      if (!q) return;

      setLastSentQuestion(q);
      setInput("");
      sendMessage(q, activeSessionId);
    },
    [activeSessionId, sendMessage]
  );

  useEffect(() => {
    if (initialQuery && !hasAutoSentRef.current && !activeSessionId) {
      hasAutoSentRef.current = true;
      handleSend(initialQuery);
    }
  }, [initialQuery, activeSessionId, handleSend]);

  const handleNewChat = () => {
    reset();
    setActiveSessionId(null);
    setInput("");
    setLastSentQuestion("");
  };

  const handleSelectSession = (sessionId: string) => {
    reset();
    setActiveSessionId(sessionId);
    setInput("");
    setLastSentQuestion("");
  };

  const handleRetry = () => {
    if (lastSentQuestion) {
      sendMessage(lastSentQuestion, activeSessionId);
    }
  };

  return (
    <div className="flex flex-col lg:flex-row gap-6 items-stretch">
      {/* Sessions History Sidebar */}
      <ChatSidebar
        activeSessionId={activeSessionId}
        onSelectSession={handleSelectSession}
        onNewChat={handleNewChat}
        isStreaming={isStreaming}
      />

      {/* Main Multi-Turn Chat Conversation Area */}
      <main className="flex-1 flex flex-col rounded-xl border border-subtle bg-surface shadow-sm overflow-hidden h-[540px] sm:h-[620px]">
        {/* Chat Thread Header */}
        <div className="px-4 py-3 border-b border-subtle/60 flex items-center justify-between gap-3 bg-surface-2/30">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="size-7 rounded-lg bg-accent/10 border border-accent/20 flex items-center justify-center text-accent shrink-0">
              <Bot className="size-4" />
            </div>
            <div className="min-w-0">
              <h2 className="text-xs sm:text-sm font-semibold text-foreground truncate">
                {sessionDetail?.title || "New Operational Chat"}
              </h2>
              <span className="text-[10px] text-faint flex items-center gap-1">
                <span className="size-1.5 rounded-full bg-emerald-400" />
                LangGraph ReAct Agent (Live DB + KB)
              </span>
            </div>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={handleNewChat}
            disabled={isStreaming}
            className="h-7 px-2.5 text-xs gap-1.5 border-subtle text-muted hover:text-foreground hidden sm:flex"
          >
            <MessageSquarePlus className="size-3.5" />
            New
          </Button>
        </div>

        {/* Message List Area */}
        <ChatMessageList
          messages={sessionDetail?.messages || []}
          streamingUserMessage={streamingUserMessage}
          streamingSteps={streamingSteps}
          streamingContent={streamingContent}
          streamingCitations={streamingCitations}
          streamingUsedContext={streamingUsedContext}
          isStreaming={isStreaming}
          isLoadingSession={Boolean(activeSessionId && isLoadingSession)}
          onSelectPrompt={(prompt) => handleSend(prompt)}
        />

        {/* Chat Input Box */}
        <ChatInputBox
          input={input}
          setInput={setInput}
          onSend={handleSend}
          onStop={stop}
          onRetry={handleRetry}
          isStreaming={isStreaming}
          error={error}
          limitInfo={limitInfo}
        />
      </main>
    </div>
  );
}
