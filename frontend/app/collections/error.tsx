/**
 * Collections Error Boundary
 * ==========================
 * Error handling for collection pages.
 */

'use client';

import { useEffect } from 'react';
import { AlertCircle, Home } from 'lucide-react';
import Link from 'next/link';

export default function CollectionError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Collection error:', error);
  }, [error]);

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gray-50 dark:bg-gray-950">
      <div className="max-w-md w-full text-center space-y-6">
        <div className="flex justify-center">
          <div className="rounded-full bg-red-100 dark:bg-red-900/20 p-4">
            <AlertCircle className="h-12 w-12 text-red-600 dark:text-red-400" />
          </div>
        </div>

        <div className="space-y-2">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-50">
            Failed to Load Collection
          </h2>
          <p className="text-gray-600 dark:text-gray-400">
            {error.message || 'An unexpected error occurred while loading products'}
          </p>
        </div>

        <div className="flex gap-4 justify-center">
          <button
            onClick={reset}
            className="px-6 py-3 bg-brand-primary text-white rounded-lg font-medium hover:bg-brand-primary/90 transition-colors"
          >
            Try Again
          </button>
          <Link
            href="/"
            className="inline-flex items-center gap-2 px-6 py-3 border border-gray-300 dark:border-gray-700 text-gray-900 dark:text-gray-50 rounded-lg font-medium hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
          >
            <Home className="h-4 w-4" />
            Go Home
          </Link>
        </div>
      </div>
    </div>
  );
}
