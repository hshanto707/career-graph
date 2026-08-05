import { apiClient } from "@/lib/apiClient";

export interface SkillEntry {
  name: string;
  proficiency: number;
  years: number;
}

export interface ExperienceItem {
  title: string;
  company: string;
  start_month: number;
  start_year: number;
  end_month: number | null;
  end_year: number | null;
  is_current: boolean;
  description?: string;
}

export interface ProfileOut {
  id: string;
  user_id: string;
  major: string | null;
  graduation_year: number | null;
  skills: SkillEntry[];
  target_roles: string[];
  experience: ExperienceItem[];
  updated_at: string;
}

export interface ProfileUpdatePayload {
  major?: string | null;
  graduation_year?: number | null;
  skills?: SkillEntry[];
  target_roles?: string[];
  experience?: ExperienceItem[];
}

export const profileApi = {
  get: () => apiClient.get<ProfileOut>("/profile"),
  update: (payload: ProfileUpdatePayload) => apiClient.put<ProfileOut>("/profile", payload),
  addOrUpdateSkill: (payload: SkillEntry) => apiClient.post<ProfileOut>("/profile/skills", payload),
};
