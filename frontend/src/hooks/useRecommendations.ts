// React Query hooks for the three independent Recommendations sections
// (jobs, skills, courses). Each hook hits its own endpoint and is allowed to
// fail/load/succeed independently of the others -- one section erroring
// must never take down the other two (see docs/test-plan.md F7).

import { useQuery } from "@tanstack/react-query";
import { recommendationsApi } from "@/lib/api/recommendations";
import { ApiError } from "@/lib/apiClient";

// Each section has its own queryKey/queryFn so a failure in one (e.g.
// courses) never affects the query state of the other two (jobs, skills) --
// React Query tracks/retries/caches them completely independently. The
// global QueryCache error handler (wired in App.tsx) takes care of surfacing
// a toast for any of these on failure; the hooks themselves stay toast-free
// so they're trivial to test in isolation.

export function useJobRecommendations(limit = 10) {
  return useQuery({
    queryKey: ["recommendations", "jobs", limit],
    queryFn: () => recommendationsApi.jobs(limit),
    meta: { toastLabel: "Job recommendations" },
  });
}

export function useSkillRecommendations(limit = 10) {
  return useQuery({
    queryKey: ["recommendations", "skills", limit],
    queryFn: () => recommendationsApi.skills(limit),
    meta: { toastLabel: "Skill recommendations" },
  });
}

export function useCourseRecommendations(targetJobId?: string, limit = 10) {
  return useQuery({
    queryKey: ["recommendations", "courses", targetJobId ?? null, limit],
    queryFn: () => recommendationsApi.courses(targetJobId, limit),
    meta: { toastLabel: "Course recommendations" },
  });
}

/** Shared helper so each section can render a friendly inline error string
 * without duplicating the ApiError/NetworkError unwrapping logic. */
export function describeRecommendationError(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  if (error instanceof Error) return error.message;
  return "Something went wrong.";
}
