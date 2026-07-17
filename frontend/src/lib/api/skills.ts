import { apiClient } from "@/lib/apiClient";

export interface SkillDemandOut {
  skill_name: string;
  demand_count: number;
  demand_score: number;
  trend: number | null;
}

export interface MissingSkillOut {
  skill_name: string;
  importance: string;
  estimated_learning_weeks: number;
}

export interface MilestoneOut {
  week_range: string;
  skill_name: string;
  course_title: string | null;
  course_url: string | null;
  goal: string;
}

export interface GapAnalysisResponse {
  target_job_id: string | null;
  readiness_score: number;
  matched_skills: string[];
  missing_skills: MissingSkillOut[];
  explanation: string;
  encouragement: string;
  roadmap: MilestoneOut[];
  message?: string | null;
}

export const skillsApi = {
  market: () => apiClient.get<SkillDemandOut[]>("/skills/market"),
  gap: (targetJobId?: string) =>
    apiClient.get<GapAnalysisResponse>(
      `/skills/gap${targetJobId ? `?target_job_id=${encodeURIComponent(targetJobId)}` : ""}`
    ),
};
