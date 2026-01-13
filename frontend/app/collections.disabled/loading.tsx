/**
 * Collections Loading State
 * =========================
 * Loading placeholder for collection pages.
 */

import { Loader2 } from 'lucide-react';

export default function CollectionLoading() {
  return (
    <div className="min-h-screen bg-white dark:bg-gray-950">
      {/* Hero Section Skeleton */}
      <div className="h-[600px] bg-gray-100 dark:bg-gray-800 animate-pulse" />

      {/* Products Section */}
      <div className="max-w-7xl mx-auto px-4 py-16">
        <div className="flex items-center justify-center gap-4 mb-8">
          <Loader2 className="h-8 w-8 text-brand-primary animate-spin" />
          <p className="text-lg text-gray-600 dark:text-gray-400">
            Loading collection...
          </p>
        </div>

        {/* Product Grid Skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {Array.from({ length: 12 }).map((_, i) => (
            <div key={i} className="space-y-4">
              <div className="aspect-square bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse" />
              <div className="space-y-2">
                <div className="h-4 bg-gray-100 dark:bg-gray-800 rounded animate-pulse" />
                <div className="h-4 w-2/3 bg-gray-100 dark:bg-gray-800 rounded animate-pulse" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
