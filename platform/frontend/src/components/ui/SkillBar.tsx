/**
 * SkillBar — shows a skill name with a proficiency progress bar.
 */
interface SkillBarProps {
  name: string
  proficiency: number  // 0–10
  years?: number
  showYears?: boolean
}

const LEVEL_LABELS = ['', 'Beginner', 'Beginner', 'Basic', 'Basic', 'Intermediate', 'Intermediate', 'Proficient', 'Proficient', 'Expert', 'Master']
const LEVEL_COLORS = [
  'bg-gray-200',
  'bg-red-400', 'bg-orange-400',
  'bg-yellow-400', 'bg-yellow-500',
  'bg-blue-400', 'bg-blue-500',
  'bg-primary-500', 'bg-primary-600',
  'bg-green-500', 'bg-green-600',
]

export function SkillBar({ name, proficiency, years, showYears = true }: SkillBarProps) {
  const level = Math.round(Math.min(10, Math.max(0, proficiency)))
  const pct = level * 10

  return (
    <div className="flex items-center gap-3 py-2">
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm font-medium text-gray-800 truncate">{name}</span>
          <div className="flex items-center gap-2 flex-shrink-0 ml-2">
            <span className="text-xs text-gray-500">{LEVEL_LABELS[level]}</span>
            <span className="text-xs font-semibold text-gray-700">{level}/10</span>
          </div>
        </div>
        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${LEVEL_COLORS[level]}`}
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>
      {showYears && years !== undefined && (
        <span className="text-xs text-gray-400 flex-shrink-0 w-14 text-right">
          {years}y exp
        </span>
      )}
    </div>
  )
}
