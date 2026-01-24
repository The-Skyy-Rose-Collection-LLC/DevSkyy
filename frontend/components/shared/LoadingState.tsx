'use client';

import { Loader2 } from 'lucide-react';

interface LoadingStateProps {
  /** Loading message */
  message?: string;
  /** Size variant */
  size?: 'sm' | 'md' | 'lg';
  /** Full page centered */
  fullPage?: boolean;
}

const sizeClasses = {
  sm: 'h-4 w-4',
  md: 'h-8 w-8',
  lg: 'h-12 w-12',
};

/**
 * Reusable loading state component.
 *
 * @example
 * <LoadingState message="Loading data..." size="lg" fullPage />
 */
export function LoadingState({
  message = 'Loading...',
  size = 'md',
  fullPage = false,
}: LoadingStateProps) {
  const content = (
    <div className="flex flex-col items-center justify-center gap-3">
      <Loader2 className={`${sizeClasses[size]} animate-spin text-rose-500`} />
      {message && (
        <p className="text-sm text-gray-400" aria-live="polite">
          {message}
        </p>
      )}
    </div>
  );

  if (fullPage) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        {content}
      </div>
    );
  }

  return content;
}

export default LoadingState;
