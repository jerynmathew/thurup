/**
 * Reusable Input component.
 */

import { InputHTMLAttributes, forwardRef } from 'react';
import clsx from 'clsx';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  fullWidth?: boolean;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, fullWidth = false, className, ...props }, ref) => {
    return (
      <div className={clsx('flex flex-col gap-2', { 'w-full': fullWidth })}>
        {label && (
          <label className="block text-sm font-medium text-slate-300">
            {label}
          </label>
        )}
        <input
          ref={ref}
          className={clsx(
            'px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400',
            'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            { 'border-red-500 focus:ring-red-500': error },
            className
          )}
          {...props}
        />
        {error && <span className="text-sm text-red-400">{error}</span>}
      </div>
    );
  }
);

Input.displayName = 'Input';
