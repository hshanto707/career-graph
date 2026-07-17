import { TrendingUp, Target, AlertTriangle, BarChart3, CheckCircle2, Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';
import { AppLayout } from '@/components/layout/AppLayout';
import { StatCard } from '@/components/ui/stat-card';
import { SkillBar } from '@/components/ui/skill-bar';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { useDashboard } from '@/hooks/useDashboard';

function DashboardSkeleton() {
  return (
    <div className="space-y-6 md:space-y-8" data-testid="dashboard-skeleton">
      <div>
        <h1 className="page-title">Dashboard</h1>
        <p className="page-subtitle">Your career readiness at a glance</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
        {[0, 1, 2].map((i) => (
          <div key={i} className="stat-card space-y-3">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-8 w-20" />
            <Skeleton className="h-3 w-40" />
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 md:gap-6">
        <div className="stat-card space-y-4">
          <Skeleton className="h-5 w-48" />
          {[0, 1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-6 w-full" />
          ))}
        </div>
        <div className="stat-card space-y-4">
          <Skeleton className="h-5 w-48" />
          {[0, 1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-6 w-full" />
          ))}
        </div>
      </div>
    </div>
  );
}

function DashboardError({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="space-y-6 md:space-y-8">
      <div>
        <h1 className="page-title">Dashboard</h1>
        <p className="page-subtitle">Your career readiness at a glance</p>
      </div>
      <div className="stat-card flex flex-col items-center text-center gap-3 py-12">
        <AlertTriangle className="h-8 w-8 text-destructive" />
        <p className="font-medium text-foreground">Couldn't load your dashboard</p>
        <p className="text-sm text-muted-foreground max-w-sm">
          Something went wrong while fetching your career readiness data. Please try again.
        </p>
        <Button onClick={onRetry}>Retry</Button>
      </div>
    </div>
  );
}

function EmptyProfileState() {
  return (
    <div className="space-y-6 md:space-y-8">
      <div>
        <h1 className="page-title">Dashboard</h1>
        <p className="page-subtitle">Your career readiness at a glance</p>
      </div>
      <div className="stat-card flex flex-col items-center text-center gap-3 py-12">
        <Sparkles className="h-8 w-8 text-primary" />
        <p className="font-medium text-foreground">Complete your profile to see your dashboard</p>
        <p className="text-sm text-muted-foreground max-w-sm">
          Add your skills and a target role so we can calculate your job readiness score and
          match you against real market demand.
        </p>
        <Button asChild>
          <Link to="/profile/edit">Complete Profile</Link>
        </Button>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const { data, isLoading, isError, refetch } = useDashboard();

  if (isLoading) {
    return (
      <AppLayout>
        <DashboardSkeleton />
      </AppLayout>
    );
  }

  if (isError || !data) {
    return (
      <AppLayout>
        <DashboardError onRetry={() => refetch()} />
      </AppLayout>
    );
  }

  const {
    job_readiness_score,
    skills_matched,
    total_required_skills,
    missing_high_demand_skills,
    market_demand,
  } = data;

  const hasProfileData = total_required_skills > 0 || skills_matched > 0 || market_demand.length > 0;

  if (!hasProfileData) {
    return (
      <AppLayout>
        <EmptyProfileState />
      </AppLayout>
    );
  }

  const isMissing = (skillName: string) => missing_high_demand_skills.includes(skillName);
  const ownedSkills = market_demand.filter((s) => !isMissing(s.skill_name));
  const missingSkills = market_demand.filter((s) => isMissing(s.skill_name));
  const hasNoMissingSkills = missing_high_demand_skills.length === 0;

  return (
    <AppLayout>
      <div className="space-y-6 md:space-y-8">
        {/* Page Header */}
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">
            Your career readiness at a glance
          </p>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
          <StatCard
            title="Job Readiness Score"
            value={`${job_readiness_score}%`}
            subtitle="Based on market demand"
            icon={<Target className="h-5 w-5" />}
          />
          <StatCard
            title="Skills Matched"
            value={`${skills_matched} / ${total_required_skills}`}
            subtitle="For target roles"
            icon={<TrendingUp className="h-5 w-5" />}
          />
          <StatCard
            title="Missing High-Demand Skills"
            value={missing_high_demand_skills.length}
            subtitle={
              hasNoMissingSkills
                ? "You're covered on high-demand skills"
                : missing_high_demand_skills.join(', ')
            }
            icon={
              hasNoMissingSkills ? (
                <CheckCircle2 className="h-5 w-5" />
              ) : (
                <AlertTriangle className="h-5 w-5" />
              )
            }
            className="sm:col-span-2 lg:col-span-1"
          />
        </div>

        {/* Skill Gap Visualization */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 md:gap-6">
          <div className="stat-card">
            <div className="flex items-center gap-2 mb-4 md:mb-6">
              <BarChart3 className="h-5 w-5 text-primary shrink-0" />
              <h2 className="section-title mb-0">Skill Gap Analysis</h2>
            </div>
            <p className="text-sm text-muted-foreground mb-6">
              Your skills compared to market requirements
            </p>

            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-medium text-foreground mb-3">
                  Skills You Have
                </h3>
                <div className="space-y-3">
                  {ownedSkills.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No matched skills yet.</p>
                  ) : (
                    ownedSkills.slice(0, 5).map((skill) => (
                      <SkillBar
                        key={skill.skill_name}
                        skill={skill.skill_name}
                        value={skill.demand_score}
                        owned={true}
                      />
                    ))
                  )}
                </div>
              </div>

              <div className="border-t border-border pt-4">
                <h3 className="text-sm font-medium text-foreground mb-3">
                  Skills to Acquire
                </h3>
                <div className="space-y-3">
                  {missingSkills.length === 0 ? (
                    <p className="text-sm text-muted-foreground">
                      You're covered — no high-demand skills missing.
                    </p>
                  ) : (
                    missingSkills.slice(0, 4).map((skill) => (
                      <SkillBar
                        key={skill.skill_name}
                        skill={skill.skill_name}
                        value={skill.demand_score}
                        owned={false}
                      />
                    ))
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Market Skill Demand */}
          <div className="stat-card">
            <h2 className="section-title">Current Market Skill Demand</h2>
            <p className="text-sm text-muted-foreground mb-6">
              Top skills ranked by employer demand
            </p>

            <div className="space-y-3">
              {market_demand.length === 0 ? (
                <p className="text-sm text-muted-foreground">No market demand data available yet.</p>
              ) : (
                market_demand.map((item, index) => {
                  const owned = !isMissing(item.skill_name);
                  return (
                    <div
                      key={item.skill_name}
                      className="flex items-center justify-between py-2 border-b border-border last:border-0"
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-sm font-medium text-muted-foreground w-6">
                          {index + 1}.
                        </span>
                        <span className="text-sm font-medium text-foreground">
                          {item.skill_name}
                        </span>
                        {owned && (
                          <span className="text-xs text-primary font-medium">
                            ✓
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="w-24 h-1.5 bg-muted rounded-full overflow-hidden">
                          <div
                            className="h-full bg-primary rounded-full"
                            style={{ width: `${item.demand_score}%` }}
                          />
                        </div>
                        <span className="text-sm text-muted-foreground w-8">
                          {item.demand_score}%
                        </span>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
