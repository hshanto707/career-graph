/**
 * ToastContext — lightweight notification system (no external library).
 * Usage: wrap app with <ToastProvider>, call useToast() in components.
 */
import { createContext, useContext, useState, useCallback, ReactNode } from 'react'
import { Toast, type ToastType } from '@/components/ui/Toast'

interface ToastItem {
  id: number
  message: string
  type: ToastType
}

interface ToastAPI {
  success: (message: string) => void
  error: (message: string) => void
  info: (message: string) => void
}

const ToastContext = createContext<ToastAPI | null>(null)

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([])

  const dismiss = useCallback((id: number) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])

  const push = useCallback((message: string, type: ToastType) => {
    const id = Date.now() + Math.random()
    setToasts(prev => [...prev, { id, message, type }])
  }, [])

  const api: ToastAPI = {
    success: (msg) => push(msg, 'success'),
    error: (msg) => push(msg, 'error'),
    info: (msg) => push(msg, 'info'),
  }

  return (
    <ToastContext.Provider value={api}>
      {children}
      {/* Fixed-position toast stack — top-right */}
      <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
        {toasts.map(t => (
          <div key={t.id} className="pointer-events-auto">
            <Toast id={t.id} message={t.message} type={t.type} onDismiss={dismiss} />
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast(): ToastAPI {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used within <ToastProvider>')
  return ctx
}
