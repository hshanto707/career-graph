/**
 * DashboardPage — Overview of the student's career intelligence.
 * Shows: readiness score, skills count, market demand, top job match.
 */
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { dashboardApi } from '@/api/dashboardApi'
import { marketApi } from '@/api/marketApi'
import { recommendationsApi } from '@/api/recommendationsApi'
import { StatCard } from '@/components/ui/StatCard'
import { JobCard } from '@/components/ui/JobCard'
import { SkeletonStatGrid, SkeletonCard } from '@/components/ui/Skeleton'
import { PageHeader } from '@/components/ui/PageHeader'
import { useAuth } from '@/hooks/useAuth'
import {
  TrendingUp, Briefcase, BarChart3, Star,
  BookOpen, ArrowRight, Zap
} from 'lucide-react'

export default function DashboardPage() {
  const { user } = useAuth()

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: dashboardApi.getStats,
  })

  const { data: market } = useQuery({
    queryKey: ['market-insights'],
    queryFn: marketApi.getInsights,
  })

  const { data: recsData } = useQuery({
    queryKey: ['recommendations', 5],
    queryFn: () => recommendationsApi.getJobRecommendations(5),
  })

  if (statsLoading) return (
    <div className="max-w-6xl mx-auto">
      <SkeletonStatGrid />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-3">
          {[0, 1, 2].map(i => <SkeletonCard key={i} />)}
        </div>
      </div>
    </div>
  )

  const topJobs = recsData?.recommendations?.slice(0, 3) ?? []
  const topSkills = market?.top_skills?.slice(0, 5) ?? []

  return (
    <div className="max-w-6xl mx-auto">
      <PageHeader
        title={`Welcome back, ${user?.name?.split(' ')[0] ?? 'there'} 👋`}
        subtitle="Here's your career intelligence overview"
      />

      {/* KPI Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard
          title="Skills Declared"
          value={stats?.skills_count ?? 0}
          subtitle="In your profile"
          icon={<BookOpen className="w-6 h-6 text-primary-600" />}
          iconBg="bg-primary-50"
        />
        <StatCard
          title="Top Job Readiness"
          value={`${stats?.top_job_readiness ?? 0}%`}
          subtitle="Best matching job"
          icon={<TrendingUp className="w-6 h-6 text-green-600" />}
          iconBg="bg-green-50"
        />
        <StatCard
          title="Jobs in Market"
          value={(stats?.total_jobs_in_market ?? 0).toLocaleString()}
          subtitle="Available opportunities"
          icon={<Briefcase className="w-6 h-6 text-blue-600" />}
          iconBg="bg-blue-50"
        />
        <StatCard
          title="Top Demanded Skill"
          value={stats?.top_demanded_skill ?? '–'}
          subtitle="In the market"
          icon={<Zap className="w-6 h-6 text-amber-600" />}
          iconBg="bg-amber-50"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Top Job Recommendations */}
        <div className="lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-800">Top Job Matches</h2>
            <Link to="/recommendations" className="text-sm text-primary-600 hover:underline flex items-center gap-1">
              See all <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
          <div className="space-y-3">
            {topJobs.length > 0 ? (
              topJobs.map(job => (
                <JobCard
                  key={job.job_id}
                  id={job.job_id}
                  title={job.title}
                  company={job.company}
                  location={job.location}
                  employment_type={job.employment_type}
                  salary_min={job.salary_min}
                  salary_max={job.salary_max}
                  score={job.score}
                  matched_skills={job.matched_skills}
                />
              ))
            ) : (
              <div className="card p-8 text-center">
                <Briefcase className="w-10 h-10 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-600 font-medium">No job recommendations yet</p>
                <p className="text-sm text-gray-400 mt-1">Add skills to your profile to get personalized matches</p>
                <Link to="/profile/edit" className="btn-primary mt-4 inline-flex">
                  Add Skills
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* Market Demand */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-800">Market Demand</h2>
            <Link to="/skills" className="text-sm text-primary-600 hover:underline flex items-center gap-1">
              Full analysis <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
          <div className="card p-5">
            {topSkills.length > 0 ? (
              <div className="space-y-3">
                {topSkills.map((skill, idx) => (
                  <div key={skill.name} className="flex items-center gap-3">
                    <span className="w-5 text-xs font-bold text-gray-400 text-center flex-shrink-0">
                      {idx + 1}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-sm font-medium text-gray-800 truncate">{skill.name}</span>
                        <span className="text-xs text-gray-500 ml-2 flex-shrink-0">{skill.demand_count} jobs</span>
                      </div>
                      <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-primary-400 rounded-full"
                          style={{ width: `${skill.demand_score}%` }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-400 text-center py-4">Loading market data...</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
