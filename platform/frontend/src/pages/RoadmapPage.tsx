/**
 * RoadmapPage — Build a personalized learning roadmap for any target job.
 * Route: /roadmap
 */
import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { jobsApi } from '@/api/jobsApi'
import { gapApi } from '@/api/gapApi'
import { PageHeader } from '@/components/ui/PageHeader'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { SkeletonCard } from '@/components/ui/Skeleton'
import {
  Search, Map, Target, CheckCircle2, XCircle, BookOpen,
  Loader2, ChevronDown, ChevronUp
} from 'lucide-react'
import type { GapAnalysisResult, RoadmapMilestone } from '@/types'

function MilestoneCard({ milestone }: { milestone: RoadmapMilestone }) {
  return (
    <div className="flex gap-4">
      <div className="flex flex-col items-center">
        <div className="w-8 h-8 rounded-full bg-primary-600 text-white text-sm font-bold flex items-center justify-center flex-shrink-0">
          {milestone.week}
        </div>
        <div className="w-0.5 bg-gray-200 flex-1 mt-2" />
      </div>
      <div className="pb-5 flex-1">
        <div className="card p-4">
          <p className="text-xs font-semibold text-primary-600 uppercase tracking-wide mb-2">
            Week {milestone.week}
          </p>
          <div className="flex flex-wrap gap-1.5 mb-2">
            {milestone.skills.map(s => (
              <span key={s} className="badge bg-primary-50 text-primary-700 font-medium">{s}</span>
            ))}
          </div>
          <p className="text-xs text-gray-400">{milestone.description}</p>
        </div>
      </div>
    </div>
  )
}

export default function RoadmapPage() {
  const [jobSearch, setJobSearch] = useState('')
  const [selectedJob, setSelectedJob] = useState<{ id: string; title: string; company: string } | null>(null)
  const [showDropdown, setShowDropdown] = useState(false)

  const { data: jobsData } = useQuery({
    queryKey: ['jobs-roadmap', jobSearch],
    queryFn: () => jobsApi.getJobs({ search: jobSearch, limit: 8 }),
    enabled: jobSearch.length >= 2,
  })

  const roadmapMutation = useMutation({
    mutationFn: () => gapApi.analyzeGap({ target_job_id: selectedJob!.id, explain: true }),
  })

  const jobs = jobsData?.jobs ?? []
  const result = roadmapMutation.data as GapAnalysisResult | undefined
  const milestones = result?.roadmap?.milestones ?? []

  function selectJob(id: string, title: string, company: string) {
    setSelectedJob({ id, title, company })
    setJobSearch(`${title} — ${company}`)
    setShowDropdown(false)
    roadmapMutation.reset()
  }

  return (
    <div className="max-w-3xl mx-auto">
      <PageHeader
        title="Learning Roadmap"
        subtitle="Select a target job and build a personalized step-by-step learning plan"
        icon={<Map className="w-6 h-6" />}
      />

      {/* Job selection */}
      <div className="card p-5 mb-6">
        <p className="text-sm text-gray-500 mb-3">Search for your target job role</p>
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            className="input pl-10"
            placeholder="e.g. Data Engineer, Frontend Developer..."
            value={jobSearch}
            onChange={e => {
              setJobSearch(e.target.value)
              setShowDropdown(true)
              setSelectedJob(null)
              roadmapMutation.reset()
            }}
            onFocus={() => setShowDropdown(true)}
          />
          {showDropdown && jobs.length > 0 && (
            <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg overflow-hidden">
              {jobs.map(job => (
                <button
                  key={job.id}
                  type="button"
                  className="w-full px-4 py-2.5 text-left hover:bg-gray-50 border-b border-gray-50 last:border-0"
                  onClick={() => selectJob(job.id, job.title, job.company)}
                >
                  <p className="text-sm font-medium text-gray-800">{job.title}</p>
                  <p className="text-xs text-gray-400">{job.company} · {job.location}</p>
                </button>
              ))}
            </div>
          )}
        </div>

        <button
          onClick={() => { setShowDropdown(false); roadmapMutation.mutate() }}
          disabled={!selectedJob || roadmapMutation.isPending}
          className="btn-primary w-full flex items-center justify-center gap-2"
        >
          {roadmapMutation.isPending
            ? <><Loader2 className="w-4 h-4 animate-spin" /> Building roadmap...</>
            : <><BookOpen className="w-4 h-4" /> Build Roadmap</>
          }
        </button>
      </div>

      {/* Loading skeleton */}
      {roadmapMutation.isPending && (
        <div className="space-y-3">
          {[0, 1, 2].map(i => <SkeletonCard key={i} />)}
        </div>
      )}

      {/* Error */}
      {roadmapMutation.isError && (
        <div className="card p-5 text-center text-red-500">
          {(roadmapMutation.error as Error).message}
        </div>
      )}

      {/* Result */}
      {result && !roadmapMutation.isPending && (
        <div className="space-y-5">
          {/* Readiness score */}
          <div className="card p-5">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-lg font-semibold text-gray-800">Readiness Score</h2>
              <span
                className="text-2xl font-bold"
                style={{
                  color: result.readiness_score >= 70 ? '#16a34a'
                    : result.readiness_score >= 40 ? '#d97706' : '#dc2626'
                }}
              >
                {Math.round(result.readiness_score)}%
              </span>
            </div>
            <div className="flex gap-4 text-sm text-gray-600">
              <span className="flex items-center gap-1">
                <CheckCircle2 className="w-4 h-4 text-green-500" />
                {result.matched_skills.length} matched
              </span>
              <span className="flex items-center gap-1">
                <XCircle className="w-4 h-4 text-red-400" />
                {result.missing_skills.length} to learn
              </span>
            </div>
          </div>

          {/* LLM summary */}
          {result.explanation && (
            <div className="bg-blue-50 border border-blue-100 rounded-xl p-5">
              <p className="text-sm font-medium text-blue-800 mb-1">Career Coach Insight</p>
              <p className="text-sm text-blue-700">{result.explanation}</p>
              {result.encouragement && (
                <p className="text-xs text-blue-500 mt-2 font-medium">{result.encouragement}</p>
              )}
            </div>
          )}

          {/* Roadmap timeline */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-800">Learning Path</h2>
              {result.roadmap && (
                <span className="text-sm text-gray-500">
                  {milestones.length} weeks · {result.roadmap.total_skills} skills
                </span>
              )}
            </div>

            {milestones.length === 0 ? (
              <div className="card p-8 text-center">
                <CheckCircle2 className="w-10 h-10 text-green-500 mx-auto mb-3" />
                <p className="font-medium text-gray-800">You're fully ready for this role!</p>
                <p className="text-sm text-gray-500 mt-1">No skills to learn — apply with confidence.</p>
              </div>
            ) : (
              <div className="space-y-0">
                {milestones.map(m => <MilestoneCard key={m.week} milestone={m} />)}
              </div>
            )}

            {result.roadmap?.summary && (
              <div className="mt-3 p-3 bg-gray-50 rounded-lg">
                <p className="text-xs text-gray-500 italic">{result.roadmap.summary}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Empty state */}
      {!result && !roadmapMutation.isPending && !roadmapMutation.isError && (
        <div className="card p-12 text-center">
          <Target className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500 font-medium">Select a job to build your roadmap</p>
          <p className="text-sm text-gray-400 mt-1">Search above and click "Build Roadmap"</p>
        </div>
      )}
    </div>
  )
}
