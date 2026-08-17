"use client";

import { useState } from "react";
import {
  AlertTriangle,
  BookOpen,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Cpu,
  Layers,
  Loader2,
  Server,
  Users,
} from "lucide-react";

import type { AgentStep } from "@/types/chat";

interface AgentThoughtTrailProps {
  steps: AgentStep[];
  isStreaming?: boolean;
}

function getToolIcon(tool: string) {
  switch (tool) {
    case "retrieve_docs":
      return <BookOpen className="size-3.5 text-blue-400" />;
    case "query_services":
      return <Server className="size-3.5 text-emerald-400" />;
    case "query_incidents":
      return <AlertTriangle className="size-3.5 text-amber-400" />;
    case "query_users":
      return <Users className="size-3.5 text-purple-400" />;
    case "get_service_detail":
      return <Layers className="size-3.5 text-cyan-400" />;
    default:
      return <Cpu className="size-3.5 text-accent" />;
  }
}

function formatToolTitle(step: AgentStep): string {
  const { tool, type, args, summary } = step;
  if (type === "tool_call") {
    switch (tool) {
      case "retrieve_docs":
        return `Searching runbooks for "${args?.query ?? ""}"`;
      case "query_services":
        return args?.status
          ? `Checking services with status '${args.status}'`
          : "Querying live services catalog";
      case "query_incidents":
        return args?.severity
          ? `Querying ${String(args.severity).toUpperCase()} incidents`
          : "Checking active incident records";
      case "query_users":
        return args?.role
          ? `Looking up ${args.role} users`
          : "Looking up team and user accounts";
      case "get_service_detail":
        return `Looking up service '${args?.name_or_id ?? ""}'`;
      default:
        return `Executing ${tool}`;
    }
  } else {
    return summary || `Completed ${tool}`;
  }
}

export function AgentThoughtTrail({
  steps,
  isStreaming = false,
}: AgentThoughtTrailProps) {
  const [isExpanded, setIsExpanded] = useState<boolean>(true);

  if (!steps || steps.length === 0) return null;

  return (
    <div className="rounded-xl border border-subtle/70 bg-surface/80 text-xs overflow-hidden shadow-xs">
      {/* Collapsible Header */}
      <button
        type="button"
        onClick={() => setIsExpanded((prev) => !prev)}
        className="w-full flex items-center justify-between gap-2 px-3 py-2 bg-surface-2/40 hover:bg-surface-2/70 transition-colors text-left cursor-pointer"
        aria-expanded={isExpanded}
        aria-label="Toggle agent reasoning steps"
      >
        <div className="flex items-center gap-2">
          <Cpu className="size-3.5 text-accent animate-pulse" />
          <span className="font-medium text-foreground text-[11px] tracking-wide uppercase">
            {isStreaming ? "Agent Reasoning..." : "Reasoning Steps"} ({steps.length})
          </span>
        </div>

        <div className="flex items-center gap-1 text-muted">
          {isStreaming && (
            <Loader2 className="size-3 animate-spin text-accent" />
          )}
          {isExpanded ? (
            <ChevronUp className="size-3.5" />
          ) : (
            <ChevronDown className="size-3.5" />
          )}
        </div>
      </button>

      {/* Steps List */}
      {isExpanded && (
        <div className="p-2.5 space-y-1.5 border-t border-subtle/50 font-mono text-[11px]">
          {steps.map((step, idx) => {
            const isCall = step.type === "tool_call";
            const isLast = idx === steps.length - 1;

            return (
              <div
                key={`step-${idx}`}
                className="flex items-start gap-2 rounded-lg p-1.5 bg-surface-2/30"
              >
                <div className="shrink-0 mt-0.5">
                  {getToolIcon(step.tool)}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-medium text-foreground truncate">
                      {formatToolTitle(step)}
                    </span>
                    {isCall ? (
                      isLast && isStreaming ? (
                        <Loader2 className="size-3 animate-spin text-accent shrink-0" />
                      ) : (
                        <span className="text-[10px] text-faint shrink-0">call</span>
                      )
                    ) : (
                      <CheckCircle2 className="size-3 text-emerald-400 shrink-0" />
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
