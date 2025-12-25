/**
 * Agent Detail Page
 * =================
 * Detailed view and control for a single SuperAgent.
 */

'use client';

import { use } from 'react';
import Link from 'next/link';
import {
  ArrowLeft,
  Play,
  Square,
  Brain,
  Settings,
  Wrench,
  Activity,
  Clock,
  DollarSign,
  CheckCircle,
  Loader2,
  Sparkles,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from 'recharts';
import { TaskExecutor, MetricsCard, TaskHistoryPanel } from '@/components';
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
import { useAgent, useAgentTools, useAgentControl, useAgentMetrics } from '@/lib/hooks';
import {
  formatNumber,
  formatPercent,
  formatDuration,
  formatCurrency,
  getAgentDisplayName,
  getAgentDescription,
} from '@/lib/utils';
import type { SuperAgentType } from '@/lib/types';

interface AgentPageProps {
  params: Promise<{ agent: string }>;
}

const PROMPT_TECHNIQUES = [
  'Chain of Thought',
  'Few-Shot',
  'Tree of Thoughts',
  'ReAct',
  'RAG',
  'Constitutional',
  'Self-Consistency',
  'Structured Output',
  'Role-Based',
  'Meta-Prompting',
  'Prompt Chaining',
  'Analogical',
  'Socratic',
  'Contrastive',
  'Recursive',
  'Multi-Persona',
  'Constraint-Based',
];

export default function AgentDetailPage({ params }: AgentPageProps) {
  const { agent: agentType } = use(params);
  const { data: agent, mutate: refreshAgent, isLoading } = useAgent(agentType as SuperAgentType);
  const { data: tools } = useAgentTools(agentType as SuperAgentType);
  const { data: agentMetrics } = useAgentMetrics(agentType as SuperAgentType);
  const { start, stop, triggerLearning, isStarting, isStopping, isLearning } =
    useAgentControl(agentType as SuperAgentType);

  if (isLoading || !agent) {
    return (
      <div className="flex items-center justify-center h-[50vh]">
        <Loader2 className="h-8 w-8 animate-spin text-brand-primary" />
      </div>
    );
  }

  // Prepare chart data
  const tasksByCategoryData = agentMetrics?.tasksByCategory
    ? Object.entries(agentMetrics.tasksByCategory).map(([category, count]) => ({
        category: category.charAt(0).toUpperCase() + category.slice(1),
        tasks: count,
      }))
    : [];

  const techniqueData = PROMPT_TECHNIQUES.map((technique, idx) => ({
    technique: technique.split(' ')[0],
    fullName: technique,
    usage: Math.random() * 100, // Would come from real metrics
  }));

  const handleStart = async () => {
    await start();
    refreshAgent();
  };

  const handleStop = async () => {
    await stop();
    refreshAgent();
  };

  const handleLearn = async () => {
    await triggerLearning();
    refreshAgent();
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/agents">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back
            </Button>
          </Link>
          <div>
            <div className="flex items-center gap-3">
              <div className={`h-10 w-10 rounded-lg bg-agent-${agent.type} flex items-center justify-center`}>
                <Sparkles className="h-5 w-5 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold">{agent.name}</h1>
                <p className="text-gray-500">{agent.description}</p>
              </div>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge
            variant={
              agent.status === 'running'
                ? 'success'
                : agent.status === 'error'
                  ? 'destructive'
                  : agent.status === 'learning'
                    ? 'warning'
                    : 'secondary'
            }
            className="text-sm"
          >
            {agent.status}
          </Badge>
        </div>
      </div>

      {/* Control Panel */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Control Panel
          </CardTitle>
        </CardHeader>
        <CardContent className="flex gap-4">
          {agent.status === 'running' ? (
            <Button
              variant="outline"
              onClick={handleStop}
              disabled={isStopping}
            >
              {isStopping ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Square className="mr-2 h-4 w-4" />
              )}
              Stop Agent
            </Button>
          ) : (
            <Button onClick={handleStart} disabled={isStarting}>
              {isStarting ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Play className="mr-2 h-4 w-4" />
              )}
              Start Agent
            </Button>
          )}
          <Button
            variant="secondary"
            onClick={handleLearn}
            disabled={isLearning || agent.status !== 'idle'}
          >
            {isLearning ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Brain className="mr-2 h-4 w-4" />
            )}
            Trigger Learning
          </Button>
        </CardContent>
      </Card>

      {/* Metrics Row */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricsCard
          title="Tasks Completed"
          value={formatNumber(agent.stats.tasksCompleted)}
          icon={Activity}
        />
        <MetricsCard
          title="Success Rate"
          value={formatPercent(agent.stats.successRate)}
          icon={CheckCircle}
        />
        <MetricsCard
          title="Avg Latency"
          value={formatDuration(agent.stats.avgLatencyMs)}
          icon={Clock}
        />
        <MetricsCard
          title="Total Cost"
          value={formatCurrency(agent.stats.totalCostUsd)}
          icon={DollarSign}
        />
      </div>

      {/* Tabs */}
      <Tabs defaultValue="tools">
        <TabsList>
          <TabsTrigger value="tools">Tools ({tools?.length || 0})</TabsTrigger>
          <TabsTrigger value="techniques">17 Techniques</TabsTrigger>
          <TabsTrigger value="metrics">Metrics</TabsTrigger>
          <TabsTrigger value="execute">Execute Task</TabsTrigger>
        </TabsList>

        {/* Tools Tab */}
        <TabsContent value="tools" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Wrench className="h-5 w-5" />
                Available Tools
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2">
                {tools?.map((tool) => (
                  <div
                    key={tool.name}
                    className="border rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-800"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-medium">{tool.name}</h3>
                      <Badge variant="outline">{tool.category}</Badge>
                    </div>
                    <p className="text-sm text-gray-500 mb-3">
                      {tool.description}
                    </p>
                    <div className="flex flex-wrap gap-1">
                      {tool.parameters.map((param) => (
                        <Badge
                          key={param.name}
                          variant={param.required ? 'default' : 'secondary'}
                          className="text-xs"
                        >
                          {param.name}: {param.type}
                        </Badge>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Techniques Tab */}
        <TabsContent value="techniques" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Brain className="h-5 w-5" />
                17 Prompt Engineering Techniques
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {PROMPT_TECHNIQUES.map((technique, idx) => (
                  <div
                    key={technique}
                    className="border rounded-lg p-4"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium">{technique}</span>
                      <Badge variant="secondary" className="text-xs">
                        #{idx + 1}
                      </Badge>
                    </div>
                    <Progress
                      value={Math.random() * 100}
                      className="h-1.5"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Used {Math.floor(Math.random() * 100)} times
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Metrics Tab */}
        <TabsContent value="metrics" className="mt-4">
          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Tasks by Category</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-[300px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={tasksByCategoryData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="category" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="tasks" fill="#B76E79" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Technique Usage</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-[300px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <RadarChart data={techniqueData.slice(0, 8)}>
                      <PolarGrid />
                      <PolarAngleAxis dataKey="technique" />
                      <PolarRadiusAxis />
                      <Radar
                        name="Usage"
                        dataKey="usage"
                        stroke="#B76E79"
                        fill="#B76E79"
                        fillOpacity={0.5}
                      />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Execute Tab */}
        <TabsContent value="execute" className="mt-4">
          <TaskExecutor defaultAgent={agent.type} />
        </TabsContent>
      </Tabs>

      {/* Capabilities */}
      <Card>
        <CardHeader>
          <CardTitle>Agent Capabilities</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {agent.capabilities.map((cap) => (
              <Badge key={cap} variant="outline">
                {cap}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Agent Task History */}
      <TaskHistoryPanel
        agentType={agent.type}
        limit={10}
        title={`${agent.name} Task History`}
      />
    </div>
  );
}
