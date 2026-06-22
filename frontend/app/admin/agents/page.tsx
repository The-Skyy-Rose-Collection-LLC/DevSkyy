'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Users,
  Brain,
  Zap,
  ShoppingCart,
  Globe,
  Link,
  Layers,
  Cpu,
  Image,
  FileText,
  Megaphone,
  Bot,
  RefreshCw,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { useAgents } from '@/hooks';
import type { AgentInfo } from '@/lib/api/types';

const CATEGORY_ICONS: Record<string, LucideIcon> = {
  general: Bot,
  infrastructure: Cpu,
  ai: Brain,
  visual: Image,
  web: Globe,
  integration: Link,
  render: Layers,
  core: Cpu,
  automation: Zap,
  ecommerce: ShoppingCart,
  marketing: Megaphone,
  content: FileText,
};

function getCategoryIcon(category: string): LucideIcon {
  return CATEGORY_ICONS[category] ?? Bot;
}

export default function AgentsPage() {
  const { data, loading, error, refresh } = useAgents();
  const [selectedAgent, setSelectedAgent] = useState<AgentInfo | null>(null);
  const [activeTab, setActiveTab] = useState('all');

  const categories = data ? Object.entries(data.agents_by_category) : [];
  const filteredAgents = data
    ? activeTab === 'all'
      ? data.agents
      : data.agents.filter((a) => a.category === activeTab)
    : [];

  if (loading && !data) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white">AI Agents</h1>
            <p className="text-gray-400 mt-1">Loading agents...</p>
          </div>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          {[...Array(3)].map((_, i) => (
            <Card key={i} className="bg-gray-900 border-gray-800 animate-pulse">
              <CardContent className="pt-6">
                <div className="h-12 bg-gray-800 rounded" />
              </CardContent>
            </Card>
          ))}
        </div>
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {[...Array(8)].map((_, i) => (
            <Card key={i} className="bg-gray-900 border-gray-800 animate-pulse">
              <CardContent className="pt-6">
                <div className="h-16 bg-gray-800 rounded" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold text-white">AI Agents</h1>
        <Card className="bg-gray-900 border-red-800">
          <CardContent className="pt-6">
            <p className="text-red-400">Failed to load agents: {error}</p>
            <Button onClick={refresh} className="mt-4" variant="outline">
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">AI Agents</h1>
          <p className="text-gray-400 mt-1">
            Manage {data?.total_agents ?? '...'} AI agents powering DevSkyy
          </p>
        </div>
        <div className="flex items-center gap-4">
          <Badge variant="outline" className="border-green-500 text-green-400">
            {data?.active_agents ?? 0} Active
          </Badge>
          <Button
            size="sm"
            variant="ghost"
            onClick={refresh}
            className="text-gray-400 hover:text-white"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="bg-gray-900 border-gray-800">
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="h-12 w-12 rounded-lg bg-rose-500/10 flex items-center justify-center">
                <Brain className="h-6 w-6 text-rose-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">{data?.total_agents ?? '—'}</p>
                <p className="text-sm text-gray-400">Total Agents</p>
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
                <p className="text-2xl font-bold text-white">{data?.active_agents ?? '—'}</p>
                <p className="text-sm text-gray-400">Active Agents</p>
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
                <p className="text-2xl font-bold text-white">
                  {data ? Object.keys(data.agents_by_category).length : '—'}
                </p>
                <p className="text-sm text-gray-400">Categories</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Category Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="bg-gray-800 flex-wrap h-auto gap-1 p-1">
          <TabsTrigger value="all" className="data-[state=active]:bg-gray-700">
            All ({data?.total_agents ?? 0})
          </TabsTrigger>
          {categories.map(([cat, count]) => (
            <TabsTrigger
              key={cat}
              value={cat}
              className="data-[state=active]:bg-gray-700 capitalize"
            >
              {cat} ({count})
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      {/* Agent Grid — rendered outside TabsContent to avoid N-content pattern for dynamic categories */}
      <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {filteredAgents.map((agent) => {
          const Icon = getCategoryIcon(agent.category);
          const isSelected =
            selectedAgent?.name === agent.name && selectedAgent?.category === agent.category;
          return (
            <Card
              key={`${agent.category}/${agent.name}`}
              className={`bg-gray-900 border-gray-800 cursor-pointer transition-all hover:border-rose-500/50 ${
                isSelected ? 'border-rose-500' : ''
              }`}
              onClick={() => setSelectedAgent(isSelected ? null : agent)}
            >
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 min-w-0">
                    <div className="h-9 w-9 rounded-lg bg-gray-800 flex items-center justify-center shrink-0">
                      <Icon className="h-4 w-4 text-rose-400" />
                    </div>
                    <div className="min-w-0">
                      <CardTitle className="text-sm text-white leading-tight truncate">
                        {agent.name.replace(/_/g, ' ')}
                      </CardTitle>
                      <p className="text-xs text-gray-500 capitalize">{agent.category}</p>
                    </div>
                  </div>
                  <Badge
                    variant="outline"
                    className="border-green-500 text-green-400 text-xs shrink-0"
                  >
                    {agent.status}
                  </Badge>
                </div>
              </CardHeader>
              {agent.capabilities.length > 0 && (
                <CardContent className="pt-0 pb-3">
                  <div className="flex flex-wrap gap-1">
                    {agent.capabilities.slice(0, 2).map((cap) => (
                      <Badge
                        key={cap}
                        variant="secondary"
                        className="bg-gray-800 text-gray-300 text-xs"
                      >
                        {cap}
                      </Badge>
                    ))}
                    {agent.capabilities.length > 2 && (
                      <Badge
                        variant="secondary"
                        className="bg-gray-800 text-gray-300 text-xs"
                      >
                        +{agent.capabilities.length - 2}
                      </Badge>
                    )}
                  </div>
                </CardContent>
              )}
            </Card>
          );
        })}
      </div>

      {/* Agent Detail Panel */}
      {selectedAgent && (
        <Card className="bg-gray-900 border-rose-500/30">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-lg bg-rose-500/10 flex items-center justify-center">
                  {(() => {
                    const Icon = getCategoryIcon(selectedAgent.category);
                    return <Icon className="h-6 w-6 text-rose-400" />;
                  })()}
                </div>
                <div>
                  <CardTitle className="text-white">
                    {selectedAgent.name.replace(/_/g, ' ')}
                  </CardTitle>
                  <CardDescription className="text-gray-400 capitalize">
                    {selectedAgent.category} · v{selectedAgent.version}
                  </CardDescription>
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
                {selectedAgent.capabilities.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {selectedAgent.capabilities.map((cap) => (
                      <Badge key={cap} className="bg-gray-800 text-gray-300">
                        {cap}
                      </Badge>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">No capabilities listed</p>
                )}
              </div>
              <div>
                <h4 className="text-sm font-medium text-gray-400 mb-2">Info</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Status:</span>
                    <span className="text-white capitalize">{selectedAgent.status}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Version:</span>
                    <span className="text-white">{selectedAgent.version}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Category:</span>
                    <span className="text-white capitalize">{selectedAgent.category}</span>
                  </div>
                  {selectedAgent.last_execution && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Last Run:</span>
                      <span className="text-white">{selectedAgent.last_execution}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
