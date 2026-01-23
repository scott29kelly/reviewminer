import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import { LucideIcon } from 'lucide-react';

interface StatsCardProps {
  title: string;
  value: string | number;
  description?: string;
  icon?: LucideIcon;
  trend?: {
    value: number;
    label: string;
  };
  className?: string;
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'danger';
}

const variantStyles = {
  default: {
    icon: 'bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400',
    accent: 'from-zinc-500/10',
  },
  primary: {
    icon: 'bg-indigo-100 dark:bg-indigo-500/20 text-indigo-600 dark:text-indigo-400',
    accent: 'from-indigo-500/10',
  },
  success: {
    icon: 'bg-emerald-100 dark:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400',
    accent: 'from-emerald-500/10',
  },
  warning: {
    icon: 'bg-amber-100 dark:bg-amber-500/20 text-amber-600 dark:text-amber-400',
    accent: 'from-amber-500/10',
  },
  danger: {
    icon: 'bg-rose-100 dark:bg-rose-500/20 text-rose-600 dark:text-rose-400',
    accent: 'from-rose-500/10',
  },
};

export function StatsCard({
  title,
  value,
  description,
  icon: Icon,
  trend,
  className,
  variant = 'default',
}: StatsCardProps) {
  const styles = variantStyles[variant];

  return (
    <Card className={cn(
      'relative overflow-hidden transition-all duration-200 hover:shadow-lg hover:shadow-black/5 dark:hover:shadow-black/20',
      'border-border/50 bg-card',
      className
    )}>
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div className="space-y-3">
            <p className="text-sm font-medium text-muted-foreground">
              {title}
            </p>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold tracking-tight">{value}</span>
              {trend && (
                <span
                  className={cn(
                    'inline-flex items-center text-xs font-semibold rounded-full px-2 py-0.5',
                    trend.value >= 0 
                      ? 'text-emerald-600 dark:text-emerald-400 bg-emerald-100 dark:bg-emerald-500/20' 
                      : 'text-rose-600 dark:text-rose-400 bg-rose-100 dark:bg-rose-500/20'
                  )}
                >
                  {trend.value >= 0 ? '+' : ''}{trend.value}%
                </span>
              )}
            </div>
            {description && (
              <p className="text-sm text-muted-foreground">{description}</p>
            )}
          </div>
          {Icon && (
            <div className={cn(
              'flex h-12 w-12 items-center justify-center rounded-xl',
              styles.icon
            )}>
              <Icon className="h-6 w-6" />
            </div>
          )}
        </div>
      </CardContent>
      {/* Subtle gradient accent */}
      <div className={cn(
        'absolute inset-0 bg-gradient-to-br to-transparent pointer-events-none opacity-50',
        styles.accent
      )} />
    </Card>
  );
}
