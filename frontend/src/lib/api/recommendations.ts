import { apiClient } from "@/lib/apiClient";

export interface JobRecommendationOut {
  job_id: string;
  title: string | null;
  match_percentage: number;
  matched_skills: string[];
  why_recommended: string;
}

export interface SkillRecommendationOut {
  skill_name: string;
  demand_score: number;
  demand_count: number;
}

export interface CourseRecommendationOut {
  course_id: string | null;
  title: string | null;
  provider: string | null;
  url: string | null;
  duration: string | null;
  free: boolean;
  skill_name: string | null;
}

export const recommendationsApi = {
  jobs: (limit = 10) => apiClient.get<JobRecommendationOut[]>(`/recommendations/jobs?limit=${limit}`),
  skills: (limit = 10) => apiClient.get<SkillRecommendationOut[]>(`/recommendations/skills?limit=${limit}`),
  courses: (targetJobId?: string, limit = 10) =>
    apiClient.get<CourseRecommendationOut[]>(
      `/recommendations/courses?limit=${limit}${
        targetJobId ? `&target_job_id=${encodeURIComponent(targetJobId)}` : ""
      }`
    ),
};
