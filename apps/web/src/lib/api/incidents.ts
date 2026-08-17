/**
 * Typed API functions for incidents domain.
 */

import { apiClient } from "@/lib/api/client";
import type {
  IncidentItem,
  IncidentListParams,
  PaginatedIncidentsResponse,
} from "@/types/incident";

/**
 * Fetch paginated incidents with optional filters and sorting.
 */
export async function fetchIncidents(
  params: IncidentListParams
): Promise<PaginatedIncidentsResponse> {
  const { data } = await apiClient.get<PaginatedIncidentsResponse>(
    "/api/v1/incidents",
    {
      params: {
        page: params.page,
        page_size: params.page_size,
        sort_by: params.sort_by,
        sort_dir: params.sort_dir,
        search: params.search || undefined,
        status: params.status,
        severity: params.severity,
        service_id: params.service_id || undefined,
      },
    }
  );
  return data;
}

/**
 * Fetch a single incident by ID.
 */
export async function fetchIncident(id: string): Promise<IncidentItem> {
  const { data } = await apiClient.get<IncidentItem>(`/api/v1/incidents/${id}`);
  return data;
}

/**
 * Resolve an incident (Admin or Manager).
 */
export async function resolveIncident(id: string): Promise<IncidentItem> {
  const { data } = await apiClient.post<IncidentItem>(
    `/api/v1/incidents/${id}/resolve`
  );
  return data;
}
