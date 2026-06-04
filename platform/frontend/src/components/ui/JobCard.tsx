/**
 * JobCard — displays a job posting in a card format.
 */
import { MapPin, Building2, DollarSign } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'

interface JobCardProps {
  id: string
  title: string
  company: string
  location: string
  employment_type: string
  salary_min?: number | null
  salary_max?: number | null
  skills_required?: string[]
  score?: number       // 0–1, for recommendations
  matched_skills?: string[]
  missing_skills?: string[]
  onSelect?: (id: string) => void
}

const TYPE_COLORS: Record<string, string> = {
  'Full-time':  'bg-green-100 text-green-700',
  'Part-time':  'bg-blue-100 text-blue-700',
  'Contract':   'bg-purple-100 text-purple-700',
  'Internship': 'bg-orange-100 text-orange-700',
}

function formatSalary(min?: number | null, max?: number | null): string {
  if (!min && !max) return ''
  const fmt = (n: number) => n >= 1000 ? `$${Math.round(n / 1000)}k` : `$${n}`
  if (min && max) return `${fmt(min)} – ${fmt(max)}`
  if (min) return `From ${fmt(min)}`
  return `Up to ${fmt(max!)}`
}

export function JobCard({ id, title, company, location, employment_type, salary_min, salary_max, skills_required = [], score, matched_skills = [], missing_skills = [], onSelect }: JobCardProps) {
  const salary = formatSalary(salary_min, salary_max)
  const typeColor = TYPE_COLORS[employment_type] ?? 'bg-gray-100 text-gray-700'
  const navigate = useNavigate()

  return (
    <div
      className="card p-5 cursor-pointer hover:shadow-md transition-shadow"
      onClick={() => onSelect ? onSelect(id) : navigate(`/jobs/${id}`)}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <Link
            to={`/jobs/${id}`}
            className="font-semibold text-gray-900 truncate hover:text-primary-600 transition-colors block"
            onClick={e => e.stopPropagation()}
          >
            {title}
          </Link>
          <div className="flex items-center gap-3 mt-1 flex-wrap">
            <span className="flex items-center gap-1 text-sm text-gray-500">
              <Building2 className="w-3.5 h-3.5" />{company}
            </span>
            <span className="flex items-center gap-1 text-sm text-gray-500">
              <MapPin className="w-3.5 h-3.5" />{location}
            </span>
          </div>
        </div>
        <div className="flex flex-col items-end gap-1.5 flex-shrink-0">
          <span className={`badge ${typeColor}`}>{employment_type}</span>
          {score !== undefined && (
            <span className="text-sm font-semibold text-primary-600">{Math.round(score * 100)}% match</span>
          )}
        </div>
      </div>

      {/* Salary */}
      {salary && (
        <div className="flex items-center gap-1 mt-2 text-sm text-gray-600">
          <DollarSign className="w-3.5 h-3.5 text-green-500" />
          <span>{salary}</span>
        </div>
      )}

      {/* Matched skills (for recommendations) */}
      {matched_skills.length > 0 && (
        <div className="mt-3">
          <p className="text-xs font-medium text-gray-500 mb-1.5">Matched skills</p>
          <div className="flex flex-wrap gap-1.5">
            {matched_skills.slice(0, 5).map(s => (
              <span key={s} className="badge bg-green-100 text-green-700">{s}</span>
            ))}
            {matched_skills.length > 5 && (
              <span className="badge bg-gray-100 text-gray-500">+{matched_skills.length - 5}</span>
            )}
          </div>
        </div>
      )}

      {/* Skills (for job explorer) */}
      {matched_skills.length === 0 && skills_required.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {skills_required.slice(0, 6).map(s => (
            <span key={s} className="badge bg-gray-100 text-gray-600">{s}</span>
          ))}
          {skills_required.length > 6 && (
            <span className="badge bg-gray-100 text-gray-400">+{skills_required.length - 6}</span>
          )}
        </div>
      )}
    </div>
  )
}
