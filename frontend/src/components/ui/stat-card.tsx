import { ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: ReactNode;
  trend?: 'up' | 'down' | 'neutral';
  className?: string;
}

export function StatCard({
  title,
  value,
  subtitle,
  icon,
  className,
}: StatCardProps) {
  return (
    <div className={cn('stat-card', className)}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="stat-label truncate">{title}</p>
          <p className="stat-value mt-1.5 md:mt-2">{value}</p>
          {subtitle && (
            <p className="text-xs md:text-sm text-muted-foreground mt-1 line-clamp-2">{subtitle}</p>
          )}
        </div>
        {icon && (
          <div className="p-1.5 md:p-2 bg-accent rounded-lg text-accent-foreground shrink-0">
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}
