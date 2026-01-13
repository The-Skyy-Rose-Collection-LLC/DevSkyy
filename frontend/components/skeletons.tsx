/**
 * Skeleton Components
 * ===================
 * Loading placeholders for streaming UI.
 */

import { Card, CardContent, CardHeader } from '@/components/ui';

export function MetricsCardsSkeleton() {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <div
          key={i}
          className="h-32 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse"
        />
      ))}
    </div>
  );
}

export function ChartSkeleton({ className = '' }: { className?: string }) {
  return (
    <Card className={className}>
      <CardHeader>
        <div className="h-6 w-32 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
      </CardHeader>
      <CardContent>
        <div className="h-[250px] bg-gray-100 dark:bg-gray-800 rounded animate-pulse" />
      </CardContent>
    </Card>
  );
}

export function AgentsGridSkeleton() {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: 6 }).map((_, i) => (
        <div
          key={i}
          className="h-[300px] bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse"
        />
      ))}
    </div>
  );
}

export function DashboardSkeleton() {
  return (
    <div className="space-y-8">
      {/* Header Skeleton */}
      <div className="space-y-2">
        <div className="h-8 w-48 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
        <div className="h-4 w-96 bg-gray-100 dark:bg-gray-800 rounded animate-pulse" />
      </div>

      {/* Metrics Cards */}
      <MetricsCardsSkeleton />

      {/* Charts */}
      <div className="grid gap-4 lg:grid-cols-3">
        <ChartSkeleton className="lg:col-span-2" />
        <ChartSkeleton />
      </div>

      {/* Agents Grid */}
      <AgentsGridSkeleton />
    </div>
  );
}

export function ProductGridSkeleton() {
  return (
    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: 9 }).map((_, i) => (
        <div key={i} className="space-y-4">
          <div className="aspect-square bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse" />
          <div className="space-y-2">
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
            <div className="h-4 w-2/3 bg-gray-100 dark:bg-gray-800 rounded animate-pulse" />
          </div>
        </div>
      ))}
    </div>
  );
}
