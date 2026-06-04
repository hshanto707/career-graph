import { apiClient, unwrap } from '@/lib/apiClient'
import type { JobRecommendation, RecommendedSkill } from '@/types'

interface JobRecsResponse { recommendations: JobRecommendation[] }
interface SkillRecsResponse { recommended_skills: RecommendedSkill[] }
interface CoursesResponse { courses: unknown[] }

export const recommendationsApi = {
  getJobRecommendations: (topN = 20) =>
    unwrap(apiClient.get<{ success: boolean; data: JobRecsResponse; message: string }>(`/recommendations/jobs?top_n=${topN}`)),

  getSkillRecommendations: () =>
    unwrap(apiClient.get<{ success: boolean; data: SkillRecsResponse; message: string }>('/recommendations/skills')),

  getCourseRecommendations: () =>
    unwrap(apiClient.get<{ success: boolean; data: CoursesResponse; message: string }>('/recommendations/courses')),
}
