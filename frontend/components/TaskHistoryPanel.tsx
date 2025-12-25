/**
 * TaskHistoryPanel Component
 * ==========================
 * Displays recent task history in a compact table format.
 */

'use client';

import Link from 'next/link';
import {
  Clock,
  CheckCircle,
  XCircle,
  Loader2,
  AlertCircle,
  ExternalLink,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent, Badge, Button } from './ui';
import { useTasks } from '@/lib/hooks';
import {
  formatRelativeTime,
  formatDuration,
  formatCurrency,
  getAgentDisplayName,
  truncate,
} from '@/lib/utils';
import type { SuperAgentType, TaskResponse } from '@/lib/types';

interface TaskHistoryPanelProps {
  agentType?: SuperAgentType;
  limit?: number;
  showViewAll?: boolean;
  title?: string;
}

const statusIcons = {
  completed: <CheckCircle className="h-4 w-4 text-green-500" />,
  failed: <XCircle className="h-4 w-4 text-red-500" />,
  running: <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />,
  pending: <AlertCircle className="h-4 w-4 text-yellow-500" />,
};

const statusColors = {
  completed: 'success',
  failed: 'destructive',
  running: 'default',
  pending: 'warning',
} as const;

export function TaskHistoryPanel({
  agentType,
  limit = 5,
  showViewAll = true,
  title = 'Recent Tasks',
}: TaskHistoryPanelProps) {
  const { data: tasks, isLoading } = useTasks({ agentType, limit });

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="flex items-center gap-2 text-base">
          <Clock className="h-5 w-5" />
          {title}
        </CardTitle>
        {showViewAll && (
          <Link href="/tasks">
            <Button variant="ghost" size="sm">
              View All
              <ExternalLink className="ml-1 h-3 w-3" />
            </Button>
          </Link>
        )}
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 3 }).map((_, i) => (
              <div
                key={i}
                className="h-12 bg-gray-100 dark:bg-gray-800 rounded animate-pulse"
              />
            ))}
          </div>
        ) : !tasks || tasks.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Clock className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No tasks yet</p>
          </div>
        ) : (
          <div className="space-y-2">
            {tasks.map((task: TaskResponse) => (
              <TaskRow key={task.taskId} task={task} />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function TaskRow({ task }: { task: TaskResponse }) {
  return (
    <div className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800/50 border border-transparent hover:border-gray-200 dark:hover:border-gray-700 transition-colors">
      <div className="flex items-center gap-3 min-w-0 flex-1">
        {statusIcons[task.status]}
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium truncate">
            {truncate(task.prompt || 'Task', 50)}
          </p>
          <div className="flex items-center gap-2 text-xs text-gray-500">
            {task.agentType && (
              <Badge variant="outline" className="text-xs py-0">
                {getAgentDisplayName(task.agentType).split(' ')[0]}
              </Badge>
            )}
            {task.createdAt && (
              <span>{formatRelativeTime(task.createdAt)}</span>
            )}
          </div>
        </div>
      </div>
      <div className="flex items-center gap-3 text-xs text-gray-500 ml-2">
        {task.metrics?.durationMs && (
          <span className="hidden sm:inline">
            {formatDuration(task.metrics.durationMs)}
          </span>
        )}
        {task.metrics?.costUsd && (
          <span className="hidden md:inline">
            {formatCurrency(task.metrics.costUsd)}
          </span>
        )}
        {task.metrics?.provider && (
          <Badge variant={task.metrics.provider} className="text-xs">
            {task.metrics.provider}
          </Badge>
        )}
        <Badge variant={statusColors[task.status]} className="text-xs">
          {task.status}
        </Badge>
      </div>
    </div>
  );
}

