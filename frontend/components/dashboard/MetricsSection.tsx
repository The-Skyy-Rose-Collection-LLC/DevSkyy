/**
 * Metrics Section
 * ===============
 * Async server component that fetches and displays metrics cards.
 */

import { Activity, Zap, DollarSign, CheckCircle } from 'lucide-react';
import { MetricsCard } from '@/components';
import { formatNumber, formatPercent, formatCurrency, formatDuration } from '@/lib/utils';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function getMetrics() {
  try {
    const res = await fetch(`${API_URL}/api/v1/metrics`, {
      next: { revalidate: 60 }, // Cache for 60 seconds
      headers: { 'Content-Type': 'application/json' },
    });

    if (!res.ok) return null;
    return res.json();
  } catch (error) {
    console.error('Failed to fetch metrics:', error);
    return null;
  }
}

export async function MetricsSection() {
  const metrics = await getMetrics();

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <MetricsCard
        title="Total Tasks"
        value={formatNumber(metrics?.totalTasks || 0)}
        description={`${formatNumber(metrics?.tasksToday || 0)} today`}
        icon={Activity}
        trend={{ value: 12, label: 'vs last period' }}
      />
      <MetricsCard
        title="Success Rate"
        value={formatPercent(metrics?.successRate || 0)}
        icon={CheckCircle}
        trend={{ value: 3, label: 'vs last period' }}
      />
      <MetricsCard
        title="Avg Latency"
        value={formatDuration(metrics?.avgLatencyMs || 0)}
        icon={Zap}
        trend={{ value: -8, label: 'faster' }}
      />
      <MetricsCard
        title="Total Cost"
        value={formatCurrency(metrics?.totalCostUsd || 0)}
        description={`${formatCurrency(metrics?.costToday || 0)} today`}
        icon={DollarSign}
      />
    </div>
  );
}
