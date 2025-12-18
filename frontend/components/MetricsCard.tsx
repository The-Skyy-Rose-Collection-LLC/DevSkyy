/**
 * MetricsCard Component
 * =====================
 * Displays key metrics with trend indicators.
 */

import { ArrowUp, ArrowDown, Minus, type LucideIcon } from 'lucide-react';
import { Card, CardContent } from './ui/card';
import { cn } from '@/lib/utils';

interface MetricsCardProps {
  title: string;
  value: string | number;
  description?: string;
  icon?: LucideIcon;
  trend?: {
    value: number;
    label: string;
  };
  className?: string;
}

export function MetricsCard({
  title,
  value,
  description,
  icon: Icon,
  trend,
  className,
}: MetricsCardProps) {
  const TrendIcon =
    trend?.value !== undefined
      ? trend.value > 0
        ? ArrowUp
        : trend.value < 0
          ? ArrowDown
          : Minus
      : null;

  const trendColor =
    trend?.value !== undefined
      ? trend.value > 0
        ? 'text-green-500'
        : trend.value < 0
          ? 'text-red-500'
          : 'text-gray-500'
      : '';

  return (
    <Card className={cn('', className)}>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
            {title}
          </p>
          {Icon && (
            <Icon className="h-4 w-4 text-gray-500 dark:text-gray-400" />
          )}
        </div>
        <div className="mt-2 flex items-baseline gap-2">
          <p className="text-2xl font-bold">{value}</p>
          {trend && TrendIcon && (
            <span className={cn('flex items-center text-sm', trendColor)}>
              <TrendIcon className="h-3 w-3 mr-0.5" />
              {Math.abs(trend.value)}%
            </span>
          )}
        </div>
        {description && (
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            {description}
          </p>
        )}
        {trend?.label && (
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            {trend.label}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
