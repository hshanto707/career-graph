/**
 * Toast — single notification card, auto-dismissable.
 */
import { useEffect } from 'react'
import { CheckCircle2, XCircle, Info, X } from 'lucide-react'

export type ToastType = 'success' | 'error' | 'info'

interface ToastProps {
  id: number
  message: string
  type: ToastType
  onDismiss: (id: number) => void
}

const CONFIG: Record<ToastType, { bg: string; icon: React.ReactNode }> = {
  success: {
    bg: 'bg-green-50 border-green-200 text-green-800',
    icon: <CheckCircle2 className="w-4 h-4 text-green-500 flex-shrink-0" />,
  },
  error: {
    bg: 'bg-red-50 border-red-200 text-red-700',
    icon: <XCircle className="w-4 h-4 text-red-500 flex-shrink-0" />,
  },
  info: {
    bg: 'bg-blue-50 border-blue-200 text-blue-800',
    icon: <Info className="w-4 h-4 text-blue-500 flex-shrink-0" />,
  },
}

export function Toast({ id, message, type, onDismiss }: ToastProps) {
  const { bg, icon } = CONFIG[type]

  useEffect(() => {
    const timer = setTimeout(() => onDismiss(id), 3000)
    return () => clearTimeout(timer)
  }, [id, onDismiss])

  return (
    <div
      className={`flex items-center gap-2.5 px-4 py-3 rounded-lg border shadow-md max-w-sm w-full animate-fade-in ${bg}`}
      role="alert"
    >
      {icon}
      <span className="text-sm flex-1 font-medium">{message}</span>
      <button
        onClick={() => onDismiss(id)}
        className="flex-shrink-0 opacity-50 hover:opacity-100 transition-opacity"
        aria-label="Dismiss"
      >
        <X className="w-3.5 h-3.5" />
      </button>
    </div>
  )
}
