"use client";

import { AlertCircle, RotateCcw, Server } from "lucide-react";

import { ServiceCard } from "@/components/services/service-card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import type { ServiceItem } from "@/types/service";

interface ServicesListProps {
  services: ServiceItem[];
  isLoading: boolean;
  isError: boolean;
  error?: Error | null;
  onRetry: () => void;
  onResetFilters: () => void;
  hasActiveFilters: boolean;
}

export function ServicesList({
  services,
  isLoading,
  isError,
  error,
  onRetry,
  onResetFilters,
  hasActiveFilters,
}: ServicesListProps) {
  // 1. Loading State
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <div
            key={`skel-${i}`}
            className="flex flex-col justify-between rounded-xl border border-subtle bg-surface p-5 space-y-4"
          >
            <div className="space-y-2.5">
              <div className="flex items-center justify-between">
                <Skeleton className="h-5 w-32" />
                <Skeleton className="h-5 w-16 rounded-full" />
              </div>
              <Skeleton className="h-3.5 w-full" />
              <Skeleton className="h-3.5 w-3/4" />
            </div>
            <div className="grid grid-cols-2 gap-3 border-t border-subtle/50 pt-3">
              <Skeleton className="h-8 w-20" />
              <Skeleton className="h-8 w-20" />
            </div>
            <div className="border-t border-subtle/50 pt-3 flex justify-between">
              <Skeleton className="h-3 w-24" />
              <Skeleton className="h-3 w-16" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  // 2. Error State
  if (isError) {
    return (
      <div className="flex min-h-[280px] flex-col items-center justify-center rounded-xl border border-destructive/30 bg-destructive/5 p-8 text-center">
        <div className="flex size-12 items-center justify-center rounded-full bg-destructive/10 text-destructive mb-3">
          <AlertCircle className="size-6" />
        </div>
        <h3 className="text-sm font-semibold text-foreground">
          Failed to load services
        </h3>
        <p className="mt-1 max-w-sm text-xs text-muted">
          {error?.message || "An unexpected error occurred while fetching services."}
        </p>
        <Button
          variant="outline"
          size="sm"
          onClick={onRetry}
          className="mt-4 gap-1.5 border-subtle text-xs"
        >
          <RotateCcw className="size-3.5" />
          Retry
        </Button>
      </div>
    );
  }

  // 3. Empty State
  if (services.length === 0) {
    return (
      <div className="flex min-h-[280px] flex-col items-center justify-center rounded-xl border border-dashed border-subtle bg-surface/50 p-8 text-center">
        <div className="flex size-12 items-center justify-center rounded-full bg-surface-2 text-muted mb-3">
          <Server className="size-6" />
        </div>
        <h3 className="text-sm font-semibold text-foreground">
          No services found
        </h3>
        <p className="mt-1 max-w-sm text-xs text-muted">
          {hasActiveFilters
            ? "No services match your active filter criteria."
            : "No registered services available in this environment."}
        </p>
        {hasActiveFilters && (
          <Button
            variant="outline"
            size="sm"
            onClick={onResetFilters}
            className="mt-4 text-xs border-subtle"
          >
            Clear filters
          </Button>
        )}
      </div>
    );
  }

  // 4. Success Grid
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {services.map((service) => (
        <ServiceCard key={service.id} service={service} />
      ))}
    </div>
  );
}
