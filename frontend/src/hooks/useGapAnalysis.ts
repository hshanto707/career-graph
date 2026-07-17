// Data-fetching hooks for the Skill Analysis page.
//
// Two pieces:
//   - useTargetRoles(): reads the student's profile so the page can build a
//     target-job selector from `target_roles` (last entry = "current" pick,
//     mirroring the backend's own resolve_target_job_id() convention -- see
//     docs/algorithmic-agents-decisions.md's B6/B7 section).
//   - useGapAnalysis(): a mutation wrapping POST /gap-analysis, the explicit
//     "caller picked a specific job" entry point per the reconciled
//     /skills/gap vs. /gap-analysis contract. The Skill Analysis page fires
//     this whenever the selected target job changes (including the initial
//     auto-selection), so there is exactly one code path that produces a
//     gap result for this page, regardless of whether the student changed
//     the selector or just landed on the page.

import { useMutation, useQuery } from "@tanstack/react-query";
import { gapApi } from "@/lib/api/gap";
import { profileApi, type ProfileOut } from "@/lib/api/profile";
import type { GapAnalysisResponse } from "@/lib/api/skills";

export function useTargetRoles() {
  return useQuery<ProfileOut>({
    queryKey: ["profile"],
    queryFn: profileApi.get,
  });
}

export function useGapAnalysis() {
  return useMutation<GapAnalysisResponse, unknown, string>({
    mutationFn: (targetJobId: string) => gapApi.analyze(targetJobId),
  });
}
