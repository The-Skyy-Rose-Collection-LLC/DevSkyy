'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface StatsCardProps {
  /** Card title */
  title: string;
  /** Main value to display */
  value: string | number;
  /** Description below the value */
  description: string;
  /** Icon component */
  icon: React.ComponentType<{ className?: string }>;
  /** Trend text */
  trend?: string;
  /** Trend direction for coloring */
  trendDirection?: 'up' | 'down' | 'neutral';
  /** Optional className */
  className?: string;
}

/**
 * Dashboard stats card with icon, value, and trend indicator.
 *
 * @example
 * <StatsCard
 *   title="Total Revenue"
 *   value="$12,345"
 *   description="This month"
 *   icon={DollarSign}
 *   trend="+12% from last month"
 *   trendDirection="up"
 * />
 */
export function StatsCard({
  title,
  value,
  description,
  icon: Icon,
  trend,
  trendDirection = 'up',
  className = '',
}: StatsCardProps) {
  const trendColors = {
    up: 'text-green-400',
    down: 'text-red-400',
    neutral: 'text-gray-400',
  };

  const TrendIcon = {
    up: TrendingUp,
    down: TrendingDown,
    neutral: Minus,
  }[trendDirection];

  return (
    <Card className={`bg-gray-900 border-gray-800 ${className}`}>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-gray-400">
          {title}
        </CardTitle>
        <Icon className="h-4 w-4 text-rose-400" aria-hidden="true" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold text-white">{value}</div>
        <p className="text-xs text-gray-500">{description}</p>
        {trend && (
          <div
            className={`mt-2 flex items-center text-xs ${trendColors[trendDirection]}`}
          >
            <TrendIcon className="mr-1 h-3 w-3" aria-hidden="true" />
            <span>{trend}</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default StatsCard;
