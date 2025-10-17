/**
 * Loading spinner component.
 */

import clsx from 'clsx';

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
}

export function Spinner({ size = 'md', className }: SpinnerProps) {
  return (
    <div
      className={clsx(
        'animate-spin rounded-full border-t-2 border-b-2 border-primary-500',
        {
          'h-4 w-4': size === 'sm',
          'h-8 w-8': size === 'md',
          'h-12 w-12': size === 'lg',
          'h-16 w-16': size === 'xl',
        },
        className
      )}
    />
  );
}

interface LoadingProps {
  text?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

export function Loading({ text = 'Loading...', size = 'lg' }: LoadingProps) {
  return (
    <div className="flex flex-col items-center justify-center p-8">
      <Spinner size={size} className="mb-4" />
      <p className="text-slate-400 text-lg">{text}</p>
    </div>
  );
}
