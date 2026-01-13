/**
 * Charts Section
 * ==============
 * Client component for interactive charts with server-fetched data.
 */

'use client';

import { Trophy, TrendingUp } from 'lucide-react';
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
import { Card, CardHeader, CardTitle, CardContent, Badge } from '@/components/ui';
import { getProviderDisplayName } from '@/lib/utils';
import type { LLMProvider } from '@/lib/types';

const LLM_COLORS: Record<LLMProvider, string> = {
  anthropic: '#d97757',
  openai: '#10a37f',
  google: '#4285f4',
  mistral: '#ff7000',
  cohere: '#39594d',
  groq: '#f55036',
};

interface ChartsSectionProps {
  taskChartData?: Array<{ time: string; tasks: number }>;
  roundTableWinsData?: Array<{
    name: string;
    value: number;
    provider: LLMProvider;
  }>;
}

export function ChartsSection({
  taskChartData = [],
  roundTableWinsData = [],
}: ChartsSectionProps) {
  return (
    <div className="grid gap-4 lg:grid-cols-3">
      {/* Tasks Over Time */}
      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Tasks Over Time
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[250px]">
            {taskChartData.length > 0 ? (
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
            ) : (
              <div className="flex items-center justify-center h-full text-gray-500">
                No data available
              </div>
            )}
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
            {roundTableWinsData.length > 0 ? (
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
            ) : (
              <div className="flex items-center justify-center h-full text-gray-500">
                No competitions yet
              </div>
            )}
          </div>
          {roundTableWinsData.length > 0 && (
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
          )}
        </CardContent>
      </Card>
    </div>
  );
}
