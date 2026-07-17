import { apiClient } from "@/lib/apiClient";

export interface UserOut {
  id: string;
  email: string;
  name: string;
  created_at: string;
}

export interface TokenResponse {
  token: string;
  user: UserOut;
}

export interface RegisterPayload {
  email: string;
  password: string;
  name: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export const authApi = {
  register: (payload: RegisterPayload) =>
    apiClient.post<TokenResponse>("/auth/register", payload, { skipAuth: true }),
  login: (payload: LoginPayload) =>
    apiClient.post<TokenResponse>("/auth/login", payload, { skipAuth: true }),
  me: () => apiClient.get<UserOut>("/auth/me"),
};
