/**
 * TanStack Query hooks for services domain.
 */

import { keepPreviousData, useQuery } from "@tanstack/react-query";

import { fetchService, fetchServices } from "@/lib/api/services";
import { queryKeys } from "@/lib/query/keys";
import type {
  ServiceDetail,
  ServiceItem,
  ServiceListParams,
} from "@/types/service";

/**
 * Hook to fetch services list with optional search, status filtering, and sorting.
 */
export function useServices(params?: ServiceListParams) {
  return useQuery<ServiceItem[]>({
    queryKey: queryKeys.services.list(params),
    queryFn: () => fetchServices(params),
    placeholderData: keepPreviousData,
  });
}

/**
 * Hook to fetch single service details.
 */
export function useService(id: string | null) {
  return useQuery<ServiceDetail>({
    queryKey: queryKeys.services.detail(id ?? ""),
    queryFn: () => fetchService(id!),
    enabled: id !== null && id.length > 0,
  });
}
