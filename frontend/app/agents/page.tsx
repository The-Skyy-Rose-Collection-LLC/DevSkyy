/**
 * Agents Overview Page
 * ====================
 * View and manage all 6 SuperAgents.
 */

'use client';

import { useState } from 'react';
import { Bot, Filter, RefreshCw } from 'lucide-react';
import { AgentCard } from '@/components';
import { Card, Button, Badge, Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui';
import { useAgents } from '@/lib/hooks';
import type { AgentStatus, SuperAgentType } from '@/lib/types';

const agentTypes: SuperAgentType[] = [
  'commerce',
  'creative',
  'marketing',
  'support',
  'operations',
  'analytics',
];

const statusFilters: (AgentStatus | 'all')[] = [
  'all',
  'running',
  'idle',
  'learning',
  'error',
];

export default function AgentsPage() {
  const [statusFilter, setStatusFilter] = useState<AgentStatus | 'all'>('all');
  const { data: agents, mutate: refreshAgents, isLoading } = useAgents();

  const filteredAgents = agents?.filter(
    (agent) => statusFilter === 'all' || agent.status === statusFilter
  );

  const statusCounts = agents?.reduce(
    (acc, agent) => {
      acc[agent.status] = (acc[agent.status] || 0) + 1;
      return acc;
    },
    {} as Record<AgentStatus, number>
  );

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Bot className="h-8 w-8" />
            SuperAgents
          </h1>
          <p className="text-gray-500 mt-1">
            Manage and monitor your 6 AI agents with 17 prompt techniques each
          </p>
        </div>
        <Button onClick={() => refreshAgents()} disabled={isLoading}>
          <RefreshCw
            className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`}
          />
          Refresh
        </Button>
      </div>

      {/* Status Summary */}
      <div className="flex gap-4">
        {statusFilters.map((status) => (
          <Button
            key={status}
            variant={statusFilter === status ? 'default' : 'outline'}
            size="sm"
            onClick={() => setStatusFilter(status)}
          >
            {status.charAt(0).toUpperCase() + status.slice(1)}
            {status !== 'all' && statusCounts?.[status as AgentStatus] && (
              <Badge variant="secondary" className="ml-2">
                {statusCounts[status as AgentStatus]}
              </Badge>
            )}
          </Button>
        ))}
      </div>

      {/* Agent Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {isLoading ? (
          // Skeleton loading
          Array.from({ length: 6 }).map((_, i) => (
            <Card
              key={i}
              className="h-[350px] animate-pulse bg-gray-100 dark:bg-gray-800"
            />
          ))
        ) : filteredAgents?.length === 0 ? (
          <div className="col-span-full text-center py-12">
            <Bot className="h-12 w-12 mx-auto text-gray-400 mb-4" />
            <p className="text-gray-500">No agents match the current filter</p>
          </div>
        ) : (
          filteredAgents?.map((agent) => (
            <AgentCard
              key={agent.id}
              agent={agent}
              onRefresh={() => refreshAgents()}
            />
          ))
        )}
      </div>

      {/* Agent Capabilities Overview */}
      <Card>
        <div className="p-6">
          <h2 className="text-xl font-bold mb-4">Agent Capabilities Matrix</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 px-4">Agent</th>
                  <th className="text-left py-2 px-4">Primary Tools</th>
                  <th className="text-left py-2 px-4">ML Focus</th>
                  <th className="text-left py-2 px-4">Status</th>
                </tr>
              </thead>
              <tbody>
                {agents?.map((agent) => (
                  <tr key={agent.id} className="border-b hover:bg-gray-50 dark:hover:bg-gray-800">
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <div
                          className={`h-3 w-3 rounded-full bg-agent-${agent.type}`}
                        />
                        <span className="font-medium">{agent.name}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex flex-wrap gap-1">
                        {agent.tools.slice(0, 3).map((tool) => (
                          <Badge key={tool.name} variant="outline" className="text-xs">
                            {tool.name}
                          </Badge>
                        ))}
                        {agent.tools.length > 3 && (
                          <Badge variant="outline" className="text-xs">
                            +{agent.tools.length - 3}
                          </Badge>
                        )}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex flex-wrap gap-1">
                        {agent.mlModels.slice(0, 2).map((model) => (
                          <Badge key={model} variant="secondary" className="text-xs">
                            {model}
                          </Badge>
                        ))}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <Badge
                        variant={
                          agent.status === 'running'
                            ? 'success'
                            : agent.status === 'error'
                              ? 'destructive'
                              : 'secondary'
                        }
                      >
                        {agent.status}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </Card>
    </div>
  );
}
