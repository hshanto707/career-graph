import { apiClient } from "@/lib/apiClient";
import type { SkillDemandOut } from "@/lib/api/skills";

export interface DashboardStatsOut {
  job_readiness_score: number;
  skills_matched: number;
  total_required_skills: number;
  missing_high_demand_skills: string[];
  matched_market_skills: string[];
  market_demand: SkillDemandOut[];
}

export const dashboardApi = {
  get: () => apiClient.get<DashboardStatsOut>("/dashboard"),
};
