import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { profileApi, type ProfileOut, type ProfileUpdatePayload, type SkillEntry } from "@/lib/api/profile";

export const PROFILE_QUERY_KEY = ["profile"] as const;

/** GET /profile — the authenticated student's profile. */
export function useProfile() {
  return useQuery({
    queryKey: PROFILE_QUERY_KEY,
    queryFn: profileApi.get,
  });
}

/**
 * PUT /profile — full profile update (major, graduation year, skills,
 * target roles, experience). Invalidates the profile cache on success so
 * Dashboard/Recommendations (which independently derive from the same
 * server state) pick up the change on their next fetch.
 */
export function useUpdateProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ProfileUpdatePayload) => profileApi.update(payload),
    onSuccess: (data: ProfileOut) => {
      // The mutation response is already the fresh profile -- write it
      // straight into the cache instead of re-invalidating (and thus
      // re-fetching) the same key we just updated.
      queryClient.setQueryData(PROFILE_QUERY_KEY, data);
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["recommendations"] });
    },
  });
}

/**
 * POST /profile/skills — add or update a single skill (proficiency/years).
 * Used by the edit-profile skill add flow so a new skill shows up without a
 * full page reload.
 */
export function useAddSkill() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: SkillEntry) => profileApi.addOrUpdateSkill(payload),
    onSuccess: (data: ProfileOut) => {
      queryClient.setQueryData(PROFILE_QUERY_KEY, data);
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["recommendations"] });
    },
  });
}
