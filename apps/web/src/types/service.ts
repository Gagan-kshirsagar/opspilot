/**
 * Service management types — mirrors backend Pydantic schemas.
 */

export type ServiceStatus = "healthy" | "degraded" | "down";

export type ServiceSortByField = "name" | "status" | "uptime_pct" | "created_at";

export type SortDirection = "asc" | "desc";

export interface ServiceListParams {
  search?: string;
  status?: ServiceStatus[];
  sort_by?: ServiceSortByField;
  sort_dir?: SortDirection;
}

export interface ServiceItem {
  id: string;
  name: string;
  status: ServiceStatus;
  uptime_pct: number;
  owner_user_id: string;
  owner_name: string;
  note: string | null;
  created_at: string;
  updated_at: string;
}

export interface ServiceDetail extends ServiceItem {
  open_incident_count: number;
}
