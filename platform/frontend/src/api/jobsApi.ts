import { apiClient, unwrap } from '@/lib/apiClient'
import type { JobsResponse, Job, JobFilters } from '@/types'

export const jobsApi = {
  getJobs: (filters: JobFilters = {}) => {
    const params = new URLSearchParams()
    if (filters.search) params.set('search', filters.search)
    if (filters.location) params.set('location', filters.location)
    if (filters.employment_type) params.set('employment_type', filters.employment_type)
    if (filters.skill) params.set('skill', filters.skill)
    params.set('limit', String(filters.limit ?? 20))
    params.set('offset', String(filters.offset ?? 0))
    return unwrap(apiClient.get<{ success: boolean; data: JobsResponse; message: string }>(`/jobs?${params}`))
  },

  getJob: (jobId: string) =>
    unwrap(apiClient.get<{ success: boolean; data: Job; message: string }>(`/jobs/${jobId}`)),
}
