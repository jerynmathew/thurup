/**
 * Reusable Select component.
 */

import { SelectHTMLAttributes, ReactNode, forwardRef } from 'react';
import clsx from 'clsx';

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  fullWidth?: boolean;
  children: ReactNode;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, error, fullWidth = false, className, children, ...props }, ref) => {
    return (
      <div className={clsx('flex flex-col gap-2', { 'w-full': fullWidth })}>
        {label && (
          <label className="block text-sm font-medium text-slate-300">
            {label}
          </label>
        )}
        <select
          ref={ref}
          className={clsx(
            'px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white',
            'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            { 'border-red-500 focus:ring-red-500': error },
            className
          )}
          {...props}
        >
          {children}
        </select>
        {error && <span className="text-sm text-red-400">{error}</span>}
      </div>
    );
  }
);

Select.displayName = 'Select';
