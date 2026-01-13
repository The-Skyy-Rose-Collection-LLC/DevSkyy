/**
 * Loading State
 * =============
 * Displays while route segments are loading.
 */

import { Loader2 } from 'lucide-react';

export default function Loading() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <div className="text-center space-y-4">
        <Loader2 className="h-12 w-12 text-brand-primary animate-spin mx-auto" />
        <p className="text-gray-600 dark:text-gray-400 font-medium">
          Loading...
        </p>
      </div>
    </div>
  );
}
