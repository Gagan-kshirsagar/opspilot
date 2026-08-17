"use client";

import { useState } from "react";
import {
  MessageSquare,
  Plus,
  Trash2,
  Loader2,
  Clock,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useChatSessions, useDeleteChatSession } from "@/lib/query/chat";
import { formatRelativeTime } from "@/lib/utils/format";
import type { ChatSession } from "@/types/chat";

interface ChatSidebarProps {
  activeSessionId: string | null;
  onSelectSession: (sessionId: string) => void;
  onNewChat: () => void;
  isStreaming: boolean;
}

export function ChatSidebar({
  activeSessionId,
  onSelectSession,
  onNewChat,
  isStreaming,
}: ChatSidebarProps) {
  const { data: sessions, isLoading, isError } = useChatSessions();
  const deleteMutation = useDeleteChatSession();
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleDelete = async (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    if (confirm("Are you sure you want to delete this conversation?")) {
      setDeletingId(sessionId);
      try {
        await deleteMutation.mutateAsync(sessionId);
        if (activeSessionId === sessionId) {
          onNewChat();
        }
      } finally {
        setDeletingId(null);
      }
    }
  };

  return (
    <aside className="w-full lg:w-72 shrink-0 flex flex-col rounded-xl border border-subtle bg-surface shadow-sm overflow-hidden h-[540px] sm:h-[620px]">
      {/* Top Header & New Chat Button */}
      <div className="p-3.5 border-b border-subtle/60 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <MessageSquare className="size-4 text-accent" />
          <span className="text-xs font-semibold uppercase tracking-wider text-foreground">
            Conversations
          </span>
        </div>
        <Button
          size="sm"
          onClick={onNewChat}
          disabled={isStreaming}
          className="h-8 gap-1.5 px-3 bg-accent text-accent-foreground hover:bg-accent-hover text-xs font-medium"
        >
          <Plus className="size-3.5" />
          New Chat
        </Button>
      </div>

      {/* Sessions List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {isLoading && (
          <div className="space-y-2 p-2">
            <Skeleton className="h-10 w-full rounded-lg" />
            <Skeleton className="h-10 w-full rounded-lg" />
            <Skeleton className="h-10 w-full rounded-lg" />
          </div>
        )}

        {isError && (
          <div className="p-4 text-center text-xs text-muted">
            Failed to load past chats.
          </div>
        )}

        {!isLoading && !isError && (!sessions || sessions.length === 0) && (
          <div className="p-6 text-center text-xs text-muted flex flex-col items-center justify-center h-full">
            <Clock className="size-5 text-faint mb-2" />
            <p>No chat history yet.</p>
            <p className="text-[11px] text-faint mt-0.5">
              Start a new conversation to ask OpsPilot.
            </p>
          </div>
        )}

        {sessions?.map((session: ChatSession) => {
          const isActive = session.id === activeSessionId;
          const isDeleting = deletingId === session.id;

          return (
            <div
              key={session.id}
              onClick={() => {
                if (!isStreaming) {
                  onSelectSession(session.id);
                }
              }}
              className={`group flex items-center justify-between gap-2 rounded-lg px-3 py-2.5 text-xs transition-colors cursor-pointer ${
                isActive
                  ? "bg-accent/10 text-foreground border border-accent/30 font-medium"
                  : "text-muted hover:text-foreground hover:bg-surface-2/60 border border-transparent"
              } ${isStreaming ? "opacity-60 pointer-events-none" : ""}`}
            >
              <div className="min-w-0 flex-1">
                <p className="truncate text-xs">{session.title}</p>
                <span className="text-[10px] text-faint block mt-0.5">
                  {formatRelativeTime(session.updated_at)}
                </span>
              </div>

              <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  type="button"
                  onClick={(e) => handleDelete(e, session.id)}
                  disabled={isDeleting}
                  aria-label="Delete chat session"
                  className="rounded p-1 text-faint hover:text-destructive hover:bg-surface-2 transition-colors cursor-pointer"
                >
                  {isDeleting ? (
                    <Loader2 className="size-3.5 animate-spin" />
                  ) : (
                    <Trash2 className="size-3.5" />
                  )}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </aside>
  );
}
