import { apiClient } from '@/lib/apiClient'
import { saveToken, saveUser } from '@/lib/auth'
import type { RegisterRequest, LoginRequest, TokenData } from '@/types'

export const authApi = {
  async register(data: RegisterRequest): Promise<TokenData> {
    const res = await apiClient.post<{ success: boolean; data: TokenData; message: string }>('/auth/register', data)
    const tokenData = res.data.data!
    saveToken(tokenData.access_token)
    saveUser({ user_id: tokenData.user_id, name: tokenData.name, email: tokenData.email })
    return tokenData
  },

  async login(data: LoginRequest): Promise<TokenData> {
    const res = await apiClient.post<{ success: boolean; data: TokenData; message: string }>('/auth/login', data)
    const tokenData = res.data.data!
    saveToken(tokenData.access_token)
    saveUser({ user_id: tokenData.user_id, name: tokenData.name, email: tokenData.email })
    return tokenData
  },
}
