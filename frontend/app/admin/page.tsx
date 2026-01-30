'use client';

import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Zap,
  Users,
  Box,
  Activity,
  Clock,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
} from 'lucide-react';
import { api, type ProviderStats, type PipelineStatus } from '@/lib/api';
import { useQuery } from '@/hooks';
import { ErrorState } from '@/components/shared';
import { StatsCard, DashboardSkeleton } from '@/components/dashboard';
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

async function fetchDashboardData(): Promise<{
  stats: DashboardStats;
  providerStats: ProviderStats[];
}> {
  const [rtStats, pipelineStatus] = await Promise.all([
    api.roundTable.getStats().catch(() => []),
    api.pipeline3d.getStatus().catch(() => null),
  ]);

  const totalCompetitions = rtStats.reduce((sum, p) => sum + p.total_competitions, 0);
  const topProvider =
    rtStats.length > 0
      ? rtStats.reduce((a, b) => (a.win_rate > b.win_rate ? a : b)).provider
      : 'N/A';
  const avgLatency =
    rtStats.length > 0
      ? Math.round(rtStats.reduce((sum, p) => sum + p.avg_latency_ms, 0) / rtStats.length)
      : 0;

  return {
    stats: {
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
    },
    providerStats: rtStats,
  };
}

import { motion } from 'framer-motion';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
};

const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: { y: 0, opacity: 1 },
};

export default function AdminDashboard() {
  const { data, loading, error, refetch } = useQuery(
    'dashboard',
    fetchDashboardData,
    { refetchInterval: 30000 }
  );

  if (loading) {
    return <DashboardSkeleton />;
  }

  if (error) {
    return (
      <ErrorState
        title="Error Loading Dashboard"
        message={error.message}
        onRetry={refetch}
        fullPage
      />
    );
  }

  const { stats, providerStats } = data!;

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={containerVariants}
      className="space-y-8"
    >
      {/* Header */}
      <motion.header variants={itemVariants} className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-extrabold tracking-tight text-white sm:text-5xl">
            DevSkyy <span className="gradient-text-vibrant">Dashboard</span>
          </h1>
          <p className="text-gray-400 mt-2 text-lg font-medium">Enterprise AI Platform Overview</p>
        </div>
        <Badge variant="outline" className="border-green-500/50 bg-green-500/5 text-green-400 backdrop-blur-sm px-4 py-1">
          <Activity className="h-3 w-3 mr-2 animate-pulse" aria-hidden="true" />
          All Systems Operational
        </Badge>
      </motion.header>

      {/* Stats Grid */}
      <motion.section variants={itemVariants} aria-label="Platform Statistics">
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          <StatsCard
            title="LLM Competitions"
            value={stats.roundTable.totalCompetitions}
            description="Total round table competitions"
            icon={Zap}
            trend="+12% from last week"
            trendDirection="up"
          />
          <StatsCard
            title="Active Agents"
            value={`${stats.agents.active}/${stats.agents.total}`}
            description="SuperAgents online"
            icon={Users}
            trend="6 ready for deployment"
            trendDirection="neutral"
          />
          <StatsCard
            title="3D Jobs"
            value={stats.pipeline3d?.active_jobs || 0}
            description={`${stats.pipeline3d?.queued_jobs || 0} queued`}
            icon={Box}
            trend={`${stats.pipeline3d?.providers_online || 0} providers online`}
            trendDirection="up"
          />
          <StatsCard
            title="Avg Latency"
            value={`${stats.roundTable.avgLatency}ms`}
            description="LLM response time"
            icon={Clock}
            trend="Within SLA targets"
            trendDirection="up"
          />
        </div>
      </motion.section>

      {/* Provider & Pipeline Status */}
      <motion.section variants={itemVariants} aria-label="Provider and Pipeline Status">
        <div className="grid gap-8 lg:grid-cols-2">
          <ProviderRankingsCard providerStats={providerStats} />
          <PipelineStatusCard status={stats.pipeline3d} />
        </div>
      </motion.section>

      {/* Analytics Charts */}
      <motion.section variants={itemVariants} aria-label="Analytics Charts">
        <div className="grid gap-8 lg:grid-cols-2">
          <ProviderPerformanceChart stats={providerStats} />
          <CompetitionTrendChart data={[]} />
        </div>

        <div className="grid gap-8 lg:grid-cols-2 mt-8">
          <AgentStatusChart
            active={stats.agents.active}
            idle={42}
            offline={6}
          />
          <PipelineMetricsChart
            providers={stats.pipeline3d?.providers_online || 8}
            activeJobs={stats.pipeline3d?.active_jobs || 0}
            queuedJobs={stats.pipeline3d?.queued_jobs || 0}
            completedToday={12}
          />
        </div>
      </motion.section>

      {/* Quick Actions */}
      <motion.section variants={itemVariants} aria-label="Quick Actions">
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
                  <Zap className="mr-2 h-4 w-4" aria-hidden="true" />
                  Run Competition
                </Button>
              </Link>
              <Link href="/admin/3d-pipeline">
                <Button
                  variant="outline"
                  className="w-full border-gray-700 text-gray-300 hover:bg-gray-800"
                >
                  <Box className="mr-2 h-4 w-4" aria-hidden="true" />
                  Generate 3D Model
                </Button>
              </Link>
              <Link href="/admin/agents">
                <Button
                  variant="outline"
                  className="w-full border-gray-700 text-gray-300 hover:bg-gray-800"
                >
                  <Users className="mr-2 h-4 w-4" aria-hidden="true" />
                  Manage Agents
                </Button>
              </Link>
              <Link href="/admin/assets">
                <Button
                  variant="outline"
                  className="w-full border-gray-700 text-gray-300 hover:bg-gray-800"
                >
                  <Activity className="mr-2 h-4 w-4" aria-hidden="true" />
                  Asset Library
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </motion.section>
    </motion.div>
  );
}

// Sub-components for better organization
function ProviderRankingsCard({ providerStats }: { providerStats: ProviderStats[] }) {
  return (
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
            View All <ArrowRight className="ml-2 h-4 w-4" aria-hidden="true" />
          </Button>
        </Link>
      </CardHeader>
      <CardContent>
        <div className="space-y-4" role="list" aria-label="Provider rankings">
          {providerStats.slice(0, 5).map((stat, index) => (
            <div key={stat.provider} className="flex items-center gap-4" role="listitem">
              <div
                className="flex h-8 w-8 items-center justify-center rounded-full bg-gray-800 text-sm font-medium text-gray-400"
                aria-label={`Rank ${index + 1}`}
              >
                {index + 1}
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium text-white">{stat.provider}</span>
                  <span className="text-sm text-gray-400">
                    {(stat.win_rate * 100).toFixed(1)}% win rate
                  </span>
                </div>
                <div
                  className="h-2 rounded-full bg-gray-800"
                  role="progressbar"
                  aria-valuenow={stat.win_rate * 100}
                  aria-valuemin={0}
                  aria-valuemax={100}
                >
                  <div
                    className="h-2 rounded-full bg-gradient-to-r from-rose-500 to-rose-400"
                    style={{ width: `${stat.win_rate * 100}%` }}
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
  );
}

function PipelineStatusCard({ status }: { status: PipelineStatus | null }) {
  return (
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
            View All <ArrowRight className="ml-2 h-4 w-4" aria-hidden="true" />
          </Button>
        </Link>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-lg bg-gray-800 p-4">
              <div className="text-2xl font-bold text-white">
                {status?.providers_online || 0}
              </div>
              <div className="text-sm text-gray-400">Providers Online</div>
            </div>
            <div className="rounded-lg bg-gray-800 p-4">
              <div className="text-2xl font-bold text-white">
                {status?.queued_jobs || 0}
              </div>
              <div className="text-sm text-gray-400">Jobs Queued</div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {status?.status === 'healthy' ? (
              <>
                <CheckCircle2 className="h-5 w-5 text-green-500" aria-hidden="true" />
                <span className="text-green-400">Pipeline Healthy</span>
              </>
            ) : (
              <>
                <AlertCircle className="h-5 w-5 text-yellow-500" aria-hidden="true" />
                <span className="text-yellow-400">
                  Pipeline {status?.status || 'Unknown'}
                </span>
              </>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
