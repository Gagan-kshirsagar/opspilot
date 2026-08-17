/**
 * Typed API functions for services domain.
 */

import { apiClient } from "@/lib/api/client";
import type {
  ServiceDetail,
  ServiceItem,
  ServiceListParams,
} from "@/types/service";

/**
 * Fetch all services with optional filters and sorting.
 */
export async function fetchServices(
  params?: ServiceListParams
): Promise<ServiceItem[]> {
  const { data } = await apiClient.get<ServiceItem[]>("/api/v1/services", {
    params: {
      search: params?.search || undefined,
      status: params?.status,
      sort_by: params?.sort_by,
      sort_dir: params?.sort_dir,
    },
  });
  return data;
}

/**
 * Fetch a single service by ID.
 */
export async function fetchService(id: string): Promise<ServiceDetail> {
  const { data } = await apiClient.get<ServiceDetail>(
    `/api/v1/services/${id}`
  );
  return data;
}
