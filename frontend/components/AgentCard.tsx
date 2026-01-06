/**
 * AgentCard Component
 * ===================
 * Displays a SuperAgent's status and controls.
 */

'use client';

import Link from 'next/link';
import {
  ShoppingCart,
  Palette,
  Megaphone,
  HeadphonesIcon,
  Settings,
  BarChart3,
  Play,
  Square,
  Brain,
  CheckCircle,
  AlertCircle,
  Loader2,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import type { AgentInfo, SuperAgentType } from '@/lib/types';
import {
  formatNumber,
  formatPercent,
  formatDuration,
  formatCurrency,
} from '@/lib/utils';
import { useAgentControl } from '@/lib/hooks';

const agentIcons: Record<SuperAgentType, React.ElementType> = {
  commerce: ShoppingCart,
  creative: Palette,
  marketing: Megaphone,
  support: HeadphonesIcon,
  operations: Settings,
  analytics: BarChart3,
};

const statusIcons = {
  idle: CheckCircle,
  running: Loader2,
  error: AlertCircle,
  learning: Brain,
};

const statusColors = {
  idle: 'text-gray-500',
  running: 'text-green-500',
  error: 'text-red-500',
  learning: 'text-purple-500',
};

interface AgentCardProps {
  agent: AgentInfo;
  onRefresh?: () => void;
}

export function AgentCard({ agent, onRefresh }: AgentCardProps) {
  const Icon = agentIcons[agent.type];
  const StatusIcon = statusIcons[agent.status];
  const { start, stop, triggerLearning, isStarting, isStopping, isLearning } =
    useAgentControl(agent.type);

  const handleStart = async () => {
    await start();
    onRefresh?.();
  };

  const handleStop = async () => {
    await stop();
    onRefresh?.();
  };

  const handleLearn = async () => {
    await triggerLearning();
    onRefresh?.();
  };

  return (
    <Card className="relative overflow-hidden">
      {/* Status indicator stripe */}
      <div
        className={`absolute left-0 top-0 h-full w-1 ${
          agent.status === 'running'
            ? 'bg-green-500'
            : agent.status === 'error'
              ? 'bg-red-500'
              : agent.status === 'learning'
                ? 'bg-purple-500'
                : 'bg-gray-300'
        }`}
      />

      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div
              className={`rounded-lg p-2 bg-agent-${agent.type} bg-opacity-10`}
            >
              <Icon className={`h-5 w-5 text-agent-${agent.type}`} />
            </div>
            <div>
              <CardTitle className="text-base">{agent.name}</CardTitle>
              <p className="text-xs text-gray-500">{agent.description}</p>
            </div>
          </div>
          <div className="flex items-center gap-1">
            <StatusIcon
              className={`h-4 w-4 ${statusColors[agent.status]} ${
                agent.status === 'running' ? 'animate-spin' : ''
              }`}
            />
            <Badge
              variant={
                agent.status === 'running'
                  ? 'success'
                  : agent.status === 'error'
                    ? 'destructive'
                    : 'secondary'
              }
              className="text-xs"
            >
              {agent.status}
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Stats Grid */}
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1">
            <p className="text-xs text-gray-500">Tasks Completed</p>
            <p className="font-semibold">
              {formatNumber(agent.stats.tasksCompleted)}
            </p>
          </div>
          <div className="space-y-1">
            <p className="text-xs text-gray-500">Success Rate</p>
            <p className="font-semibold">
              {formatPercent(agent.stats.successRate)}
            </p>
          </div>
          <div className="space-y-1">
            <p className="text-xs text-gray-500">Avg Latency</p>
            <p className="font-semibold">
              {formatDuration(agent.stats.avgLatencyMs)}
            </p>
          </div>
          <div className="space-y-1">
            <p className="text-xs text-gray-500">Total Cost</p>
            <p className="font-semibold">
              {formatCurrency(agent.stats.totalCostUsd)}
            </p>
          </div>
        </div>

        {/* Success Rate Progress */}
        <div className="space-y-1">
          <div className="flex justify-between text-xs">
            <span className="text-gray-500">Success Rate</span>
            <span className="font-medium">
              {formatPercent(agent.stats.successRate)}
            </span>
          </div>
          <Progress
            value={agent.stats.successRate * 100}
            className="h-1.5"
            indicatorClassName={
              agent.stats.successRate > 0.9
                ? 'bg-green-500'
                : agent.stats.successRate > 0.7
                  ? 'bg-yellow-500'
                  : 'bg-red-500'
            }
          />
        </div>

        {/* Capabilities Preview */}
        <div className="flex flex-wrap gap-1">
          {agent.capabilities.slice(0, 4).map((cap) => (
            <Badge key={cap} variant="outline" className="text-xs">
              {cap}
            </Badge>
          ))}
          {agent.capabilities.length > 4 && (
            <Badge variant="outline" className="text-xs">
              +{agent.capabilities.length - 4} more
            </Badge>
          )}
        </div>
      </CardContent>

      <CardFooter className="gap-2 pt-4 border-t flex-wrap">
        {agent.status === 'running' ? (
          <Button
            variant="outline"
            size="sm"
            onClick={handleStop}
            disabled={isStopping}
            className="flex-1"
          >
            {isStopping ? (
              <Loader2 className="mr-1 h-3 w-3 animate-spin" />
            ) : (
              <Square className="mr-1 h-3 w-3" />
            )}
            Stop
          </Button>
        ) : (
          <Button
            variant="default"
            size="sm"
            onClick={handleStart}
            disabled={isStarting}
            className="flex-1"
          >
            {isStarting ? (
              <Loader2 className="mr-1 h-3 w-3 animate-spin" />
            ) : (
              <Play className="mr-1 h-3 w-3" />
            )}
            Start
          </Button>
        )}
        <Button
          variant="secondary"
          size="sm"
          onClick={handleLearn}
          disabled={isLearning || agent.status !== 'idle'}
          className="flex-1"
        >
          {isLearning ? (
            <Loader2 className="mr-1 h-3 w-3 animate-spin" />
          ) : (
            <Brain className="mr-1 h-3 w-3" />
          )}
          Learn
        </Button>
        <Button variant="outline" size="sm" asChild className="flex-1">
          <Link href={`/agents/${agent.type}`}>Details</Link>
        </Button>
        <Button variant="default" size="sm" asChild className="flex-1">
          <Link href={`/agents/${agent.type}/chat`}>Chat</Link>
        </Button>
      </CardFooter>
    </Card>
  );
}
