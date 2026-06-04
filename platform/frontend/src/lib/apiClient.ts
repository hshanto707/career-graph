import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { getToken, clearAuth } from './auth'

// Use Vite proxy — requests to /api/* are proxied to backend:8000
const BASE_URL = '/api/v1'

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
})

// Request interceptor: attach JWT token to every request
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor: handle 401 by clearing auth and redirecting
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      clearAuth()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  },
)

/** Extract data from the APIResponse envelope, throws on success=false */
export async function unwrap<T>(promise: Promise<{ data: { success: boolean; data: T; message: string } }>): Promise<T> {
  const response = await promise
  const body = response.data
  if (!body.success) {
    throw new Error(body.message || 'API error')
  }
  if (body.data === null || body.data === undefined) {
    return body.data as T
  }
  return body.data
}
