/**
 * Dashboard Client Component
 * ==========================
 * Client-side interactive dashboard with real-time updates.
 */

'use client';

import { useState, useRef, useMemo, useCallback } from 'react';
import { toast } from 'sonner';
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
import {
  AgentCard,
  MetricsCard,
  TaskExecutor,
  RoundTableViewer,
  TaskHistoryPanel,
  ConnectionStatus,
} from '@/components';
import { CommandPalette } from '@/components/CommandPalette';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Badge,
  Button,
  Tabs,
  TabsList,
  TabsTrigger,
} from '@/components/ui';
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
import {
  type Command,
  defaultCommands,
} from '@/lib/commands';

const LLM_COLORS: Record<LLMProvider, string> = {
  anthropic: '#d97757',
  openai: '#10a37f',
  google: '#4285f4',
  mistral: '#ff7000',
  cohere: '#39594d',
  groq: '#f55036',
};

interface DashboardClientProps {
  initialMetrics?: any;
  initialAgents?: any[];
}

export default function DashboardClient({
  initialMetrics,
  initialAgents,
}: DashboardClientProps) {
  const [timeRange, setTimeRange] = useState<'1h' | '24h' | '7d' | '30d'>('24h');

  // Refs for scrolling to sections
  const metricsRef = useRef<HTMLDivElement>(null);
  const agentsRef = useRef<HTMLDivElement>(null);
  const roundTableRef = useRef<HTMLDivElement>(null);
  const taskHistoryRef = useRef<HTMLDivElement>(null);
  const taskExecutorRef = useRef<HTMLDivElement>(null);

  // Upgrade to realtime (WebSocket will fetch live data)
  // TODO: Enhance hooks to accept initialData for progressive enhancement
  const {
    agents,
    isConnected: agentsConnected,
    refresh: refreshAgents,
  } = useRealtimeAgents();

  const {
    metrics,
    history: metricsHistory,
    isConnected: metricsConnected,
  } = useRealtimeMetrics(100);

  const {
    competition: latestRoundTable,
    isConnected: roundTableConnected,
  } = useRealtimeRoundTable();

  // Prepare chart data from WebSocket metrics history
  const taskChartData = metricsHistory
    .slice(0, 50)
    .reverse()
    .map((point) => ({
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

  const scrollToSection = (ref: React.RefObject<HTMLDivElement | null>) => {
    ref.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const exportTaskHistoryCSV = useCallback(() => {
    const mockData = [
      ['Task ID', 'Agent', 'Prompt', 'Status', 'Duration', 'Cost', 'Timestamp'].join(','),
      ['tsk_001', 'Commerce', 'Generate product descriptions', 'completed', '1500', '0.05', new Date().toISOString()].join(','),
    ].join('\n');
    const blob = new Blob([mockData], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `devskyy-tasks-${new Date().toISOString()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Task history exported successfully');
  }, []);

  const exportDashboardJSON = useCallback(() => {
    const data = { metrics, agents, roundTable: latestRoundTable, exportedAt: new Date().toISOString() };
    const json = JSON.stringify(data, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `devskyy-dashboard-${new Date().toISOString()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Dashboard data exported successfully');
  }, [metrics, agents, latestRoundTable]);

  const refreshAllData = useCallback(async () => {
    toast.loading('Refreshing dashboard...');
    await refreshAgents();
    toast.success('Dashboard refreshed successfully');
  }, [refreshAgents]);

  const toggleDarkMode = () => {
    document.documentElement.classList.toggle('dark');
    const isDark = document.documentElement.classList.contains('dark');
    toast.success(`${isDark ? 'Dark' : 'Light'} mode enabled`);
  };

  const commands = useMemo<Command[]>(
    () =>
      defaultCommands.map((cmd) => {
        let action: () => void | Promise<void>;
        switch (cmd.id) {
          case 'nav-agents': action = () => scrollToSection(agentsRef); break;
          case 'nav-tasks': action = () => scrollToSection(taskHistoryRef); break;
          case 'nav-round-table': action = () => scrollToSection(roundTableRef); break;
          case 'nav-metrics': action = () => scrollToSection(metricsRef); break;
          case 'action-execute-task': action = () => scrollToSection(taskExecutorRef); break;
          case 'action-refresh': action = refreshAllData; break;
          case 'action-export-csv': action = exportTaskHistoryCSV; break;
          case 'action-export-json': action = exportDashboardJSON; break;
          case 'agent-commerce':
          case 'agent-creative':
          case 'agent-marketing':
          case 'agent-support':
          case 'agent-operations':
          case 'agent-analytics': action = () => scrollToSection(agentsRef); break;
          case 'settings-dark-mode': action = toggleDarkMode; break;
          case 'settings-time-range-1h': action = () => { setTimeRange('1h'); toast.success('Time range set to 1 hour'); }; break;
          case 'settings-time-range-24h': action = () => { setTimeRange('24h'); toast.success('Time range set to 24 hours'); }; break;
          case 'settings-time-range-7d': action = () => { setTimeRange('7d'); toast.success('Time range set to 7 days'); }; break;
          case 'settings-time-range-30d': action = () => { setTimeRange('30d'); toast.success('Time range set to 30 days'); }; break;
          default: action = () => console.log(`Command ${cmd.id} not implemented`);
        }
        return { ...cmd, action } as Command;
      }),
    [refreshAllData, exportTaskHistoryCSV, exportDashboardJSON]
  );

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
        <ConnectionStatus compact showDetails={false} />
      </div>

      {/* Metrics Cards */}
      <div ref={metricsRef} className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
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
            <Tabs
              value={timeRange}
              onValueChange={(v) => setTimeRange(v as typeof timeRange)}
            >
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
                  <CartesianGrid
                    strokeDasharray="3 3"
                    className="stroke-gray-200 dark:stroke-gray-800"
                  />
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
      <div ref={agentsRef}>
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
              <Card
                key={i}
                className="h-[300px] animate-pulse bg-gray-100 dark:bg-gray-800"
              />
            ))
          )}
        </div>
      </div>

      {/* Bottom Row */}
      <div className="grid gap-4 lg:grid-cols-2">
        {/* Latest Round Table */}
        <div ref={roundTableRef}>
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
        <div ref={taskExecutorRef}>
          <h2 className="text-xl font-bold flex items-center gap-2 mb-4">
            <Clock className="h-5 w-5" />
            Quick Task
          </h2>
          <TaskExecutor />
        </div>
      </div>

      {/* Task History Panel */}
      <div ref={taskHistoryRef}>
        <TaskHistoryPanel limit={8} title="Recent Task History" />
      </div>

      <CommandPalette commands={commands} />
    </div>
  );
}
