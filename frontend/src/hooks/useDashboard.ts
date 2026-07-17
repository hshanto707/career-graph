import { useQuery, type UseQueryResult } from "@tanstack/react-query";
import { dashboardApi, type DashboardStatsOut } from "@/lib/api/dashboard";

/**
 * Fetches the current student's dashboard snapshot (readiness score, skill
 * match counts, missing high-demand skills, market demand) via
 * `GET /dashboard`, cached under React Query's "dashboard" key.
 */
export function useDashboard(): UseQueryResult<DashboardStatsOut, Error> {
  return useQuery({
    queryKey: ["dashboard"],
    queryFn: dashboardApi.get,
  });
}
