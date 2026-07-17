import { MapPin, Building2, Clock } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Job } from '@/lib/mockData';

interface JobCardProps {
  job: Job;
  onClick?: () => void;
}

export function JobCard({ job, onClick }: JobCardProps) {
  const getMatchColor = (percentage: number) => {
    if (percentage >= 75) return 'match-score-high';
    if (percentage >= 50) return 'match-score-medium';
    return 'match-score-low';
  };

  return (
    <div
      onClick={onClick}
      className="stat-card cursor-pointer hover:border-primary/50 transition-colors"
    >
      <div className="flex items-start justify-between gap-3 md:gap-4">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-foreground text-sm md:text-base truncate">{job.title}</h3>
          <div className="flex flex-wrap items-center gap-2 md:gap-3 mt-1.5 md:mt-2 text-xs md:text-sm text-muted-foreground">
            <span className="flex items-center gap-1">
              <Building2 className="h-3.5 w-3.5 md:h-4 md:w-4 shrink-0" />
              <span className="truncate">{job.company}</span>
            </span>
            <span className="flex items-center gap-1">
              <MapPin className="h-3.5 w-3.5 md:h-4 md:w-4 shrink-0" />
              <span className="truncate">{job.location}</span>
            </span>
          </div>
          <div className="flex items-center gap-1.5 mt-2 md:mt-3">
            <Clock className="h-3 w-3 md:h-3.5 md:w-3.5 text-muted-foreground shrink-0" />
            <span className="text-xs text-muted-foreground">{job.type}</span>
          </div>
          <div className="flex flex-wrap gap-1 md:gap-1.5 mt-2 md:mt-3">
            {job.requiredSkills.slice(0, 3).map((skill) => (
              <span key={skill} className="skill-tag text-xs">
                {skill}
              </span>
            ))}
            {job.requiredSkills.length > 3 && (
              <span className="text-xs text-muted-foreground">
                +{job.requiredSkills.length - 3} more
              </span>
            )}
          </div>
        </div>
        <div className={cn('match-score shrink-0', getMatchColor(job.matchPercentage))}>
          {job.matchPercentage}%
        </div>
      </div>
    </div>
  );
}
