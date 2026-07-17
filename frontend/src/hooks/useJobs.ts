// Data-fetching hook for the Job Explorer (catalog) page -- see F5 in
// docs/features-todo.md and docs/test-plan.md.
//
// GET /jobs is a plain catalog endpoint (type/location/search/limit/offset
// only -- see backend/app/schemas/job.py's JobOut, which has no
// requiredSkills/matchPercentage/whyRecommended fields at all). Per the
// documented decision in docs/algorithmic-agents-decisions.md ("Open
// decision #3"), this page never fabricates a personalized match score --
// that is exclusive to GET /recommendations/jobs on the Recommendations
// page. This hook is a thin, honest wrapper around that catalog endpoint.
//
// Pagination + the out-of-order race guard are both handled by
// useInfiniteQuery itself: the query key includes every filter (type,
// location, debounced search). When a filter changes, the key changes, so
// an in-flight request for the *previous* key resolving late updates a
// cache entry the page is no longer subscribed to -- it can never clobber
// the currently-rendered filter combination's data. This is the same
// mechanism React Query uses to guarantee "last key wins" and is why no
// manual AbortController/request-id bookkeeping is needed here.

import { useEffect, useState } from "react";
import { useInfiniteQuery } from "@tanstack/react-query";
import { jobsApi, type JobOut } from "@/lib/api/jobs";

export const JOBS_PAGE_SIZE = 10;
export const SEARCH_DEBOUNCE_MS = 400;

export interface UseJobsFilters {
  /** "All" (or empty) means "no filter" -- callers pass their sentinel value
   * straight through and this hook normalizes it. */
  type?: string;
  location?: string;
  search?: string;
}

function normalize(value: string | undefined): string | undefined {
  if (!value) return undefined;
  const trimmed = value.trim();
  if (trimmed === "" || trimmed.toLowerCase() === "all") return undefined;
  return trimmed;
}

/** Debounces only the search term -- type/location filters (dropdowns) apply
 * immediately since there's no "typing" to settle. */
export function useDebouncedValue<T>(value: T, delayMs: number): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(timer);
  }, [value, delayMs]);

  return debounced;
}

export function useJobs(filters: UseJobsFilters) {
  const debouncedSearch = useDebouncedValue(filters.search ?? "", SEARCH_DEBOUNCE_MS);

  const type = normalize(filters.type);
  const location = normalize(filters.location);
  const search = normalize(debouncedSearch);

  const query = useInfiniteQuery({
    queryKey: ["jobs", { type: type ?? null, location: location ?? null, search: search ?? null }],
    queryFn: ({ pageParam }) =>
      jobsApi.list({
        type,
        location,
        search,
        limit: JOBS_PAGE_SIZE,
        offset: pageParam,
      }),
    initialPageParam: 0,
    getNextPageParam: (lastPage, allPages) => {
      if (lastPage.length < JOBS_PAGE_SIZE) return undefined;
      return allPages.length * JOBS_PAGE_SIZE;
    },
    meta: { toastLabel: "Jobs" },
  });

  const jobs: JobOut[] = query.data?.pages.flat() ?? [];

  return {
    jobs,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    isFetchingNextPage: query.isFetchingNextPage,
    hasNextPage: Boolean(query.hasNextPage),
    fetchNextPage: query.fetchNextPage,
    isSearchPending: (filters.search ?? "") !== debouncedSearch,
  };
}
