/**
 * Error Boundary
 * ==============
 * Handles errors at the route level with recovery option.
 */

'use client';

import { useEffect } from 'react';
import { AlertCircle } from 'lucide-react';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log error to monitoring service (Sentry, etc.)
    console.error('Route error:', error);
  }, [error]);

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <div className="max-w-md w-full text-center space-y-6">
        <div className="flex justify-center">
          <div className="rounded-full bg-red-100 dark:bg-red-900/20 p-4">
            <AlertCircle className="h-12 w-12 text-red-600 dark:text-red-400" />
          </div>
        </div>

        <div className="space-y-2">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-50">
            Something went wrong!
          </h2>
          <p className="text-gray-600 dark:text-gray-400">
            {error.message || 'An unexpected error occurred'}
          </p>
          {error.digest && (
            <p className="text-xs text-gray-500 font-mono">
              Error ID: {error.digest}
            </p>
          )}
        </div>

        <button
          onClick={reset}
          className="w-full px-6 py-3 bg-brand-primary text-white rounded-lg font-medium hover:bg-brand-primary/90 transition-colors"
        >
          Try again
        </button>
      </div>
    </div>
  );
}
