/**
 * Dashboard Home Page
 * ===================
 * Main dashboard with metrics, agents overview, and recent activity.
 */

'use client';

import { useState } from 'react';
import {
  Activity,
  Zap,
  DollarSign,
  CheckCircle,
  Bot,
  Trophy,
  TrendingUp,
  Clock,
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { AgentCard, MetricsCard, TaskExecutor, RoundTableViewer, TaskHistoryPanel } from '@/components';
import { Card, CardHeader, CardTitle, CardContent, Badge, Button, Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui';
import {
  useRealtimeAgents,
  useRealtimeMetrics,
  useRealtimeRoundTable,
} from '@/lib/hooks/useRealtime';
import {
  formatNumber,
  formatPercent,
  formatCurrency,
  formatDuration,
  getProviderDisplayName,
} from '@/lib/utils';
import type { LLMProvider } from '@/lib/types';

const LLM_COLORS: Record<LLMProvider, string> = {
  anthropic: '#d97757',
  openai: '#10a37f',
  google: '#4285f4',
  mistral: '#ff7000',
  cohere: '#39594d',
  groq: '#f55036',
};

export default function DashboardPage() {
  const [timeRange, setTimeRange] = useState<'1h' | '24h' | '7d' | '30d'>('24h');

  const { agents, isConnected: agentsConnected, refresh: refreshAgents } = useRealtimeAgents();
  const { metrics, history: metricsHistory, isConnected: metricsConnected } = useRealtimeMetrics(100);
  const { competition: latestRoundTable, isConnected: roundTableConnected } = useRealtimeRoundTable();

  // Prepare chart data from WebSocket metrics history
  const taskChartData = metricsHistory.slice(0, 50).reverse().map((point) => ({
    time: new Date(point.timestamp).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    }),
    tasks: point.active_agents || 0,
  }));

  const roundTableWinsData = metrics?.roundTableWins
    ? Object.entries(metrics.roundTableWins).map(([provider, wins]) => ({
        name: getProviderDisplayName(provider as LLMProvider),
        value: wins,
        provider: provider as LLMProvider,
      }))
    : [];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-gray-500 mt-1">
            Monitor your 6 SuperAgents and LLM Round Table
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="success" className="animate-pulse-glow">
            <Activity className="mr-1 h-3 w-3" />
            System Online
          </Badge>
        </div>
      </div>

      {/* Metrics Cards */}
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

      {/* Charts Row */}
      <div className="grid gap-4 lg:grid-cols-3">
        {/* Tasks Over Time */}
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Tasks Over Time
            </CardTitle>
            <Tabs value={timeRange} onValueChange={(v) => setTimeRange(v as typeof timeRange)}>
              <TabsList>
                <TabsTrigger value="1h">1H</TabsTrigger>
                <TabsTrigger value="24h">24H</TabsTrigger>
                <TabsTrigger value="7d">7D</TabsTrigger>
                <TabsTrigger value="30d">30D</TabsTrigger>
              </TabsList>
            </Tabs>
          </CardHeader>
          <CardContent>
            <div className="h-[250px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={taskChartData}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-800" />
                  <XAxis
                    dataKey="time"
                    className="text-xs"
                    tick={{ fill: '#9ca3af' }}
                  />
                  <YAxis className="text-xs" tick={{ fill: '#9ca3af' }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'white',
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px',
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="tasks"
                    stroke="#B76E79"
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Round Table Wins */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Trophy className="h-5 w-5 text-yellow-500" />
              Round Table Wins
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[200px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={roundTableWinsData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    label={({ name, percent }) =>
                      `${name.split(' ')[0]} ${(percent * 100).toFixed(0)}%`
                    }
                    labelLine={false}
                  >
                    {roundTableWinsData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={LLM_COLORS[entry.provider]}
                      />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              {roundTableWinsData.map((entry) => (
                <Badge
                  key={entry.provider}
                  variant={entry.provider}
                  className="text-xs"
                >
                  {entry.name}: {String(entry.value)}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Agents Grid */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold flex items-center gap-2">
            <Bot className="h-5 w-5" />
            SuperAgents
          </h2>
          <Button variant="outline" size="sm" onClick={() => refreshAgents()}>
            Refresh
          </Button>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {agents?.map((agent) => (
            <AgentCard
              key={agent.id}
              agent={agent}
              onRefresh={() => refreshAgents()}
            />
          )) || (
            // Skeleton loading
            Array.from({ length: 6 }).map((_, i) => (
              <Card key={i} className="h-[300px] animate-pulse bg-gray-100 dark:bg-gray-800" />
            ))
          )}
        </div>
      </div>

      {/* Bottom Row */}
      <div className="grid gap-4 lg:grid-cols-2">
        {/* Latest Round Table */}
        <div>
          <h2 className="text-xl font-bold flex items-center gap-2 mb-4">
            <Trophy className="h-5 w-5 text-yellow-500" />
            Latest Round Table
          </h2>
          {latestRoundTable ? (
            <RoundTableViewer entry={latestRoundTable} />
          ) : (
            <Card className="h-[300px] flex items-center justify-center">
              <p className="text-gray-500">No recent competitions</p>
            </Card>
          )}
        </div>

        {/* Quick Task Executor */}
        <div>
          <h2 className="text-xl font-bold flex items-center gap-2 mb-4">
            <Clock className="h-5 w-5" />
            Quick Task
          </h2>
          <TaskExecutor />
        </div>
      </div>

      {/* Task History Panel */}
      <TaskHistoryPanel limit={8} title="Recent Task History" />
    </div>
  );
}
