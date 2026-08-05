import { apiClient } from "@/lib/apiClient";

export interface JobOut {
  id: string;
  title: string | null;
  company: string | null;
  location: string | null;
  type: string | null;
  source: string | null;
  salary_min: number | null;
  salary_max: number | null;
}

/** GET /jobs/{id} only -- adds the job's required skills (plain factual
 * REQUIRES-edge data, not a personalized score). Not present on `JobOut`
 * from the list/catalog endpoint. */
export interface JobDetailOut extends JobOut {
  required_skills: string[];
}

export interface JobFilters {
  type?: string;
  location?: string;
  search?: string;
  limit?: number;
  offset?: number;
}

function toQueryString(filters: JobFilters): string {
  const params = new URLSearchParams();
  if (filters.type) params.set("type", filters.type);
  if (filters.location) params.set("location", filters.location);
  if (filters.search) params.set("search", filters.search);
  if (filters.limit !== undefined) params.set("limit", String(filters.limit));
  if (filters.offset !== undefined) params.set("offset", String(filters.offset));
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

export const jobsApi = {
  list: (filters: JobFilters = {}) => apiClient.get<JobOut[]>(`/jobs${toQueryString(filters)}`),
  get: (jobId: string) => apiClient.get<JobDetailOut>(`/jobs/${jobId}`),
  /** GET /jobs/titles?search= — distinct job-title suggestions, used by the
   * target-role Combobox on Edit Profile. */
  titles: (query?: string, limit = 20) => {
    const params = new URLSearchParams();
    if (query) params.set("search", query);
    params.set("limit", String(limit));
    return apiClient.get<string[]>(`/jobs/titles?${params.toString()}`);
  },
};
