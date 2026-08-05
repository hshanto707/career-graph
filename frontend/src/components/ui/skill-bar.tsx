import { cn } from '@/lib/utils';

interface SkillBarProps {
  skill: string;
  value: number;
  maxValue?: number;
  owned?: boolean;
  showValue?: boolean;
}

export function SkillBar({
  skill,
  value,
  maxValue = 100,
  owned = false,
  showValue = true,
}: SkillBarProps) {
  const percentage = (value / maxValue) * 100;

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-sm">
        <span className={cn(
          'font-medium',
          owned ? 'text-foreground' : 'text-muted-foreground'
        )}>
          {skill}
          {owned && (
            <span className="ml-2 text-xs text-primary">✓ Owned</span>
          )}
        </span>
        {showValue && (
          <span className="text-muted-foreground">{Math.round(value)}%</span>
        )}
      </div>
      <div className="h-2 bg-muted rounded-full overflow-hidden">
        <div
          className={cn(
            'h-full rounded-full transition-all duration-300',
            owned ? 'bg-primary' : 'bg-muted-foreground/30'
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
