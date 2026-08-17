/**
 * TanStack Query hooks for incidents domain.
 */

import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import type { AxiosError } from "axios";

import {
  fetchIncident,
  fetchIncidents,
  resolveIncident,
} from "@/lib/api/incidents";
import type { ErrorResponse } from "@/lib/auth/types";
import { queryKeys } from "@/lib/query/keys";
import type {
  IncidentItem,
  IncidentListParams,
  PaginatedIncidentsResponse,
} from "@/types/incident";

/**
 * Hook to fetch paginated incidents.
 */
export function useIncidents(params: IncidentListParams) {
  return useQuery<PaginatedIncidentsResponse>({
    queryKey: queryKeys.incidents.list(params),
    queryFn: () => fetchIncidents(params),
    placeholderData: keepPreviousData,
  });
}

/**
 * Hook to fetch single incident details.
 */
export function useIncident(id: string | null) {
  return useQuery<IncidentItem>({
    queryKey: queryKeys.incidents.detail(id ?? ""),
    queryFn: () => fetchIncident(id!),
    enabled: id !== null && id.length > 0,
  });
}

/**
 * Hook to resolve an incident.
 * Invalidates incidents list, detail, and services on success.
 */
export function useResolveIncident() {
  const qc = useQueryClient();

  return useMutation<IncidentItem, AxiosError<ErrorResponse>, string>({
    mutationFn: (id: string) => resolveIncident(id),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: queryKeys.incidents.all });
      qc.invalidateQueries({ queryKey: queryKeys.services.all });
      if (data.id) {
        qc.invalidateQueries({ queryKey: queryKeys.incidents.detail(data.id) });
      }
    },
  });
}
