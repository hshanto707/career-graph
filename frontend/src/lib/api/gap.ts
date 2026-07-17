import { apiClient } from "@/lib/apiClient";
import type { GapAnalysisResponse } from "@/lib/api/skills";

export type { GapAnalysisResponse };

export const gapApi = {
  analyze: (targetJobId: string) =>
    apiClient.post<GapAnalysisResponse>("/gap-analysis", { target_job_id: targetJobId }),
};
