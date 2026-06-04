import { apiClient, unwrap } from '@/lib/apiClient'
import type { DashboardStats } from '@/types'

export const dashboardApi = {
  getStats: () =>
    unwrap(apiClient.get<{ success: boolean; data: DashboardStats; message: string }>('/dashboard')),
}
