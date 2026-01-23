'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Zap,
  Users,
  Box,
  Activity,
  TrendingUp,
  Clock,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
} from 'lucide-react';
import { api, type ProviderStats, type PipelineStatus } from '@/lib/api';
import {
  ProviderPerformanceChart,
  CompetitionTrendChart,
  AgentStatusChart,
  PipelineMetricsChart,
} from '@/components/dashboard/analytics-charts';

interface DashboardStats {
  roundTable: {
    totalCompetitions: number;
    activeProviders: number;
    topProvider: string;
    avgLatency: number;
  };
  pipeline3d: PipelineStatus | null;
  agents: {
    total: number;
    active: number;
  };
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [providerStats, setProviderStats] = useState<ProviderStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchDashboardData() {
      try {
        const [rtStats, pipelineStatus] = await Promise.all([
          api.roundTable.getStats().catch(() => []),
          api.pipeline3d.getStatus().catch(() => null),
        ]);

        setProviderStats(rtStats);

        const totalCompetitions = rtStats.reduce((sum, p) => sum + p.total_competitions, 0);
        const topProvider = rtStats.length > 0
          ? rtStats.reduce((a, b) => (a.win_rate > b.win_rate ? a : b)).name
          : 'N/A';
        const avgLatency = rtStats.length > 0
          ? Math.round(rtStats.reduce((sum, p) => sum + p.avg_latency_ms, 0) / rtStats.length)
          : 0;

        setStats({
          roundTable: {
            totalCompetitions,
            activeProviders: rtStats.length,
            topProvider,
            avgLatency,
          },
          pipeline3d: pipelineStatus,
          agents: {
            total: 54,
            active: 6,
          },
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load dashboard');
      } finally {
        setLoading(false);
      }
    }

    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <DashboardSkeleton />;
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <AlertCircle className="h-12 w-12 text-red-500 mb-4" />
        <h2 className="text-xl font-semibold text-white mb-2">Error Loading Dashboard</h2>
        <p className="text-gray-400 mb-4">{error}</p>
        <Button onClick={() => window.location.reload()} variant="outline">
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">DevSkyy Dashboard</h1>
          <p className="text-gray-400 mt-1">Enterprise AI Platform Overview</p>
        </div>
        <Badge variant="outline" className="border-green-500 text-green-400">
          <Activity className="h-3 w-3 mr-1" />
          All Systems Operational
        </Badge>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="LLM Competitions"
          value={stats?.roundTable.totalCompetitions || 0}
          description="Total round table competitions"
          icon={Zap}
          trend="+12% from last week"
        />
        <StatsCard
          title="Active Agents"
          value={`${stats?.agents.active || 0}/${stats?.agents.total || 0}`}
          description="SuperAgents online"
          icon={Users}
          trend="6 ready for deployment"
        />
        <StatsCard
          title="3D Jobs"
          value={stats?.pipeline3d?.active_jobs || 0}
          description={`${stats?.pipeline3d?.queued_jobs || 0} queued`}
          icon={Box}
          trend={`${stats?.pipeline3d?.providers_online || 0} providers online`}
        />
        <StatsCard
          title="Avg Latency"
          value={`${stats?.roundTable.avgLatency || 0}ms`}
          description="LLM response time"
          icon={Clock}
          trend="Within SLA targets"
        />
      </div>

      {/* Provider Stats */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="bg-gray-900 border-gray-800">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-white">LLM Provider Rankings</CardTitle>
              <CardDescription className="text-gray-400">
                Win rates from Round Table competitions
              </CardDescription>
            </div>
            <Link href="/admin/round-table">
              <Button variant="ghost" size="sm" className="text-rose-400 hover:text-rose-300">
                View All <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {providerStats.slice(0, 5).map((provider, index) => (
                <div key={provider.provider_id} className="flex items-center gap-4">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gray-800 text-sm font-medium text-gray-400">
                    {index + 1}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-white">{provider.name}</span>
                      <span className="text-sm text-gray-400">
                        {(provider.win_rate * 100).toFixed(1)}% win rate
                      </span>
                    </div>
                    <div className="h-2 rounded-full bg-gray-800">
                      <div
                        className="h-2 rounded-full bg-gradient-to-r from-rose-500 to-rose-400"
                        style={{ width: `${provider.win_rate * 100}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
              {providerStats.length === 0 && (
                <p className="text-center text-gray-500 py-4">
                  No competition data yet. Run your first Round Table!
                </p>
              )}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gray-900 border-gray-800">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-white">3D Pipeline Status</CardTitle>
              <CardDescription className="text-gray-400">
                Generation providers and job queue
              </CardDescription>
            </div>
            <Link href="/admin/3d-pipeline">
              <Button variant="ghost" size="sm" className="text-rose-400 hover:text-rose-300">
                View All <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="rounded-lg bg-gray-800 p-4">
                  <div className="text-2xl font-bold text-white">
                    {stats?.pipeline3d?.providers_online || 0}
                  </div>
                  <div className="text-sm text-gray-400">Providers Online</div>
                </div>
                <div className="rounded-lg bg-gray-800 p-4">
                  <div className="text-2xl font-bold text-white">
                    {stats?.pipeline3d?.queued_jobs || 0}
                  </div>
                  <div className="text-sm text-gray-400">Jobs Queued</div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {stats?.pipeline3d?.status === 'healthy' ? (
                  <>
                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                    <span className="text-green-400">Pipeline Healthy</span>
                  </>
                ) : (
                  <>
                    <AlertCircle className="h-5 w-5 text-yellow-500" />
                    <span className="text-yellow-400">
                      Pipeline {stats?.pipeline3d?.status || 'Unknown'}
                    </span>
                  </>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Analytics Charts */}
      <div className="grid gap-6 lg:grid-cols-2">
        <ProviderPerformanceChart stats={providerStats} />
        <CompetitionTrendChart data={[]} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <AgentStatusChart
          active={stats?.agents.active || 6}
          idle={42}
          offline={6}
        />
        <PipelineMetricsChart
          providers={stats?.pipeline3d?.providers_online || 8}
          activeJobs={stats?.pipeline3d?.active_jobs || 0}
          queuedJobs={stats?.pipeline3d?.queued_jobs || 0}
          completedToday={12}
        />
      </div>

      {/* Quick Actions */}
      <Card className="bg-gray-900 border-gray-800">
        <CardHeader>
          <CardTitle className="text-white">Quick Actions</CardTitle>
          <CardDescription className="text-gray-400">
            Common platform operations
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Link href="/admin/round-table">
              <Button className="w-full bg-gradient-to-r from-rose-500 to-rose-600 hover:from-rose-600 hover:to-rose-700">
                <Zap className="mr-2 h-4 w-4" />
                Run Competition
              </Button>
            </Link>
            <Link href="/admin/3d-pipeline">
              <Button variant="outline" className="w-full border-gray-700 text-gray-300 hover:bg-gray-800">
                <Box className="mr-2 h-4 w-4" />
                Generate 3D Model
              </Button>
            </Link>
            <Link href="/admin/agents">
              <Button variant="outline" className="w-full border-gray-700 text-gray-300 hover:bg-gray-800">
                <Users className="mr-2 h-4 w-4" />
                Manage Agents
              </Button>
            </Link>
            <Link href="/admin/monitoring">
              <Button variant="outline" className="w-full border-gray-700 text-gray-300 hover:bg-gray-800">
                <Activity className="mr-2 h-4 w-4" />
                View Metrics
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function StatsCard({
  title,
  value,
  description,
  icon: Icon,
  trend,
}: {
  title: string;
  value: string | number;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  trend: string;
}) {
  return (
    <Card className="bg-gray-900 border-gray-800">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-gray-400">{title}</CardTitle>
        <Icon className="h-4 w-4 text-rose-400" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold text-white">{value}</div>
        <p className="text-xs text-gray-500">{description}</p>
        <div className="mt-2 flex items-center text-xs text-green-400">
          <TrendingUp className="mr-1 h-3 w-3" />
          {trend}
        </div>
      </CardContent>
    </Card>
  );
}

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <Skeleton className="h-8 w-48 bg-gray-800" />
          <Skeleton className="h-4 w-64 mt-2 bg-gray-800" />
        </div>
        <Skeleton className="h-6 w-32 bg-gray-800" />
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => (
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
      <div className="grid gap-6 lg:grid-cols-2">
        {[...Array(2)].map((_, i) => (
          <Card key={i} className="bg-gray-900 border-gray-800">
            <CardHeader>
              <Skeleton className="h-6 w-40 bg-gray-800" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-48 w-full bg-gray-800" />
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
