// Debounced autocomplete-suggestion hooks for the skill-name and
// target-role Combobox inputs on Edit Profile. Mirrors the debounce
// pattern in useJobs.ts (useDebouncedValue) so typing doesn't fire a
// request per keystroke.

import { useQuery } from "@tanstack/react-query";
import { skillsApi } from "@/lib/api/skills";
import { jobsApi } from "@/lib/api/jobs";
import { useDebouncedValue } from "@/hooks/useJobs";

const SUGGESTIONS_DEBOUNCE_MS = 300;

export function useSkillSuggestions(query: string) {
  const debounced = useDebouncedValue(query, SUGGESTIONS_DEBOUNCE_MS);

  const { data, isFetching } = useQuery({
    queryKey: ["skill-suggestions", debounced],
    queryFn: () => skillsApi.search(debounced),
    placeholderData: (previous) => previous,
  });

  return { suggestions: data ?? [], isLoading: isFetching };
}

export function useJobTitleSuggestions(query: string) {
  const debounced = useDebouncedValue(query, SUGGESTIONS_DEBOUNCE_MS);

  const { data, isFetching } = useQuery({
    queryKey: ["job-title-suggestions", debounced],
    queryFn: () => jobsApi.titles(debounced),
    placeholderData: (previous) => previous,
  });

  return { suggestions: data ?? [], isLoading: isFetching };
}
