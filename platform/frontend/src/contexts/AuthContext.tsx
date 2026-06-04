/**
 * AuthContext — provides user state and login/logout to the entire app.
 * Stored in localStorage so state persists across page refreshes.
 */
import React, { createContext, useContext, useState, useCallback, type ReactNode } from 'react'
import { getUser, clearAuth, type StoredUser } from '@/lib/auth'

interface AuthContextValue {
  user: StoredUser | null
  isAuthenticated: boolean
  setUser: (user: StoredUser | null) => void
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUserState] = useState<StoredUser | null>(() => getUser())

  const setUser = useCallback((u: StoredUser | null) => {
    setUserState(u)
  }, [])

  const logout = useCallback(() => {
    clearAuth()
    setUserState(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, setUser, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuthContext(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuthContext must be used inside AuthProvider')
  return ctx
}
