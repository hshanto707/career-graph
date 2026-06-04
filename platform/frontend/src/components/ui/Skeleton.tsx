/**
 * Skeleton loading components — use instead of spinners on page-level loads.
 * Tailwind animate-pulse provides the shimmer effect.
 */

import type { CSSProperties } from 'react'

function SkeletonBlock({ className = '', style }: { className?: string; style?: CSSProperties }) {
  return <div className={`bg-gray-200 rounded animate-pulse ${className}`} style={style} />
}

export function SkeletonText({ lines = 1, className = '' }: { lines?: number; className?: string }) {
  return (
    <div className={`space-y-2 ${className}`}>
      {Array.from({ length: lines }).map((_, i) => (
        <SkeletonBlock
          key={i}
          className={`h-4 ${i === lines - 1 && lines > 1 ? 'w-3/4' : 'w-full'}`}
        />
      ))}
    </div>
  )
}

export function SkeletonCard({ className = '' }: { className?: string }) {
  return (
    <div className={`card p-5 space-y-3 ${className}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 space-y-2">
          <SkeletonBlock className="h-5 w-2/3" />
          <SkeletonBlock className="h-4 w-1/2" />
        </div>
        <SkeletonBlock className="h-6 w-16 rounded-full" />
      </div>
      <div className="flex gap-1.5">
        {[60, 45, 55, 40].map((w, i) => (
          <SkeletonBlock key={i} className="h-5 rounded-full" style={{ width: `${w}px` }} />
        ))}
      </div>
    </div>
  )
}

export function SkeletonRow({ className = '' }: { className?: string }) {
  return (
    <div className={`flex items-center gap-3 px-5 py-4 ${className}`}>
      <SkeletonBlock className="h-7 w-7 rounded-full flex-shrink-0" />
      <div className="flex-1 space-y-1.5">
        <SkeletonBlock className="h-4 w-1/3" />
        <SkeletonBlock className="h-2 w-full rounded-full" />
      </div>
      <SkeletonBlock className="h-7 w-20 rounded-lg flex-shrink-0" />
    </div>
  )
}

export function SkeletonStatGrid() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      {[0, 1, 2, 3].map(i => (
        <div key={i} className="card p-5 space-y-3">
          <div className="flex items-center justify-between">
            <SkeletonBlock className="h-4 w-24" />
            <SkeletonBlock className="h-10 w-10 rounded-xl" />
          </div>
          <SkeletonBlock className="h-8 w-20" />
          <SkeletonBlock className="h-3 w-28" />
        </div>
      ))}
    </div>
  )
}
