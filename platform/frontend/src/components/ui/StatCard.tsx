/**
 * StatCard — displays a single KPI metric on the dashboard.
 */
import type { ReactNode } from 'react'

interface StatCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon: ReactNode
  iconBg?: string   // Tailwind bg color class
  trend?: { value: number; label: string }
}

export function StatCard({ title, value, subtitle, icon, iconBg = 'bg-primary-100', trend }: StatCardProps) {
  return (
    <div className="card p-6 flex items-start gap-4">
      <div className={`flex items-center justify-center w-12 h-12 rounded-xl flex-shrink-0 ${iconBg}`}>
        {icon}
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-gray-500 truncate">{title}</p>
        <p className="text-2xl font-bold text-gray-900 mt-0.5">{value}</p>
        {subtitle && <p className="text-sm text-gray-500 mt-0.5 truncate">{subtitle}</p>}
        {trend && (
          <p className={`text-xs font-medium mt-1 ${trend.value >= 0 ? 'text-green-600' : 'text-red-500'}`}>
            {trend.value >= 0 ? '↑' : '↓'} {Math.abs(trend.value)}% {trend.label}
          </p>
        )}
      </div>
    </div>
  )
}
