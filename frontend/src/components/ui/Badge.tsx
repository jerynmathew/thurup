/**
 * Badge component for displaying status and labels.
 */

import { ReactNode } from 'react';
import clsx from 'clsx';

interface BadgeProps {
  children: ReactNode;
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'danger' | 'info';
  size?: 'sm' | 'md';
  className?: string;
}

export function Badge({ children, variant = 'default', size = 'md', className }: BadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center font-medium rounded-full',
        {
          // Variants
          'bg-slate-700 text-slate-200': variant === 'default',
          'bg-primary-500/20 text-primary-300 border border-primary-500/50': variant === 'primary',
          'bg-green-500/20 text-green-300 border border-green-500/50': variant === 'success',
          'bg-yellow-500/20 text-yellow-300 border border-yellow-500/50': variant === 'warning',
          'bg-red-500/20 text-red-300 border border-red-500/50': variant === 'danger',
          'bg-blue-500/20 text-blue-300 border border-blue-500/50': variant === 'info',

          // Sizes
          'px-2 py-0.5 text-xs': size === 'sm',
          'px-3 py-1 text-sm': size === 'md',
        },
        className
      )}
    >
      {children}
    </span>
  );
}
