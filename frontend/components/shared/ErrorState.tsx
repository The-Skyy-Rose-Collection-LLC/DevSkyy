'use client';

import { AlertCircle, RefreshCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface ErrorStateProps {
  /** Error title */
  title?: string;
  /** Error message */
  message: string;
  /** Retry callback */
  onRetry?: () => void;
  /** Full page centered */
  fullPage?: boolean;
}

/**
 * Reusable error state component with optional retry.
 *
 * @example
 * <ErrorState
 *   title="Failed to load data"
 *   message={error.message}
 *   onRetry={refetch}
 *   fullPage
 * />
 */
export function ErrorState({
  title = 'Something went wrong',
  message,
  onRetry,
  fullPage = false,
}: ErrorStateProps) {
  const content = (
    <div className="flex flex-col items-center justify-center gap-4 text-center">
      <div className="rounded-full bg-red-500/10 p-3">
        <AlertCircle className="h-8 w-8 text-red-500" />
      </div>
      <div>
        <h3 className="text-lg font-semibold text-white">{title}</h3>
        <p className="mt-1 text-sm text-gray-400">{message}</p>
      </div>
      {onRetry && (
        <Button
          onClick={onRetry}
          variant="outline"
          className="border-gray-700 text-gray-300 hover:bg-gray-800"
        >
          <RefreshCcw className="mr-2 h-4 w-4" />
          Try Again
        </Button>
      )}
    </div>
  );

  if (fullPage) {
    return (
      <div className="flex min-h-[400px] items-center justify-center py-12">
        {content}
      </div>
    );
  }

  return content;
}

export default ErrorState;
