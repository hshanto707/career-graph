/**
 * RecommendationsPage — Personalized job, skill, and course recommendations.
 * Three tabs: Jobs (Jaccard-ranked), Skills (market gaps), Courses (by missing skills).
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { recommendationsApi } from '@/api/recommendationsApi'
import { JobCard } from '@/components/ui/JobCard'
import { SkeletonCard } from '@/components/ui/Skeleton'
import { EmptyState } from '@/components/ui/EmptyState'
import { PageHeader } from '@/components/ui/PageHeader'
import { Star, TrendingUp, Briefcase, BookOpen, ExternalLink } from 'lucide-react'
import { Link } from 'react-router-dom'
import type { Course } from '@/types'

type Tab = 'jobs' | 'skills' | 'courses'

function CourseCard({ course }: { course: Course }) {
  return (
    <div className="card p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-gray-900 truncate">{course.title}</h3>
            {course.free !== undefined && (
              <span className={`badge flex-shrink-0 ${course.free ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
                {course.free ? 'Free' : 'Paid'}
              </span>
            )}
          </div>
          <p className="text-sm text-gray-500 mt-0.5">{course.provider}{course.duration ? ` · ${course.duration}` : ''}</p>
        </div>
        {course.url && (
          <a
            href={course.url}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-secondary text-xs py-1 px-3 flex items-center gap-1 flex-shrink-0"
          >
            <ExternalLink className="w-3 h-3" />
            Open
          </a>
        )}
      </div>
      {course.teaches_skills.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {course.teaches_skills.map(s => (
            <span key={s} className="badge bg-primary-50 text-primary-700">{s}</span>
          ))}
        </div>
      )}
    </div>
  )
}

export default function RecommendationsPage() {
  const [tab, setTab] = useState<Tab>('jobs')

  const { data: jobRecs, isLoading: jobsLoading } = useQuery({
    queryKey: ['recommendations-jobs'],
    queryFn: () => recommendationsApi.getJobRecommendations(20),
    enabled: tab === 'jobs',
  })

  const { data: skillRecs, isLoading: skillsLoading } = useQuery({
    queryKey: ['recommendations-skills'],
    queryFn: recommendationsApi.getSkillRecommendations,
    enabled: tab === 'skills',
  })

  const { data: courseRecs, isLoading: coursesLoading } = useQuery({
    queryKey: ['recommendations-courses'],
    queryFn: recommendationsApi.getCourseRecommendations,
    enabled: tab === 'courses',
  })

  const jobs = jobRecs?.recommendations ?? []
  const skills = skillRecs?.recommended_skills ?? []
  const courses = (courseRecs?.courses ?? []) as Course[]

  return (
    <div className="max-w-4xl mx-auto">
      <PageHeader
        title="Recommendations"
        subtitle="Personalized job matches and skills to learn, ranked by your profile"
      />

      {/* Tabs */}
      <div className="flex gap-1 p-1 bg-gray-100 rounded-xl mb-6 w-fit">
        {([
          { key: 'jobs',    label: 'Job Matches',     icon: Briefcase },
          { key: 'skills',  label: 'Skills to Learn', icon: TrendingUp },
          { key: 'courses', label: 'Courses',          icon: BookOpen },
        ] as const).map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              tab === key
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        ))}
      </div>

      {/* Jobs Tab */}
      {tab === 'jobs' && (
        <>
          {jobsLoading ? (
            <div className="space-y-3">
              {[0, 1, 2].map(i => <SkeletonCard key={i} />)}
            </div>
          ) : jobs.length === 0 ? (
            <EmptyState
              icon={<Briefcase className="w-12 h-12" />}
              title="No recommendations yet"
              description="Add skills to your profile to get personalized job matches."
              action={<Link to="/profile" className="btn-primary">Go to Profile</Link>}
            />
          ) : (
            <div className="space-y-3">
              <p className="text-sm text-gray-500 mb-2">
                Ranked by skill overlap with your profile. Score = Jaccard similarity.
              </p>
              {jobs.map(job => (
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
                  missing_skills={job.missing_skills}
                />
              ))}
            </div>
          )}
        </>
      )}

      {/* Skills Tab */}
      {tab === 'skills' && (
        <>
          {skillsLoading ? (
            <div className="space-y-3">
              {[0, 1, 2].map(i => <SkeletonCard key={i} />)}
            </div>
          ) : skills.length === 0 ? (
            <EmptyState
              icon={<TrendingUp className="w-12 h-12" />}
              title="No skill recommendations"
              description="You already have all the top demanded skills, or add more skills to your profile."
            />
          ) : (
            <div className="space-y-3">
              <p className="text-sm text-gray-500 mb-2">
                Most demanded skills in the market that you haven't declared yet — ranked by employer demand.
              </p>
              <div className="card divide-y divide-gray-50">
                {skills.map((skill, idx) => (
                  <div key={skill.name} className="flex items-center gap-4 px-5 py-4">
                    <span className="w-7 h-7 rounded-full bg-primary-50 text-primary-600 text-xs font-bold flex items-center justify-center flex-shrink-0">
                      {idx + 1}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-medium text-gray-800">{skill.name}</span>
                        <span className="text-sm text-gray-500">{skill.demand_count} jobs require this</span>
                      </div>
                      <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-primary-400 rounded-full"
                          style={{ width: `${skill.demand_score}%` }}
                        />
                      </div>
                    </div>
                    <Link
                      to="/profile"
                      className="btn-secondary text-xs py-1 px-3 flex-shrink-0"
                    >
                      Add to Profile
                    </Link>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {/* Courses Tab */}
      {tab === 'courses' && (
        <>
          {coursesLoading ? (
            <div className="space-y-3">
              {[0, 1, 2].map(i => <SkeletonCard key={i} />)}
            </div>
          ) : courses.length === 0 ? (
            <EmptyState
              icon={<BookOpen className="w-12 h-12" />}
              title="No course recommendations"
              description="Complete a gap analysis first, or add skills to your profile to get course suggestions."
              action={<Link to="/skills" className="btn-primary">Run Gap Analysis</Link>}
            />
          ) : (
            <div className="space-y-3">
              <p className="text-sm text-gray-500 mb-2">
                Courses that teach skills missing from your profile, ranked by relevance.
              </p>
              {courses.map(course => (
                <CourseCard key={course.id} course={course} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}
