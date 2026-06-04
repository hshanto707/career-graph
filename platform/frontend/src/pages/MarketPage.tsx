/**
 * MarketPage — Market intelligence: top skills, job categories, your gaps.
 * Route: /market
 */
import { useQuery } from '@tanstack/react-query'
import { marketApi } from '@/api/marketApi'
import { profileApi } from '@/api/profileApi'
import { PageHeader } from '@/components/ui/PageHeader'
import { StatCard } from '@/components/ui/StatCard'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { useAuth } from '@/hooks/useAuth'
import { Link } from 'react-router-dom'
import { BarChart2, TrendingUp, Briefcase, AlertCircle } from 'lucide-react'

function SkillBar({ name, demand_score, demand_count, rank }: {
  name: string
  demand_score: number
  demand_count: number
  rank: number
}) {
  const hue = Math.max(200 - rank * 4, 160)
  return (
    <div className="flex items-center gap-3 py-2.5 border-b border-gray-50 last:border-0">
      <span className="w-6 text-xs font-bold text-gray-300 text-right flex-shrink-0">{rank}</span>
      <div className="flex-1 min-w-0">
        <div className="flex justify-between items-center mb-1">
          <span className="text-sm font-medium text-gray-800 truncate">{name}</span>
          <span className="text-xs text-gray-400 ml-2 flex-shrink-0">{demand_count.toLocaleString()} jobs</span>
        </div>
        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all"
            style={{
              width: `${demand_score}%`,
              backgroundColor: `hsl(${hue}, 65%, 45%)`,
            }}
          />
        </div>
      </div>
    </div>
  )
}

export default function MarketPage() {
  const { user } = useAuth()

  const { data: market, isLoading } = useQuery({
    queryKey: ['market-insights'],
    queryFn: marketApi.getInsights,
  })

  const { data: profile } = useQuery({
    queryKey: ['profile'],
    queryFn: profileApi.getProfile,
    enabled: !!user,
  })

  if (isLoading) return <LoadingSpinner text="Loading market data..." />

  const topSkills = market?.top_skills ?? []
  const categories = market?.top_categories ?? []
  const totalJobs = market?.total_jobs ?? 0

  // "Missing from top 10" — diff user's skills against top 10 market skills
  const top10Names = new Set(topSkills.slice(0, 10).map(s => s.name))
  const userSkillNames = new Set(profile?.skills?.map(s => s.name) ?? [])
  const missingTop10 = [...top10Names].filter(s => !userSkillNames.has(s))

  const totalCategoryJobs = categories.reduce((sum, c) => sum + c.job_count, 0) || 1

  return (
    <div className="max-w-5xl mx-auto">
      <PageHeader
        title="Market Intelligence"
        subtitle="Understand what employers are looking for and where the opportunities are"
        icon={<BarChart2 className="w-6 h-6" />}
      />

      {/* KPI */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        <StatCard
          title="Total Jobs"
          value={totalJobs.toLocaleString()}
          subtitle="In the knowledge graph"
          icon={<Briefcase className="w-6 h-6 text-primary-600" />}
          iconBg="bg-primary-50"
        />
        <StatCard
          title="Unique Skills"
          value={topSkills.length.toLocaleString()}
          subtitle="Tracked across all jobs"
          icon={<TrendingUp className="w-6 h-6 text-green-600" />}
          iconBg="bg-green-50"
        />
        <StatCard
          title="Top Skill"
          value={topSkills[0]?.name ?? '–'}
          subtitle={`${topSkills[0]?.demand_count ?? 0} job postings`}
          icon={<BarChart2 className="w-6 h-6 text-amber-600" />}
          iconBg="bg-amber-50"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Top 30 Skills */}
        <div className="lg:col-span-2">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">Top 30 In-Demand Skills</h2>
          <div className="card px-3 py-1">
            {topSkills.slice(0, 30).map((skill, idx) => (
              <SkillBar
                key={skill.name}
                name={skill.name}
                demand_score={skill.demand_score}
                demand_count={skill.demand_count}
                rank={idx + 1}
              />
            ))}
            {topSkills.length === 0 && (
              <p className="text-sm text-gray-400 text-center py-8">No market data yet. Ingest job data first.</p>
            )}
          </div>
        </div>

        {/* Right sidebar */}
        <div className="space-y-5">
          {/* Job Categories */}
          {categories.length > 0 && (
            <div>
              <h2 className="text-lg font-semibold text-gray-800 mb-4">Job Categories</h2>
              <div className="card p-4 space-y-3">
                {categories.slice(0, 8).map(cat => {
                  const pct = Math.round((cat.job_count / totalCategoryJobs) * 100)
                  return (
                    <div key={cat.name}>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="font-medium text-gray-700 truncate">{cat.name}</span>
                        <span className="text-gray-400 flex-shrink-0 ml-2">{pct}%</span>
                      </div>
                      <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-primary-400 rounded-full"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Missing from top 10 */}
          {user ? (
            <div>
              <h2 className="text-lg font-semibold text-gray-800 mb-4">Your Top 10 Gaps</h2>
              {missingTop10.length === 0 ? (
                <div className="card p-4 text-center">
                  <p className="text-sm text-green-600 font-medium">You have all top 10 skills! 🎉</p>
                </div>
              ) : (
                <div className="card p-4">
                  <p className="text-xs text-gray-500 mb-3">Top demanded skills you haven't declared:</p>
                  <div className="flex flex-wrap gap-1.5 mb-3">
                    {missingTop10.map(s => (
                      <span key={s} className="badge bg-amber-50 text-amber-700 border border-amber-100">{s}</span>
                    ))}
                  </div>
                  <Link to="/profile/edit" className="text-xs text-primary-600 hover:underline">
                    Add skills to profile →
                  </Link>
                </div>
              )}
            </div>
          ) : (
            <div className="card p-4 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-gray-700">See your skill gaps</p>
                <p className="text-xs text-gray-500 mt-0.5">
                  <Link to="/login" className="text-primary-600 hover:underline">Sign in</Link> to compare your skills against the top 10.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
