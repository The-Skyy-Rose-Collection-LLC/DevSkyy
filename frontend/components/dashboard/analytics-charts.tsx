'use client';

import { useMemo } from 'react';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  RadialBar,
  RadialBarChart,
  XAxis,
  YAxis,
} from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  ChartLegend,
  ChartLegendContent,
} from '@/components/ui/chart';
import type { ProviderStats } from '@/lib/api';

// SkyyRose brand colors
const BRAND_COLORS = {
  rose: '#B76E79',
  roseLight: '#D4A5AC',
  roseDark: '#8B4D55',
  purple: '#7C3AED',
  blue: '#3B82F6',
  cyan: '#06B6D4',
  emerald: '#10B981',
  amber: '#F59E0B',
};

const CHART_COLORS = [
  BRAND_COLORS.rose,
  BRAND_COLORS.purple,
  BRAND_COLORS.blue,
  BRAND_COLORS.cyan,
  BRAND_COLORS.emerald,
  BRAND_COLORS.amber,
];

interface ProviderPerformanceChartProps {
  stats: ProviderStats[];
}

export function ProviderPerformanceChart({ stats }: ProviderPerformanceChartProps) {
  const chartConfig: ChartConfig = useMemo(() => {
    const config: ChartConfig = {};
    stats.forEach((stat, index) => {
      config[stat.provider_id] = {
        label: stat.name,
        color: CHART_COLORS[index % CHART_COLORS.length],
      };
    });
    return config;
  }, [stats]);

  const chartData = useMemo(() => {
    return stats.map((stat, index) => ({
      name: stat.name,
      winRate: Math.round(stat.win_rate * 100),
      avgScore: Math.round(stat.avg_score * 100) / 100,
      competitions: stat.total_competitions,
      fill: CHART_COLORS[index % CHART_COLORS.length],
    }));
  }, [stats]);

  if (stats.length === 0) {
    return (
      <Card className="bg-gray-900/80 border-gray-700 backdrop-blur-sm">
        <CardHeader>
          <CardTitle className="text-white">Provider Performance</CardTitle>
          <CardDescription className="text-gray-400">
            Run competitions to see performance data
          </CardDescription>
        </CardHeader>
        <CardContent className="h-64 flex items-center justify-center">
          <p className="text-gray-500">No data available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-gray-900/80 border-gray-700 backdrop-blur-sm overflow-hidden">
      <div className="h-1 bg-gradient-to-r from-rose-500 via-purple-500 to-blue-500" />
      <CardHeader>
        <CardTitle className="text-white">Provider Win Rates</CardTitle>
        <CardDescription className="text-gray-400">
          Performance comparison across LLM providers
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer config={chartConfig} className="h-64 w-full">
          <BarChart data={chartData} layout="vertical" margin={{ left: 0, right: 16 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" horizontal={false} />
            <YAxis
              dataKey="name"
              type="category"
              tickLine={false}
              axisLine={false}
              width={100}
              tick={{ fill: '#9CA3AF', fontSize: 12 }}
            />
            <XAxis
              type="number"
              domain={[0, 100]}
              tickLine={false}
              axisLine={false}
              tick={{ fill: '#9CA3AF', fontSize: 12 }}
              tickFormatter={(value) => `${value}%`}
            />
            <ChartTooltip
              content={<ChartTooltipContent />}
              cursor={{ fill: 'rgba(255,255,255,0.05)' }}
            />
            <Bar
              dataKey="winRate"
              radius={[0, 4, 4, 0]}
              className="drop-shadow-lg"
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.fill} />
              ))}
            </Bar>
          </BarChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}

interface CompetitionTrendChartProps {
  data: Array<{
    date: string;
    competitions: number;
    avgLatency: number;
  }>;
}

export function CompetitionTrendChart({ data }: CompetitionTrendChartProps) {
  const chartConfig: ChartConfig = {
    competitions: {
      label: 'Competitions',
      color: BRAND_COLORS.rose,
    },
    avgLatency: {
      label: 'Avg Latency (ms)',
      color: BRAND_COLORS.purple,
    },
  };

  // Generate sample data if empty
  const chartData = data.length > 0 ? data : generateSampleTrendData();

  return (
    <Card className="bg-gray-900/80 border-gray-700 backdrop-blur-sm overflow-hidden">
      <div className="h-1 bg-gradient-to-r from-rose-500 to-purple-500" />
      <CardHeader>
        <CardTitle className="text-white">Competition Trends</CardTitle>
        <CardDescription className="text-gray-400">
          Daily competition volume and response times
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer config={chartConfig} className="h-64 w-full">
          <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="competitionsGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={BRAND_COLORS.rose} stopOpacity={0.4} />
                <stop offset="95%" stopColor={BRAND_COLORS.rose} stopOpacity={0} />
              </linearGradient>
              <linearGradient id="latencyGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={BRAND_COLORS.purple} stopOpacity={0.4} />
                <stop offset="95%" stopColor={BRAND_COLORS.purple} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
            <XAxis
              dataKey="date"
              tickLine={false}
              axisLine={false}
              tick={{ fill: '#9CA3AF', fontSize: 11 }}
            />
            <YAxis
              tickLine={false}
              axisLine={false}
              tick={{ fill: '#9CA3AF', fontSize: 11 }}
            />
            <ChartTooltip content={<ChartTooltipContent />} />
            <Area
              type="monotone"
              dataKey="competitions"
              stroke={BRAND_COLORS.rose}
              strokeWidth={2}
              fill="url(#competitionsGradient)"
            />
            <ChartLegend content={<ChartLegendContent />} />
          </AreaChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}

interface AgentStatusChartProps {
  active: number;
  idle: number;
  offline: number;
}

export function AgentStatusChart({ active, idle, offline }: AgentStatusChartProps) {
  const total = active + idle + offline;

  const chartConfig: ChartConfig = {
    active: { label: 'Active', color: BRAND_COLORS.emerald },
    idle: { label: 'Idle', color: BRAND_COLORS.amber },
    offline: { label: 'Offline', color: '#6B7280' },
  };

  const chartData = [
    { name: 'Active', value: active, fill: BRAND_COLORS.emerald },
    { name: 'Idle', value: idle, fill: BRAND_COLORS.amber },
    { name: 'Offline', value: offline, fill: '#6B7280' },
  ];

  const radialData = [
    {
      name: 'Agents',
      active: (active / total) * 100,
      fill: BRAND_COLORS.rose,
    },
  ];

  return (
    <Card className="bg-gray-900/80 border-gray-700 backdrop-blur-sm overflow-hidden">
      <div className="h-1 bg-gradient-to-r from-emerald-500 via-amber-500 to-gray-500" />
      <CardHeader>
        <CardTitle className="text-white">Agent Status</CardTitle>
        <CardDescription className="text-gray-400">
          Current status of {total} agents
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer config={chartConfig} className="h-48 w-full">
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={45}
              outerRadius={70}
              paddingAngle={3}
              dataKey="value"
              strokeWidth={0}
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.fill} className="drop-shadow-lg" />
              ))}
            </Pie>
            <ChartTooltip content={<ChartTooltipContent />} />
            <ChartLegend content={<ChartLegendContent />} />
          </PieChart>
        </ChartContainer>
        <div className="mt-4 grid grid-cols-3 gap-2 text-center">
          <div className="rounded-lg bg-emerald-500/10 p-2">
            <div className="text-lg font-bold text-emerald-400">{active}</div>
            <div className="text-xs text-gray-400">Active</div>
          </div>
          <div className="rounded-lg bg-amber-500/10 p-2">
            <div className="text-lg font-bold text-amber-400">{idle}</div>
            <div className="text-xs text-gray-400">Idle</div>
          </div>
          <div className="rounded-lg bg-gray-500/10 p-2">
            <div className="text-lg font-bold text-gray-400">{offline}</div>
            <div className="text-xs text-gray-400">Offline</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

interface PipelineMetricsChartProps {
  providers: number;
  activeJobs: number;
  queuedJobs: number;
  completedToday: number;
}

export function PipelineMetricsChart({
  providers,
  activeJobs,
  queuedJobs,
  completedToday,
}: PipelineMetricsChartProps) {
  const chartConfig: ChartConfig = {
    value: { label: 'Count', color: BRAND_COLORS.rose },
  };

  const chartData = [
    { metric: 'Providers', value: providers, fill: BRAND_COLORS.blue },
    { metric: 'Active', value: activeJobs, fill: BRAND_COLORS.rose },
    { metric: 'Queued', value: queuedJobs, fill: BRAND_COLORS.amber },
    { metric: 'Completed', value: completedToday, fill: BRAND_COLORS.emerald },
  ];

  return (
    <Card className="bg-gray-900/80 border-gray-700 backdrop-blur-sm overflow-hidden">
      <div className="h-1 bg-gradient-to-r from-blue-500 via-rose-500 to-emerald-500" />
      <CardHeader>
        <CardTitle className="text-white">3D Pipeline Metrics</CardTitle>
        <CardDescription className="text-gray-400">
          Current pipeline activity
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer config={chartConfig} className="h-48 w-full">
          <BarChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
            <XAxis
              dataKey="metric"
              tickLine={false}
              axisLine={false}
              tick={{ fill: '#9CA3AF', fontSize: 11 }}
            />
            <YAxis
              tickLine={false}
              axisLine={false}
              tick={{ fill: '#9CA3AF', fontSize: 11 }}
            />
            <ChartTooltip content={<ChartTooltipContent />} />
            <Bar dataKey="value" radius={[4, 4, 0, 0]}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.fill} />
              ))}
            </Bar>
          </BarChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}

// Helper function to generate sample trend data
function generateSampleTrendData() {
  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  return days.map((day) => ({
    date: day,
    competitions: Math.floor(Math.random() * 50) + 10,
    avgLatency: Math.floor(Math.random() * 200) + 100,
  }));
}
