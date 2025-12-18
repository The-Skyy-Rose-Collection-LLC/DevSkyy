/**
 * Round Table Page
 * ================
 * View LLM competitions and run new tournaments.
 */

'use client';

import { useState } from 'react';
import {
  Trophy,
  Play,
  RefreshCw,
  Filter,
  Clock,
  DollarSign,
  Target,
  Loader2,
  Crown,
  Sparkles,
} from 'lucide-react';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';
import { RoundTableViewer, MetricsCard } from '@/components';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Button,
  Badge,
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from '@/components/ui';
import {
  useRoundTableHistory,
  useLLMProviders,
  useRunCompetition,
  useLatestRoundTable,
} from '@/lib/hooks';
import {
  formatNumber,
  formatPercent,
  formatDuration,
  formatCurrency,
  getProviderDisplayName,
  formatRelativeTime,
} from '@/lib/utils';
import type { LLMProvider, CompetitionStatus } from '@/lib/types';

const LLM_COLORS: Record<LLMProvider, string> = {
  anthropic: '#d97757',
  openai: '#10a37f',
  google: '#4285f4',
  mistral: '#ff7000',
  cohere: '#39594d',
  groq: '#f55036',
};

const statusFilters: (CompetitionStatus | 'all')[] = [
  'all',
  'completed',
  'ab_testing',
  'scoring',
  'collecting',
  'failed',
];

export default function RoundTablePage() {
  const [prompt, setPrompt] = useState('');
  const [statusFilter, setStatusFilter] = useState<CompetitionStatus | 'all'>('all');
  const [selectedEntry, setSelectedEntry] = useState<string | null>(null);

  const { data: history, mutate: refreshHistory, isLoading } = useRoundTableHistory({
    limit: 50,
    status: statusFilter === 'all' ? undefined : statusFilter,
  });
  const { data: providers } = useLLMProviders();
  const { data: latest } = useLatestRoundTable();
  const { trigger: runCompetition, isMutating: isRunning } = useRunCompetition();

  const handleRunCompetition = async () => {
    if (!prompt.trim() || isRunning) return;
    await runCompetition({ prompt: prompt.trim() });
    setPrompt('');
    refreshHistory();
  };

  // Calculate win statistics
  const winStats = history?.reduce(
    (acc, entry) => {
      if (entry.winner) {
        acc[entry.winner.provider] = (acc[entry.winner.provider] || 0) + 1;
        acc.total++;
      }
      return acc;
    },
    { total: 0 } as Record<string, number>
  ) || { total: 0 };

  const winChartData = Object.entries(winStats)
    .filter(([key]) => key !== 'total')
    .map(([provider, wins]) => ({
      name: getProviderDisplayName(provider as LLMProvider),
      value: wins,
      provider: provider as LLMProvider,
    }));

  // Average metrics
  const avgMetrics = history?.reduce(
    (acc, entry) => {
      if (entry.totalDurationMs) acc.totalDuration += entry.totalDurationMs;
      if (entry.totalCostUsd) acc.totalCost += entry.totalCostUsd;
      acc.count++;
      return acc;
    },
    { totalDuration: 0, totalCost: 0, count: 0 }
  ) || { totalDuration: 0, totalCost: 0, count: 0 };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Trophy className="h-8 w-8 text-yellow-500" />
            LLM Round Table
          </h1>
          <p className="text-gray-500 mt-1">
            All LLMs compete, top 2 finalists go through A/B testing, winner is implemented
          </p>
        </div>
        <Button onClick={() => refreshHistory()} disabled={isLoading}>
          <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Run Competition */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-yellow-500" />
            Run New Competition
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-4">
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Enter a prompt to pit all LLMs against each other..."
              className="flex-1 min-h-[80px] rounded-md border border-gray-300 dark:border-gray-700 bg-transparent px-3 py-2 text-sm placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-primary"
              disabled={isRunning}
            />
          </div>
          <div className="flex items-center justify-between">
            <div className="flex gap-2">
              {providers?.map((provider) => (
                <Badge
                  key={provider.provider}
                  variant={provider.status === 'available' ? (provider.provider as LLMProvider) : 'secondary'}
                  className="text-xs"
                >
                  {getProviderDisplayName(provider.provider as LLMProvider)}
                  {provider.status !== 'available' && ' (unavailable)'}
                </Badge>
              ))}
            </div>
            <Button onClick={handleRunCompetition} disabled={!prompt.trim() || isRunning}>
              {isRunning ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Running Competition...
                </>
              ) : (
                <>
                  <Play className="mr-2 h-4 w-4" />
                  Start Competition
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Stats Row */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricsCard
          title="Total Competitions"
          value={formatNumber(winStats.total)}
          icon={Trophy}
        />
        <MetricsCard
          title="Avg Duration"
          value={
            avgMetrics.count > 0
              ? formatDuration(avgMetrics.totalDuration / avgMetrics.count)
              : '-'
          }
          icon={Clock}
        />
        <MetricsCard
          title="Avg Cost"
          value={
            avgMetrics.count > 0
              ? formatCurrency(avgMetrics.totalCost / avgMetrics.count)
              : '-'
          }
          icon={DollarSign}
        />
        <MetricsCard
          title="Active Providers"
          value={providers?.filter((p) => p.status === 'available').length || 0}
          icon={Target}
        />
      </div>

      {/* Charts */}
      <div className="grid gap-4 lg:grid-cols-2">
        {/* Win Distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Crown className="h-5 w-5 text-yellow-500" />
              Win Distribution
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[250px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={winChartData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    label={({ name, percent }) =>
                      `${name.split(' ')[0]} ${(percent * 100).toFixed(0)}%`
                    }
                  >
                    {winChartData.map((entry, index) => (
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
          </CardContent>
        </Card>

        {/* Wins by Provider */}
        <Card>
          <CardHeader>
            <CardTitle>Wins by Provider</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[250px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={winChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value">
                    {winChartData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={LLM_COLORS[entry.provider]}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Competition History */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold">Competition History</h2>
          <div className="flex gap-2">
            {statusFilters.map((status) => (
              <Button
                key={status}
                variant={statusFilter === status ? 'default' : 'outline'}
                size="sm"
                onClick={() => setStatusFilter(status)}
              >
                {status.charAt(0).toUpperCase() + status.slice(1).replace('_', ' ')}
              </Button>
            ))}
          </div>
        </div>

        <Tabs defaultValue="list">
          <TabsList>
            <TabsTrigger value="list">List View</TabsTrigger>
            <TabsTrigger value="detail">Detail View</TabsTrigger>
          </TabsList>

          <TabsContent value="list" className="mt-4">
            <div className="space-y-4">
              {isLoading ? (
                Array.from({ length: 3 }).map((_, i) => (
                  <Card key={i} className="h-[150px] animate-pulse bg-gray-100 dark:bg-gray-800" />
                ))
              ) : history?.length === 0 ? (
                <Card className="p-8 text-center">
                  <Trophy className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                  <p className="text-gray-500">No competitions found</p>
                </Card>
              ) : (
                history?.map((entry) => (
                  <Card
                    key={entry.id}
                    className={`cursor-pointer transition-all hover:shadow-md ${
                      selectedEntry === entry.id ? 'ring-2 ring-brand-primary' : ''
                    }`}
                    onClick={() => setSelectedEntry(entry.id)}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <Badge
                              variant={
                                entry.status === 'completed'
                                  ? 'success'
                                  : entry.status === 'failed'
                                    ? 'destructive'
                                    : 'warning'
                              }
                            >
                              {entry.status}
                            </Badge>
                            {entry.winner && (
                              <Badge variant={entry.winner.provider as LLMProvider}>
                                <Crown className="mr-1 h-3 w-3" />
                                {getProviderDisplayName(entry.winner.provider)}
                              </Badge>
                            )}
                          </div>
                          <p className="text-sm line-clamp-2">{entry.prompt}</p>
                          <div className="flex gap-4 mt-2 text-xs text-gray-500">
                            <span>{formatRelativeTime(entry.createdAt)}</span>
                            {entry.totalDurationMs && (
                              <span>{formatDuration(entry.totalDurationMs)}</span>
                            )}
                            {entry.totalCostUsd && (
                              <span>{formatCurrency(entry.totalCostUsd)}</span>
                            )}
                            <span>{entry.participants.length} participants</span>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </TabsContent>

          <TabsContent value="detail" className="mt-4">
            {selectedEntry ? (
              <RoundTableViewer
                entry={history?.find((e) => e.id === selectedEntry)!}
                expanded
              />
            ) : latest ? (
              <RoundTableViewer entry={latest} expanded />
            ) : (
              <Card className="p-8 text-center">
                <p className="text-gray-500">Select a competition to view details</p>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
