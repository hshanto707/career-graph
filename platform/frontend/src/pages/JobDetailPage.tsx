/**
 * JobDetailPage — Full detail view for a single job posting.
 * Route: /jobs/:jobId
 */
import { useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { jobsApi } from '@/api/jobsApi'
import { gapApi } from '@/api/gapApi'
import { profileApi } from '@/api/profileApi'
import { GapResult } from '@/components/ui/GapResult'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { useToast } from '@/contexts/ToastContext'
import {
  ArrowLeft, MapPin, Building2, Clock, DollarSign,
  Target, Loader2, BookmarkPlus
} from 'lucide-react'
import type { JobDetail } from '@/types'

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

export default function JobDetailPage() {
  const { jobId } = useParams<{ jobId: string }>()
  const toast = useToast()
  const queryClient = useQueryClient()
  const [gapVisible, setGapVisible] = useState(false)

  const { data: job, isLoading, error } = useQuery({
    queryKey: ['job', jobId],
    queryFn: () => jobsApi.getJob(jobId!),
    enabled: !!jobId,
  })

  const gapMutation = useMutation({
    mutationFn: () => gapApi.analyzeGap({ target_job_id: jobId!, explain: false }),
    onSuccess: () => setGapVisible(true),
    onError: (e: Error) => toast.error(e.message),
  })

  const addTargetMutation = useMutation({
    mutationFn: async () => {
      const profile = await profileApi.getProfile()
      const current = profile.target_roles ?? []
      if (!current.includes(job?.title ?? '')) {
        await profileApi.updateProfile({ target_roles: [...current, job?.title ?? ''] })
      }
    },
    onSuccess: () => {
      toast.success('Added to target roles')
      queryClient.invalidateQueries({ queryKey: ['profile'] })
    },
    onError: (e: Error) => toast.error(e.message),
  })

  if (isLoading) return <LoadingSpinner text="Loading job..." />

  if (error || !job) {
    return (
      <div className="max-w-3xl mx-auto">
        <EmptyState
          icon={<Target className="w-12 h-12" />}
          title="Job not found"
          description="This job posting may have been removed."
          action={<Link to="/jobs" className="btn-primary">Back to Jobs</Link>}
        />
      </div>
    )
  }

  const jobDetail = job as unknown as JobDetail
  const mustSkills = jobDetail.skills_required?.filter(s => s.importance === 'must') ?? []
  const niceSkills = jobDetail.skills_required?.filter(s => s.importance !== 'must') ?? []
  const salary = formatSalary(job.salary_min, job.salary_max)
  const typeColor = TYPE_COLORS[job.employment_type] ?? 'bg-gray-100 text-gray-700'

  return (
    <div className="max-w-3xl mx-auto">
      {/* Back link */}
      <Link to="/jobs" className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 mb-5">
        <ArrowLeft className="w-4 h-4" /> Back to Jobs
      </Link>

      {/* Header */}
      <div className="card p-6 mb-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <h1 className="text-2xl font-bold text-gray-900">{job.title}</h1>
            <div className="flex flex-wrap items-center gap-3 mt-2">
              <span className="flex items-center gap-1 text-gray-500">
                <Building2 className="w-4 h-4" />{job.company}
              </span>
              <span className="flex items-center gap-1 text-gray-500">
                <MapPin className="w-4 h-4" />{job.location}
              </span>
              {salary && (
                <span className="flex items-center gap-1 text-gray-500">
                  <DollarSign className="w-4 h-4" />{salary}
                </span>
              )}
            </div>
          </div>
          <span className={`badge ${typeColor} flex-shrink-0`}>{job.employment_type}</span>
        </div>

        {/* Skills */}
        <div className="mt-5 space-y-3">
          {mustSkills.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">Required Skills</p>
              <div className="flex flex-wrap gap-1.5">
                {mustSkills.map(s => (
                  <span key={s.name} className="badge bg-red-50 text-red-600 border border-red-100">{s.name}</span>
                ))}
              </div>
            </div>
          )}
          {niceSkills.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">Nice to Have</p>
              <div className="flex flex-wrap gap-1.5">
                {niceSkills.map(s => (
                  <span key={s.name} className="badge bg-gray-100 text-gray-600">{s.name}</span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Description */}
        {job.description && (
          <div className="mt-5 pt-5 border-t border-gray-100">
            <p className="text-sm text-gray-700 whitespace-pre-line">{job.description}</p>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3 mt-6 pt-5 border-t border-gray-100">
          <button
            onClick={() => gapMutation.mutate()}
            disabled={gapMutation.isPending}
            className="btn-primary flex items-center gap-2"
          >
            {gapMutation.isPending
              ? <><Loader2 className="w-4 h-4 animate-spin" /> Analyzing...</>
              : <><Target className="w-4 h-4" /> Analyze My Gap</>
            }
          </button>
          <button
            onClick={() => addTargetMutation.mutate()}
            disabled={addTargetMutation.isPending}
            className="btn-secondary flex items-center gap-2"
          >
            {addTargetMutation.isPending
              ? <Loader2 className="w-4 h-4 animate-spin" />
              : <BookmarkPlus className="w-4 h-4" />
            }
            Add to Targets
          </button>
        </div>
      </div>

      {/* Inline gap result */}
      {gapVisible && gapMutation.data && (
        <div className="card p-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">Gap Analysis Result</h2>
          <GapResult data={gapMutation.data} showRoadmap />
        </div>
      )}
    </div>
  )
}
