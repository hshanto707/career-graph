import { Link } from 'react-router-dom';
import { Mail, GraduationCap, Target, Briefcase, Edit, AlertCircle } from 'lucide-react';
import { AppLayout } from '@/components/layout/AppLayout';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { useAuth } from '@/hooks/useAuth';
import { useProfile } from '@/hooks/useProfile';
import { formatExperienceDateRange } from '@/lib/experienceDates';

export default function Profile() {
  const { user } = useAuth();
  const { data: profile, isLoading, isError, refetch } = useProfile();

  return (
    <AppLayout>
      <div className="space-y-6 md:space-y-8 max-w-4xl">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="page-title">Profile</h1>
            <p className="page-subtitle">Your career profile overview</p>
          </div>
          <Link to="/profile/edit">
            <Button variant="outline" className="gap-2 w-full sm:w-auto">
              <Edit className="h-4 w-4" />
              Edit Profile
            </Button>
          </Link>
        </div>

        {isLoading && (
          <div className="space-y-6" data-testid="profile-loading">
            <div className="stat-card space-y-4">
              <Skeleton className="h-5 w-40" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-2/3" />
            </div>
            <div className="stat-card space-y-4">
              <Skeleton className="h-5 w-32" />
              <Skeleton className="h-4 w-full" />
            </div>
          </div>
        )}

        {!isLoading && isError && (
          <div className="stat-card flex flex-col items-center gap-3 py-10 text-center">
            <AlertCircle className="h-8 w-8 text-destructive" />
            <p className="font-medium text-foreground">Couldn't load your profile.</p>
            <Button variant="outline" onClick={() => refetch()}>
              Try again
            </Button>
          </div>
        )}

        {!isLoading && !isError && profile && (
          <>
            {/* Basic Info */}
            <div className="stat-card">
              <h2 className="section-title">Basic Information</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-accent rounded-lg">
                      <GraduationCap className="h-5 w-5 text-accent-foreground" />
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Name</p>
                      <p className="font-medium text-foreground">{user?.name ?? '—'}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-accent rounded-lg">
                      <Mail className="h-5 w-5 text-accent-foreground" />
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Email</p>
                      <p className="font-medium text-foreground">{user?.email ?? '—'}</p>
                    </div>
                  </div>
                </div>
                <div className="space-y-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Major</p>
                    <p className="font-medium text-foreground">{profile.major || 'Not set'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Expected Graduation</p>
                    <p className="font-medium text-foreground">
                      {profile.graduation_year ?? 'Not set'}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Current Skills */}
            <div className="stat-card">
              <h2 className="section-title">Current Skills</h2>
              {profile.skills.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  You haven't added any skills yet. Add some in Edit Profile so we can
                  match you with jobs and courses.
                </p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {profile.skills.map((skill) => (
                    <span key={skill.name} className="skill-tag" title={`Proficiency ${skill.proficiency}/10 · ${skill.years}y`}>
                      {skill.name}
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Target Roles */}
            <div className="stat-card">
              <div className="flex items-center gap-2 mb-4">
                <Target className="h-5 w-5 text-primary" />
                <h2 className="section-title mb-0">Target Job Roles</h2>
              </div>
              {profile.target_roles.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No target roles set yet. Add one in Edit Profile to unlock personalized
                  recommendations.
                </p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {profile.target_roles.map((role) => (
                    <span
                      key={role}
                      className="inline-flex items-center px-4 py-2 rounded-lg bg-muted text-sm font-medium text-foreground"
                    >
                      {role}
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Experience */}
            <div className="stat-card">
              <div className="flex items-center gap-2 mb-4">
                <Briefcase className="h-5 w-5 text-primary" />
                <h2 className="section-title mb-0">Experience</h2>
              </div>
              {profile.experience.length === 0 ? (
                <p className="text-sm text-muted-foreground">No experience added yet.</p>
              ) : (
                <div className="space-y-6">
                  {profile.experience.map((exp, index) => (
                    <div key={index} className="border-l-2 border-primary pl-4 py-1">
                      <h3 className="font-medium text-foreground">{exp.title}</h3>
                      <p className="text-sm text-muted-foreground">
                        {exp.company} · {formatExperienceDateRange(exp)}
                      </p>
                      {exp.description && (
                        <p className="text-sm text-muted-foreground mt-2">{exp.description}</p>
                      )}
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
