/**
 * Tasks List Page
 * ================
 * Full task history with filtering, similar to WooCommerce orders view.
 */

'use client';

import { useState } from 'react';
import {
  ListTodo,
  RefreshCw,
  CheckCircle,
  XCircle,
  Loader2,
  AlertCircle,
  Filter,
  Clock,
  DollarSign,
  Zap,
} from 'lucide-react';
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
} from '@/components/ui';
import { MetricsCard } from '@/components';
import { useTasks } from '@/lib/hooks';
import {
  formatRelativeTime,
  formatDuration,
  formatCurrency,
  getAgentDisplayName,
  truncate,
  formatNumber,
} from '@/lib/utils';
import type { SuperAgentType, TaskResponse } from '@/lib/types';

const AGENT_TYPES: SuperAgentType[] = [
  'commerce',
  'creative',
  'marketing',
  'support',
  'operations',
  'analytics',
];

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

export default function TasksPage() {
  const [agentFilter, setAgentFilter] = useState<SuperAgentType | undefined>();
  const [statusFilter, setStatusFilter] = useState<string>('all');
  
  const { data: tasks, isLoading, mutate } = useTasks({ 
    agentType: agentFilter, 
    limit: 50 
  });

  // Calculate stats from tasks
  const completedTasks = tasks?.filter((t) => t.status === 'completed').length || 0;
  const failedTasks = tasks?.filter((t) => t.status === 'failed').length || 0;
  const totalCost = tasks?.reduce((sum, t) => sum + (t.metrics?.costUsd || 0), 0) || 0;
  const avgDuration = tasks?.length
    ? tasks.reduce((sum, t) => sum + (t.metrics?.durationMs || 0), 0) / tasks.length
    : 0;

  // Filter tasks by status
  const filteredTasks = statusFilter === 'all' 
    ? tasks 
    : tasks?.filter((t) => t.status === statusFilter);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <ListTodo className="h-8 w-8 text-brand-primary" />
            Task History
          </h1>
          <p className="text-gray-500 mt-1">
            View and manage all agent task executions
          </p>
        </div>
        <Button onClick={() => mutate()} disabled={isLoading}>
          <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Stats Row */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricsCard
          title="Total Tasks"
          value={formatNumber(tasks?.length || 0)}
          icon={ListTodo}
        />
        <MetricsCard
          title="Completed"
          value={formatNumber(completedTasks)}
          description={`${failedTasks} failed`}
          icon={CheckCircle}
        />
        <MetricsCard
          title="Avg Duration"
          value={formatDuration(avgDuration)}
          icon={Clock}
        />
        <MetricsCard
          title="Total Cost"
          value={formatCurrency(totalCost)}
          icon={DollarSign}
        />
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4">
        {/* Agent Filter */}
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-gray-500" />
          <span className="text-sm text-gray-500">Agent:</span>
          <select
            className="border rounded-md px-3 py-1.5 text-sm bg-white dark:bg-gray-900"
            value={agentFilter || ''}
            onChange={(e) => setAgentFilter(e.target.value as SuperAgentType || undefined)}
          >
            <option value="">All Agents</option>
            {AGENT_TYPES.map((type) => (
              <option key={type} value={type}>
                {getAgentDisplayName(type)}
              </option>
            ))}
          </select>
        </div>

        {/* Status Filter */}
        <Tabs value={statusFilter} onValueChange={setStatusFilter}>
          <TabsList>
            <TabsTrigger value="all">All</TabsTrigger>
            <TabsTrigger value="completed">Completed</TabsTrigger>
            <TabsTrigger value="running">Running</TabsTrigger>
            <TabsTrigger value="failed">Failed</TabsTrigger>
            <TabsTrigger value="pending">Pending</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* Task List */}
      <Card>
        <CardHeader>
          <CardTitle>Tasks ({filteredTasks?.length || 0})</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="h-16 bg-gray-100 dark:bg-gray-800 rounded animate-pulse" />
              ))}
            </div>
          ) : !filteredTasks || filteredTasks.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <ListTodo className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No tasks found</p>
              <p className="text-sm mt-1">Tasks will appear here as agents execute them</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b text-left text-sm text-gray-500">
                    <th className="pb-3 font-medium">Task</th>
                    <th className="pb-3 font-medium">Agent</th>
                    <th className="pb-3 font-medium">Status</th>
                    <th className="pb-3 font-medium">Provider</th>
                    <th className="pb-3 font-medium text-right">Duration</th>
                    <th className="pb-3 font-medium text-right">Cost</th>
                    <th className="pb-3 font-medium text-right">Time</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {filteredTasks.map((task: TaskResponse) => (
                    <TaskTableRow key={task.taskId} task={task} />
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function TaskTableRow({ task }: { task: TaskResponse }) {
  return (
    <tr className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
      <td className="py-3">
        <div className="flex items-center gap-2">
          {statusIcons[task.status]}
          <span className="text-sm font-medium">
            {truncate(task.prompt || task.taskId, 40)}
          </span>
        </div>
      </td>
      <td className="py-3">
        {task.agentType && (
          <Badge variant="outline" className="text-xs">
            {getAgentDisplayName(task.agentType).split(' ')[0]}
          </Badge>
        )}
      </td>
      <td className="py-3">
        <Badge variant={statusColors[task.status]} className="text-xs">
          {task.status}
        </Badge>
      </td>
      <td className="py-3">
        {task.metrics?.provider && (
          <Badge variant={task.metrics.provider} className="text-xs">
            {task.metrics.provider}
          </Badge>
        )}
      </td>
      <td className="py-3 text-right text-sm text-gray-500">
        {task.metrics?.durationMs ? formatDuration(task.metrics.durationMs) : '-'}
      </td>
      <td className="py-3 text-right text-sm text-gray-500">
        {task.metrics?.costUsd ? formatCurrency(task.metrics.costUsd) : '-'}
      </td>
      <td className="py-3 text-right text-sm text-gray-500">
        {task.createdAt ? formatRelativeTime(task.createdAt) : '-'}
      </td>
    </tr>
  );
}

