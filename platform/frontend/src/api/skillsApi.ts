import { apiClient, unwrap } from '@/lib/apiClient'
import type { MarketSkillsResponse, SkillGapResponse } from '@/types'

export const skillsApi = {
  getMarketSkills: () =>
    unwrap(apiClient.get<{ success: boolean; data: MarketSkillsResponse; message: string }>('/skills/market')),

  getSkillGap: (targetJobId: string) =>
    unwrap(apiClient.get<{ success: boolean; data: SkillGapResponse; message: string }>(`/skills/gap?target_job_id=${targetJobId}`)),
}
