'use client';

import { useQuery } from '@tanstack/react-query';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Activity,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Box,
  Image,
  Globe,
  Mail,
  RefreshCw,
} from 'lucide-react';
import { Button } from '@/components/ui/button';

interface QueueStats {
  waiting: number;
  active: number;
  completed: number;
  failed: number;
  delayed: number;
}

const QUEUE_META: Record<
  string,
  { label: string; icon: typeof Box; color: string }
> = {
  'generate-3d-asset': {
    label: '3D Generation',
    icon: Box,
    color: 'text-purple-400',
  },
  'process-image': {
    label: 'Image Processing',
    icon: Image,
    color: 'text-blue-400',
  },
  'sync-wordpress': {
    label: 'WordPress Sync',
    icon: Globe,
    color: 'text-green-400',
  },
  'send-email': {
    label: 'Email',
    icon: Mail,
    color: 'text-rose-400',
  },
};

async function fetchQueueStats(): Promise<Record<string, QueueStats>> {
  const response = await fetch('/api/jobs');
  if (!response.ok) throw new Error('Failed to load queue stats');
  const data = await response.json();
  return data.stats;
}

export default function JobsPage() {
  const {
    data: stats,
    isLoading,
    refetch,
  } = useQuery({
    queryKey: ['job-queue-stats'],
    queryFn: fetchQueueStats,
    refetchInterval: 5000,
  });

  return (
    <div className="space-y-8">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-extrabold tracking-tight text-white">
            Job Queue
          </h1>
          <p className="text-gray-400 mt-2 text-lg">
            Background job processing and queue health
          </p>
        </div>
        <Button
          variant="outline"
          className="border-gray-700 text-gray-300 hover:bg-gray-800"
          onClick={() => refetch()}
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </header>

      {isLoading ? (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Card
              key={i}
              className="bg-gray-900 border-gray-800 animate-pulse"
            >
              <CardContent className="h-48" />
            </Card>
          ))}
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {Object.entries(stats || {}).map(([queue, queueStats]) => {
            const meta = QUEUE_META[queue] || {
              label: queue,
              icon: Activity,
              color: 'text-gray-400',
            };
            const Icon = meta.icon;
            const total =
              queueStats.waiting +
              queueStats.active +
              queueStats.completed +
              queueStats.failed;

            return (
              <Card key={queue} className="bg-gray-900 border-gray-800">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Icon className={`h-5 w-5 ${meta.color}`} />
                      <CardTitle className="text-white text-base">
                        {meta.label}
                      </CardTitle>
                    </div>
                    {queueStats.active > 0 && (
                      <Badge
                        variant="outline"
                        className="border-green-500/50 bg-green-500/10 text-green-400"
                      >
                        <Activity className="h-3 w-3 mr-1 animate-pulse" />
                        Active
                      </Badge>
                    )}
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-2 rounded bg-gray-800/50">
                      <div className="flex items-center gap-1.5 mb-1">
                        <Clock className="h-3 w-3 text-yellow-400" />
                        <span className="text-xs text-gray-400">Waiting</span>
                      </div>
                      <p className="text-lg font-bold text-white">
                        {queueStats.waiting}
                      </p>
                    </div>
                    <div className="p-2 rounded bg-gray-800/50">
                      <div className="flex items-center gap-1.5 mb-1">
                        <Activity className="h-3 w-3 text-blue-400" />
                        <span className="text-xs text-gray-400">Active</span>
                      </div>
                      <p className="text-lg font-bold text-white">
                        {queueStats.active}
                      </p>
                    </div>
                    <div className="p-2 rounded bg-gray-800/50">
                      <div className="flex items-center gap-1.5 mb-1">
                        <CheckCircle2 className="h-3 w-3 text-green-400" />
                        <span className="text-xs text-gray-400">Done</span>
                      </div>
                      <p className="text-lg font-bold text-white">
                        {queueStats.completed}
                      </p>
                    </div>
                    <div className="p-2 rounded bg-gray-800/50">
                      <div className="flex items-center gap-1.5 mb-1">
                        <AlertTriangle className="h-3 w-3 text-red-400" />
                        <span className="text-xs text-gray-400">Failed</span>
                      </div>
                      <p className="text-lg font-bold text-white">
                        {queueStats.failed}
                      </p>
                    </div>
                  </div>
                  <div className="text-xs text-gray-500">
                    {total.toLocaleString()} total processed
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Summary */}
      <Card className="bg-gray-900 border-gray-800">
        <CardHeader>
          <CardTitle className="text-white">Queue Overview</CardTitle>
          <CardDescription className="text-gray-400">
            Aggregate statistics across all job queues
          </CardDescription>
        </CardHeader>
        <CardContent>
          {stats && (
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              {['waiting', 'active', 'completed', 'failed', 'delayed'].map(
                (status) => {
                  const total = Object.values(stats).reduce(
                    (sum, s) => sum + (s[status as keyof QueueStats] || 0),
                    0,
                  );
                  return (
                    <div
                      key={status}
                      className="p-4 rounded-lg bg-gray-800/50 text-center"
                    >
                      <p className="text-2xl font-bold text-white">{total}</p>
                      <p className="text-xs text-gray-400 capitalize mt-1">
                        {status}
                      </p>
                    </div>
                  );
                },
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
