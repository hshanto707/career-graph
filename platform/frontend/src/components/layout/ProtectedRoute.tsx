/**
 * ProtectedRoute — wraps routes that require authentication.
 * Redirects to /login if no JWT is stored.
 */
import { Navigate } from 'react-router-dom'
import { isAuthenticated } from '@/lib/auth'
import type { ReactNode } from 'react'

interface Props {
  children: ReactNode
}

export function ProtectedRoute({ children }: Props) {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />
  }
  return <>{children}</>
}
