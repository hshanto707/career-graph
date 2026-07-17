import { apiClient } from "@/lib/apiClient";
import type { SkillDemandOut } from "@/lib/api/skills";

export interface MarketInsightsOut {
  top_skills: SkillDemandOut[];
  trend_bullets: string[];
  summary: string;
}

export const marketApi = {
  insights: () => apiClient.get<MarketInsightsOut>("/market/insights"),
};
