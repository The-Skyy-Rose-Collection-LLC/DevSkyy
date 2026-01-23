'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Users,
  Brain,
  Zap,
  ShoppingCart,
  Palette,
  Box,
  BarChart3,
  Tag,
  Play,
  Pause,
  Settings,
  ChevronRight,
} from 'lucide-react';

interface Agent {
  id: string;
  name: string;
  type: 'super' | 'specialized';
  status: 'active' | 'idle' | 'offline';
  description: string;
  capabilities: string[];
  lastRun?: string;
  runCount: number;
  icon: React.ComponentType<{ className?: string }>;
}

const superAgents: Agent[] = [
  {
    id: 'analytics',
    name: 'Analytics Agent',
    type: 'super',
    status: 'active',
    description: 'Dashboard analytics, metrics aggregation, and reporting',
    capabilities: ['Real-time metrics', 'KPI tracking', 'Report generation', 'Anomaly detection'],
    lastRun: '2 minutes ago',
    runCount: 1247,
    icon: BarChart3,
  },
  {
    id: 'wordpress',
    name: 'WordPress Agent',
    type: 'super',
    status: 'active',
    description: 'WooCommerce sync, product management, and theme deployment',
    capabilities: ['Product sync', 'Media upload', 'Theme generation', 'Order management'],
    lastRun: '5 minutes ago',
    runCount: 892,
    icon: ShoppingCart,
  },
  {
    id: 'creative',
    name: 'Creative Agent',
    type: 'super',
    status: 'idle',
    description: 'Content generation, copywriting, and brand voice maintenance',
    capabilities: ['Product descriptions', 'Blog posts', 'Social media', 'Email campaigns'],
    lastRun: '1 hour ago',
    runCount: 567,
    icon: Palette,
  },
  {
    id: 'tripo',
    name: '3D Generation Agent',
    type: 'super',
    status: 'active',
    description: 'Text-to-3D and image-to-3D model generation with Tripo3D',
    capabilities: ['Text-to-3D', 'Image-to-3D', 'Model optimization', 'AR-ready output'],
    lastRun: '15 minutes ago',
    runCount: 234,
    icon: Box,
  },
  {
    id: 'asset-tagging',
    name: 'Asset Tagging Agent',
    type: 'super',
    status: 'idle',
    description: 'Automatic asset categorization and metadata tagging',
    capabilities: ['Image classification', 'Tag generation', 'Category mapping', 'SEO optimization'],
    lastRun: '30 minutes ago',
    runCount: 1456,
    icon: Tag,
  },
  {
    id: 'operations',
    name: 'Operations Agent',
    type: 'super',
    status: 'active',
    description: 'Business operations, inventory management, and order processing',
    capabilities: ['Inventory sync', 'Order routing', 'Fulfillment', 'Analytics'],
    lastRun: '1 minute ago',
    runCount: 2341,
    icon: Zap,
  },
];

const specializedAgents = [
  'Visual Generation Agent',
  'Collection Content Agent',
  'WordPress Deployment Agent',
  'Conversation Editing Agent',
  'RAG Query Optimizer',
  'Brand Context Manager',
];

export default function AgentsPage() {
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);

  const activeCount = superAgents.filter((a) => a.status === 'active').length;
  const totalRuns = superAgents.reduce((sum, a) => sum + a.runCount, 0);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">AI Agents</h1>
          <p className="text-gray-400 mt-1">Manage 54 AI agents powering DevSkyy</p>
        </div>
        <div className="flex items-center gap-4">
          <Badge variant="outline" className="border-green-500 text-green-400">
            {activeCount} Active
          </Badge>
          <Badge variant="outline" className="border-gray-600 text-gray-400">
            {totalRuns.toLocaleString()} Total Runs
          </Badge>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card className="bg-gray-900 border-gray-800">
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="h-12 w-12 rounded-lg bg-rose-500/10 flex items-center justify-center">
                <Brain className="h-6 w-6 text-rose-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">6</p>
                <p className="text-sm text-gray-400">SuperAgents</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gray-900 border-gray-800">
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="h-12 w-12 rounded-lg bg-blue-500/10 flex items-center justify-center">
                <Users className="h-6 w-6 text-blue-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">48</p>
                <p className="text-sm text-gray-400">Specialized Agents</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gray-900 border-gray-800">
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="h-12 w-12 rounded-lg bg-green-500/10 flex items-center justify-center">
                <Zap className="h-6 w-6 text-green-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">{activeCount}</p>
                <p className="text-sm text-gray-400">Currently Active</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gray-900 border-gray-800">
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="h-12 w-12 rounded-lg bg-purple-500/10 flex items-center justify-center">
                <BarChart3 className="h-6 w-6 text-purple-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">17</p>
                <p className="text-sm text-gray-400">Reasoning Techniques</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="super" className="space-y-4">
        <TabsList className="bg-gray-800">
          <TabsTrigger value="super" className="data-[state=active]:bg-gray-700">
            SuperAgents (6)
          </TabsTrigger>
          <TabsTrigger value="specialized" className="data-[state=active]:bg-gray-700">
            Specialized (48)
          </TabsTrigger>
        </TabsList>

        <TabsContent value="super">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {superAgents.map((agent) => (
              <Card
                key={agent.id}
                className={`bg-gray-900 border-gray-800 cursor-pointer transition-all hover:border-rose-500/50 ${
                  selectedAgent?.id === agent.id ? 'border-rose-500' : ''
                }`}
                onClick={() => setSelectedAgent(agent)}
              >
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="h-10 w-10 rounded-lg bg-gray-800 flex items-center justify-center">
                        <agent.icon className="h-5 w-5 text-rose-400" />
                      </div>
                      <div>
                        <CardTitle className="text-lg text-white">{agent.name}</CardTitle>
                        <CardDescription className="text-gray-500 text-xs">
                          Last run: {agent.lastRun}
                        </CardDescription>
                      </div>
                    </div>
                    <Badge
                      variant="outline"
                      className={
                        agent.status === 'active'
                          ? 'border-green-500 text-green-400'
                          : agent.status === 'idle'
                          ? 'border-yellow-500 text-yellow-400'
                          : 'border-red-500 text-red-400'
                      }
                    >
                      {agent.status}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-400 mb-4">{agent.description}</p>
                  <div className="flex flex-wrap gap-1 mb-4">
                    {agent.capabilities.slice(0, 3).map((cap) => (
                      <Badge key={cap} variant="secondary" className="bg-gray-800 text-gray-300 text-xs">
                        {cap}
                      </Badge>
                    ))}
                    {agent.capabilities.length > 3 && (
                      <Badge variant="secondary" className="bg-gray-800 text-gray-300 text-xs">
                        +{agent.capabilities.length - 3}
                      </Badge>
                    )}
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">
                      {agent.runCount.toLocaleString()} runs
                    </span>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-8 w-8 p-0 text-gray-400 hover:text-white"
                      >
                        <Settings className="h-4 w-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        className={`h-8 w-8 p-0 ${
                          agent.status === 'active' ? 'text-yellow-400' : 'text-green-400'
                        }`}
                      >
                        {agent.status === 'active' ? (
                          <Pause className="h-4 w-4" />
                        ) : (
                          <Play className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="specialized">
          <Card className="bg-gray-900 border-gray-800">
            <CardHeader>
              <CardTitle className="text-white">Specialized Agents</CardTitle>
              <CardDescription className="text-gray-400">
                Task-specific agents for targeted operations
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-2 md:grid-cols-2 lg:grid-cols-3">
                {specializedAgents.map((agent) => (
                  <div
                    key={agent}
                    className="flex items-center justify-between rounded-lg bg-gray-800 p-3"
                  >
                    <span className="text-gray-300">{agent}</span>
                    <ChevronRight className="h-4 w-4 text-gray-500" />
                  </div>
                ))}
                <div className="flex items-center justify-center rounded-lg bg-gray-800/50 border-2 border-dashed border-gray-700 p-3">
                  <span className="text-gray-500">+42 more agents...</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Agent Details Panel */}
      {selectedAgent && (
        <Card className="bg-gray-900 border-gray-800 border-rose-500/30">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-lg bg-rose-500/10 flex items-center justify-center">
                  <selectedAgent.icon className="h-6 w-6 text-rose-400" />
                </div>
                <div>
                  <CardTitle className="text-white">{selectedAgent.name}</CardTitle>
                  <CardDescription className="text-gray-400">Agent Details</CardDescription>
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSelectedAgent(null)}
                className="text-gray-400"
              >
                Close
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid gap-6 md:grid-cols-2">
              <div>
                <h4 className="text-sm font-medium text-gray-400 mb-2">Capabilities</h4>
                <div className="flex flex-wrap gap-2">
                  {selectedAgent.capabilities.map((cap) => (
                    <Badge key={cap} className="bg-gray-800 text-gray-300">
                      {cap}
                    </Badge>
                  ))}
                </div>
              </div>
              <div>
                <h4 className="text-sm font-medium text-gray-400 mb-2">Statistics</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Total Runs:</span>
                    <span className="text-white">{selectedAgent.runCount.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Last Run:</span>
                    <span className="text-white">{selectedAgent.lastRun}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Status:</span>
                    <span className="text-white capitalize">{selectedAgent.status}</span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
