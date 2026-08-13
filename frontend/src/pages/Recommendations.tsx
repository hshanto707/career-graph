import { Briefcase, Lightbulb, BookOpen, ExternalLink, AlertTriangle, Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';
import { AppLayout } from '@/components/layout/AppLayout';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { cn } from '@/lib/utils';
import {
  useJobRecommendations,
  useSkillRecommendations,
  useCourseRecommendations,
  describeRecommendationError,
} from '@/hooks/useRecommendations';
import type {
  JobRecommendationOut,
  SkillRecommendationOut,
  CourseRecommendationOut,
} from '@/lib/api/recommendations';

const RENDER_LIMIT = 10;

function getMatchColor(score: number) {
  if (score >= 80) return 'match-score-high';
  if (score >= 60) return 'match-score-medium';
  return 'match-score-low';
}

function jobWhyRecommended(job: JobRecommendationOut): string {
  if (job.why_recommended && job.why_recommended.trim().length > 0) {
    return job.why_recommended;
  }
  const matched = job.matched_skills.slice(0, 3).join(', ');
  return matched
    ? `Matched on ${matched} and ${job.matched_skills.length} of your skills overall.`
    : 'Ranked using your profile and current market demand for this role.';
}

function SectionSkeleton() {
  return (
    <div className="space-y-3 md:space-y-4">
      {[0, 1, 2].map((i) => (
        <div key={i} className="stat-card space-y-3">
          <Skeleton className="h-4 w-1/3" />
          <Skeleton className="h-3 w-1/2" />
          <Skeleton className="h-10 w-full" />
        </div>
      ))}
    </div>
  );
}

function SectionError({ label, error, onRetry }: { label: string; error: unknown; onRetry: () => void }) {
  return (
    <div className="stat-card flex flex-col items-center text-center gap-3 py-10">
      <AlertTriangle className="h-7 w-7 text-destructive" />
      <p className="font-medium text-foreground">Couldn't load {label}</p>
      <p className="text-sm text-muted-foreground max-w-sm">{describeRecommendationError(error)}</p>
      <Button variant="outline" size="sm" onClick={onRetry}>
        Try again
      </Button>
    </div>
  );
}

function SectionEmpty({ title, message }: { title: string; message: string }) {
  return (
    <div className="stat-card flex flex-col items-center text-center gap-2 py-10">
      <Sparkles className="h-7 w-7 text-primary" />
      <p className="font-medium text-foreground">{title}</p>
      <p className="text-sm text-muted-foreground max-w-sm">{message}</p>
    </div>
  );
}

function AllEmptyState() {
  return (
    <div className="stat-card flex flex-col items-center text-center gap-3 py-12">
      <Sparkles className="h-8 w-8 text-primary" />
      <p className="font-medium text-foreground">No recommendations yet</p>
      <p className="text-sm text-muted-foreground max-w-md">
        We don't have enough profile data to personalize jobs, skills, or courses for you yet.
        Add your skills and a target role in your profile to unlock recommendations.
      </p>
      <Button asChild>
        <Link to="/profile/edit">Complete Profile</Link>
      </Button>
    </div>
  );
}

export default function Recommendations() {
  const jobsQuery = useJobRecommendations(RENDER_LIMIT);
  const skillsQuery = useSkillRecommendations(RENDER_LIMIT);
  const coursesQuery = useCourseRecommendations(undefined, RENDER_LIMIT);

  const jobs = jobsQuery.data ?? [];
  const skills = skillsQuery.data ?? [];
  const courses = coursesQuery.data ?? [];

  const allLoaded = !jobsQuery.isLoading && !skillsQuery.isLoading && !coursesQuery.isLoading;
  const allSucceededEmpty =
    allLoaded &&
    !jobsQuery.isError &&
    !skillsQuery.isError &&
    !coursesQuery.isError &&
    jobs.length === 0 &&
    skills.length === 0 &&
    courses.length === 0;

  return (
    <AppLayout>
      <div className="space-y-4 md:space-y-6">
        {/* Page Header */}
        <div>
          <h1 className="page-title">Recommendations</h1>
          <p className="page-subtitle">
            Personalized suggestions based on your profile and market data
          </p>
        </div>

        {allSucceededEmpty ? (
          <AllEmptyState />
        ) : (
          <Tabs defaultValue="jobs" className="space-y-4 md:space-y-6">
            <TabsList className="bg-muted p-1 rounded-lg w-full sm:w-auto grid grid-cols-3 sm:inline-flex">
              <TabsTrigger
                value="jobs"
                className="gap-1.5 md:gap-2 data-[state=active]:bg-background text-xs sm:text-sm"
              >
                <Briefcase className="h-3.5 w-3.5 md:h-4 md:w-4" />
                <span>Jobs</span>
              </TabsTrigger>
              <TabsTrigger
                value="skills"
                className="gap-1.5 md:gap-2 data-[state=active]:bg-background text-xs sm:text-sm"
              >
                <Lightbulb className="h-3.5 w-3.5 md:h-4 md:w-4" />
                <span>Skills</span>
              </TabsTrigger>
              <TabsTrigger
                value="courses"
                className="gap-1.5 md:gap-2 data-[state=active]:bg-background text-xs sm:text-sm"
              >
                <BookOpen className="h-3.5 w-3.5 md:h-4 md:w-4" />
                <span>Courses</span>
              </TabsTrigger>
            </TabsList>

            {/* Jobs Tab */}
            <TabsContent value="jobs" className="space-y-3 md:space-y-4">
              {jobsQuery.isLoading ? (
                <SectionSkeleton />
              ) : jobsQuery.isError ? (
                <SectionError
                  label="job recommendations"
                  error={jobsQuery.error}
                  onRetry={() => jobsQuery.refetch()}
                />
              ) : jobs.length === 0 ? (
                <SectionEmpty
                  title="No job recommendations yet"
                  message="Add skills and a target role to your profile so we can match you against open roles."
                />
              ) : (
                jobs.map((job) => (
                  <div key={job.job_id} className="stat-card">
                    <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 sm:gap-4">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between sm:block">
                          <div className="flex items-center gap-2 flex-wrap">
                            <h3 className="font-semibold text-foreground text-sm md:text-base">
                              {job.title ?? 'Untitled role'}
                            </h3>
                            {job.match_source === 'gnn' && (
                              <span
                                className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full bg-primary/10 text-primary text-[10px] font-medium"
                                title="This ranking was refined by our trained GraphSAGE model, not just rule-based matching."
                              >
                                <Sparkles className="h-2.5 w-2.5" />
                                AI-ranked
                              </span>
                            )}
                          </div>
                          <div className="sm:hidden text-center shrink-0">
                            <div
                              className={cn(
                                'match-score w-10 h-10 text-xs',
                                getMatchColor(job.match_percentage)
                              )}
                            >
                              {Math.round(job.match_percentage)}%
                            </div>
                          </div>
                        </div>
                        <div className="mt-3 md:mt-4 p-2.5 md:p-3 bg-muted/50 rounded-lg">
                          <p className="text-xs md:text-sm text-muted-foreground">
                            <span className="font-medium text-foreground">
                              Why recommended:
                            </span>{' '}
                            {jobWhyRecommended(job)}
                          </p>
                        </div>
                      </div>
                      <div className="hidden sm:block text-center shrink-0">
                        <div
                          className={cn(
                            'match-score',
                            getMatchColor(job.match_percentage)
                          )}
                        >
                          {Math.round(job.match_percentage)}%
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">Match</p>
                      </div>
                    </div>
                    <div className="mt-3 md:mt-4 pt-3 md:pt-4 border-t border-border flex justify-end">
                      <Button variant="outline" size="sm" className="gap-2 text-xs md:text-sm" asChild>
                        <Link to={`/jobs?jobId=${encodeURIComponent(job.job_id)}`}>
                          View Details
                          <ExternalLink className="h-3.5 w-3.5 md:h-4 md:w-4" />
                        </Link>
                      </Button>
                    </div>
                  </div>
                ))
              )}
            </TabsContent>

            {/* Skills Tab */}
            <TabsContent value="skills" className="space-y-4">
              {skillsQuery.isLoading ? (
                <SectionSkeleton />
              ) : skillsQuery.isError ? (
                <SectionError
                  label="skill recommendations"
                  error={skillsQuery.error}
                  onRetry={() => skillsQuery.refetch()}
                />
              ) : skills.length === 0 ? (
                <SectionEmpty
                  title="No skill gaps to close right now"
                  message="You're matching well against your target roles' most in-demand skills. Set a target role in your profile to get tailored suggestions."
                />
              ) : (
                skills.map((skill: SkillRecommendationOut, index: number) => (
                  <div key={skill.skill_name} className="stat-card">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-3">
                          <span className="text-lg font-bold text-muted-foreground">
                            #{index + 1}
                          </span>
                          <h3 className="font-semibold text-foreground">
                            {skill.skill_name}
                          </h3>
                        </div>
                        <div className="mt-4 p-3 bg-muted/50 rounded-lg">
                          <p className="text-sm text-muted-foreground">
                            <span className="font-medium text-foreground">
                              Why recommended:
                            </span>{' '}
                            {skill.why_recommended ??
                              `This skill appears in ${skill.demand_count} job listing${
                                skill.demand_count === 1 ? '' : 's'
                              } for your target roles, with a demand score of ${Math.round(
                                skill.demand_score
                              )}%.`}
                          </p>
                        </div>
                      </div>
                      <div className="text-center shrink-0">
                        <div className={cn('match-score', getMatchColor(skill.demand_score))}>
                          {Math.round(skill.demand_score)}%
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">Demand</p>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </TabsContent>

            {/* Courses Tab */}
            <TabsContent value="courses" className="space-y-4">
              {coursesQuery.isLoading ? (
                <SectionSkeleton />
              ) : coursesQuery.isError ? (
                <SectionError
                  label="course recommendations"
                  error={coursesQuery.error}
                  onRetry={() => coursesQuery.refetch()}
                />
              ) : courses.length === 0 ? (
                <SectionEmpty
                  title="No course recommendations right now"
                  message="Once you have a skill gap against a target role, we'll suggest courses to close it."
                />
              ) : (
                courses.map((course: CourseRecommendationOut) => (
                  <div key={course.course_id ?? course.title ?? course.skill_name} className="stat-card">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <h3 className="font-semibold text-foreground">
                          {course.title ?? 'Untitled course'}
                        </h3>
                        <p className="text-sm text-muted-foreground mt-1">
                          {[course.provider, course.duration].filter(Boolean).join(' · ')}
                        </p>
                        {course.skill_name && (
                          <div className="mt-2">
                            <span className="skill-tag text-xs">{course.skill_name}</span>
                          </div>
                        )}
                        <div className="mt-4 p-3 bg-muted/50 rounded-lg">
                          <p className="text-sm text-muted-foreground">
                            <span className="font-medium text-foreground">
                              Why recommended:
                            </span>{' '}
                            {course.skill_name
                              ? `Teaches ${course.skill_name}, one of your missing target-role skills.`
                              : 'Recommended based on your current skill gaps.'}
                          </p>
                        </div>
                      </div>
                      <div className="text-center shrink-0">
                        <span
                          className={cn(
                            'inline-block px-2 py-1 rounded-full text-xs font-medium',
                            course.free
                              ? 'bg-primary/10 text-primary'
                              : 'bg-muted text-muted-foreground'
                          )}
                        >
                          {course.free ? 'Free' : 'Paid'}
                        </span>
                      </div>
                    </div>
                    <div className="mt-4 pt-4 border-t border-border flex justify-end">
                      {course.url ? (
                        <Button size="sm" className="gap-2" asChild>
                          <a href={course.url} target="_blank" rel="noreferrer">
                            Start Learning
                            <ExternalLink className="h-4 w-4" />
                          </a>
                        </Button>
                      ) : (
                        <Button size="sm" className="gap-2" disabled>
                          Start Learning
                        </Button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </TabsContent>
          </Tabs>
        )}
      </div>
    </AppLayout>
  );
}
