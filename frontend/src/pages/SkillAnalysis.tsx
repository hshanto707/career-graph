import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  TrendingUp,
  CheckCircle2,
  Clock,
  Sparkles,
  PartyPopper,
  Loader2,
  AlertTriangle,
  ExternalLink,
} from 'lucide-react';
import { AppLayout } from '@/components/layout/AppLayout';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { useGapAnalysis, useTargetRoles } from '@/hooks/useGapAnalysis';
import type { MilestoneOut } from '@/lib/api/skills';

const FALLBACK_EXPLANATION =
  "Detailed AI insights aren't available right now, but the readiness score and skill breakdown below are accurate and ready to use.";
const FALLBACK_ENCOURAGEMENT =
  'Keep going -- every skill you close on this list moves you closer to your target role.';

/** Sort key for a milestone's `week_range` (e.g. "1-2", "Week 3-4", "5"). Falls
 * back to +Infinity (sorts last) if no leading number can be found, rather
 * than throwing or silently mis-ordering the roadmap. */
function weekRangeSortKey(weekRange: string): number {
  const match = weekRange.match(/\d+/);
  return match ? Number(match[0]) : Number.POSITIVE_INFINITY;
}

function sortedRoadmap(roadmap: MilestoneOut[]): MilestoneOut[] {
  return [...roadmap].sort((a, b) => weekRangeSortKey(a.week_range) - weekRangeSortKey(b.week_range));
}

export default function SkillAnalysis() {
  const { data: profile, isLoading: isProfileLoading } = useTargetRoles();
  const targetRoles = profile?.target_roles ?? [];

  const [selectedJobId, setSelectedJobId] = useState<string>('');
  const gapAnalysis = useGapAnalysis();

  // Auto-select the "current" target role (last entry = most recently added,
  // same convention the backend's resolve_target_job_id() uses) once the
  // profile loads, and run the analysis immediately.
  useEffect(() => {
    if (!selectedJobId && targetRoles.length > 0) {
      const defaultJobId = targetRoles[targetRoles.length - 1];
      setSelectedJobId(defaultJobId);
      gapAnalysis.mutate(defaultJobId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [targetRoles.join('|')]);

  const handleSelectJob = (jobId: string) => {
    setSelectedJobId(jobId);
    gapAnalysis.mutate(jobId);
  };

  const result = gapAnalysis.data;
  const isReady100 = !!result && result.readiness_score >= 100 && result.missing_skills.length === 0;
  const explanationText = result?.explanation?.trim() ? result.explanation : FALLBACK_EXPLANATION;
  const encouragementText = result?.encouragement?.trim() ? result.encouragement : FALLBACK_ENCOURAGEMENT;

  return (
    <AppLayout>
      <div className="space-y-6 md:space-y-8">
        <div>
          <h1 className="page-title">Skill Gap Analysis</h1>
          <p className="page-subtitle">
            Detailed breakdown of your skills versus market requirements
          </p>
        </div>

        {isProfileLoading && (
          <div className="stat-card space-y-3" data-testid="profile-loading">
            <Skeleton className="h-6 w-1/3" />
            <Skeleton className="h-4 w-2/3" />
          </div>
        )}

        {!isProfileLoading && targetRoles.length === 0 && (
          <div className="stat-card">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-accent rounded-lg shrink-0">
                <TrendingUp className="h-5 w-5 text-accent-foreground" />
              </div>
              <div>
                <h2 className="section-title mb-1">Set a target role to get started</h2>
                <p className="text-sm text-muted-foreground">
                  You haven't set a target role yet, so we can't run a skill gap analysis.
                  Head to your profile and add one to see your readiness score and
                  personalized roadmap.
                </p>
                <Link
                  to="/profile/edit"
                  className="inline-flex items-center gap-1 text-sm font-medium text-primary mt-3"
                >
                  Go to Profile <ExternalLink className="h-3.5 w-3.5" />
                </Link>
              </div>
            </div>
          </div>
        )}

        {!isProfileLoading && targetRoles.length > 0 && (
          <div className="stat-card">
            <div className="flex flex-col sm:flex-row sm:items-center gap-3 sm:justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-accent rounded-lg">
                  <TrendingUp className="h-5 w-5 text-accent-foreground" />
                </div>
                <div>
                  <h2 className="section-title mb-0">Target Role</h2>
                  <p className="text-sm text-muted-foreground mt-1">
                    Choose which target role to analyze your skills against
                  </p>
                </div>
              </div>
              <div>
                <label htmlFor="target-job-select" className="sr-only">
                  Target job
                </label>
                <select
                  id="target-job-select"
                  aria-label="Target job"
                  value={selectedJobId}
                  onChange={(e) => handleSelectJob(e.target.value)}
                  className="flex h-10 w-full sm:w-64 items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                >
                  {targetRoles.map((jobId) => (
                    <option key={jobId} value={jobId}>
                      {jobId}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        )}

        {gapAnalysis.isPending && (
          <div className="stat-card" data-testid="gap-analysis-loading">
            <div className="flex items-center gap-3 py-6 justify-center text-muted-foreground">
              <Loader2 className="h-5 w-5 animate-spin" />
              <span className="text-sm font-medium">
                Analyzing your skills against this role... this can take a moment.
              </span>
            </div>
          </div>
        )}

        {gapAnalysis.isError && (
          <div className="stat-card border border-destructive/30">
            <div className="flex items-center gap-3 text-destructive">
              <AlertTriangle className="h-5 w-5 shrink-0" />
              <p className="text-sm font-medium">
                We couldn't run the skill gap analysis. Please try selecting your target role
                again.
              </p>
            </div>
          </div>
        )}

        {result && !gapAnalysis.isPending && (
          <>
            {/* Readiness Score */}
            <div className="stat-card">
              <div className="flex items-center justify-between mb-2">
                <h2 className="section-title mb-0">Readiness Score</h2>
                <span className="text-2xl font-bold text-foreground">
                  {Math.round(result.readiness_score)}%
                </span>
              </div>
              <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary rounded-full"
                  style={{ width: `${Math.min(100, Math.max(0, result.readiness_score))}%` }}
                />
              </div>

              {isReady100 && (
                <div className="flex items-center gap-2 mt-4 text-success">
                  <PartyPopper className="h-5 w-5" />
                  <p className="text-sm font-medium">
                    You're fully ready for this role -- every required skill is covered!
                  </p>
                </div>
              )}
            </div>

            {/* Matched / Missing Skills */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6">
              <div className="stat-card">
                <h2 className="section-title">Matched Skills</h2>
                {result.matched_skills.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    No matched skills yet -- your missing-skills roadmap below shows where to
                    start.
                  </p>
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {result.matched_skills.map((skill) => (
                      <Badge key={skill} variant="secondary" className="gap-1">
                        <CheckCircle2 className="h-3.5 w-3.5" />
                        {skill}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>

              <div className="stat-card">
                <h2 className="section-title">Missing Skills</h2>
                {result.missing_skills.length === 0 ? (
                  <p className="text-sm text-success font-medium">
                    You're covered -- no missing skills for this role.
                  </p>
                ) : (
                  <div className="space-y-3">
                    {result.missing_skills.map((skill) => (
                      <div
                        key={skill.skill_name}
                        className="flex items-center justify-between gap-3 p-3 bg-muted/50 rounded-lg"
                      >
                        <div>
                          <span className="font-medium text-foreground text-sm">
                            {skill.skill_name}
                          </span>
                          <p className="text-xs text-muted-foreground capitalize">
                            {skill.importance} priority
                          </p>
                        </div>
                        <div className="flex items-center gap-1 text-xs text-muted-foreground shrink-0">
                          <Clock className="h-3.5 w-3.5" />
                          {skill.estimated_learning_weeks} wk
                          {skill.estimated_learning_weeks === 1 ? '' : 's'}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* LLM Explanation / Encouragement */}
            <div className="bg-primary/5 border border-primary/20 rounded-lg p-6">
              <div className="flex items-center gap-3 mb-3">
                <Sparkles className="h-5 w-5 text-primary" />
                <h3 className="font-semibold text-foreground">Your Analysis</h3>
              </div>
              <p className="text-foreground">{explanationText}</p>
              <p className="text-sm text-muted-foreground mt-2">{encouragementText}</p>
            </div>

            {/* Roadmap */}
            <div className="stat-card">
              <h2 className="section-title">Your Learning Roadmap</h2>
              {result.roadmap.length === 0 ? (
                <p className="text-sm text-success font-medium">
                  No roadmap needed -- you already meet the requirements for this role.
                </p>
              ) : (
                <div
                  className="space-y-4 max-h-[32rem] overflow-y-auto pr-1"
                  data-testid="roadmap-scroll-container"
                >
                  {sortedRoadmap(result.roadmap).map((milestone, index) => (
                    <div
                      key={`${milestone.week_range}-${milestone.skill_name}-${index}`}
                      className="flex gap-4 border-l-2 border-primary/30 pl-4 py-1"
                    >
                      <div className="w-20 shrink-0 text-xs font-semibold text-primary">
                        Week {milestone.week_range}
                      </div>
                      <div className="flex-1">
                        <p className="font-medium text-foreground text-sm">
                          {milestone.skill_name}
                        </p>
                        <p className="text-xs text-muted-foreground mt-0.5">{milestone.goal}</p>
                        {milestone.course_title && (
                          <a
                            href={milestone.course_url ?? undefined}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center gap-1 text-xs font-medium text-primary mt-1"
                          >
                            {milestone.course_title}
                            <ExternalLink className="h-3 w-3" />
                          </a>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </AppLayout>
  );
}
