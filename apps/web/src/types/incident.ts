/**
 * Incident management types — mirrors backend Pydantic schemas.
 */

export type IncidentSeverity = "sev1" | "sev2" | "sev3";

export type IncidentStatus = "open" | "investigating" | "resolved";

export type IncidentSortByField =
  | "title"
  | "severity"
  | "status"
  | "service_name"
  | "created_at";

export type SortDirection = "asc" | "desc";

export interface IncidentListParams {
  page?: number;
  page_size?: number;
  sort_by?: IncidentSortByField;
  sort_dir?: SortDirection;
  search?: string;
  status?: IncidentStatus[];
  severity?: IncidentSeverity[];
  service_id?: string;
}

export interface IncidentItem {
  id: string;
  title: string;
  severity: IncidentSeverity;
  status: IncidentStatus;
  service_id: string;
  service_name: string;
  assignee_id: string | null;
  assignee_name: string | null;
  resolved_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface PaginatedIncidentsResponse {
  items: IncidentItem[];
  total: number;
  page: number;
  page_size: number;
}
