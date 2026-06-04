/**
 * SkillsPage — Market skill demand + personal gap analysis.
 * Two sections:
 *   1. Market Demand — top skills across all job postings
 *   2. Gap Analysis — select a target job and see readiness score + roadmap
 */
import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { skillsApi } from '@/api/skillsApi'
import { gapApi } from '@/api/gapApi'
import { jobsApi } from '@/api/jobsApi'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { PageHeader } from '@/components/ui/PageHeader'
import { GapResult } from '@/components/ui/GapResult'
import { TrendingUp, Target, Loader2, Search } from 'lucide-react'

export default function SkillsPage() {
  const [gapJobId, setGapJobId] = useState('')
  const [jobSearch, setJobSearch] = useState('')
  const [showDropdown, setShowDropdown] = useState(false)

  const { data: marketData, isLoading: marketLoading } = useQuery({
    queryKey: ['market-skills'],
    queryFn: skillsApi.getMarketSkills,
  })

  const { data: jobsData } = useQuery({
    queryKey: ['jobs-search', jobSearch],
    queryFn: () => jobsApi.getJobs({ search: jobSearch, limit: 8 }),
    enabled: jobSearch.length >= 2,
  })

  const gapMutation = useMutation({
    mutationFn: () => gapApi.analyzeGap({ target_job_id: gapJobId }),
  })

  const topSkills = marketData?.top_skills ?? []
  const jobs = jobsData?.jobs ?? []

  function selectJob(id: string, title: string, company: string) {
    setGapJobId(id)
    setJobSearch(`${title} — ${company}`)
    setShowDropdown(false)
    gapMutation.reset()
  }

  return (
    <div className="max-w-5xl mx-auto">
      <PageHeader
        title="Skill Analysis"
        subtitle="Understand market demand and analyze your readiness for any job"
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* ─── Market Demand ───────────────────────────────── */}
        <div>
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="w-5 h-5 text-primary-500" />
            <h2 className="text-lg font-semibold text-gray-800">Market Demand</h2>
          </div>

          {marketLoading ? (
            <LoadingSpinner />
          ) : (
            <div className="card divide-y divide-gray-50">
              {topSkills.slice(0, 20).map((skill, idx) => (
                <div key={skill.name} className="flex items-center gap-3 px-5 py-3">
                  <span className="w-6 text-xs font-bold text-gray-300 text-center flex-shrink-0">
                    {idx + 1}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-sm font-medium text-gray-800 truncate">{skill.name}</span>
                      <span className="text-xs text-gray-400 ml-2 flex-shrink-0">{skill.demand_count} jobs</span>
                    </div>
                    <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full"
                        style={{
                          width: `${skill.demand_score}%`,
                          backgroundColor: `hsl(${220 - idx * 5}, 75%, ${50 + idx * 1}%)`,
                        }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* ─── Gap Analysis ────────────────────────────────── */}
        <div>
          <div className="flex items-center gap-2 mb-4">
            <Target className="w-5 h-5 text-primary-500" />
            <h2 className="text-lg font-semibold text-gray-800">Gap Analysis</h2>
          </div>

          <div className="card p-5">
            <p className="text-sm text-gray-500 mb-4">
              Select a target job to see how ready you are and which skills to learn.
            </p>

            {/* Job search */}
            <div className="relative mb-4">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                className="input pl-10"
                placeholder="Search for a target job..."
                value={jobSearch}
                onChange={e => { setJobSearch(e.target.value); setShowDropdown(true); setGapJobId('') }}
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
              onClick={() => { setShowDropdown(false); gapMutation.mutate() }}
              disabled={!gapJobId || gapMutation.isPending}
              className="btn-primary w-full mb-5"
            >
              {gapMutation.isPending ? (
                <><Loader2 className="w-4 h-4 mr-2 animate-spin inline" /> Analyzing...</>
              ) : 'Analyze My Gap'}
            </button>

            {gapMutation.isError && (
              <div className="text-sm text-red-500 text-center py-2">
                {(gapMutation.error as Error).message}
              </div>
            )}

            {gapMutation.data && (
              <GapResult data={gapMutation.data} showRoadmap={false} />
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
