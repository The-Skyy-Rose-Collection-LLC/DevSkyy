'use client';

import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

/**
 * Loading skeleton for the dashboard page.
 * Shows placeholder content while data is loading.
 */
export function DashboardSkeleton() {
  return (
    <div className="space-y-6" aria-busy="true" aria-label="Loading dashboard">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Skeleton className="h-8 w-48 bg-gray-800" />
          <Skeleton className="h-4 w-64 mt-2 bg-gray-800" />
        </div>
        <Skeleton className="h-6 w-32 bg-gray-800" />
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i} className="bg-gray-900 border-gray-800">
            <CardHeader className="pb-2">
              <Skeleton className="h-4 w-24 bg-gray-800" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-16 bg-gray-800" />
              <Skeleton className="h-3 w-32 mt-2 bg-gray-800" />
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Main Cards */}
      <div className="grid gap-6 lg:grid-cols-2">
        {Array.from({ length: 2 }).map((_, i) => (
          <Card key={i} className="bg-gray-900 border-gray-800">
            <CardHeader>
              <Skeleton className="h-6 w-40 bg-gray-800" />
              <Skeleton className="h-4 w-56 mt-1 bg-gray-800" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-48 w-full bg-gray-800" />
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Charts */}
      <div className="grid gap-6 lg:grid-cols-2">
        {Array.from({ length: 2 }).map((_, i) => (
          <Card key={i} className="bg-gray-900 border-gray-800">
            <CardHeader>
              <Skeleton className="h-6 w-32 bg-gray-800" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-64 w-full bg-gray-800" />
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

export default DashboardSkeleton;
