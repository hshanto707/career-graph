import { apiClient, unwrap } from '@/lib/apiClient'
import type { GapAnalysisRequest, GapAnalysisResult } from '@/types'

export const gapApi = {
  analyzeGap: (data: GapAnalysisRequest) =>
    unwrap(apiClient.post<{ success: boolean; data: GapAnalysisResult; message: string }>('/gap-analysis', data)),
}
