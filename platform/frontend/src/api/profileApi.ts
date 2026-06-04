import { apiClient, unwrap } from '@/lib/apiClient'
import type { Profile, ProfileUpdateRequest, AddSkillRequest } from '@/types'

export const profileApi = {
  getProfile: () =>
    unwrap(apiClient.get<{ success: boolean; data: Profile; message: string }>('/profile')),

  updateProfile: (data: ProfileUpdateRequest) =>
    unwrap(apiClient.put<{ success: boolean; data: Profile; message: string }>('/profile', data)),

  addSkill: (data: AddSkillRequest) =>
    unwrap(apiClient.post<{ success: boolean; data: unknown; message: string }>('/profile/skills', data)),

  removeSkill: (skillName: string) =>
    unwrap(apiClient.delete<{ success: boolean; data: unknown; message: string }>(`/profile/skills/${encodeURIComponent(skillName)}`)),
}
