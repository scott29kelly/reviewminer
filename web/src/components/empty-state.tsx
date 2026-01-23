'use client';

import { motion } from 'framer-motion';
import { LucideIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import Link from 'next/link';

interface EmptyStateAction {
  label: string;
  href?: string;
  onClick?: () => void;
  variant?: 'default' | 'outline' | 'secondary';
  icon?: LucideIcon;
}

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  actions?: EmptyStateAction[];
  className?: string;
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  actions,
  className = '',
}: EmptyStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`flex flex-col items-center justify-center py-16 px-4 text-center ${className}`}
    >
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.1, duration: 0.3 }}
        className="relative mb-6"
      >
        <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/20 to-violet-500/20 rounded-full blur-2xl scale-150" />
        <div className="relative rounded-2xl bg-gradient-to-br from-indigo-500/10 to-violet-500/10 p-6 border border-indigo-500/10">
          <Icon className="h-10 w-10 text-indigo-500 dark:text-indigo-400" />
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 5 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.3 }}
        className="space-y-2 max-w-sm"
      >
        <h3 className="text-xl font-semibold tracking-tight">{title}</h3>
        <p className="text-muted-foreground text-sm leading-relaxed">{description}</p>
      </motion.div>

      {actions && actions.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 5 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.3 }}
          className="flex flex-wrap items-center justify-center gap-3 mt-8"
        >
          {actions.map((action, index) => {
            const ActionIcon = action.icon;
            const isPrimary = action.variant === 'default' || (!action.variant && index === 0);
            
            const buttonContent = (
              <>
                {ActionIcon && <ActionIcon className="mr-2 h-4 w-4" />}
                {action.label}
              </>
            );

            const buttonClassName = isPrimary
              ? 'rounded-xl bg-gradient-to-r from-indigo-500 to-violet-500 hover:from-indigo-600 hover:to-violet-600 text-white shadow-lg shadow-indigo-500/25'
              : 'rounded-xl border-border/50';

            if (action.href) {
              return (
                <Button
                  key={index}
                  variant={isPrimary ? 'default' : (action.variant || 'outline')}
                  className={buttonClassName}
                  asChild
                >
                  <Link href={action.href}>{buttonContent}</Link>
                </Button>
              );
            }

            return (
              <Button
                key={index}
                variant={isPrimary ? 'default' : (action.variant || 'outline')}
                className={buttonClassName}
                onClick={action.onClick}
              >
                {buttonContent}
              </Button>
            );
          })}
        </motion.div>
      )}
    </motion.div>
  );
}

// Compact variant for inline/card empty states
export function EmptyStateCompact({
  icon: Icon,
  message,
  action,
}: {
  icon: LucideIcon;
  message: string;
  action?: { label: string; onClick?: () => void; href?: string };
}) {
  return (
    <div className="flex flex-col items-center justify-center py-10 px-4 text-center">
      <div className="rounded-xl bg-gradient-to-br from-indigo-500/10 to-violet-500/10 p-4 mb-4">
        <Icon className="h-6 w-6 text-indigo-500 dark:text-indigo-400" />
      </div>
      <p className="text-sm text-muted-foreground mb-4">{message}</p>
      {action && (
        action.href ? (
          <Button variant="outline" size="sm" className="rounded-xl border-border/50" asChild>
            <Link href={action.href}>{action.label}</Link>
          </Button>
        ) : (
          <Button variant="outline" size="sm" className="rounded-xl border-border/50" onClick={action.onClick}>
            {action.label}
          </Button>
        )
      )}
    </div>
  );
}
