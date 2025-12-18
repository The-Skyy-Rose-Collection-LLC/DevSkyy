/**
 * A/B Testing Dashboard Page
 * ==========================
 * View A/B test results and statistics.
 */

'use client';

import { useState } from 'react';
import {
  FlaskConical,
  RefreshCw,
  Trophy,
  TrendingUp,
  Target,
  BarChart3,
  CheckCircle,
  XCircle,
  Scale,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { MetricsCard } from '@/components';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Button,
  Badge,
  Progress,
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from '@/components/ui';
import { useABTestHistory, useABTestStats } from '@/lib/hooks';
import {
  formatNumber,
  formatPercent,
  formatRelativeTime,
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

export default function ABTestingPage() {
  const { data: history, mutate: refreshHistory, isLoading } = useABTestHistory({ limit: 50 });
  const { data: stats } = useABTestStats();

  // Prepare chart data
  const winsByProvider = stats?.winsByProvider
    ? Object.entries(stats.winsByProvider).map(([provider, wins]) => ({
        name: getProviderDisplayName(provider as LLMProvider),
        wins,
        provider: provider as LLMProvider,
      }))
    : [];

  const confidenceDistribution = history?.reduce(
    (acc, test) => {
      const bucket =
        test.confidence >= 0.95
          ? '95-100%'
          : test.confidence >= 0.9
            ? '90-95%'
            : test.confidence >= 0.8
              ? '80-90%'
              : test.confidence >= 0.7
                ? '70-80%'
                : '<70%';
      acc[bucket] = (acc[bucket] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  ) || {};

  const confidenceChartData = Object.entries(confidenceDistribution).map(
    ([range, count]) => ({
      range,
      count,
    })
  );

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <FlaskConical className="h-8 w-8 text-purple-500" />
            A/B Testing Dashboard
          </h1>
          <p className="text-gray-500 mt-1">
            Statistical comparison of LLM responses from Round Table finalists
          </p>
        </div>
        <Button onClick={() => refreshHistory()} disabled={isLoading}>
          <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Stats Row */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricsCard
          title="Total A/B Tests"
          value={formatNumber(stats?.totalTests || 0)}
          icon={FlaskConical}
        />
        <MetricsCard
          title="Avg Confidence"
          value={formatPercent(stats?.avgConfidence || 0)}
          icon={Target}
        />
        <MetricsCard
          title="Clear Winners"
          value={
            history?.filter((t) => t.winner !== 'tie').length || 0
          }
          description="Statistically significant"
          icon={Trophy}
        />
        <MetricsCard
          title="Ties"
          value={
            history?.filter((t) => t.winner === 'tie').length || 0
          }
          description="No significant difference"
          icon={Scale}
        />
      </div>

      {/* Charts Row */}
      <div className="grid gap-4 lg:grid-cols-2">
        {/* Wins by Provider */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Trophy className="h-5 w-5 text-yellow-500" />
              A/B Test Wins by Provider
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[250px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={winsByProvider}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="wins">
                    {winsByProvider.map((entry, index) => (
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

        {/* Confidence Distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Confidence Distribution
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[250px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={confidenceChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="range" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#B76E79" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Test History */}
      <Card>
        <CardHeader>
          <CardTitle>Recent A/B Tests</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {isLoading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <div
                  key={i}
                  className="h-24 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse"
                />
              ))
            ) : history?.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <FlaskConical className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No A/B tests found</p>
              </div>
            ) : (
              history?.map((test) => (
                <ABTestCard key={test.id} test={test} />
              ))
            )}
          </div>
        </CardContent>
      </Card>

      {/* How It Works */}
      <Card>
        <CardHeader>
          <CardTitle>How A/B Testing Works</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-6 md:grid-cols-4">
            <div className="text-center">
              <div className="h-12 w-12 rounded-full bg-brand-primary/10 flex items-center justify-center mx-auto mb-3">
                <span className="text-lg font-bold text-brand-primary">1</span>
              </div>
              <h3 className="font-medium mb-1">Round Table</h3>
              <p className="text-sm text-gray-500">
                All LLMs compete and responses are scored
              </p>
            </div>
            <div className="text-center">
              <div className="h-12 w-12 rounded-full bg-brand-primary/10 flex items-center justify-center mx-auto mb-3">
                <span className="text-lg font-bold text-brand-primary">2</span>
              </div>
              <h3 className="font-medium mb-1">Top 2 Selected</h3>
              <p className="text-sm text-gray-500">
                Best scoring responses become finalists
              </p>
            </div>
            <div className="text-center">
              <div className="h-12 w-12 rounded-full bg-brand-primary/10 flex items-center justify-center mx-auto mb-3">
                <span className="text-lg font-bold text-brand-primary">3</span>
              </div>
              <h3 className="font-medium mb-1">A/B Comparison</h3>
              <p className="text-sm text-gray-500">
                Statistical analysis determines winner
              </p>
            </div>
            <div className="text-center">
              <div className="h-12 w-12 rounded-full bg-brand-primary/10 flex items-center justify-center mx-auto mb-3">
                <span className="text-lg font-bold text-brand-primary">4</span>
              </div>
              <h3 className="font-medium mb-1">Implementation</h3>
              <p className="text-sm text-gray-500">
                Winning response is used and logged
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

interface ABTestCardProps {
  test: {
    id: string;
    taskType: string;
    variantA: string;
    variantB: string;
    winner: string;
    confidence: number;
    createdAt: string;
  };
}

function ABTestCard({ test }: ABTestCardProps) {
  const isWinnerA = test.winner === 'A' || test.winner === test.variantA;
  const isWinnerB = test.winner === 'B' || test.winner === test.variantB;
  const isTie = test.winner === 'tie';

  return (
    <div className="border rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Badge variant="outline">{test.taskType}</Badge>
          <span className="text-sm text-gray-500">
            {formatRelativeTime(test.createdAt)}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">Confidence:</span>
          <Badge
            variant={
              test.confidence >= 0.95
                ? 'success'
                : test.confidence >= 0.8
                  ? 'warning'
                  : 'secondary'
            }
          >
            {formatPercent(test.confidence)}
          </Badge>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* Variant A */}
        <div
          className={`rounded-lg p-3 border-2 ${
            isWinnerA
              ? 'border-green-500 bg-green-50 dark:bg-green-900/20'
              : 'border-gray-200 dark:border-gray-700'
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="font-medium">Variant A</span>
            {isWinnerA && <CheckCircle className="h-5 w-5 text-green-500" />}
          </div>
          <Badge variant={test.variantA as LLMProvider}>
            {getProviderDisplayName(test.variantA as LLMProvider)}
          </Badge>
        </div>

        {/* Variant B */}
        <div
          className={`rounded-lg p-3 border-2 ${
            isWinnerB
              ? 'border-green-500 bg-green-50 dark:bg-green-900/20'
              : 'border-gray-200 dark:border-gray-700'
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="font-medium">Variant B</span>
            {isWinnerB && <CheckCircle className="h-5 w-5 text-green-500" />}
          </div>
          <Badge variant={test.variantB as LLMProvider}>
            {getProviderDisplayName(test.variantB as LLMProvider)}
          </Badge>
        </div>
      </div>

      {isTie && (
        <div className="mt-3 text-center">
          <Badge variant="secondary">
            <Scale className="mr-1 h-3 w-3" />
            No statistically significant difference
          </Badge>
        </div>
      )}

      {/* Confidence Bar */}
      <div className="mt-4">
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          <span>Statistical Confidence</span>
          <span>{formatPercent(test.confidence)}</span>
        </div>
        <Progress
          value={test.confidence * 100}
          className="h-2"
          indicatorClassName={
            test.confidence >= 0.95
              ? 'bg-green-500'
              : test.confidence >= 0.8
                ? 'bg-yellow-500'
                : 'bg-gray-400'
          }
        />
      </div>
    </div>
  );
}
