import { apiClient, unwrap } from '@/lib/apiClient'
import type { MarketInsights } from '@/types'

export const marketApi = {
  getInsights: () =>
    unwrap(apiClient.get<{ success: boolean; data: MarketInsights; message: string }>('/market/insights')),
}
